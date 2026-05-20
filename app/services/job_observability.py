"""Structured lifecycle logging for ingestion jobs."""

import json
from datetime import datetime
from typing import Optional

from talkingdb.logger.console import logger
from talkingdb.models.job.job import JobModel


def _diff_ms(start_iso: Optional[str], end_iso: Optional[str]) -> Optional[int]:
    """Return the duration between two ISO timestamps in milliseconds."""
    if not start_iso or not end_iso:
        return None

    try:
        start = datetime.fromisoformat(start_iso)
        end = datetime.fromisoformat(end_iso)
    except ValueError:
        return None

    return int((end - start).total_seconds() * 1000)


def emit_lifecycle(job: JobModel, *, rollback_ms: Optional[int] = None) -> None:
    """Emit one structured lifecycle record.

    Called from the single terminal-transition site (``_finalize``) right
    after the state-guarded UPDATE wins, so every record corresponds to
    exactly one real transition.
    """
    record = {
        "event": "job.lifecycle",
        "job_id": job.job_id,
        "state": job.state.value,
        "stage": job.stage.value if job.stage else None,
        "file_size_bytes": job.file_size_bytes,
        "queue_wait_ms": _diff_ms(job.created_at, job.started_at),
        "processing_ms": _diff_ms(job.started_at, job.completed_at),
        "rollback_ms": rollback_ms,
        "error_code": job.error_code.value if job.error_code else None,
        "idempotency_key": job.idempotency_key,
        "user_id": job.user_id,
        "filename": job.filename,
    }

    logger.info(json.dumps(record, default=str))
