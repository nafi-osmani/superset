#!/usr/bin/env python3
"""Seed GitHub issues for Devin tech-debt remediation demo."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

ISSUES = [
    {
        "title": "Remove deprecated Celery beat options fallback in scheduler tasks",
        "body": """## Summary
Remove deprecated fallback logic in Celery scheduler tasks that reads retention period from beat schedule `options`.

## Files
- `superset/tasks/scheduler.py` (lines ~172–232)

## Tasks
Remove the three TODO blocks in `prune_query`, `prune_logs`, and `prune_tasks` that:
1. Read `retention_period_days` from `request.properties` when the kwarg is None
2. Log a deprecation warning about using `options` instead of `kwargs`

The tasks should rely solely on the `retention_period_days` function parameter.

## Acceptance criteria
- [ ] All three deprecated fallback blocks removed
- [ ] No behavior change when `retention_period_days` is passed via kwargs (the supported path)

## Verification
```bash
pytest tests/unit_tests/tasks/
pre-commit run mypy --files superset/tasks/scheduler.py
```
""",
    },
    {
        "title": "Remove stale MCP filter-tool TODO comments",
        "body": """## Summary
Remove obsolete TODO comments referencing removed MCP tools (`get_dashboard_available_filters`, `get_dataset_available_filters`). These were unified into `get_schema`.

## Files
- `tests/unit_tests/mcp_service/dashboard/tool/test_dashboard_tools.py` (line ~1106)
- `tests/unit_tests/mcp_service/dataset/tool/test_dataset_tools.py` (line ~1059)

## Tasks
Delete the stale `# TODO (Phase 3+): Add tests for get_*_available_filters tool` comments.

## Verification
```bash
pytest tests/unit_tests/mcp_service/dashboard/tool/test_dashboard_tools.py
pytest tests/unit_tests/mcp_service/dataset/tool/test_dataset_tools.py
```
""",
    },
    {
        "title": "Fix typo in PR lint workflow comment",
        "body": """## Summary
Fix a typo in the PR lint GitHub Actions workflow comment.

## File
- `.github/workflows/pr-lint.yml` (line 6)

## Change
Replace `explicity` with `explicitly` in the workflow comment.

## Verification
```bash
pre-commit run check-yaml --files .github/workflows/pr-lint.yml
```
""",
    },
    {
        "title": "Rename DB migration conflict workflow file",
        "body": """## Summary
Rename the DB migration conflict check workflow file to fix a typo in the filename.

## Change
Rename:
- `.github/workflows/check_db_migration_confict.yml`
to:
- `.github/workflows/check_db_migration_conflict.yml`

No content changes required — GitHub discovers workflows by file path.

## Verification
```bash
pre-commit run check-yaml --files .github/workflows/check_db_migration_conflict.yml
```
""",
    },
]


def check_github_ready(repo: str) -> bool:
    """Verify Issues are enabled and gh is authenticated."""
    result = subprocess.run(
        ["gh", "api", f"repos/{repo}", "--jq", ".has_issues"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(f"Cannot access repo {repo}. Run: gh auth login", file=sys.stderr)
        return False

    if result.stdout.strip() != "true":
        print(
            f"GitHub Issues are disabled on {repo}.\n"
            f"Enable them at: https://github.com/{repo}/settings\n"
            "  Settings → General → Features → Issues → check Enable",
            file=sys.stderr,
        )
        return False

    label_check = subprocess.run(
        [
            "gh",
            "label",
            "create",
            "devin-autofix",
            "--repo",
            repo,
            "--color",
            "0E8A16",
            "--description",
            "Trigger Devin auto-remediation",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if label_check.returncode != 0 and "already exists" not in label_check.stderr.lower():
        print(f"Note: could not create label (may already exist): {label_check.stderr}")

    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Create seed issues for Devin demo")
    parser.add_argument(
        "--repo",
        required=True,
        help="GitHub repo in owner/name format (e.g. your-user/superset)",
    )
    parser.add_argument(
        "--label",
        default="devin-autofix",
        help="Label to apply (default: devin-autofix)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing",
    )
    args = parser.parse_args()

    if not args.dry_run and not check_github_ready(args.repo):
        return 1

    created: list[dict[str, str | int]] = []

    for issue in ISSUES:
        cmd = [
            "gh",
            "issue",
            "create",
            "--repo",
            args.repo,
            "--title",
            issue["title"],
            "--body",
            issue["body"],
            "--label",
            args.label,
        ]
        if args.dry_run:
            print("DRY RUN:", " ".join(cmd[:8]), "...")
            continue

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print(f"Failed to create issue: {issue['title']}", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            return 1

        url = result.stdout.strip()
        number = url.rstrip("/").split("/")[-1]
        created.append({"title": issue["title"], "number": number, "url": url})
        print(f"Created issue #{number}: {issue['title']}")

    if args.dry_run:
        print(f"\nWould create {len(ISSUES)} issues with label '{args.label}'")
    else:
        print(f"\nCreated {len(created)} issues:")
        print(json.dumps(created, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
