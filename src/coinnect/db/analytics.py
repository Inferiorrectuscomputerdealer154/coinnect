"""
Analytics, provider config, and suggestions — all in one SQLite store.

search_log      → every /v1/quote call (for human + bot usage stats)
provider_config → enable/disable individual providers from the backoffice
suggestions     → community-submitted provider suggestions
suggestion_votes→ one vote per device fingerprint per suggestion
"""

import logging
import sqlite3
from datetime import datetime, UTC
from pathlib import Path

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).parent.parent.parent.parent
DB_PATH = _REPO_ROOT / "data" / "history.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


# ── Init ────────────────────────────────────────────────────────────────────

def init_analytics_db() -> None:
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS search_log (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                ts           TEXT NOT NULL,
                from_currency TEXT NOT NULL,
                to_currency   TEXT NOT NULL,
                amount        REAL NOT NULL,
                routes_found  INTEGER NOT NULL DEFAULT 0,
                api_key_prefix TEXT DEFAULT NULL,
                user_agent    TEXT DEFAULT NULL,
                source        TEXT DEFAULT 'web'
            );
            CREATE INDEX IF NOT EXISTS idx_search_ts
                ON search_log(ts);
            CREATE INDEX IF NOT EXISTS idx_search_corridor
                ON search_log(from_currency, to_currency);

            CREATE TABLE IF NOT EXISTS provider_config (
                name        TEXT PRIMARY KEY,
                enabled     INTEGER NOT NULL DEFAULT 1,
                paused_note TEXT DEFAULT NULL,
                updated_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS suggestions (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT NOT NULL,
                url          TEXT DEFAULT NULL,
                note         TEXT DEFAULT NULL,
                fingerprint  TEXT NOT NULL,
                votes        INTEGER NOT NULL DEFAULT 1,
                status       TEXT NOT NULL DEFAULT 'open',
                admin_note   TEXT DEFAULT NULL,
                created_at   TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS suggestion_votes (
                suggestion_id INTEGER NOT NULL,
                fingerprint   TEXT NOT NULL,
                created_at    TEXT NOT NULL,
                PRIMARY KEY (suggestion_id, fingerprint)
            );
        """)
    logger.info("Analytics DB tables ready")


# ── Search logging ──────────────────────────────────────────────────────────

def log_search(
    from_currency: str,
    to_currency: str,
    amount: float,
    routes_found: int,
    api_key: str | None = None,
    user_agent: str | None = None,
    source: str = "web",
) -> None:
    """Fire-and-forget — called from background task, never blocks the response."""
    try:
        with _connect() as conn:
            conn.execute("""
                INSERT INTO search_log
                    (ts, from_currency, to_currency, amount, routes_found,
                     api_key_prefix, user_agent, source)
                VALUES (?,?,?,?,?,?,?,?)
            """, (
                datetime.now(UTC).isoformat(),
                from_currency, to_currency, amount, routes_found,
                (api_key[:8] if api_key else None),
                (user_agent[:200] if user_agent else None),
                source,
            ))
    except Exception as e:
        logger.debug(f"search_log insert failed: {e}")


# ── Provider config ─────────────────────────────────────────────────────────

_provider_cache: dict[str, bool] = {}   # name → enabled, warmed on startup
_provider_cache_loaded = False


def _load_provider_cache() -> None:
    global _provider_cache_loaded
    try:
        with _connect() as conn:
            rows = conn.execute("SELECT name, enabled FROM provider_config").fetchall()
            for r in rows:
                _provider_cache[r["name"]] = bool(r["enabled"])
        _provider_cache_loaded = True
    except Exception as e:
        logger.warning(f"Provider config cache load failed: {e}")


def is_provider_enabled(name: str) -> bool:
    if not _provider_cache_loaded:
        _load_provider_cache()
    return _provider_cache.get(name, True)   # default: enabled


def set_provider_enabled(name: str, enabled: bool, note: str | None = None) -> None:
    now = datetime.now(UTC).isoformat()
    with _connect() as conn:
        conn.execute("""
            INSERT INTO provider_config (name, enabled, paused_note, updated_at)
            VALUES (?,?,?,?)
            ON CONFLICT(name) DO UPDATE SET
                enabled=excluded.enabled,
                paused_note=excluded.paused_note,
                updated_at=excluded.updated_at
        """, (name, 1 if enabled else 0, note, now))
    _provider_cache[name] = enabled
    logger.info(f"Provider '{name}' {'enabled' if enabled else 'disabled'}: {note}")


def get_all_provider_configs() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT name, enabled, paused_note, updated_at FROM provider_config ORDER BY name"
        ).fetchall()
        return [dict(r) for r in rows]


# ── Stats ────────────────────────────────────────────────────────────────────

def get_stats() -> dict:
    """Return dashboard stats for the admin backoffice."""
    conn = _connect()
    try:
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        # Today's searches
        searches_today = conn.execute(
            "SELECT COUNT(*) FROM search_log WHERE substr(ts,1,10)=?", (today,)
        ).fetchone()[0]
        # API key searches today
        api_searches_today = conn.execute(
            "SELECT COUNT(*) FROM search_log WHERE substr(ts,1,10)=? AND api_key_prefix IS NOT NULL",
            (today,)
        ).fetchone()[0]
        # Total searches
        searches_total = conn.execute("SELECT COUNT(*) FROM search_log").fetchone()[0]
        # Top corridors today
        top_corridors = conn.execute("""
            SELECT from_currency||'/'||to_currency AS corridor, COUNT(*) AS cnt
            FROM search_log WHERE substr(ts,1,10)=?
            GROUP BY corridor ORDER BY cnt DESC LIMIT 10
        """, (today,)).fetchall()
        # Searches last 7 days (daily buckets)
        daily = conn.execute("""
            SELECT substr(ts,1,10) AS day, COUNT(*) AS cnt
            FROM search_log
            WHERE ts >= datetime('now', '-7 days')
            GROUP BY day ORDER BY day ASC
        """).fetchall()
        # Active API keys (same DB file)
        keys_total = conn.execute("SELECT COUNT(*) FROM api_keys").fetchone()[0]
        return {
            "searches_today": searches_today,
            "api_searches_today": api_searches_today,
            "web_searches_today": searches_today - api_searches_today,
            "searches_total": searches_total,
            "keys_total": keys_total,
            "top_corridors": [dict(r) for r in top_corridors],
            "daily_searches": [dict(r) for r in daily],
            "date": today,
        }
    finally:
        conn.close()


def get_recent_searches(limit: int = 50) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("""
            SELECT ts, from_currency, to_currency, amount, routes_found,
                   api_key_prefix, source
            FROM search_log ORDER BY ts DESC LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]


# ── Suggestions ─────────────────────────────────────────────────────────────

def create_suggestion(name: str, url: str | None, note: str | None, fingerprint: str) -> dict:
    now = datetime.now(UTC).isoformat()
    with _connect() as conn:
        cur = conn.execute("""
            INSERT INTO suggestions (name, url, note, fingerprint, votes, created_at)
            VALUES (?,?,?,?,1,?)
        """, (name, url, note, fingerprint, now))
        sid = cur.lastrowid
        conn.execute(
            "INSERT INTO suggestion_votes (suggestion_id, fingerprint, created_at) VALUES (?,?,?)",
            (sid, fingerprint, now)
        )
    return {"id": sid, "name": name, "votes": 1}


def upvote_suggestion(suggestion_id: int, fingerprint: str) -> dict:
    now = datetime.now(UTC).isoformat()
    with _connect() as conn:
        # Check already voted
        existing = conn.execute(
            "SELECT 1 FROM suggestion_votes WHERE suggestion_id=? AND fingerprint=?",
            (suggestion_id, fingerprint)
        ).fetchone()
        if existing:
            return {"error": "already_voted"}
        conn.execute(
            "INSERT INTO suggestion_votes (suggestion_id, fingerprint, created_at) VALUES (?,?,?)",
            (suggestion_id, fingerprint, now)
        )
        conn.execute(
            "UPDATE suggestions SET votes=votes+1 WHERE id=?", (suggestion_id,)
        )
        row = conn.execute("SELECT votes FROM suggestions WHERE id=?", (suggestion_id,)).fetchone()
        return {"id": suggestion_id, "votes": row["votes"] if row else 0}


def get_suggestions(status: str = "open") -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("""
            SELECT id, name, url, note, votes, status, admin_note, created_at
            FROM suggestions WHERE status=?
            ORDER BY votes DESC, created_at DESC
        """, (status,)).fetchall()
        return [dict(r) for r in rows]


def set_suggestion_status(suggestion_id: int, status: str) -> None:
    with _connect() as conn:
        conn.execute("UPDATE suggestions SET status=? WHERE id=?", (status, suggestion_id))


def set_suggestion_admin_note(suggestion_id: int, note: str) -> None:
    with _connect() as conn:
        conn.execute("UPDATE suggestions SET admin_note=? WHERE id=?", (note, suggestion_id))
