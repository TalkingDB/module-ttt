import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    Path,
    Response,
    UploadFile,
    status,
)

from talkingdb.clients.sqlite import sqlite_conn
from talkingdb.helpers import spool
from talkingdb.helpers.auth import verify_api_key
from talkingdb.helpers.client import config
from talkingdb.helpers.validation import validate_file_type, validate_file_size
from talkingdb.models.api.response import ErrorResponse
from talkingdb.models.document.document import DocumentModel
from talkingdb.models.document.indexes.index import FileIndexModel
from talkingdb.models.job import store as job_store
from talkingdb.models.job.job import JobModel
from talkingdb.models.metadata.metadata import DEFAULT_METADATA, Metadata
from talkingdb_ce.client import CEClient

from app.core import config as job_config
from app.model.documents import DocumentUploadResponse
from app.model.jobs import JobAcceptedResponse, JobStatusResponse
from app.services import jobs
from app.services.indexer import IndexerService

router = APIRouter(prefix="/v1", tags=["Documents"])


@router.post(
    "/documents",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    deprecated=True,
    summary="[DEPRECATED] Upload and index a document synchronously",
    description=(
        "**Deprecated.** Use the asynchronous ingestion-job endpoints instead:\n\n"
        "  * `POST /v1/documents/jobs` to submit (returns a job_id immediately)\n"
        "  * `GET  /v1/documents/jobs/{job_id}` to poll progress\n"
        "  * `POST /v1/documents/jobs/{job_id}/cancel` to cancel\n\n"
        "This endpoint blocks until parsing + indexing complete (seconds to "
        "minutes) and offers no progress reporting or cancellation. It is kept "
        "for backwards compatibility and will be removed in a future release.\n\n"
        "Upload a document file to be parsed, indexed, and stored as a graph "
        "structure. Currently supports .docx files. Returns the graph ID and "
        "processing metadata."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or missing API key"},
        413: {"model": ErrorResponse, "description": "File exceeds maximum allowed size"},
        415: {"model": ErrorResponse, "description": "Unsupported file type"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal processing error"},
    },
)
async def upload_document(
    file: UploadFile = File(..., description="The document file to upload (.docx)"),
    metadata: Optional[str] = Form(DEFAULT_METADATA, description="JSON metadata string"),
    api_key: str = Depends(verify_api_key),
):
    ext = validate_file_type(file)
    file_size = await validate_file_size(file)

    _metadata = Metadata.from_json(metadata)
    _metadata = Metadata.ensure_metadata(_metadata)

    start = time.time()
    try:
        client = CEClient(config)
        result = await client.parse_file(file=file, metadata=_metadata)

        indexer = IndexerService()
        indexer.graph_file_index(FileIndexModel(**result["file_index"]))
        index = indexer.index_document(DocumentModel.from_dict(result["document"]))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "PROCESSING_ERROR",
                "message": str(e),
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "PROCESSING_ERROR",
                "message": f"Failed to process document: {type(e).__name__}",
            },
        )

    processing_time_ms = int((time.time() - start) * 1000)

    return DocumentUploadResponse(
        graph_id=index.graph_id,
        filename=file.filename,
        file_type=ext,
        file_size_bytes=file_size,
        processing_time_ms=processing_time_ms,
        created_at=datetime.now(timezone.utc),
    )


