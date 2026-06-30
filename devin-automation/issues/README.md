# Seed Issues for Devin Demo

These four issues represent real tech-debt in Apache Superset. Create them in your fork with the `devin-autofix` label.

## Create via script

```bash
gh auth login   # if not already authenticated
python scripts/create_issues.py --repo YOUR_USER/superset
```

## Create manually

Apply the `devin-autofix` label to each issue after creation.

| # | Title | Primary file(s) |
|---|-------|-----------------|
| 1 | Remove deprecated Celery beat options fallback in scheduler tasks | `superset/tasks/scheduler.py` |
| 2 | Remove stale MCP filter-tool TODO comments | `tests/unit_tests/mcp_service/...` |
| 3 | Fix typo in PR lint workflow comment | `.github/workflows/pr-lint.yml` |
| 4 | Rename DB migration conflict workflow file | `.github/workflows/check_db_migration_confict.yml` |

Issue bodies are embedded in `scripts/create_issues.py` (ISSUES constant).

**Demo tip:** Start with issue #3 — it is the smallest, fastest fix for validating the full loop.
