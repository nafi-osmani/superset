#!/usr/bin/env bash
# Simulate webhooks for all 4 demo issues (#6-#9 on nafi-osmani/superset).
set -euo pipefail

SECRET="${GITHUB_WEBHOOK_SECRET:-dev-local-secret}"
REPO="${GITHUB_REPO:-nafi-osmani/superset}"
URL="${WEBHOOK_URL:-http://localhost:8080/webhooks/github}"
SCRIPT_DIR="$(dirname "$0")"

declare -A ISSUE_TITLES=(
  [6]="Remove deprecated Celery beat options fallback in scheduler tasks"
  [7]="Remove stale MCP filter-tool TODO comments"
  [8]="Fix typo in PR lint workflow comment"
  [9]="Rename DB migration conflict workflow file"
)

declare -A ISSUE_BODIES=(
  [6]="See superset/tasks/scheduler.py lines 172-232. Remove deprecated options fallback."
  [7]="Remove TODO comments in test_dashboard_tools.py:1106 and test_dataset_tools.py:1059."
  [8]="Fix explicity -> explicitly in .github/workflows/pr-lint.yml line 6."
  [9]="Rename check_db_migration_confict.yml to check_db_migration_conflict.yml."
)

for n in 6 7 8 9; do
  echo "=== Triggering issue #${n} ==="
  python3 "${SCRIPT_DIR}/simulate_webhook.py" \
    --issue-number "$n" \
    --repo "$REPO" \
    --secret "$SECRET" \
    --url "$URL" \
    --title "${ISSUE_TITLES[$n]}" \
    --body "${ISSUE_BODIES[$n]}"
  echo ""
  sleep 2
done

echo "Done. Check http://localhost:8080/dashboard"
