#!/usr/bin/env python3
"""Simulate a GitHub issues.labeled webhook for local demo."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sys

import httpx

DEFAULT_ISSUES = {
    1: {
        "title": "Remove deprecated Celery beat options fallback in scheduler tasks",
        "body": "See superset/tasks/scheduler.py lines 172-232. Remove deprecated options fallback.",
    },
    2: {
        "title": "Remove stale MCP filter-tool TODO comments",
        "body": "Remove TODO comments in test_dashboard_tools.py:1106 and test_dataset_tools.py:1059.",
    },
    3: {
        "title": "Fix typo in PR lint workflow comment",
        "body": "Fix explicity -> explicitly in .github/workflows/pr-lint.yml line 6.",
    },
    4: {
        "title": "Rename DB migration conflict workflow file",
        "body": "Rename check_db_migration_confict.yml to check_db_migration_conflict.yml.",
    },
}


def build_payload(
    issue_number: int,
    repo: str,
    title: str,
    body: str,
    label: str,
) -> dict:
    return {
        "action": "labeled",
        "issue": {
            "number": issue_number,
            "title": title,
            "body": body,
            "html_url": f"https://github.com/{repo}/issues/{issue_number}",
            "labels": [{"name": label}, {"name": "tech-debt"}],
        },
        "label": {"name": label},
        "repository": {"full_name": repo},
    }


def sign_payload(payload_bytes: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulate GitHub webhook")
    parser.add_argument(
        "--issue-number",
        type=int,
        default=3,
        help="Issue number to simulate (default: 3 — smallest fix)",
    )
    parser.add_argument(
        "--repo",
        default=os.environ.get("GITHUB_REPO", "your-user/superset"),
        help="GitHub repo owner/name",
    )
    parser.add_argument(
        "--label",
        default=os.environ.get("TRIGGER_LABEL", "devin-autofix"),
        help="Label that triggers remediation",
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8080/webhooks/github",
        help="Webhook endpoint URL",
    )
    parser.add_argument(
        "--secret",
        default=os.environ.get("GITHUB_WEBHOOK_SECRET", "dev-local-secret"),
        help="Webhook HMAC secret",
    )
    parser.add_argument("--title", help="Override issue title")
    parser.add_argument("--body", help="Override issue body")
    args = parser.parse_args()

    preset = DEFAULT_ISSUES.get(args.issue_number, DEFAULT_ISSUES[3])
    title = args.title or preset["title"]
    body = args.body or preset["body"]

    payload = build_payload(
        issue_number=args.issue_number,
        repo=args.repo,
        title=title,
        body=body,
        label=args.label,
    )
    payload_bytes = json.dumps(payload).encode()
    signature = sign_payload(payload_bytes, args.secret)

    print(f"POST {args.url}")
    print(f"Issue #{args.issue_number}: {title}")
    print(f"Signature: {signature[:20]}...")

    response = httpx.post(
        args.url,
        content=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "issues",
            "X-Hub-Signature-256": signature,
        },
        timeout=60.0,
    )

    print(f"Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except json.JSONDecodeError:
        print(response.text)

    return 0 if response.status_code < 400 else 1


if __name__ == "__main__":
    sys.exit(main())
