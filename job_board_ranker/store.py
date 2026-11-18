"""SQLite store so each run only shows postings it has not seen before."""
from __future__ import annotations

import sqlite3

from .boards import Posting

SCHEMA = """CREATE TABLE IF NOT EXISTS seen (
    source TEXT, external_id TEXT, company TEXT, title TEXT, url TEXT,
    first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (source, external_id))"""


def open_db(path: str = "postings.db") -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute(SCHEMA)
    return conn


def new_only(conn: sqlite3.Connection, postings: list[Posting]) -> list[Posting]:
    """Record every posting and return only those not seen before."""
    fresh = []
    for p in postings:
        cur = conn.execute(
            "INSERT OR IGNORE INTO seen (source, external_id, company, title, url) VALUES (?,?,?,?,?)",
            (p.source, p.external_id, p.company, p.title, p.url))
        if cur.rowcount:
            fresh.append(p)
    conn.commit()
    return fresh
