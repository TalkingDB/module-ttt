"""Unit tests for the Pydantic models in app.model.projects."""

import pytest
from pydantic import ValidationError

from app.model.jobs import JobStatusResponse
from app.model.projects import (
    ProjectCreateRequest,
    ProjectResponse,
    ProjectTreeItem,
    ProjectTreeResponse,
)


class TestProjectCreateRequest:
    def test_valid_payload(self):
        req = ProjectCreateRequest(name="My Project", logo="data:image/png;base64,abc")
        assert req.name == "My Project"

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            ProjectCreateRequest(logo="data:image/png;base64,abc")

    def test_missing_logo_raises(self):
        with pytest.raises(ValidationError):
            ProjectCreateRequest(name="My Project")


class TestProjectResponse:
    def test_valid_payload(self):
        proj = ProjectResponse(
            project_id="p1",
            name="My Project",
            document_count=0,
            created_at="2026-01-01T00:00:00Z",
        )
        assert proj.logo_url is None
        assert proj.last_interaction_at is None

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            ProjectResponse(project_id="p1", name="My Project")


class TestProjectTreeItem:
    def test_defaults_documents_to_empty_list(self):
        item = ProjectTreeItem(
            project_id="p1",
            name="My Project",
            document_count=0,
            created_at="2026-01-01T00:00:00Z",
        )
        assert item.documents == []

    def test_nested_documents(self):
        job = JobStatusResponse(job_id="j1", job_type="document", state="COMPLETED")
        item = ProjectTreeItem(
            project_id="p1",
            name="My Project",
            document_count=1,
            created_at="2026-01-01T00:00:00Z",
            documents=[job],
        )
        assert item.documents[0].job_id == "j1"


class TestProjectTreeResponse:
    def test_defaults_are_empty_lists(self):
        tree = ProjectTreeResponse()
        assert tree.documents == []
        assert tree.projects == []

    def test_with_root_documents_and_nested_projects(self):
        job = JobStatusResponse(job_id="j1", job_type="document", state="QUEUED")
        proj = ProjectTreeItem(
            project_id="p1",
            name="My Project",
            document_count=0,
            created_at="2026-01-01T00:00:00Z",
        )
        tree = ProjectTreeResponse(documents=[job], projects=[proj])
        assert len(tree.documents) == 1
        assert len(tree.projects) == 1
