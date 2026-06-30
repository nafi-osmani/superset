"""FastAPI application: webhook handler, metrics, and dashboard."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from config import settings
from devin_client import DevinClient
from github_handler import (
    format_started_comment,
    parse_issue_event,
    post_issue_comment,
    should_trigger,
    verify_github_signature,
)
from poller import SessionPoller
from store import JobStore

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

store = JobStore()
devin = DevinClient()
poller = SessionPoller(store=store, devin=devin)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    store.init_db()
    await poller.start()
    yield
    await poller.stop()


app = FastAPI(
    title="Superset Tech Debt Remediator",
    description="Event-driven Devin automation for Apache Superset tech debt",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhooks/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
) -> JSONResponse:
    payload_bytes = await request.body()

    if not verify_github_signature(payload_bytes, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")

    if x_github_event != "issues":
        return JSONResponse({"status": "ignored", "reason": "not an issues event"})

    import json

    payload = json.loads(payload_bytes)
    event = parse_issue_event(payload)
    if event is None:
        return JSONResponse({"status": "ignored", "reason": "no issue in payload"})

    if not should_trigger(event):
        return JSONResponse(
            {
                "status": "ignored",
                "reason": f"label {settings.trigger_label!r} not triggered",
            }
        )

    issue_number = event["issue_number"]
    repo = event["repo"]

    if store.has_active_job(issue_number, repo):
        return JSONResponse(
            {
                "status": "skipped",
                "reason": "active remediation already in progress",
                "issue_number": issue_number,
            }
        )

    job = store.create_job(
        issue_number=issue_number,
        issue_title=event["issue_title"],
        repo=repo,
    )

    try:
        session = devin.create_remediation_session(
            issue_number=issue_number,
            issue_title=event["issue_title"],
            issue_body=event["issue_body"],
            repo=repo,
        )
    except Exception as exc:
        logger.exception("Failed to create Devin session for issue #%s", issue_number)
        store.mark_failed(job.id, str(exc))
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    session_id = session["session_id"]
    session_url = session["url"]
    status = session.get("status", "running")

    store.update_session(
        job_id=job.id,
        devin_session_id=session_id,
        devin_url=session_url,
        status=status,
    )

    comment_body = format_started_comment(session_id, session_url)
    comment_id = post_issue_comment(repo, issue_number, comment_body)
    if comment_id:
        store.set_github_comment_id(job.id, comment_id)

    logger.info(
        "Created Devin session %s for issue #%s in %s",
        session_id,
        issue_number,
        repo,
    )

    return JSONResponse(
        {
            "status": "created",
            "job_id": job.id,
            "issue_number": issue_number,
            "session_id": session_id,
            "session_url": session_url,
        }
    )


@app.get("/api/metrics")
async def metrics() -> dict[str, Any]:
    return store.get_metrics()


@app.get("/api/sessions")
async def sessions(limit: int = 100, offset: int = 0) -> dict[str, Any]:
    jobs = store.list_jobs(limit=limit, offset=offset)
    return {
        "sessions": [
            {
                "id": job.id,
                "issue_number": job.issue_number,
                "issue_title": job.issue_title,
                "repo": job.repo,
                "devin_session_id": job.devin_session_id,
                "devin_url": job.devin_url,
                "status": job.status,
                "pr_url": job.pr_url,
                "acus_consumed": job.acus_consumed,
                "created_at": job.created_at,
                "completed_at": job.completed_at,
                "duration_sec": job.duration_sec,
                "error_message": job.error_message,
            }
            for job in jobs
        ],
        "limit": limit,
        "offset": offset,
    }


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard() -> str:
    metrics_data = store.get_metrics()
    jobs = store.list_jobs(limit=50)

    def fmt_ts(ts: int | None) -> str:
        if ts is None:
            return "—"
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    rows = ""
    for job in jobs:
        pr_cell = (
            f'<a href="{job.pr_url}">{job.pr_url}</a>' if job.pr_url else "—"
        )
        devin_cell = (
            f'<a href="{job.devin_url}">{job.devin_session_id}</a>'
            if job.devin_url
            else "—"
        )
        rows += f"""
        <tr>
          <td>#{job.issue_number}</td>
          <td>{job.issue_title}</td>
          <td><code>{job.status}</code></td>
          <td>{devin_cell}</td>
          <td>{pr_cell}</td>
          <td>{job.acus_consumed:.2f}</td>
          <td>{fmt_ts(job.created_at)}</td>
          <td>{job.duration_sec or "—"}</td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Superset Tech Debt Remediator</title>
  <meta http-equiv="refresh" content="30">
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; background: #f8f9fa; }}
    h1 {{ color: #1a1a2e; }}
    .metrics {{ display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 2rem; }}
    .card {{
      background: white; border-radius: 8px; padding: 1rem 1.5rem;
      box-shadow: 0 1px 3px rgba(0,0,0,.1); min-width: 140px;
    }}
    .card .value {{ font-size: 2rem; font-weight: 700; color: #2563eb; }}
    .card .label {{ color: #64748b; font-size: 0.875rem; }}
    table {{ border-collapse: collapse; width: 100%; background: white;
             border-radius: 8px; overflow: hidden;
             box-shadow: 0 1px 3px rgba(0,0,0,.1); }}
    th, td {{ padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid #e2e8f0; }}
    th {{ background: #1e293b; color: white; }}
    tr:hover {{ background: #f1f5f9; }}
    code {{ background: #e2e8f0; padding: 2px 6px; border-radius: 4px; }}
    a {{ color: #2563eb; }}
  </style>
</head>
<body>
  <h1>Superset Tech Debt Remediator</h1>
  <p>Event-driven Devin automation — auto-refreshes every 30s</p>

  <div class="metrics">
    <div class="card"><div class="value">{metrics_data["active"]}</div><div class="label">Active</div></div>
    <div class="card"><div class="value">{metrics_data["completed"]}</div><div class="label">Completed</div></div>
    <div class="card"><div class="value">{metrics_data["failed"]}</div><div class="label">Failed</div></div>
    <div class="card"><div class="value">{metrics_data["success_rate"]}%</div><div class="label">Success Rate</div></div>
    <div class="card"><div class="value">{metrics_data["avg_duration_sec"]}s</div><div class="label">Avg Duration</div></div>
    <div class="card"><div class="value">{metrics_data["total_acus"]}</div><div class="label">Total ACUs</div></div>
    <div class="card"><div class="value">{metrics_data["issues_with_pr"]}</div><div class="label">PRs Opened</div></div>
  </div>

  <h2>Recent Sessions</h2>
  <table>
    <thead>
      <tr>
        <th>Issue</th><th>Title</th><th>Status</th><th>Devin Session</th>
        <th>PR</th><th>ACUs</th><th>Started</th><th>Duration (s)</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>

  <p style="margin-top:2rem;color:#64748b">
    API: <a href="/api/metrics">/api/metrics</a> ·
    <a href="/api/sessions">/api/sessions</a> ·
    <a href="/health">/health</a>
  </p>
</body>
</html>"""
