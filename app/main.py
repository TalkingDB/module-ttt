from fastapi import FastAPI, Request
from app.api import root, index, documents, queries
from app.services import job_daemon
from app.services.workers import init_database
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    job_daemon.start()
    yield
    job_daemon.stop()


app = FastAPI(lifespan=lifespan, title="Module TalkingDB")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


_DEPRECATED_ROUTES: dict[tuple[str, str], str] = {
    ("POST", "/v1/documents"): "/v1/documents/jobs",
}


@app.middleware("http")
async def deprecation_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    successor = _DEPRECATED_ROUTES.get((request.method, request.url.path))
    if successor is not None:
        response.headers["Deprecation"] = "true"
        response.headers["Link"] = f'<{successor}>; rel="successor-version"'
    return response

app.include_router(root.router)
app.include_router(documents.router)
app.include_router(queries.router)
app.include_router(index.router)
