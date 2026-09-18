"""
db_reader.py — Pure SQLite reader for pre-computed Panchang databases.

No calculation logic here — only DB reads.  All datetime values are returned
as UTC ISO strings exactly as stored; callers handle any conversion needed.
"""

from __future__ import annotations

import os
import sqlite3
from typing import Any


def db_exists(db_path: str) -> bool:
    """Return True if the database file exists and is non-empty."""
    return os.path.isfile(db_path) and os.path.getsize(db_path) > 0


def _row_to_dict(cursor: sqlite3.Cursor, row: sqlite3.Row) -> dict[str, Any]:
    return {col[0]: row[col[0]] for col in cursor.description}


def get_meta(db_path: str) -> dict[str, Any] | None:
    """Return the meta table row as a dict, or None if unavailable."""
    if not db_exists(db_path):
        return None
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT * FROM meta LIMIT 1")
            row = cur.fetchone()
            if row is None:
                return None
            return dict(row)
    except sqlite3.Error:
        return None


def get_day(db_path: str, date_str: str) -> dict[str, Any] | None:
    """Return all fields for a single date (YYYY-MM-DD), or None if not found."""
    if not db_exists(db_path):
        return None
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                "SELECT * FROM panchang_days WHERE date = ?", (date_str,)
            )
            row = cur.fetchone()
            if row is None:
                return None
            return dict(row)
    except sqlite3.Error:
        return None


def get_range(db_path: str, start_date: str, end_date: str) -> list[dict[str, Any]]:
    """Return a list of day dicts for dates in [start_date, end_date] inclusive."""
    if not db_exists(db_path):
        return []
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                "SELECT * FROM panchang_days WHERE date >= ? AND date <= ? ORDER BY date",
                (start_date, end_date),
            )
            return [dict(row) for row in cur.fetchall()]
    except sqlite3.Error:
        return []
