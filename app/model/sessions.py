"""Pydantic request/response models for the sessions and history endpoints."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ------------------------------------------------------------------ sessions

class SessionCreateRequest(BaseModel):
    title: Optional[str] = Field(None, description="Human-readable label for the session")
    session_id: Optional[str] = Field(
        None,
        description=(
            "Optional client-supplied session id. "
            "If omitted, one is generated. "
            "Useful when the client uploads a document and a session simultaneously."
        ),
    )


class SessionResponse(BaseModel):
    session_id: str
    title: Optional[str]
    created_at: str


# ------------------------------------------------------------------ messages

class MessageCreateRequest(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., min_length=1, description="The message text")


class MessageResponse(BaseModel):
    message_id: str
    session_id: str
    role: str
    content: str
    created_at: str


# ------------------------------------------------------------------ history list

class SessionSummary(BaseModel):
    """One row in the history list — lightweight preview."""

    session_id: str
    title: Optional[str]
    created_at: str
    message_count: int = Field(..., description="Total Q&A turns in the session")
    document_count: int = Field(..., description="Documents uploaded in this session")
    first_message_preview: Optional[str] = Field(
        None,
        description="Truncated content of the first message in the session (max 120 chars)",
    )
    first_message_role: Optional[str] = Field(
        None, description="Role of the first message ('user' or 'assistant')"
    )


# ------------------------------------------------------------------ history detail

class DocumentSummary(BaseModel):
    """Slim document entry shown inside a session detail view."""

    job_id: str
    filename: Optional[str]
    file_size: Optional[int]
    state: str
    result_graph_id: Optional[str]
    created_at: str


class SessionDetailResponse(BaseModel):
    """Full session view: metadata + ordered Q&A + linked documents."""

    session_id: str
    title: Optional[str]
    created_at: str
    messages: List[MessageResponse] = Field(
        ..., description="All Q&A turns, oldest-first"
    )
    documents: List[DocumentSummary] = Field(
        ..., description="Documents uploaded in this session, newest-first"
    )