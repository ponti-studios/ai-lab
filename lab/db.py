"""Shared SQLite database access for the AI lab.

Database: ~/.hominem/lab.db
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path


def _default_path() -> Path:
    return Path.home() / ".hominem" / "lab.db"


def connect(path: str | Path | None = None) -> sqlite3.Connection:
    """Open a connection to the lab database."""
    db_path = Path(path) if path else _default_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_model(conn: sqlite3.Connection, model_id: str) -> None:
    """Insert a model if it doesn't already exist."""
    conn.execute(
        "INSERT OR IGNORE INTO models (provider, model_id, display_name) VALUES (?, ?, ?)",
        (model_id.split("/")[0], model_id, model_id),
    )
    conn.commit()


def save_classification(
    conn: sqlite3.Connection,
    *,
    filename: str,
    relative_path: str | None = None,
    title: str | None = None,
    word_count: int = 0,
    domains: list[str],
    confidence: float,
    reasoning: str,
    needs_review: bool = False,
    model_id: str | None = None,
) -> int:
    """Save an essay classification result."""
    if model_id:
        ensure_model(conn, model_id)
    conn.execute(
        """
        INSERT INTO essay_classifications
            (filename, relative_path, title, word_count,
             domains_json, confidence, reasoning, needs_review, model_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            filename,
            relative_path,
            title,
            word_count,
            json.dumps(domains),
            confidence,
            reasoning,
            1 if needs_review else 0,
            model_id,
        ),
    )
    conn.commit()
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def list_classifications(
    conn: sqlite3.Connection,
    *,
    limit: int = 50,
    needs_review: bool | None = None,
) -> list[dict]:
    """List essay classifications, optionally filtered by review status."""
    sql = """
        SELECT id, filename, relative_path, title, word_count,
               domains_json, confidence, reasoning, needs_review, model_id, classified_at
        FROM essay_classifications
    """
    params: list = []
    if needs_review is not None:
        sql += " WHERE needs_review = ?"
        params.append(1 if needs_review else 0)
    sql += " ORDER BY classified_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    return [
        {
            "id": r["id"],
            "filename": r["filename"],
            "relative_path": r["relative_path"],
            "title": r["title"],
            "word_count": r["word_count"],
            "domains": json.loads(r["domains_json"]),
            "confidence": r["confidence"],
            "reasoning": r["reasoning"],
            "needs_review": bool(r["needs_review"]),
            "model_id": r["model_id"],
            "classified_at": r["classified_at"],
        }
        for r in rows
    ]
