# Seed Issues for Devin Demo

Four tech-debt issues are tracked on this fork. After running `create_issues.py`, apply the **`devin-autofix`** label to each issue (manually in GitHub UI if the API cannot create labels).

## Issues on nafi-osmani/superset

| Issue | Title | Remediation |
|-------|-------|-------------|
| [#6](https://github.com/nafi-osmani/superset/issues/6) | Remove deprecated Celery scheduler fallback | Pending |
| [#7](https://github.com/nafi-osmani/superset/issues/7) | Remove stale MCP TODO comments | Pending |
| [#8](https://github.com/nafi-osmani/superset/issues/8) | Fix typo in PR lint workflow | [PR #5](https://github.com/nafi-osmani/superset/pull/5) |
| [#9](https://github.com/nafi-osmani/superset/issues/9) | Rename migration conflict workflow file | Pending |

## Create via script

```bash
gh auth login
python scripts/create_issues.py --repo nafi-osmani/superset
```

Issue bodies are defined in `scripts/create_issues.py` (`ISSUES` constant).

**Demo tip:** Issue #9 is best for a live trigger; #8 already has a Devin-opened PR.
