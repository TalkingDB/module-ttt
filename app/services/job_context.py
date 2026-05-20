"""Per-job runtime context: checkpoints, heartbeats, cancel + timeout signals.

The worker passes a :class:`JobContext` down into the pipeline (parse / index /
persist). Long-running steps call ``ctx.checkpoint(...)`` between units of
work. Each call does three things:

  1. Reads the ``cancel_requested`` flag - raises :class:`JobCancelled` if set.
  2. Checks elapsed wall-clock - raises :class:`JobTimeout` past
     ``MAX_JOB_DURATION_SECONDS``.
  3. Writes a best-effort progress + heartbeat row (rate-limited to
     ``HEARTBEAT_MIN_GAP_SECONDS`` so we don't hammer SQLite).

Progress writes are deliberately best-effort: a dropped checkpoint due to
write contention or a guarded UPDATE (state already terminal) never affects
correctness; it just means the reported percent may briefly lag actual work.
"""

import sqlite3
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from talkingdb.clients.sqlite import sqlite_conn
from talkingdb.logger.console import logger
from talkingdb.models.job import store as job_store
from talkingdb.models.job.stage import JobStage

from app.core import config


class JobControl(Exception):
    """Base class for job control-flow signals."""


class JobCancelled(JobControl):
    """Raised when a job is cancelled."""


class JobTimeout(JobControl):
    """Raised when a job exceeds the timeout."""


@dataclass
class JobContext:
    """Tracks job progress, heartbeat, and runtime state."""

    job_id: str
    started_monotonic: float = field(default_factory=time.monotonic)
    _last_heartbeat_monotonic: float = field(default=0.0)
    _stage: Optional[JobStage] = None

    # ----------------------------------------------------------- utilities
    def elapsed_seconds(self) -> float:
        """Return elapsed runtime in seconds."""
        return time.monotonic() - self.started_monotonic

    def _should_write_heartbeat(self, *, force: bool) -> bool:
        """Return whether a heartbeat should be written."""
        if force:
            return True

        return (
            time.monotonic()
            - self._last_heartbeat_monotonic
            >= config.HEARTBEAT_MIN_GAP_SECONDS
        )

    def _best_effort_progress(self, **kwargs: Any) -> None:
        """Write progress updates with best-effort semantics."""
        try:
            with sqlite_conn() as conn:
                job_store.update_progress(conn, self.job_id, **kwargs)
        except sqlite3.OperationalError as exc:
            logger.warning(
                f"[job {self.job_id}] progress write dropped: {exc}"
            )

    # -------------------------------------------------- public checkpoint API
    def set_stage(
        self,
        stage: JobStage,
        *,
        status_message: Optional[str] = None,
    ) -> None:
        """Update the current job stage."""
        self._stage = stage

        self._best_effort_progress(
            stage=stage, status_message=status_message, heartbeat=True,
        )
        self._last_heartbeat_monotonic = time.monotonic()

    def checkpoint(
        self,
        *,
        done_units: Optional[int] = None,
        total_units: Optional[int] = None,
        status_message: Optional[str] = None,
        progress_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Run cancel, timeout, and heartbeat checks."""
        with sqlite_conn() as conn:
            if job_store.is_cancel_requested(conn, self.job_id):
                raise JobCancelled(self.job_id)

        if self.elapsed_seconds() > config.MAX_JOB_DURATION_SECONDS:
            raise JobTimeout(self.job_id)

        if not self._should_write_heartbeat(force=False):
            return

        self._best_effort_progress(
            stage=self._stage,
            done_units=done_units,
            total_units=total_units,
            status_message=status_message,
            progress_details=progress_details,
            heartbeat=True,
        )
        self._last_heartbeat_monotonic = time.monotonic()
