"""Background poller for Devin session status updates."""

from __future__ import annotations

import asyncio
import logging

from config import settings
from devin_client import DevinClient
from github_handler import format_completed_comment, post_issue_comment
from store import JobStore

logger = logging.getLogger(__name__)


class SessionPoller:
    def __init__(
        self,
        store: JobStore | None = None,
        devin: DevinClient | None = None,
        interval_sec: int | None = None,
    ) -> None:
        self.store = store or JobStore()
        self.devin = devin or DevinClient()
        self.interval_sec = interval_sec or settings.poll_interval_sec
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("Session poller started (interval=%ss)", self.interval_sec)

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Session poller stopped")

    async def _loop(self) -> None:
        while self._running:
            try:
                await self.poll_once()
            except Exception:
                logger.exception("Poller iteration failed")
            await asyncio.sleep(self.interval_sec)

    async def poll_once(self) -> None:
        jobs = self.store.get_active_jobs()
        for job in jobs:
            if not job.devin_session_id:
                continue
            try:
                session = self.devin.get_session(job.devin_session_id)
            except Exception as exc:
                logger.exception(
                    "Failed to fetch session %s for job %s",
                    job.devin_session_id,
                    job.id,
                )
                self.store.mark_failed(job.id, str(exc))
                continue

            status = session.get("status", "unknown")
            pr_url = self.devin.extract_pr_url(session)
            acus = float(session.get("acus_consumed") or 0)

            self.store.update_from_devin(
                job_id=job.id,
                status=status,
                pr_url=pr_url,
                acus_consumed=acus,
            )

            if self.devin.is_terminal(status):
                updated = self.store.get_job_by_id(job.id)
                if updated:
                    comment = format_completed_comment(
                        status=status,
                        session_url=updated.devin_url or session.get("url", ""),
                        pr_url=pr_url,
                        acus_consumed=acus,
                        duration_sec=updated.duration_sec,
                    )
                    post_issue_comment(
                        repo=updated.repo,
                        issue_number=updated.issue_number,
                        body=comment,
                    )
                logger.info(
                    "Job %s (issue #%s) reached terminal status: %s",
                    job.id,
                    job.issue_number,
                    status,
                )
