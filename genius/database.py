"""Lightweight database support for Genius."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator, Optional


SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    task TEXT NOT NULL,
    payload TEXT
);

CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reminder TEXT NOT NULL,
    due_at DATETIME,
    completed INTEGER DEFAULT 0
);
"""


class DatabaseManager:
    """Thin wrapper around sqlite3 for the Genius automation app."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.path)
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.executescript(SCHEMA)
        self._connection.commit()

    @contextmanager
    def cursor(self) -> Iterator[sqlite3.Cursor]:
        cursor = self._connection.cursor()
        try:
            yield cursor
            self._connection.commit()
        finally:
            cursor.close()

    def log_action(self, task: str, payload: str | None = None) -> None:
        with self.cursor() as cur:
            cur.execute(
                "INSERT INTO audit_log (task, payload) VALUES (?, ?)",
                (task, payload),
            )

    def add_reminder(self, reminder: str, due_at: Optional[str] = None) -> int:
        with self.cursor() as cur:
            cur.execute(
                "INSERT INTO reminders (reminder, due_at) VALUES (?, ?)",
                (reminder, due_at),
            )
            return int(cur.lastrowid)

    def complete_reminder(self, reminder_id: int) -> None:
        with self.cursor() as cur:
            cur.execute(
                "UPDATE reminders SET completed = 1 WHERE id = ?",
                (reminder_id,),
            )

    def fetch_reminders(self, include_completed: bool = False) -> Iterable[tuple]:
        query = "SELECT id, reminder, due_at, completed FROM reminders"
        if not include_completed:
            query += " WHERE completed = 0"
        with self.cursor() as cur:
            cur.execute(query)
            yield from cur.fetchall()

    def close(self) -> None:
        self._connection.close()
