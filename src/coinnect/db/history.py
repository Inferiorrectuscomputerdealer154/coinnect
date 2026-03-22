"""
Rate history — SQLite store for corridor snapshots.

Captured every 3 minutes by the background task.
Used for sparkline charts and trend analysis.
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, UTC
from pathlib import Path

logger = logging.getLogger(__name__)

# data/history.db relative to repo root
_REPO_ROOT = Path(__file__).parent.parent.parent.parent  # src/coinnect/db -> repo root
DB_PATH = _REPO_ROOT / "data" / "history.db"

# Key corridors captured on every refresh
TRACKED_CORRIDORS = [
    ("USD", "MXN", 500),
    ("USD", "BRL", 500),
    ("USD", "ARS", 500),
    ("USD", "NGN", 500),
    ("USD", "KES", 500),
    ("USD", "GHS", 500),
    ("USD", "PHP", 500),
    ("USD", "INR", 500),
    ("USD", "IDR", 500),
    ("BTC", "USD", 1),
    ("BTC", "MXN", 1),
    ("BTC", "NGN", 1),
    ("ETH", "USD", 1),
    ("USDC", "MXN", 500),
    ("USDC", "NGN", 500),
    # Inverse corridors for dual-chart
    ("MXN", "USD", 5000),
    ("BRL", "USD", 2000),
    ("NGN", "USD", 500000),
]


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS rate_snapshots (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                captured_at    TEXT    NOT NULL,
                from_currency  TEXT    NOT NULL,
                to_currency    TEXT    NOT NULL,
                amount         REAL    NOT NULL,
                best_cost_pct  REAL    NOT NULL,
                best_time_min  INTEGER NOT NULL,
                they_receive   REAL    NOT NULL,
                best_via       TEXT    NOT NULL,
                routes_json    TEXT    NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_corridor_time
                ON rate_snapshots(from_currency, to_currency, captured_at);
            CREATE INDEX IF NOT EXISTS idx_captured_at
                ON rate_snapshots(captured_at);
        """)
    logger.info(f"History DB ready at {DB_PATH}")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _write_snapshot(from_currency: str, to_currency: str, amount: float, routes: list) -> None:
    best = routes[0]
    via = "+".join(dict.fromkeys(s.via for s in best.steps))
    conn = _connect()
    try:
        conn.execute("""
            INSERT INTO rate_snapshots
                (captured_at, from_currency, to_currency, amount,
                 best_cost_pct, best_time_min, they_receive, best_via, routes_json)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            datetime.now(UTC).isoformat(),
            from_currency,
            to_currency,
            amount,
            best.total_cost_pct,
            best.total_time_minutes,
            best.they_receive,
            via,
            json.dumps([{
                "rank": r.rank,
                "label": r.label,
                "total_cost_pct": r.total_cost_pct,
                "total_time_minutes": r.total_time_minutes,
                "they_receive": r.they_receive,
                "via": "+".join(dict.fromkeys(s.via for s in r.steps)),
            } for r in routes[:5]])
        ))
        conn.commit()
    finally:
        conn.close()


async def record_snapshot(from_currency: str, to_currency: str, amount: float, routes: list) -> None:
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _write_snapshot, from_currency, to_currency, amount, routes)


def _normalize_ts(col: str) -> str:
    """SQLite expression to normalize ISO timestamps to comparable format.

    Stored timestamps have 'T' separator and '+00:00' suffix which breaks
    SQLite string comparisons against datetime('now'). We strip to 19 chars
    and replace 'T' with a space to match SQLite's datetime() output format.
    """
    return f"replace(substr({col}, 1, 19), 'T', ' ')"


def get_history(from_currency: str, to_currency: str, minutes_back: int = 10080) -> list[dict]:
    """Return time-series of best route for a corridor. minutes_back default = 7 days."""
    conn = _connect()
    ts = _normalize_ts("captured_at")
    try:
        rows = conn.execute(f"""
            SELECT captured_at, best_cost_pct, they_receive, best_via, best_time_min
            FROM rate_snapshots
            WHERE from_currency = ?
              AND to_currency   = ?
              AND {ts} >= datetime('now', ? || ' minutes')
            ORDER BY captured_at ASC
        """, (from_currency, to_currency, f"-{minutes_back}")).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_stats(from_currency: str, to_currency: str, minutes_back: int = 10080) -> dict:
    """Return min/max/avg fee for a corridor over the last N minutes."""
    conn = _connect()
    ts = _normalize_ts("captured_at")
    try:
        row = conn.execute(f"""
            SELECT
                COUNT(*)            AS points,
                MIN(best_cost_pct)  AS min_fee,
                MAX(best_cost_pct)  AS max_fee,
                AVG(best_cost_pct)  AS avg_fee,
                MIN(they_receive)   AS min_receive,
                MAX(they_receive)   AS max_receive
            FROM rate_snapshots
            WHERE from_currency = ?
              AND to_currency   = ?
              AND {ts} >= datetime('now', ? || ' minutes')
        """, (from_currency, to_currency, f"-{minutes_back}")).fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


def prune_old(keep_days: int = 30) -> int:
    """Delete snapshots older than keep_days. Returns rows deleted."""
    conn = _connect()
    try:
        ts = _normalize_ts("captured_at")
        cur = conn.execute(f"""
            DELETE FROM rate_snapshots
            WHERE {ts} < datetime('now', ? || ' days')
        """, (f"-{keep_days}",))
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()
