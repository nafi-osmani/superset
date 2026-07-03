# Devin-Powered Tech Debt Remediation for Apache Superset

Event-driven automation that triggers **Devin** sessions when GitHub issues are labeled `devin-autofix`, remediating real Superset tech-debt items and tracking outcomes via a metrics dashboard.

**Branch:** `c_firstpass` | **Fork:** `nafi-osmani/superset`

---

## What this does

1. A GitHub issue gets labeled **`devin-autofix`**
2. The remediator service receives a webhook and calls **Devin API v3**
3. Devin clones the repo, makes the fix, opens a PR, and comments on the issue
4. A background poller tracks session status; **`/dashboard`** shows throughput and success rate

```
GitHub Issue (labeled devin-autofix)
        │
        ▼
  POST /webhooks/github  ──►  SQLite job store
        │
        ▼
  Devin API v3  (POST /sessions)
        │
        ▼
  Session poller (every 30s)  ──►  /dashboard metrics
        │
        ▼
  Pull Request (opened by Devin)
```

---

## Prerequisites

| Requirement | How to get it |
|-------------|---------------|
| Devin service user | [app.devin.ai](https://app.devin.ai) → Settings → Service Users → create with **`ManageOrgSessions`** |
| `DEVIN_API_KEY` | Starts with `cog_` — shown once at creation |
| `DEVIN_ORG_ID` | On the Service Users settings page (e.g. `org-...`) |
| `GITHUB_TOKEN` | PAT with `repo` + `issues:write`, or run `gh auth token` |
| GitHub Issues enabled | Fork → Settings → General → Features → **Issues** |
| Python 3.12+ | For local run (or use Docker) |

---

## Setup (one time)

### 1. Configure environment

```bash
cd devin-automation
cp .env.example .env
```

Edit `.env`:

```env
DEVIN_API_KEY=cog_your_key_here
DEVIN_ORG_ID=org-your_org_id
GITHUB_REPO=nafi-osmani/superset
GITHUB_WEBHOOK_SECRET=dev-local-secret
GITHUB_TOKEN=ghp_or_ghs_token_here
DRY_RUN=false
MAX_ACU_LIMIT=10
```

Populate `GITHUB_TOKEN` from gh CLI:

```bash
gh auth login   # if needed
gh auth token   # paste into .env
```

### 2. Install dependencies

```bash
pip install -r requirements.txt httpx
```

### 3. Seed demo issues (optional)

```bash
./scripts/setup_github.sh
python scripts/create_issues.py --repo nafi-osmani/superset
```

This creates 4 tech-debt issues with the `devin-autofix` label. Demo issues on this fork:

| Issue | Title | Best for |
|-------|-------|----------|
| [#6](https://github.com/nafi-osmani/superset/issues/6) | Remove deprecated Celery scheduler fallback | Medium |
| [#7](https://github.com/nafi-osmani/superset/issues/7) | Remove stale MCP TODO comments | Medium |
| [#8](https://github.com/nafi-osmani/superset/issues/8) | Fix typo in PR lint workflow | **Fastest fix** |
| [#9](https://github.com/nafi-osmani/superset/issues/9) | Rename migration conflict workflow file | **Good visual demo** |

---

## Run the service

Choose **Docker** or **local uvicorn**.

### Option A: Docker

```bash
cd devin-automation
docker compose up --build
```

### Option B: Local (recommended for Cursor / Cloud Agent)

```bash
cd devin-automation
set -a && source .env && set +a
export PYTHONPATH=src DATABASE_PATH=./data/remediator.db
python3 -m uvicorn app:app --host 0.0.0.0 --port 8080 --app-dir src
```

Keep this terminal open while the service runs.

### Verify it is running

```bash
curl http://localhost:8080/health
# → {"status":"ok"}
```

### Access the dashboard

Open **http://localhost:8080/dashboard**

> **Using Cursor with a remote workspace?** Forward port **8080** in the Cursor **Ports** panel. Without forwarding, your browser will show `ERR_CONNECTION_REFUSED` even though the service is running on the remote VM.

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Health check |
| `GET /dashboard` | Live metrics UI (auto-refreshes every 30s) |
| `GET /api/metrics` | JSON metrics |
| `GET /api/sessions` | Session list |
| `POST /webhooks/github` | GitHub webhook receiver |

---

## Simulate the workflow (recommended for demo)

Simulates what happens when an issue is labeled `devin-autofix` — **no ngrok or public URL required**.

### Step 1: Start the service (see above)

Ensure `DRY_RUN=false` in `.env` for a real Devin session.

### Step 2: Trigger remediation

Use the **actual GitHub issue number** from your fork. Example for issue #9:

```bash
cd devin-automation
python scripts/simulate_webhook.py \
  --issue-number 9 \
  --repo nafi-osmani/superset \
  --secret dev-local-secret \
  --title "Rename DB migration conflict workflow file" \
  --body "Rename check_db_migration_confict.yml to check_db_migration_conflict.yml"
```

For the fastest fix (issue #8):

```bash
python scripts/simulate_webhook.py \
  --issue-number 8 \
  --repo nafi-osmani/superset \
  --secret dev-local-secret \
  --title "Fix typo in PR lint workflow comment" \
  --body "Fix explicity -> explicitly in .github/workflows/pr-lint.yml line 6."
```

### Step 3: Watch the results

Expected response:

```json
{
  "status": "created",
  "session_id": "...",
  "session_url": "https://app.devin.ai/sessions/..."
}
```

Then:

1. Open **`session_url`** in the Devin UI — watch Devin work
2. Refresh **http://localhost:8080/dashboard** — job appears as `running`
3. Wait 30–60s, refresh — poller updates status; PR link appears when Devin finishes

### Dry-run mode (no Devin API calls)

Set `DRY_RUN=true` in `.env`, restart the service, then run the same simulate command. Useful for testing the webhook handler and dashboard without spending ACUs.

### Trigger all four issues

```bash
./scripts/simulate_all.sh
```

---

## Real GitHub label trigger (optional)

Same handler as simulate — requires a **publicly reachable** webhook URL.

1. Start the service locally
2. Expose port 8080: `ngrok http 8080`
3. Fork → **Settings → Webhooks → Add webhook**
   - **Payload URL:** `https://<ngrok-id>.ngrok-free.app/webhooks/github`
   - **Content type:** `application/json`
   - **Secret:** `dev-local-secret` (must match `GITHUB_WEBHOOK_SECRET` in `.env`)
   - **Events:** Issues
4. Open an issue on GitHub → add label **`devin-autofix`**

> Merging branch `c_firstpass` is **not required**. Devin clones the default branch where the tech debt already exists.

---

## Preflight checks

Run before a demo or Loom recording:

```bash
# 1. Devin API connectivity
set -a && source .env && set +a
curl -sf -X POST "https://api.devin.ai/v3/organizations/${DEVIN_ORG_ID}/sessions" \
  -H "Authorization: Bearer ${DEVIN_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Connectivity test only.","max_acu_limit":1}'
# → should return session_id and url

# 2. Service health
curl http://localhost:8080/health

# 3. Clean dashboard (optional)
rm -f data/remediator.db && restart uvicorn

# 4. GitHub preflight
./scripts/setup_github.sh
```

---

## Observability

Engineering leaders can answer "is this working?" via:

- **`/dashboard`** — active/completed/failed, success rate, avg duration, ACU spend, PR links
- **`/api/metrics`** — same data as JSON
- **Structured logs** — stdout from uvicorn or `docker compose logs -f`
- **GitHub issue comments** — session started + completion status (when `GITHUB_TOKEN` is set)

Example metrics:

```json
{
  "total_jobs": 1,
  "active": 0,
  "completed": 1,
  "failed": 0,
  "success_rate": 100.0,
  "avg_duration_sec": 842.5,
  "total_acus": 3.42,
  "issues_with_pr": 1
}
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ERR_CONNECTION_REFUSED` on dashboard | Browser hitting local machine, not remote VM | Forward port **8080** in Cursor Ports panel |
| `502` on webhook | Invalid Devin credentials | Check `DEVIN_API_KEY` and `DEVIN_ORG_ID` in `.env` |
| `"status": "skipped"` | Active session already running for that issue | Wait for completion or use a different issue number |
| `"status": "ignored"` | Wrong label | Ensure `devin-autofix` label in payload |
| `create_issues.py` fails | Issues disabled on fork | Enable at fork Settings → General → Features |
| Dashboard shows stale jobs | Old SQLite data | `rm data/remediator.db` and restart service |
| PR not appearing quickly | Devin still working | Show running session in Devin UI; poller updates every 30s |

---

## Project structure

```
devin-automation/
├── Dockerfile
├── docker-compose.yml
├── .env.example          # Copy to .env (never commit .env)
├── requirements.txt
├── README.md
├── src/
│   ├── app.py            # FastAPI: webhook + metrics + dashboard
│   ├── config.py         # Environment settings
│   ├── devin_client.py   # Devin v3 API wrapper
│   ├── github_handler.py # Webhook verify + issue comments
│   ├── poller.py         # Background session status polling
│   ├── prompts.py        # Issue → Devin prompt templates
│   └── store.py          # SQLite persistence
└── scripts/
    ├── create_issues.py  # Seed GitHub issues
    ├── setup_github.sh   # GitHub preflight checks
    ├── simulate_webhook.py  # Simulate labeled issue (demo)
    └── simulate_all.sh   # Trigger all 4 demo issues
```

---

## Why Devin (not just a linter)

| Tool | Can do | Cannot do |
|------|--------|-----------|
| Dependabot | Bump dependency versions | Remove deprecated Celery fallbacks |
| Linters | Flag problems | Run pytest, open PRs, post issue comments |
| **Devin + this service** | Full remediation loop | — |

These fixes require repo navigation, running `pre-commit`/`pytest`, and opening PRs. Devin is the autonomous IC; this service is the event-driven orchestration and observability layer.

---

## License

Apache License 2.0 — consistent with Apache Superset.
