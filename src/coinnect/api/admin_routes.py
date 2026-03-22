"""
Admin API routes — /admin/*, /v1/suggestions/*

The admin endpoints require X-Admin-Key header.
The admin key is read from COINNECT_ADMIN_KEY env var (default: 'coinnect-admin').
Suggestions endpoints are public (fingerprint-gated on the write side).
"""

import os
import logging
import time
from collections import defaultdict
from fastapi import APIRouter, HTTPException, Header, Query, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

ADMIN_KEY = os.environ.get("COINNECT_ADMIN_KEY")
if not ADMIN_KEY:
    logger.warning("COINNECT_ADMIN_KEY not set — admin endpoints will reject all requests")
    ADMIN_KEY = None


def _require_admin_key_configured() -> None:
    if ADMIN_KEY is None:
        raise HTTPException(503, "Admin endpoints disabled — COINNECT_ADMIN_KEY not configured")

admin_router = APIRouter(prefix="/admin")
suggest_router = APIRouter(prefix="/v1/suggestions")


def _require_admin(x_admin_key: str | None) -> None:
    _require_admin_key_configured()
    if not x_admin_key or x_admin_key != ADMIN_KEY:
        raise HTTPException(401, "Invalid or missing X-Admin-Key")


# ── Admin: stats ─────────────────────────────────────────────────────────────

@admin_router.get("/stats")
async def admin_stats(x_admin_key: str | None = Header(None)):
    _require_admin(x_admin_key)
    from coinnect.db.analytics import get_stats
    return get_stats()


@admin_router.get("/searches")
async def admin_searches(
    limit: int = Query(50, ge=1, le=500),
    x_admin_key: str | None = Header(None),
):
    _require_admin(x_admin_key)
    from coinnect.db.analytics import get_recent_searches
    return {"searches": get_recent_searches(limit)}


# ── Admin: provider management ────────────────────────────────────────────────

class ProviderUpdate(BaseModel):
    enabled: bool
    note: str | None = None


@admin_router.get("/providers")
async def admin_providers(x_admin_key: str | None = Header(None)):
    _require_admin(x_admin_key)
    from coinnect.db.analytics import get_all_provider_configs
    return {"providers": get_all_provider_configs()}


@admin_router.post("/providers/{name}")
async def admin_set_provider(
    name: str,
    body: ProviderUpdate,
    x_admin_key: str | None = Header(None),
):
    _require_admin(x_admin_key)
    from coinnect.db.analytics import set_provider_enabled
    set_provider_enabled(name, body.enabled, body.note)
    return {"name": name, "enabled": body.enabled}


# ── Admin: suggestions moderation ────────────────────────────────────────────

@admin_router.get("/suggestions")
async def admin_suggestions(
    status: str = Query("open"),
    x_admin_key: str | None = Header(None),
):
    _require_admin(x_admin_key)
    from coinnect.db.analytics import get_suggestions
    return {"suggestions": get_suggestions(status)}


@admin_router.post("/suggestions/{sid}/status")
async def admin_set_suggestion_status(
    sid: int,
    status: str = Query(..., pattern="^(open|accepted|rejected)$"),
    x_admin_key: str | None = Header(None),
):
    _require_admin(x_admin_key)
    from coinnect.db.analytics import set_suggestion_status
    set_suggestion_status(sid, status)
    return {"id": sid, "status": status}


@admin_router.post("/suggestions/{sid}/note")
async def admin_set_suggestion_note(
    sid: int,
    note: str = Query(..., max_length=300),
    x_admin_key: str | None = Header(None),
):
    _require_admin(x_admin_key)
    from coinnect.db.analytics import set_suggestion_admin_note
    set_suggestion_admin_note(sid, note)
    return {"id": sid, "admin_note": note}


# ── Public: suggestions (fingerprint + IP rate-limited) ───────────────────────

# Anti-abuse: limit suggestion creation and votes per IP
_suggest_ip_counts: dict[str, list[float]] = defaultdict(list)  # ip → [timestamps]
_SUGGEST_MAX_PER_HOUR = 5  # max suggestions per IP per hour
_VOTE_MAX_PER_HOUR = 20    # max votes per IP per hour


def _check_ip_rate(ip: str, limit: int) -> bool:
    """Return True if under limit, False if exceeded."""
    now = time.monotonic()
    timestamps = _suggest_ip_counts[ip]
    # Prune entries older than 1 hour
    _suggest_ip_counts[ip] = [t for t in timestamps if now - t < 3600]
    if len(_suggest_ip_counts[ip]) >= limit:
        return False
    _suggest_ip_counts[ip].append(now)
    return True


def _get_client_ip(request: Request) -> str:
    return (
        request.headers.get("CF-Connecting-IP")
        or request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.client.host
        if request.client else "unknown"
    )


class SuggestionCreate(BaseModel):
    name: str
    url: str | None = None
    note: str | None = None
    fingerprint: str


class UpvoteBody(BaseModel):
    fingerprint: str


@suggest_router.get("")
async def list_suggestions():
    from coinnect.db.analytics import get_suggestions
    return {"suggestions": get_suggestions("open")}


@suggest_router.post("")
async def create_suggestion(body: SuggestionCreate, request: Request):
    if not body.name or len(body.name) > 100:
        raise HTTPException(400, "name is required and must be under 100 chars")
    if not body.fingerprint or len(body.fingerprint) < 4:
        raise HTTPException(400, "fingerprint required")
    ip = _get_client_ip(request)
    if not _check_ip_rate(f"suggest:{ip}", _SUGGEST_MAX_PER_HOUR):
        raise HTTPException(429, "Too many suggestions — try again later")
    from coinnect.db.analytics import create_suggestion
    result = create_suggestion(body.name, body.url, body.note, body.fingerprint)
    return result


@suggest_router.post("/{sid}/upvote")
async def upvote_suggestion(sid: int, body: UpvoteBody, request: Request):
    if not body.fingerprint or len(body.fingerprint) < 4:
        raise HTTPException(400, "fingerprint required")
    ip = _get_client_ip(request)
    if not _check_ip_rate(f"vote:{ip}", _VOTE_MAX_PER_HOUR):
        raise HTTPException(429, "Too many votes — try again later")
    from coinnect.db.analytics import upvote_suggestion
    result = upvote_suggestion(sid, body.fingerprint)
    if "error" in result:
        raise HTTPException(409, result["error"])
    return result
