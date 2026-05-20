"""Async document-ingestion runtime."""

import asyncio
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Optional, Tuple

from starlette.datastructures import UploadFile

from talkingdb.clients.sqlite import sqlite_conn
from talkingdb.helpers import spool
from talkingdb.helpers.client import config as ce_config
from talkingdb.helpers.graph import rollback_graph
from talkingdb.logger.console import logger
from talkingdb.models.document.document import DocumentModel
from talkingdb.models.document.elements.primitive.table import TableModel
from talkingdb.models.document.indexes.index import FileIndexModel
from talkingdb.models.job import store as job_store
from talkingdb.models.job.error import JobErrorCode
from talkingdb.models.job.stage import JobStage
from talkingdb.models.job.state import JobState
from talkingdb.models.metadata.metadata import Metadata
from talkingdb_ce.client import CEClient

from app.core import config
from app.services.job_context import JobCancelled, JobContext, JobTimeout
from app.services.job_observability import emit_lifecycle


# ----------------------------------------------------------------- admission
class QueueFull(Exception):
    """Raised when the bounded admission queue is full."""


_executor = ThreadPoolExecutor(
    max_workers=config.MAX_WORKERS,
    thread_name_prefix="tdb-job",
)
_admission_lock = threading.Lock()
_in_flight = 0


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def acquire_slot() -> None:
    """Reserve one bounded admission slot."""
    global _in_flight
    with _admission_lock:
        if _in_flight >= config.QUEUE_CAPACITY:
            raise QueueFull()
        _in_flight += 1


def release_slot() -> None:
    """Release a slot previously held by :func:`acquire_slot`.

    Idempotently safe to call on the same code path that raised after
    acquisition - we floor at zero.
    """
    global _in_flight
    with _admission_lock:
        if _in_flight > 0:
            _in_flight -= 1


def enqueue_reserved(
    *,
    job_id: str,
    temp_path: str,
    filename: str,
    metadata_json: str,
) -> None:
    """Submit work whose slot has already been reserved.

    The wrapper guarantees the slot is released exactly once, regardless of
    how the job ends.
    """
    _executor.submit(
        _run_after_reservation, job_id, temp_path, filename, metadata_json
    )


def _run_after_reservation(
    job_id: str, temp_path: str, filename: str, metadata_json: str
) -> None:
    """Run a reserved job and always release its slot."""
    try:
        run_job(job_id, temp_path, filename, metadata_json)
    finally:
        release_slot()


# ---------------------------------------------------------------------- run
def run_job(
    job_id: str, temp_path: str, filename: str, metadata_json: str
) -> None:
    """Execute one ingestion job to a terminal state."""
    if not _transition_to_ongoing(job_id):
        spool.discard(temp_path)
        return

    ctx = JobContext(job_id=job_id)
    graph_id: Optional[str] = None
    result_summary = None

    try:
        ctx.set_stage(JobStage.PARSING, status_message="Parsing document")
        parse_result = _parse(temp_path, filename, metadata_json)

        ctx.checkpoint(status_message="Parsed; preparing to index")

        ctx.set_stage(
            JobStage.ELEMENT_EXTRACTION,
            status_message="Reading document structure",
        )
        from app.services.indexer import IndexerService

        indexer = IndexerService()
        graph_id = indexer.gm.graph_id

        with sqlite_conn() as conn:
            job_store.set_result_graph_id(conn, job_id, graph_id)

        ctx.set_stage(
            JobStage.TREE_GENERATION,
            status_message="Building document tree",
        )
        indexer.graph_file_index(FileIndexModel(**parse_result["file_index"]))

        ctx.set_stage(JobStage.INDEXING, status_message="Indexing document elements")
        document = DocumentModel.from_dict(parse_result["document"])

        def _on_progress(done: int, total: int) -> None:
            """Forward progress updates through the job context."""
            ctx.checkpoint(
                done_units=done,
                total_units=total,
                status_message=f"Indexing elements ({done}/{total})",
            )

        indexer.index_document(document, progress=_on_progress)

        ctx.set_stage(JobStage.PERSISTING, status_message="Saving graph")

        result_summary = _build_result_summary(document, ctx)

        _finalize(
            job_id,
            JobState.COMPLETED,
            graph_id=graph_id,
            temp_path=temp_path,
            result_summary=result_summary,
            status_message="Document indexed",
        )

    except JobCancelled:
        _finalize(
            job_id,
            JobState.CANCELLED,
            graph_id=graph_id,
            temp_path=temp_path,
            status_message="Upload cancelled, cleaned up",
        )
    except JobTimeout:
        _finalize(
            job_id,
            JobState.FAILED,
            graph_id=graph_id,
            temp_path=temp_path,
            error_code=JobErrorCode.TIMEOUT,
            error_message=(
                f"exceeded MAX_JOB_DURATION_SECONDS="
                f"{config.MAX_JOB_DURATION_SECONDS}"
            ),
            status_message="Upload timed out",
        )
    except BaseException as exc:
        error_code, error_message = _classify(exc)
        logger.exception(
            f"[job {job_id}] failed: {error_code.value}: {error_message}"
        )
        _finalize(
            job_id,
            JobState.FAILED,
            graph_id=graph_id,
            temp_path=temp_path,
            error_code=error_code,
            error_message=error_message,
            status_message="Upload failed",
        )


