"""Smoke tests for app.api.root.

These call the route handler directly rather than going through
TestClient(app), because the app's lifespan (init_database + MinIO
bucket + job_daemon) requires live infrastructure that isn't
available in a plain CI runner. Once test fixtures for a disposable
sqlite DB / mocked object storage exist, this can move to a real
TestClient-based integration test.
"""

from app.api import root


def test_get_org_returns_welcome_message():
    result = root.get_org()
    assert result == "Welcome to Module TalkingDB!"


def test_root_router_registers_root_route():
    paths = {route.path for route in root.router.routes}
    assert "/" in paths
