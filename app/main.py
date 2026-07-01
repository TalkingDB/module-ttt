from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import root, index, documents, jobs, queries, namespaces, public, tree, auth
from app.services import job_daemon
from app.services.workers import init_database


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

app.include_router(root.router)
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(namespaces.router)
app.include_router(jobs.router)
app.include_router(queries.router)
app.include_router(tree.router)
app.include_router(index.router)
app.include_router(public.router)