# ------------------------------------------------------------- pipeline steps
def _transition_to_ongoing(job_id: str) -> bool:
    with sqlite_conn() as conn:
        return job_store.mark_ongoing(conn, job_id, _now_iso())


def _parse(temp_path: str, filename: str, metadata_json: str) -> dict:
    """Parse a spooled document using CEClient."""
    metadata = Metadata.ensure_metadata(Metadata.from_json(metadata_json))
    client = CEClient(ce_config)
    with open(temp_path, "rb") as fh:
        upload = UploadFile(filename=filename, file=fh)
        return asyncio.run(client.parse_file(file=upload, metadata=metadata))


def _build_result_summary(document: DocumentModel, ctx: JobContext) -> dict:
    elements_total = 0
    tables = 0
    for element in document.iter_elements():
        elements_total += 1
        if isinstance(element, TableModel):
            tables += 1
    return {
        "elements": elements_total,
        "tables": tables,
        "duration_ms": int(ctx.elapsed_seconds() * 1000),
    }


# ------------------------------------------------------------- classification
def _classify(exc: BaseException) -> Tuple[JobErrorCode, str]:
    """Map an exception to a job error code and message."""
    name = type(exc).__name__
    detail = f"{name}: {exc}" if str(exc) else name

    if isinstance(exc, ValueError):
        return JobErrorCode.VALIDATION_ERROR, detail
    if isinstance(exc, sqlite3.OperationalError):
        return JobErrorCode.PERSIST_ERROR, detail

    origin = repr(exc) + " " + (exc.__class__.__module__ or "")
    if any(m in origin for m in ("docx", "talkingdb_ce", "reader")):
        return JobErrorCode.PARSE_ERROR, detail

    return JobErrorCode.INTERNAL_ERROR, detail


# ------------------------------------------------------------------ finalize
def _finalize(
    job_id: str,
    terminal_state: JobState,
    *,
    graph_id: Optional[str],
    temp_path: Optional[str],
    result_summary: Optional[dict] = None,
    error_code: Optional[JobErrorCode] = None,
    error_message: Optional[str] = None,
    status_message: Optional[str] = None,
) -> None:
    """Run cleanup and apply the terminal job transition."""
    rollback_ms: Optional[int] = None
    if terminal_state != JobState.COMPLETED:
        rollback_start = time.monotonic()
        rollback_graph(graph_id)
        rollback_ms = int((time.monotonic() - rollback_start) * 1000)

    spool.discard(temp_path)

    with sqlite_conn() as conn:
        won = job_store.finalize(
            conn,
            job_id,
            terminal_state,
            result_graph_id=graph_id if terminal_state == JobState.COMPLETED else None,
            result_summary=result_summary,
            error_code=error_code,
            error_message=error_message,
            status_message=status_message,
        )
        if won:
            terminal_job = job_store.get(conn, job_id)
            if terminal_job is not None:
                emit_lifecycle(terminal_job, rollback_ms=rollback_ms)

    if not won:
        logger.info(
            f"[job {job_id}] finalize lost the race; "
            f"current row already terminal"
        )


def finalize_externally(
    job_id: str,
    terminal_state: JobState,
    *,
    graph_id: Optional[str],
    temp_path: Optional[str],
    error_code: Optional[JobErrorCode] = None,
    error_message: Optional[str] = None,
    status_message: Optional[str] = None,
) -> None:
    """Public entry point the lifecycle daemon calls on orphans / timeouts.

    Identical semantics to the worker's internal finalize - same load-bearing
    ordering, same state-guarded UPDATE. Exposed so the daemon does not have
    to duplicate the cleanup choreography.
    """
    _finalize(
        job_id,
        terminal_state,
        graph_id=graph_id,
        temp_path=temp_path,
        error_code=error_code,
        error_message=error_message,
        status_message=status_message,
    )