@router.post(
    "/documents/jobs",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a document for asynchronous indexing",
    description=(
        "Upload a document for asynchronous indexing. "
        "Returns immediately with a stable job identifier "
        "that can be used for polling and cancellation."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or missing API key"},
        413: {"model": ErrorResponse, "description": "File exceeds maximum allowed size"},
        415: {"model": ErrorResponse, "description": "Unsupported file type"},
        429: {"model": ErrorResponse, "description": "Worker queue is full"},
        503: {"model": ErrorResponse, "description": "Spool storage exhausted"},
    },
)
async def submit_document_job(
    file: UploadFile = File(..., description="The document file to upload (.docx)"),
    metadata: Optional[str] = Form(DEFAULT_METADATA, description="JSON metadata string"),
    idempotency_key: str = Header(
        ..., alias="Idempotency-Key",
        description="Per-upload UUID; same key returns the same job until retention purge",
    ),
    user_id: Optional[str] = Header(None, alias="X-User-Id"),
    session_id: Optional[str] = Header(None, alias="X-Session-Id"),
    api_key: str = Depends(verify_api_key),
) -> JobAcceptedResponse:
    """Submit a document ingestion job for background processing."""
    validate_file_type(file)

    with sqlite_conn() as conn:
        existing = job_store.find_by_idempotency_key(conn, idempotency_key)
    if existing is not None:
        return JobAcceptedResponse(
            job_id=existing.job_id, state=existing.state.value
        )

    spool.assert_spool_capacity()

    try:
        jobs.acquire_slot()
    except jobs.QueueFull:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "QUEUE_FULL",
                "error_code": "QUEUE_FULL",
                "message": "Ingestion worker pool is at capacity",
                "retry_after_seconds": job_config.RETRY_AFTER_SECONDS,
            },
            headers={"Retry-After": str(job_config.RETRY_AFTER_SECONDS)},
        )

    temp_path: Optional[str] = None
    enqueued = False
    try:
        temp_path, size_bytes = await spool.spool_upload(file)

        metadata_json = metadata if metadata else DEFAULT_METADATA

        job = JobModel.new(
            filename=file.filename,
            idempotency_key=idempotency_key,
            user_id=user_id,
            session_id=session_id,
        )
        job.file_size_bytes = size_bytes
        job.temp_path = temp_path

        with sqlite_conn() as conn:
            job_store.insert(conn, job)

        jobs.enqueue_reserved(
            job_id=job.job_id,
            temp_path=temp_path,
            filename=file.filename or "upload.docx",
            metadata_json=metadata_json,
        )
        enqueued = True

        return JobAcceptedResponse(job_id=job.job_id, state=job.state.value)

    finally:
        if not enqueued:
            spool.discard(temp_path)
            jobs.release_slot()


def _no_store(response: Response) -> None:
    """Prevent proxies / browsers / gateways from caching job status."""
    response.headers["Cache-Control"] = "no-store"


def _job_or_404(job_id: str) -> JobModel:
    """Return a persisted job or raise HTTP 404."""
    with sqlite_conn() as conn:
        job = job_store.get(conn, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "JOB_NOT_FOUND",
                "message": f"Unknown job id: {job_id}",
            },
        )
    return job


@router.get(
    "/documents/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get current status of an ingestion job",
    description=(
        "Return the current lifecycle state and progress of a job."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or missing API key"},
        404: {"model": ErrorResponse, "description": "Unknown job id"},
    },
)
async def get_job_status(
    response: Response,
    job_id: str = Path(..., description="Stable job identifier"),
    api_key: str = Depends(verify_api_key),
) -> JobStatusResponse:
    """Fetch the latest persisted state for a job."""
    _no_store(response)
    job = _job_or_404(job_id)
    return JobStatusResponse(**job.to_status_payload())


@router.post(
    "/documents/jobs/{job_id}/cancel",
    response_model=JobStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request cancellation of an ingestion job",
    description=(
        "Request cooperative cancellation of a running job."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or missing API key"},
        404: {"model": ErrorResponse, "description": "Unknown job id"},
    },
)
async def cancel_job(
    response: Response,
    job_id: str = Path(..., description="Stable job identifier"),
    api_key: str = Depends(verify_api_key),
) -> JobStatusResponse:
    """Request cancellation for a queued or running job."""
    _no_store(response)
    _job_or_404(job_id)
    with sqlite_conn() as conn:
        updated = job_store.request_cancel(conn, job_id)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="vanished")
    return JobStatusResponse(**updated.to_status_payload())
