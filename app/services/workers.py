
from talkingdb.models.graph.graph import GraphModel
from talkingdb.models.auth.user import UserModel
from talkingdb.models.auth.api_key import APIKeyModel
from talkingdb.helpers.job import store as job_store
from talkingdb.helpers.namespace import store as namespace_store
from talkingdb.clients.sqlite import sqlite_conn

from app.services import job_daemon


def init_database():
    with sqlite_conn() as conn:
        GraphModel.init_db(conn)
        UserModel.init_db(conn)
        APIKeyModel.init_db(conn)
        job_store.init_db(conn)
        namespace_store.init_db(conn)
        namespace_store.ensure_reserved(conn)
    print("Database initialized.")


def start_workers():
    init_database()
    job_daemon.start()
    print("Workers started.")
