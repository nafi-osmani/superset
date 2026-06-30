#!/usr/bin/env bash
# Simulate webhooks for all 4 demo issues (requires running service).
set -euo pipefail

SECRET="${GITHUB_WEBHOOK_SECRET:-dev-local-secret}"
REPO="${GITHUB_REPO:-your-user/superset}"
URL="${WEBHOOK_URL:-http://localhost:8080/webhooks/github}"

for n in 1 2 3 4; do
  echo "=== Triggering issue #${n} ==="
  python3 "$(dirname "$0")/simulate_webhook.py" \
    --issue-number "$n" \
    --repo "$REPO" \
    --secret "$SECRET" \
    --url "$URL"
  echo ""
  sleep 2
done

echo "Done. Check http://localhost:8080/dashboard"
