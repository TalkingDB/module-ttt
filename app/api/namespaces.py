from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from talkingdb.clients.sqlite import sqlite_conn
from talkingdb.helpers.auth import verify_api_key
from talkingdb.helpers.job import store as job_store
from talkingdb.helpers.namespace import store as namespace_store
from talkingdb.models.api.response import ErrorResponse

from app.model.namespaces import NamespaceDocumentResponse, NamespaceResponse

router = APIRouter(prefix="/v1", tags=["Namespaces"])


@router.get(
    "/namespaces",
    response_model=List[NamespaceResponse],
    summary="List namespaces",
    description="List all namespaces and their public/private flag.",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or missing API key"},
    },
)
async def list_namespaces(
    api_key: str = Depends(verify_api_key),
) -> List[NamespaceResponse]:
    with sqlite_conn() as conn:
        items = namespace_store.list_namespaces(conn)
    return [NamespaceResponse(**ns) for ns in items]


@router.get(
    "/namespaces/{namespace}/documents",
    response_model=List[NamespaceDocumentResponse],
    summary="List documents in a namespace",
    description=(
        "List documents within a namespace. By default returns documents in any "
        "state; set ``completed_only=true`` for only ready-to-use documents."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or missing API key"},
        404: {"model": ErrorResponse, "description": "Unknown namespace"},
    },
)
async def list_namespace_documents(
    namespace: str = Path(..., description="Namespace name"),
    limit: int = Query(50, ge=1, le=500, description="Max documents to return"),
    offset: int = Query(0, ge=0, description="Number of documents to skip"),
    completed_only: bool = Query(
        False, description="Only return COMPLETED documents"
    ),
    api_key: str = Depends(verify_api_key),
) -> List[NamespaceDocumentResponse]:
    with sqlite_conn() as conn:
        if namespace_store.get_namespace(conn, namespace) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "NAMESPACE_NOT_FOUND",
                    "message": f"Unknown namespace: {namespace}",
                },
            )
        docs = job_store.list_namespace_documents(
            conn,
            namespace,
            limit=limit,
            offset=offset,
            completed_only=completed_only,
        )
    return [NamespaceDocumentResponse(**doc.to_document_payload()) for doc in docs]
