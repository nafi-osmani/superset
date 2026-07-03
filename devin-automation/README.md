# Devin-Powered Tech Debt Remediation for Apache Superset

Event-driven automation that triggers **Devin** sessions when GitHub issues are labeled `devin-autofix`, remediating real Superset tech-debt items and tracking outcomes via a metrics dashboard.

**Repository:** [github.com/nafi-osmani/superset](https://github.com/nafi-osmani/superset)  
**Branch:** `master` (default)  
**Solution path:** `devin-automation/`

---

## Submission overview

This fork contains:

| Deliverable | Location |
|-------------|----------|
| Docker-packaged automation service | [`devin-automation/`](.) — `Dockerfile`, `docker-compose.yml` |
| Run / simulate instructions | This README |
| Forked Apache Superset codebase | Repo root (`superset/`, `.github/`, etc.) |
| Selected tech-debt issues | GitHub Issues [#6–#9](https://github.com/nafi-osmani/superset/issues) |
| Devin remediation (example) | [PR #5](https://github.com/nafi-osmani/superset/pull/5) fixes [#8](https://github.com/nafi-osmani/superset/issues/8) |

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

## Demo issues and remediation status

These issues target real tech debt in Apache Superset. Apply the **`devin-autofix`** label in GitHub to trigger remediation (or use the simulate script below).

| Issue | Title | Status |
|-------|-------|--------|
| [#6](https://github.com/nafi-osmani/superset/issues/6) | Remove deprecated Celery scheduler fallback | Open — pending remediation |
| [#7](https://github.com/nafi-osmani/superset/issues/7) | Remove stale MCP TODO comments | Open — pending remediation |
| [#8](https://github.com/nafi-osmani/superset/issues/8) | Fix typo in PR lint workflow | **Remediated** — [PR #5](https://github.com/nafi-osmani/superset/pull/5) |
| [#9](https://github.com/nafi-osmani/superset/issues/9) | Rename migration conflict workflow file | Open — pending remediation |

> **Label note:** If issues were created without the `devin-autofix` label, add it manually in the GitHub UI (Labels → `devin-autofix`) before using the real webhook trigger.

---

## Prerequisites

| Requirement | How to get it |
|-------------|---------------|
| Devin service user | [app.devin.ai](https://app.devin.ai) → Settings → Service Users → **`ManageOrgSessions`** |
| `DEVIN_API_KEY` | Starts with `cog_` — shown once at creation |
| `DEVIN_ORG_ID` | Service Users settings page (e.g. `org-...`) |
| `GITHUB_TOKEN` | PAT with `repo` + `issues:write`, or `gh auth token` |
| GitHub Issues enabled | Fork → Settings → General → Features → **Issues** |
| Docker **or** Python 3.12+ | See run options below |

---

## Quick start (evaluators)

```bash
git clone https://github.com/nafi-osmani/superset.git
cd superset/devin-automation
cp .env.example .env
# Edit .env: set DEVIN_API_KEY, DEVIN_ORG_ID, GITHUB_TOKEN, GITHUB_REPO

docker compose up --build
```

In a second terminal:

```bash
cd superset/devin-automation
pip install httpx
python scripts/simulate_webhook.py \
  --issue-number 9 \
  --repo nafi-osmani/superset \
  --secret dev-local-secret \
  --title "Rename DB migration conflict workflow file" \
  --body "Rename check_db_migration_confict.yml to check_db_migration_conflict.yml"
```

Open **http://localhost:8080/dashboard** to watch the session progress.

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

Populate `GITHUB_TOKEN`:

```bash
gh auth login   # if needed
gh auth token   # paste into .env
```

### 2. Install dependencies (local run only)

```bash
pip install -r requirements.txt httpx
```

### 3. Seed issues (optional — already created on this fork)

```bash
./scripts/setup_github.sh
python scripts/create_issues.py --repo nafi-osmani/superset
```

---

## Run the service

### Option A: Docker (recommended for submission)

```bash
cd devin-automation
docker compose up --build
```

### Option B: Local uvicorn

```bash
cd devin-automation
set -a && source .env && set +a
export PYTHONPATH=src DATABASE_PATH=./data/remediator.db
python3 -m uvicorn app:app --host 0.0.0.0 --port 8080 --app-dir src
```

### Verify

```bash
curl http://localhost:8080/health
# → {"status":"ok"}
```

### Dashboard

Open **http://localhost:8080/dashboard**

> **Cursor / remote workspace:** Forward port **8080** in the Cursor **Ports** panel. Without forwarding, your browser shows `ERR_CONNECTION_REFUSED` even though the service is running on the remote VM.

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Health check |
| `GET /dashboard` | Live metrics UI (auto-refreshes every 30s) |
| `GET /api/metrics` | JSON metrics |
| `GET /api/sessions` | Session list |
| `POST /webhooks/github` | GitHub webhook receiver |

---

## Simulate the workflow (recommended for demo)

Simulates labeling an issue `devin-autofix` — **no ngrok or public URL required**.

### Step 1: Start the service

Ensure `DRY_RUN=false` in `.env` for a real Devin session.

### Step 2: Trigger remediation

Use the **actual GitHub issue number** from your fork.

**Issue #9** (workflow rename — good visual demo):

```bash
python scripts/simulate_webhook.py \
  --issue-number 9 \
  --repo nafi-osmani/superset \
  --secret dev-local-secret \
  --title "Rename DB migration conflict workflow file" \
  --body "Rename check_db_migration_confict.yml to check_db_migration_conflict.yml"
```

**Issue #8** (fastest fix — already has [PR #5](https://github.com/nafi-osmani/superset/pull/5)):

```bash
python scripts/simulate_webhook.py \
  --issue-number 8 \
  --repo nafi-osmani/superset \
  --secret dev-local-secret \
  --title "Fix typo in PR lint workflow comment" \
  --body "Fix explicity -> explicitly in .github/workflows/pr-lint.yml line 6."
```

### Step 3: Watch results

Expected response:

```json
{
  "status": "created",
  "session_id": "...",
  "session_url": "https://app.devin.ai/sessions/..."
}
```

1. Open **`session_url`** in the Devin UI
2. Refresh **http://localhost:8080/dashboard** — job shows `running`
3. Wait 30–60s, refresh — poller updates status; PR link appears when Devin finishes

### Dry-run mode (no Devin API calls)

Set `DRY_RUN=true` in `.env`, restart the service, then run the simulate command. Tests webhook handler and dashboard without spending ACUs.

### Trigger all four demo issues

```bash
for n in 6 7 8 9; do
  python scripts/simulate_webhook.py --issue-number "$n" \
    --repo nafi-osmani/superset --secret dev-local-secret
  sleep 2
done
```

---

## Real GitHub label trigger (optional)

Same handler as simulate — requires a **publicly reachable** webhook URL.

1. Start the service
2. Expose port 8080: `ngrok http 8080`
3. Fork → **Settings → Webhooks → Add webhook**
   - **Payload URL:** `https://<ngrok-id>.ngrok-free.app/webhooks/github`
   - **Content type:** `application/json`
   - **Secret:** `dev-local-secret` (must match `GITHUB_WEBHOOK_SECRET`)
   - **Events:** Issues
4. Open an issue → add label **`devin-autofix`**

No special branch merge is required — Devin clones `master` where the tech debt exists.

---

## Preflight checks

```bash
cd devin-automation

# 1. Devin API connectivity
set -a && source .env && set +a
curl -sf -X POST "https://api.devin.ai/v3/organizations/${DEVIN_ORG_ID}/sessions" \
  -H "Authorization: Bearer ${DEVIN_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Connectivity test only.","max_acu_limit":1}'

# 2. Service health
curl http://localhost:8080/health

# 3. Clean dashboard (optional)
rm -f data/remediator.db   # then restart the service

# 4. GitHub preflight
./scripts/setup_github.sh
```

---

## Observability

- **`/dashboard`** — active/completed/failed, success rate, avg duration, ACU spend, PR links
- **`/api/metrics`** — same data as JSON for leadership reporting
- **Structured logs** — `docker compose logs -f` or uvicorn stdout
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
| `ERR_CONNECTION_REFUSED` on dashboard | Browser not reaching remote VM | Forward port **8080** in Cursor Ports panel |
| `502` on webhook | Invalid Devin credentials | Check `DEVIN_API_KEY` and `DEVIN_ORG_ID` |
| `"status": "skipped"` | Active session for that issue | Wait or use a different issue number |
| `"status": "ignored"` | Wrong label in payload | Use `devin-autofix` |
| `create_issues.py` fails | Issues disabled | Enable at fork Settings → Features |
| Dashboard shows stale jobs | Old SQLite data | `rm data/remediator.db` and restart |
| PR slow to appear | Devin still working | Show Devin UI; poller updates every 30s |

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
    └── simulate_all.sh   # Trigger all demo issues (update issue numbers)
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
