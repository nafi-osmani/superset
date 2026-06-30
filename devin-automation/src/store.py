"""SQLite persistence for remediation jobs and metrics."""

from __future__ import annotations

import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from config import settings

TERMINAL_STATUSES = frozenset({"exit", "error", "suspended"})
ACTIVE_STATUSES = frozenset({"pending", "new", "claimed", "running", "resuming"})


@dataclass
class RemediationJob:
    id: int
    issue_number: int
    issue_title: str
    repo: str
    devin_session_id: str | None
    devin_url: str | None
    status: str
    pr_url: str | None
    acus_consumed: float
    created_at: int
    completed_at: int | None
    duration_sec: float | None
    error_message: str | None
    github_comment_id: int | None


class JobStore:
    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or settings.database_path

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS remediation_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    issue_number INTEGER NOT NULL,
                    issue_title TEXT NOT NULL,
                    repo TEXT NOT NULL,
                    devin_session_id TEXT,
                    devin_url TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    pr_url TEXT,
                    acus_consumed REAL DEFAULT 0,
                    created_at INTEGER NOT NULL,
                    completed_at INTEGER,
                    duration_sec REAL,
                    error_message TEXT,
                    github_comment_id INTEGER,
                    UNIQUE(issue_number, repo)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_jobs_status
                ON remediation_jobs(status)
                """
            )

    def has_active_job(self, issue_number: int, repo: str) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT status FROM remediation_jobs
                WHERE issue_number = ? AND repo = ?
                """,
                (issue_number, repo),
            ).fetchone()
        if row is None:
            return False
        return row["status"] not in TERMINAL_STATUSES

    def create_job(
        self,
        issue_number: int,
        issue_title: str,
        repo: str,
    ) -> RemediationJob:
        now = int(time.time())
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO remediation_jobs
                    (issue_number, issue_title, repo, status, created_at)
                VALUES (?, ?, ?, 'pending', ?)
                ON CONFLICT(issue_number, repo) DO UPDATE SET
                    issue_title = excluded.issue_title,
                    devin_session_id = CASE
                        WHEN remediation_jobs.status IN ('exit', 'error', 'suspended')
                        THEN NULL
                        ELSE remediation_jobs.devin_session_id
                    END,
                    devin_url = CASE
                        WHEN remediation_jobs.status IN ('exit', 'error', 'suspended')
                        THEN NULL
                        ELSE remediation_jobs.devin_url
                    END,
                    status = CASE
                        WHEN remediation_jobs.status IN ('exit', 'error', 'suspended')
                        THEN 'pending'
                        ELSE remediation_jobs.status
                    END,
                    pr_url = CASE
                        WHEN remediation_jobs.status IN ('exit', 'error', 'suspended')
                        THEN NULL
                        ELSE remediation_jobs.pr_url
                    END,
                    created_at = CASE
                        WHEN remediation_jobs.status IN ('exit', 'error', 'suspended')
                        THEN excluded.created_at
                        ELSE remediation_jobs.created_at
                    END,
                    completed_at = CASE
                        WHEN remediation_jobs.status IN ('exit', 'error', 'suspended')
                        THEN NULL
                        ELSE remediation_jobs.completed_at
                    END,
                    error_message = CASE
                        WHEN remediation_jobs.status IN ('exit', 'error', 'suspended')
                        THEN NULL
                        ELSE remediation_jobs.error_message
                    END
                """,
                (issue_number, issue_title, repo, now),
            )
            row = conn.execute(
                """
                SELECT * FROM remediation_jobs
                WHERE issue_number = ? AND repo = ?
                """,
                (issue_number, repo),
            ).fetchone()
        if row is None:
            raise RuntimeError(
                f"Failed to create or fetch job for issue #{issue_number} in {repo}"
            )
        return self._row_to_job(row)

    def update_session(
        self,
        job_id: int,
        devin_session_id: str,
        devin_url: str,
        status: str,
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                UPDATE remediation_jobs
                SET devin_session_id = ?, devin_url = ?, status = ?
                WHERE id = ?
                """,
                (devin_session_id, devin_url, status, job_id),
            )

    def update_from_devin(
        self,
        job_id: int,
        status: str,
        pr_url: str | None,
        acus_consumed: float,
        error_message: str | None = None,
    ) -> None:
        now = int(time.time())
        with self._conn() as conn:
            row = conn.execute(
                "SELECT created_at FROM remediation_jobs WHERE id = ?",
                (job_id,),
            ).fetchone()
            completed_at = now if status in TERMINAL_STATUSES else None
            duration_sec = (
                float(now - row["created_at"]) if completed_at is not None else None
            )
            conn.execute(
                """
                UPDATE remediation_jobs
                SET status = ?, pr_url = ?, acus_consumed = ?,
                    completed_at = ?, duration_sec = ?, error_message = ?
                WHERE id = ?
                """,
                (
                    status,
                    pr_url,
                    acus_consumed,
                    completed_at,
                    duration_sec,
                    error_message,
                    job_id,
                ),
            )

    def set_github_comment_id(self, job_id: int, comment_id: int) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE remediation_jobs SET github_comment_id = ? WHERE id = ?",
                (comment_id, job_id),
            )

    def mark_failed(self, job_id: int, error_message: str) -> None:
        self.update_from_devin(
            job_id=job_id,
            status="error",
            pr_url=None,
            acus_consumed=0,
            error_message=error_message,
        )

    def list_jobs(self, limit: int = 100, offset: int = 0) -> list[RemediationJob]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM remediation_jobs
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()
        return [self._row_to_job(row) for row in rows]

    def get_active_jobs(self) -> list[RemediationJob]:
        with self._conn() as conn:
            placeholders = ",".join("?" for _ in ACTIVE_STATUSES)
            rows = conn.execute(
                f"""
                SELECT * FROM remediation_jobs
                WHERE status IN ({placeholders})
                ORDER BY created_at ASC
                """,
                tuple(ACTIVE_STATUSES),
            ).fetchall()
        return [self._row_to_job(row) for row in rows]

    def get_job_by_id(self, job_id: int) -> RemediationJob | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM remediation_jobs WHERE id = ?",
                (job_id,),
            ).fetchone()
        return self._row_to_job(row) if row else None

    def get_metrics(self) -> dict[str, Any]:
        with self._conn() as conn:
            total = conn.execute("SELECT COUNT(*) AS c FROM remediation_jobs").fetchone()[
                "c"
            ]
            active = conn.execute(
                f"""
                SELECT COUNT(*) AS c FROM remediation_jobs
                WHERE status IN ({",".join("?" for _ in ACTIVE_STATUSES)})
                """,
                tuple(ACTIVE_STATUSES),
            ).fetchone()["c"]
            completed = conn.execute(
                "SELECT COUNT(*) AS c FROM remediation_jobs WHERE status = 'exit'"
            ).fetchone()["c"]
            failed = conn.execute(
                """
                SELECT COUNT(*) AS c FROM remediation_jobs
                WHERE status IN ('error', 'suspended')
                """
            ).fetchone()["c"]
            avg_duration = conn.execute(
                """
                SELECT AVG(duration_sec) AS avg FROM remediation_jobs
                WHERE duration_sec IS NOT NULL
                """
            ).fetchone()["avg"]
            total_acus = conn.execute(
                "SELECT COALESCE(SUM(acus_consumed), 0) AS s FROM remediation_jobs"
            ).fetchone()["s"]
            with_pr = conn.execute(
                """
                SELECT COUNT(*) AS c FROM remediation_jobs
                WHERE pr_url IS NOT NULL AND pr_url != ''
                """
            ).fetchone()["c"]

        finished = completed + failed
        success_rate = (completed / finished * 100) if finished > 0 else 0.0

        return {
            "total_jobs": total,
            "active": active,
            "completed": completed,
            "failed": failed,
            "success_rate": round(success_rate, 1),
            "avg_duration_sec": round(avg_duration or 0, 1),
            "total_acus": round(total_acus or 0, 2),
            "issues_with_pr": with_pr,
        }

    @staticmethod
    def _row_to_job(row: sqlite3.Row) -> RemediationJob:
        return RemediationJob(
            id=row["id"],
            issue_number=row["issue_number"],
            issue_title=row["issue_title"],
            repo=row["repo"],
            devin_session_id=row["devin_session_id"],
            devin_url=row["devin_url"],
            status=row["status"],
            pr_url=row["pr_url"],
            acus_consumed=row["acus_consumed"] or 0,
            created_at=row["created_at"],
            completed_at=row["completed_at"],
            duration_sec=row["duration_sec"],
            error_message=row["error_message"],
            github_comment_id=row["github_comment_id"],
        )
