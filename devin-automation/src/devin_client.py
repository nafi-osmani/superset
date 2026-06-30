"""Devin v3 API client."""

from __future__ import annotations

import logging
import uuid
from typing import Any

import httpx

from config import settings
from prompts import build_remediation_prompt

logger = logging.getLogger(__name__)

BASE_URL = "https://api.devin.ai/v3"
TERMINAL_STATUSES = frozenset({"exit", "error", "suspended"})


class DevinClient:
    def __init__(
        self,
        api_key: str | None = None,
        org_id: str | None = None,
        dry_run: bool | None = None,
    ) -> None:
        self.api_key = api_key or settings.devin_api_key
        self.org_id = org_id or settings.devin_org_id
        self.dry_run = dry_run if dry_run is not None else settings.dry_run

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def create_remediation_session(
        self,
        issue_number: int,
        issue_title: str,
        issue_body: str,
        repo: str,
    ) -> dict[str, Any]:
        prompt = build_remediation_prompt(
            issue_number=issue_number,
            issue_title=issue_title,
            issue_body=issue_body,
            repo=repo,
        )

        payload: dict[str, Any] = {
            "title": f"Fix Superset issue #{issue_number}: {issue_title}",
            "prompt": prompt,
            "repos": [repo],
            "tags": ["superset-tech-debt", f"issue-{issue_number}"],
            "bypass_approval": True,
        }

        if settings.max_acu_limit:
            payload["max_acu_limit"] = settings.max_acu_limit

        if settings.github_token:
            payload["session_secrets"] = [
                {"key": "GITHUB_TOKEN", "value": settings.github_token},
            ]

        if self.dry_run:
            session_id = f"dry-run-{uuid.uuid4().hex[:12]}"
            logger.info("DRY_RUN: would create Devin session for issue #%s", issue_number)
            return {
                "session_id": session_id,
                "url": f"https://app.devin.ai/sessions/{session_id}",
                "status": "running",
                "pull_requests": [],
                "acus_consumed": 0,
            }

        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{BASE_URL}/organizations/{self.org_id}/sessions",
                headers=self._headers(),
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    def get_session(self, session_id: str) -> dict[str, Any]:
        if self.dry_run or session_id.startswith("dry-run-"):
            return {
                "session_id": session_id,
                "url": f"https://app.devin.ai/sessions/{session_id}",
                "status": "exit",
                "status_detail": "finished",
                "pull_requests": [],
                "acus_consumed": 0,
            }

        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"{BASE_URL}/organizations/{self.org_id}/sessions/{session_id}",
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    def extract_pr_url(session: dict[str, Any]) -> str | None:
        pull_requests = session.get("pull_requests") or []
        if not pull_requests:
            return None
        return pull_requests[0].get("pr_url")

    @staticmethod
    def is_terminal(status: str) -> bool:
        return status in TERMINAL_STATUSES
