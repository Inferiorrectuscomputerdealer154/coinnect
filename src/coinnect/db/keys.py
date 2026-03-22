"""
API key management — self-serve, userless.

Tiers (per_day / per_hour):
  anonymous  — 20/day,    50/hour   (IP-tracked, no key required)
  free       — 1,000/day,  100/hour (self-serve key, no signup)
  agent      — 5,000/day,  200/hour (bots, AI agents, automated scripts)
  pro        — 50,000/day, 2,000/hour (future)
"""

import logging
import secrets
import sqlite3
from datetime import datetime, UTC
from pathlib import Path

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).parent.parent.parent.parent
DB_PATH = _REPO_ROOT / "data" / "history.db"

TIER_LIMITS: dict[str, dict[str, int]] = {
    "anonymous": {"day": 20,     "hour": 50},
    "free":      {"day": 1_000,  "hour": 100},
    "agent":     {"day": 5_000,  "hour": 200},
    "pro":       {"day": 50_000, "hour": 2_000},
}

# ── In-memory counters ───────────────────────────────────────────────────────
_day_str:  str = ""
_hour_str: str = ""
_day_counts:  dict[str, int] = {}   # api_key  → requests today
_hour_counts: dict[str, int] = {}   # api_key  → requests this hour
_ip_day:  dict[str, int] = {}       # client_ip → requests today   (anonymous)
_ip_hour: dict[str, int] = {}       # client_ip → requests this hour (anonymous)
_key_tier_cache: dict[str, str] = {}


def _now_day() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def _now_hour() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H")


def _reset_if_needed() -> None:
    global _day_str, _hour_str
    d = _now_day()
    h = _now_hour()
    if d != _day_str:
        _day_counts.clear()
        _ip_day.clear()
        _day_str = d
        logger.info("Daily rate counters reset")
    if h != _hour_str:
        _hour_counts.clear()
        _ip_hour.clear()
        _hour_str = h


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


# ── DB init ──────────────────────────────────────────────────────────────────

def init_keys_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS api_keys (
                api_key     TEXT PRIMARY KEY,
                tier        TEXT NOT NULL DEFAULT 'free',
                created_at  TEXT NOT NULL,
                label       TEXT DEFAULT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_api_keys_key ON api_keys(api_key);
        """)
    _warm_key_cache()
    logger.info("API keys DB ready")


def _warm_key_cache() -> None:
    try:
        with _connect() as conn:
            rows = conn.execute("SELECT api_key, tier FROM api_keys").fetchall()
            for r in rows:
                _key_tier_cache[r["api_key"]] = r["tier"]
        logger.info(f"Key cache warmed: {len(_key_tier_cache)} keys")
    except Exception as e:
        logger.warning(f"Key cache warm failed: {e}")


# ── Key operations ────────────────────────────────────────────────────────────

def create_key(tier: str = "free", label: str | None = None) -> str:
    api_key = f"cn_{secrets.token_urlsafe(24)}"
    now = datetime.now(UTC).isoformat()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO api_keys (api_key, tier, created_at, label) VALUES (?,?,?,?)",
            (api_key, tier, now, label)
        )
    _key_tier_cache[api_key] = tier
    logger.info(f"New API key created: tier={tier}")
    return api_key


def get_key_tier(api_key: str) -> str | None:
    if api_key in _key_tier_cache:
        return _key_tier_cache[api_key]
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT tier FROM api_keys WHERE api_key = ?", (api_key,)
            ).fetchone()
            if row:
                _key_tier_cache[api_key] = row["tier"]
                return row["tier"]
    except Exception:
        pass
    return None


# ── Rate limiting ─────────────────────────────────────────────────────────────

def check_rate_limit(api_key: str) -> tuple[bool, dict]:
    """
    Check key rate limits (day + hour).
    Returns (allowed, info_dict).
    On failure: info has reason, limit, used, tier.
    """
    _reset_if_needed()
    tier = get_key_tier(api_key)
    if tier is None:
        return False, {"reason": "unknown_key"}
    limits = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
    day_used  = _day_counts.get(api_key, 0)
    hour_used = _hour_counts.get(api_key, 0)

    if day_used >= limits["day"]:
        return False, {"reason": "daily_limit",  "limit": limits["day"],  "used": day_used,  "tier": tier}
    if hour_used >= limits["hour"]:
        return False, {"reason": "hourly_limit", "limit": limits["hour"], "used": hour_used, "tier": tier}

    _day_counts[api_key]  = day_used  + 1
    _hour_counts[api_key] = hour_used + 1
    return True, {
        "day_used":   day_used  + 1, "day_limit":  limits["day"],
        "hour_used":  hour_used + 1, "hour_limit": limits["hour"],
        "tier": tier,
    }


def check_anonymous(ip: str) -> tuple[bool, dict]:
    """
    Check rate limits for keyless requests by IP.
    Returns (allowed, info_dict).
    """
    _reset_if_needed()
    limits = TIER_LIMITS["anonymous"]
    day_used  = _ip_day.get(ip, 0)
    hour_used = _ip_hour.get(ip, 0)

    if day_used >= limits["day"]:
        return False, {"reason": "daily_limit",  "limit": limits["day"],  "used": day_used,  "tier": "anonymous"}
    if hour_used >= limits["hour"]:
        return False, {"reason": "hourly_limit", "limit": limits["hour"], "used": hour_used, "tier": "anonymous"}

    _ip_day[ip]  = day_used  + 1
    _ip_hour[ip] = hour_used + 1
    return True, {
        "day_used":   day_used  + 1, "day_limit":  limits["day"],
        "hour_used":  hour_used + 1, "hour_limit": limits["hour"],
        "tier": "anonymous",
    }


def get_usage(api_key: str) -> dict:
    _reset_if_needed()
    tier = get_key_tier(api_key)
    if tier is None:
        return {"error": "unknown_key"}
    limits = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
    day_used  = _day_counts.get(api_key, 0)
    hour_used = _hour_counts.get(api_key, 0)
    return {
        "api_key":         api_key[:8] + "…",
        "tier":            tier,
        "requests_today":  day_used,
        "limit_per_day":   limits["day"],
        "remaining_today": max(0, limits["day"]  - day_used),
        "requests_hour":   hour_used,
        "limit_per_hour":  limits["hour"],
        "remaining_hour":  max(0, limits["hour"] - hour_used),
        "date":            _now_day(),
        "hour":            _now_hour(),
    }
