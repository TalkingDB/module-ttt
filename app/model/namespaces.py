from typing import List, Optional

from pydantic import BaseModel, Field


class NamespaceResponse(BaseModel):
    namespace: str = Field(..., description="Stable namespace name")
    title: Optional[str] = Field(None, description="Human-readable title")
    description: Optional[str] = Field(None, description="Short curated description")
    public_read: bool = Field(
        ..., description="Whether this namespace is readable without authentication"
    )


class NamespaceDocumentResponse(BaseModel):
    id: str = Field(..., description="Stable document id (job id)")
    namespace: Optional[str] = Field(
        None, description="Namespace this document belongs to"
    )
    title: Optional[str] = Field(
        None, description="Curated title; falls back to the original filename"
    )
    description: Optional[str] = Field(
        None, description="Short curated description"
    )
    suggested_queries: List[str] = Field(
        default_factory=list,
        description="Curated example queries for this document",
    )
    result_graph_id: Optional[str] = Field(
        None, description="Graph id to query for chat execution"
    )
    state: str = Field(..., description="Document ingestion state (e.g. COMPLETED)")
