"""Sessions and conversation history API.

Endpoints
---------
POST   /v1/sessions                        — create a session
POST   /v1/sessions/{session_id}/messages  — append a chat turn
GET    /v1/history                         — list all sessions for the caller
GET    /v1/history/{session_id}            — full Q&A + documents for one session

All four routes are guarded by API key (Bearer token from /auth/api-keys),
matching the auth pattern used by POST /v1/documents.
The caller can only see and write to their own sessions.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from talkingdb.clients.sqlite import sqlite_conn
from talkingdb.helpers.job import store as job_store
from talkingdb.helpers.auth import verify_api_key
from talkingdb.helpers.session import store as session_store
from talkingdb.models.api.response import ErrorResponse

from app.model.sessions import (
    DocumentSummary,
    MessageCreateRequest,
    MessageResponse,
    SessionCreateRequest,
    SessionDetailResponse,
    SessionResponse,
    SessionSummary,
)

router = APIRouter(tags=["History"])

_PREVIEW_MAX = 120  # characters to truncate the first-message preview to


# ------------------------------------------------------------------ helpers

def _require_owned_session(
    session_id: str,
    user_email: str,
    conn,
) -> dict:
    """Return the session dict or raise 404 — also enforces ownership."""
    session = session_store.get_session(conn, session_id)
    if session is None or session["user_email"] != user_email.lower():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "SESSION_NOT_FOUND",
                "message": f"Session not found: {session_id}",
            },
        )
    return session


def _job_to_doc_summary(job) -> DocumentSummary:
    return DocumentSummary(
        job_id=job.job_id,
        filename=job.filename,
        file_size=job.file_size_bytes,
        state=job.state.value,
        result_graph_id=job.result_graph_id,
        created_at=job.created_at,
    )


# ------------------------------------------------------------------ write endpoints

@router.post(
    "/v1/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new session",
    description=(
        "Create a conversation session before (or alongside) uploading documents. "
        "The returned ``session_id`` is passed as the ``session_id`` form field "
        "when calling ``POST /v1/documents``."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or missing API key"},
    },
)
async def create_session(
    payload: SessionCreateRequest,
    user_email: str = Depends(verify_api_key),
) -> SessionResponse:
    with sqlite_conn() as conn:
        session = session_store.create_session(
            conn,
            user_email,
            title=payload.title,
            session_id=payload.session_id,
        )
    return SessionResponse(
        session_id=session["session_id"],
        title=session["title"],
        created_at=session["created_at"],
    )


@router.post(
    "/v1/sessions/{session_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Append a chat message to a session",
    description=(
        "Persist one Q&A turn (role = 'user' or 'assistant'). "
        "Call this once for the user question and once for the assistant answer."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or missing API key"},
        404: {"model": ErrorResponse, "description": "Session not found"},
        422: {"model": ErrorResponse, "description": "Invalid role or empty content"},
    },
)
async def add_message(
    payload: MessageCreateRequest,
    session_id: str = Path(..., description="Target session id"),
    user_email: str = Depends(verify_api_key),
) -> MessageResponse:
    try:
        with sqlite_conn() as conn:
            _require_owned_session(session_id, user_email, conn)
            msg = session_store.add_message(
                conn,
                session_id=session_id,
                role=payload.role,
                content=payload.content,
            )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": "INVALID_ROLE", "message": str(exc)},
        )
    return MessageResponse(**msg)


# ------------------------------------------------------------------ history: list

@router.get(
    "/v1/history",
    response_model=List[SessionSummary],
    summary="List all sessions for the current user",
    description=(
        "Returns a list of conversation sessions owned by the caller, "
        "ordered by creation time newest-first. Each entry includes a preview "
        "of the first message and counts of Q&A turns and uploaded documents."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or missing API key"},
    },
)
async def list_history(
    limit: int = Query(50, ge=1, le=200, description="Max sessions to return"),
    user_email: str = Depends(verify_api_key),
) -> List[SessionSummary]:
    with sqlite_conn() as conn:
        sessions = session_store.list_sessions(conn, user_email, limit=limit)

        summaries: List[SessionSummary] = []
        for s in sessions:
            sid = s["session_id"]

            msg_count = session_store.count_messages(conn, sid)
            first_msg = session_store.get_first_message(conn, sid)

            doc_jobs = job_store.list_documents(conn, sid, limit=1000)
            doc_count = len(doc_jobs)

            preview: Optional[str] = None
            first_role: Optional[str] = None
            if first_msg:
                preview = first_msg["content"][:_PREVIEW_MAX]
                if len(first_msg["content"]) > _PREVIEW_MAX:
                    preview += "…"
                first_role = first_msg["role"]

            summaries.append(
                SessionSummary(
                    session_id=sid,
                    title=s["title"],
                    created_at=s["created_at"],
                    message_count=msg_count,
                    document_count=doc_count,
                    first_message_preview=preview,
                    first_message_role=first_role,
                )
            )

    return summaries


# ------------------------------------------------------------------ history: detail

@router.get(
    "/v1/history/{session_id}",
    response_model=SessionDetailResponse,
    summary="Get full Q&A and documents for a single session",
    description=(
        "Returns the complete conversation history (all Q&A turns, oldest-first) "
        "and every document uploaded in this session (newest-first). "
        "The session must belong to the authenticated user."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or missing API key"},
        404: {"model": ErrorResponse, "description": "Session not found or not yours"},
    },
)
async def get_session_detail(
    session_id: str = Path(..., description="Session id to retrieve"),
    user_email: str = Depends(verify_api_key),
) -> SessionDetailResponse:
    with sqlite_conn() as conn:
        session = _require_owned_session(session_id, user_email, conn)
        messages = session_store.list_messages(conn, session_id)
        doc_jobs = job_store.list_documents(conn, session_id, limit=500)

    return SessionDetailResponse(
        session_id=session["session_id"],
        title=session["title"],
        created_at=session["created_at"],
        messages=[MessageResponse(**m) for m in messages],
        documents=[_job_to_doc_summary(j) for j in doc_jobs],
    )
