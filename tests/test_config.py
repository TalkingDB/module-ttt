"""Unit tests for app.core.config's env-var parsing helpers.

These are pure functions with no I/O beyond os.getenv, so they're
covered directly without needing app startup, a DB, or object storage.
"""

import importlib

import pytest

from app.core import config


@pytest.fixture
def reload_config(monkeypatch):
    """Reload app.core.config after mutating env vars, then restore it."""

    def _reload():
        return importlib.reload(config)

    yield _reload
    monkeypatch.undo()
    importlib.reload(config)


def test_int_returns_default_when_unset(monkeypatch):
    monkeypatch.delenv("TDB_JOB_MAX_WORKERS", raising=False)
    assert config._int("TDB_JOB_MAX_WORKERS", 7) == 7


def test_int_returns_default_when_blank(monkeypatch):
    monkeypatch.setenv("TDB_JOB_MAX_WORKERS", "   ")
    assert config._int("TDB_JOB_MAX_WORKERS", 7) == 7


def test_int_parses_valid_value(monkeypatch):
    monkeypatch.setenv("TDB_JOB_MAX_WORKERS", "12")
    assert config._int("TDB_JOB_MAX_WORKERS", 7) == 12


def test_int_falls_back_on_invalid_value(monkeypatch):
    monkeypatch.setenv("TDB_JOB_MAX_WORKERS", "not-a-number")
    assert config._int("TDB_JOB_MAX_WORKERS", 7) == 7


def test_float_returns_default_when_unset(monkeypatch):
    monkeypatch.delenv("TDB_CONTEXT_MATCH_WEIGHT", raising=False)
    assert config._float("TDB_CONTEXT_MATCH_WEIGHT", 0.4) == 0.4


def test_float_parses_valid_value(monkeypatch):
    monkeypatch.setenv("TDB_CONTEXT_MATCH_WEIGHT", "0.75")
    assert config._float("TDB_CONTEXT_MATCH_WEIGHT", 0.4) == 0.75


def test_float_falls_back_on_invalid_value(monkeypatch):
    monkeypatch.setenv("TDB_CONTEXT_MATCH_WEIGHT", "nope")
    assert config._float("TDB_CONTEXT_MATCH_WEIGHT", 0.4) == 0.4


def test_gram_weights_default_ordering():
    # Longer n-grams should be weighted at least as strongly as shorter ones
    # by default, since they're harder to match by accident.
    weights = config.GRAM_WEIGHTS
    assert weights["unigram"] < weights["bigram"] < weights["trigram"]
