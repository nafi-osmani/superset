#!/usr/bin/env bash
# Preflight checks for GitHub integration.
set -euo pipefail

REPO="${GITHUB_REPO:-nafi-osmani/superset}"

echo "=== GitHub setup for Devin remediator ==="
echo "Repo: ${REPO}"
echo ""

if ! command -v gh >/dev/null; then
  echo "ERROR: gh CLI not installed. Install from https://cli.github.com/"
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "ERROR: gh not authenticated. Run: gh auth login"
  exit 1
fi
echo "OK: gh authenticated"

HAS_ISSUES=$(gh api "repos/${REPO}" --jq '.has_issues')
if [ "${HAS_ISSUES}" = "true" ]; then
  echo "OK: GitHub Issues enabled"
else
  echo "ACTION REQUIRED: Enable Issues on your fork:"
  echo "  https://github.com/${REPO}/settings"
  echo "  Settings → General → Features → Issues"
  exit 1
fi

gh label create devin-autofix --repo "${REPO}" --color 0E8A16 \
  --description "Trigger Devin auto-remediation" 2>/dev/null || true
echo "OK: devin-autofix label ready"

echo ""
echo "Create seed issues:"
echo "  python scripts/create_issues.py --repo ${REPO}"
