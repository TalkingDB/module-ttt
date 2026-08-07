"""Unit tests for the Pydantic models in app.model.jobs and app.model.namespaces.

These models have no I/O — validation and serialization are exercised
directly through pydantic, no app/DB/MinIO startup required.
"""

import pytest
from pydantic import ValidationError

from app.model.jobs import JobAcceptedResponse, JobStatusResponse
from app.model.namespaces import NamespaceDocumentResponse, NamespaceResponse


class TestJobAcceptedResponse:
    def test_valid_payload(self):
        job = JobAcceptedResponse(
            job_id="job-1", job_type="document", session_id="sess-1", state="QUEUED"
        )
        assert job.job_id == "job-1"
        assert job.state == "QUEUED"

    def test_session_id_optional(self):
        job = JobAcceptedResponse(job_id="job-1", job_type="document", state="QUEUED")
        assert job.session_id is None

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            JobAcceptedResponse(job_type="document", state="QUEUED")


class TestJobStatusResponse:
    def _base_kwargs(self, **overrides):
        kwargs = dict(job_id="job-1", job_type="document", state="ONGOING")
        kwargs.update(overrides)
        return kwargs

    def test_minimal_valid_payload(self):
        job = JobStatusResponse(**self._base_kwargs())
        assert job.job_id == "job-1"
        assert job.state == "ONGOING"
        assert job.stage is None
        assert job.error_code is None

    def test_full_payload_round_trips(self):
        job = JobStatusResponse(
            **self._base_kwargs(
                state="COMPLETED",
                stage=None,
                progress=100,
                result_graph_id="graph-1",
                file_name="report.pdf",
                file_size=2048,
                result_summary={"elements": 42},
            )
        )
        dumped = job.model_dump()
        assert dumped["result_graph_id"] == "graph-1"
        assert dumped["file_size"] == 2048
        assert dumped["result_summary"] == {"elements": 42}

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            JobStatusResponse(job_type="document", state="FAILED")

    def test_error_fields_optional(self):
        job = JobStatusResponse(**self._base_kwargs(state="FAILED"))
        assert job.error_code is None
        assert job.error_message is None


class TestNamespaceResponse:
    def test_valid_payload(self):
        ns = NamespaceResponse(namespace="public", public_read=True)
        assert ns.namespace == "public"
        assert ns.title is None

    def test_missing_required_public_read_raises(self):
        with pytest.raises(ValidationError):
            NamespaceResponse(namespace="public")


class TestNamespaceDocumentResponse:
    def test_defaults_suggested_queries_to_empty_list(self):
        doc = NamespaceDocumentResponse(id="doc-1", state="COMPLETED")
        assert doc.suggested_queries == []

    def test_full_payload(self):
        doc = NamespaceDocumentResponse(
            id="doc-1",
            namespace="public",
            title="Annual Report",
            suggested_queries=["What was revenue?"],
            state="COMPLETED",
        )
        assert doc.title == "Annual Report"
        assert doc.suggested_queries == ["What was revenue?"]

    def test_missing_required_id_raises(self):
        with pytest.raises(ValidationError):
            NamespaceDocumentResponse(state="COMPLETED")
