# Devin-Powered Tech Debt Remediation for Apache Superset

Event-driven automation that triggers **Devin** sessions when GitHub issues are labeled `devin-autofix`, remediating real Superset tech-debt items and tracking outcomes via a metrics dashboard.

## Problem

Large OSS codebases accumulate small, well-defined tech-debt items faster than teams can prioritize them. Each fix is trivial individually, but triage + context-gathering + PR overhead makes them expensive at scale.

This service uses **Devin as the execution primitive** — our code handles orchestration, observability, and GitHub integration.

## Architecture

```
GitHub Issue (labeled devin-autofix)
        │
        ▼
  Webhook Handler  ──►  SQLite Store
        │
        ▼
  Devin API v3  (POST /sessions)
        │
        ▼
  Session Poller  ──►  GitHub comments + /dashboard metrics
        │
        ▼
  Pull Request (opened by Devin)
```

## Prerequisites

| Variable | Description |
|----------|-------------|
| `DEVIN_API_KEY` | Service user key (`cog_...`) with `ManageOrgSessions` |
| `DEVIN_ORG_ID` | Organization ID from Devin Settings |
| `GITHUB_TOKEN` | PAT with `repo` + `issues:write` (passed to Devin sessions) |
| `GITHUB_WEBHOOK_SECRET` | HMAC secret for webhook verification |
| `GITHUB_REPO` | Target repo, e.g. `your-user/superset` |

Create a Devin service user at **Settings → Service Users** with `ManageOrgSessions` permission.

## Quick Start

```bash
cd devin-automation
cp .env.example .env
# Edit .env with your credentials

docker compose up --build
```

Service runs at **http://localhost:8080**

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Health check |
| `GET /dashboard` | Live metrics dashboard (auto-refreshes) |
| `GET /api/metrics` | JSON metrics for leadership reporting |
| `GET /api/sessions` | Session list |
| `POST /webhooks/github` | GitHub webhook receiver |

## Seed GitHub Issues

Create the 4 demo tech-debt issues in your fork:

```bash
python scripts/create_issues.py --repo your-user/superset
```

Issues created (label: `devin-autofix`):

1. Remove deprecated Celery beat `options` fallback in scheduler tasks
2. Remove stale MCP filter-tool TODO comments
3. Fix typo in PR lint workflow comment *(start here — fastest fix)*
4. Rename DB migration conflict workflow file

## Demo: Simulate Webhook (no public URL needed)

With the service running locally:

```bash
# DRY_RUN mode — test without real Devin API calls
echo "DRY_RUN=true" >> .env
docker compose up --build

# In another terminal:
pip install httpx
python scripts/simulate_webhook.py --issue-number 3 --secret dev-local-secret
```

Check results:
- **Dashboard:** http://localhost:8080/dashboard
- **Metrics:** http://localhost:8080/api/metrics

## Demo: Real Devin Session

```bash
# Set real credentials in .env (DRY_RUN=false)
docker compose up --build

python scripts/simulate_webhook.py \
  --issue-number 3 \
  --repo your-user/superset \
  --secret your_webhook_secret
```

Watch the Devin session URL in the dashboard. When complete, a PR should appear linked to the issue.

## Live GitHub Webhook (optional)

1. Deploy the service to a public HTTPS endpoint (or use ngrok: `ngrok http 8080`)
2. In your fork: **Settings → Webhooks → Add webhook**
   - Payload URL: `https://your-host/webhooks/github`
   - Content type: `application/json`
   - Secret: same as `GITHUB_WEBHOOK_SECRET`
   - Events: **Issues**
3. Label any issue with `devin-autofix` to trigger remediation

## Observability

Engineering leaders can answer "is this working?" via:

- **`/dashboard`** — active/completed/failed counts, success rate, avg duration, ACUs, PR links
- **`/api/metrics`** — same data as JSON for dashboards/alerts
- **Structured logs** — `docker compose logs -f`
- **GitHub issue comments** — session started + completion status with PR link

Example metrics response:

```json
{
  "total_jobs": 4,
  "active": 1,
  "completed": 2,
  "failed": 1,
  "success_rate": 66.7,
  "avg_duration_sec": 842.5,
  "total_acus": 3.42,
  "issues_with_pr": 2
}
```

## Loom Video Talking Points (5 min)

| Segment | Content |
|---------|---------|
| **What (60s)** | Tech-debt backlog in Superset; 4 concrete issues; manual triage cost |
| **How (2.5 min)** | `docker compose up` → simulate webhook → Devin session → poller → PR → dashboard |
| **Why Devin (60s)** | Linters can't remove deprecated fallbacks + run pytest; Devin is the autonomous IC |
| **Next steps (30s)** | CodeQL findings, Dependabot, scheduled scans, Slack alerts, playbooks per issue type |

## Project Structure

```
devin-automation/
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── requirements.txt
├── README.md
├── src/
│   ├── app.py              # FastAPI: webhook + metrics + dashboard
│   ├── config.py           # Environment settings
│   ├── devin_client.py     # Devin v3 API wrapper
│   ├── github_handler.py   # Webhook verify + issue comments
│   ├── poller.py           # Background session status polling
│   ├── prompts.py          # Issue → Devin prompt templates
│   └── store.py            # SQLite persistence
└── scripts/
    ├── create_issues.py    # Seed GitHub issues
    └── simulate_webhook.py # Local demo without ngrok
```

## Why Devin (not just a linter)

These fixes require:
- Multi-file navigation across a large monorepo
- Running `pre-commit`, `pytest`, and `mypy`
- Opening PRs with proper commit messages
- Posting issue comments

Static analysis tools can *detect* these issues but cannot *remediate* them end-to-end. Devin is uniquely suited as the coding agent primitive; this service is the event-driven orchestration layer.

## License

Apache License 2.0 — consistent with Apache Superset.
