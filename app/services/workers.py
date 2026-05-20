
from talkingdb.models.graph.graph import GraphModel
from talkingdb.models.job import store as job_store
from talkingdb.clients.sqlite import sqlite_conn

from app.services import job_daemon


def init_database():
    with sqlite_conn() as conn:
        GraphModel.init_db(conn)
        job_store.init_db(conn)
    print("Database initialized.")


def start_workers():
    init_database()
    job_daemon.start()
    print("Workers started.")
