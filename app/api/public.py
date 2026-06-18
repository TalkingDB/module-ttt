from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query

from talkingdb.clients.sqlite import sqlite_conn
from talkingdb.helpers.job import store as job_store
from talkingdb.helpers.namespace import store as namespace_store

from app.api.deps import require_public_namespace
from app.model.namespaces import NamespaceDocumentResponse, NamespaceResponse

router = APIRouter(prefix="/public", tags=["Public"])


@router.get(
    "/namespaces",
    response_model=List[NamespaceResponse],
    summary="List public namespaces",
    description="Fetch a publicly readable namespace without authentication.",
)
async def list_public_namespaces() -> List[NamespaceResponse]:
    with sqlite_conn() as conn:
        items = namespace_store.list_public_namespaces(conn)
    return [NamespaceResponse(**ns) for ns in items]


@router.get(
    "/namespaces/{namespace}/documents",
    response_model=List[NamespaceDocumentResponse],
    summary="List documents in a public namespace",
    description=(
        "List the completed documents in a publicly readable namespace, each with "
        "its curated title, description and suggested queries. No authentication "
        "required."
    ),
)
async def list_public_namespace_documents(
    ns: Dict[str, Any] = Depends(require_public_namespace),
    limit: int = Query(50, ge=1, le=200, description="Max documents to return"),
    offset: int = Query(0, ge=0, description="Number of documents to skip"),
) -> List[NamespaceDocumentResponse]:
    with sqlite_conn() as conn:
        docs = job_store.list_namespace_documents(
            conn, ns["namespace"], limit=limit, offset=offset
        )
    return [NamespaceDocumentResponse(**doc.to_document_payload()) for doc in docs]
