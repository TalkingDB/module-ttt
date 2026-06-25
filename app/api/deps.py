from typing import Any, Dict

from fastapi import HTTPException, Path, status

from talkingdb.clients.sqlite import sqlite_conn
from talkingdb.helpers.namespace import store as namespace_store


def require_public_namespace(
    namespace: str = Path(..., description="Namespace name"),
) -> Dict[str, Any]:
    """Gate a route to publicly readable namespaces only."""
    with sqlite_conn() as conn:
        ns = namespace_store.get_namespace(conn, namespace)
    if ns is None or not ns["public_read"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "NAMESPACE_NOT_FOUND",
                "message": f"Unknown or non-public namespace: {namespace}",
            },
        )
    return ns
