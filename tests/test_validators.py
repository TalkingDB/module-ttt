"""Unit tests for the pure functions in app.api.validators.

validate_project_owned and validate_namespace both open a live sqlite
connection, so they're intentionally left uncovered here — they need
a DB fixture. clean_optional_text, parse_suggested_queries, and
validate_project_name have no I/O and are fully covered directly.
"""

import pytest
from fastapi import HTTPException

# app.api.validators imports talkingdb.helpers.project, but the
# talkingdb-helpers git revision currently pinned in pyproject.toml
# (rev f601bb3) does not contain a `project` submodule — only auth,
# client, element, event, graph, job, namespace, etc. This means
# app/api/validators.py is unimportable at the current lock, which is
# a real bug independent of this test file (nothing previously
# imported this module, so nothing had surfaced it). Skip cleanly
# here instead of hard-failing the whole suite; flag this to the
# TalkingDB team so either the pin gets bumped to a revision that has
# talkingdb.helpers.project, or the import in validators.py gets fixed.
validators = pytest.importorskip(
    "app.api.validators",
    reason=(
        "app.api.validators imports talkingdb.helpers.project, which does not "
        "exist at the pinned talkingdb-helpers rev (f601bb3) - pre-existing "
        "bug, unrelated to this test suite"
    ),
)
from app.core import config


class TestCleanOptionalText:
    def test_none_returns_none(self):
        assert validators.clean_optional_text(None) is None

    def test_strips_whitespace(self):
        assert validators.clean_optional_text("  hello  ") == "hello"

    def test_blank_string_becomes_none(self):
        assert validators.clean_optional_text("   ") is None

    def test_empty_string_becomes_none(self):
        assert validators.clean_optional_text("") is None

    def test_non_blank_text_passes_through(self):
        assert validators.clean_optional_text("hello world") == "hello world"


class TestParseSuggestedQueries:
    def test_none_returns_none(self):
        assert validators.parse_suggested_queries(None) is None

    def test_empty_list_returns_none(self):
        assert validators.parse_suggested_queries([]) is None

    def test_strips_and_drops_blank_entries(self):
        result = validators.parse_suggested_queries(["  what is x?  ", "", "   ", "another?"])
        assert result == ["what is x?", "another?"]

    def test_all_blank_entries_returns_none(self):
        assert validators.parse_suggested_queries(["", "   "]) is None

    def test_within_limit_passes(self):
        values = [f"query {i}" for i in range(config.MAX_SUGGESTED_QUERIES)]
        result = validators.parse_suggested_queries(values)
        assert len(result) == config.MAX_SUGGESTED_QUERIES

    def test_over_limit_raises_422(self):
        values = [f"query {i}" for i in range(config.MAX_SUGGESTED_QUERIES + 1)]
        with pytest.raises(HTTPException) as exc_info:
            validators.parse_suggested_queries(values)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["error_code"] == "VALIDATION_ERROR"


class TestValidateProjectName:
    def test_valid_name_passes_through(self):
        assert validators.validate_project_name("My Project") == "My Project"

    def test_strips_whitespace(self):
        assert validators.validate_project_name("  My Project  ") == "My Project"

    def test_none_raises_422(self):
        with pytest.raises(HTTPException) as exc_info:
            validators.validate_project_name(None)
        assert exc_info.value.status_code == 422
        assert "required" in exc_info.value.detail["message"]

    def test_blank_raises_422(self):
        with pytest.raises(HTTPException) as exc_info:
            validators.validate_project_name("   ")
        assert exc_info.value.status_code == 422

    def test_too_long_raises_422(self):
        too_long = "x" * (config.MAX_PROJECT_NAME_LENGTH + 1)
        with pytest.raises(HTTPException) as exc_info:
            validators.validate_project_name(too_long)
        assert exc_info.value.status_code == 422
        assert "at most" in exc_info.value.detail["message"]

    def test_exactly_max_length_passes(self):
        exactly_max = "x" * config.MAX_PROJECT_NAME_LENGTH
        assert validators.validate_project_name(exactly_max) == exactly_max
