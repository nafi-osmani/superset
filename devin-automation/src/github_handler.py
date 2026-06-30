"""GitHub webhook verification and issue comment helpers."""

from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any

import httpx

from config import settings

logger = logging.getLogger(__name__)


def verify_github_signature(payload: bytes, signature_header: str | None) -> bool:
    if not signature_header:
        return False
    if not signature_header.startswith("sha256="):
        return False

    expected = hmac.new(
        settings.github_webhook_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    received = signature_header.removeprefix("sha256=")

    return hmac.compare_digest(expected, received)


def parse_issue_event(payload: dict[str, Any]) -> dict[str, Any] | None:
    action = payload.get("action")
    issue = payload.get("issue")
    if not issue:
        return None

    labels = [label.get("name", "") for label in issue.get("labels", [])]
    label_added = None
    if action == "labeled":
        label_added = payload.get("label", {}).get("name")

    return {
        "action": action,
        "issue_number": issue["number"],
        "issue_title": issue.get("title", ""),
        "issue_body": issue.get("body") or "",
        "labels": labels,
        "label_added": label_added,
        "repo": payload.get("repository", {}).get("full_name", settings.github_repo),
        "html_url": issue.get("html_url", ""),
    }


def should_trigger(event: dict[str, Any]) -> bool:
    trigger = settings.trigger_label
    if event["action"] == "labeled":
        return event.get("label_added") == trigger
    if event["action"] in ("opened", "edited"):
        return trigger in event.get("labels", [])
    return False


def post_issue_comment(
    repo: str,
    issue_number: int,
    body: str,
    token: str | None = None,
) -> int | None:
    github_token = token or settings.github_token
    if not github_token:
        logger.warning("No GITHUB_TOKEN configured; skipping issue comment")
        return None

    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, json={"body": body})
            response.raise_for_status()
            return response.json().get("id")
    except httpx.HTTPError as exc:
        logger.exception("Failed to post GitHub comment: %s", exc)
        return None


def format_started_comment(session_id: str, session_url: str) -> str:
    return (
        f"🤖 **Devin remediation started**\n\n"
        f"- Session: [{session_id}]({session_url})\n"
        f"- Status: running\n\n"
        f"A pull request will be linked here when the session completes."
    )


def format_completed_comment(
    status: str,
    session_url: str,
    pr_url: str | None,
    acus_consumed: float,
    duration_sec: float | None,
) -> str:
    if status == "exit":
        emoji = "✅"
        headline = "Devin remediation completed"
    else:
        emoji = "❌"
        headline = f"Devin remediation ended ({status})"

    lines = [
        f"{emoji} **{headline}**",
        "",
        f"- Session: {session_url}",
        f"- Status: `{status}`",
        f"- ACUs consumed: {acus_consumed:.2f}",
    ]
    if duration_sec is not None:
        lines.append(f"- Duration: {duration_sec:.0f}s")
    if pr_url:
        lines.append(f"- Pull request: {pr_url}")
    return "\n".join(lines)
