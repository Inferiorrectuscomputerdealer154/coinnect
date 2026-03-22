"""
FastAPI routes — /v1/quote, /v1/exchanges, /v1/corridors, /v1/health, /v1/history,
                 /v1/keys (POST), /v1/keys/usage (GET, X-Api-Key header)
"""

import asyncio
import time
from collections import defaultdict
from datetime import datetime, UTC

from fastapi import APIRouter, Query, HTTPException, Header, Request
from pydantic import BaseModel

from coinnect.exchanges.ccxt_adapter import get_all_edges, SUPPORTED_EXCHANGES
from coinnect.exchanges.wise_adapter import get_wise_edges, get_traditional_edges
from coinnect.exchanges.yellowcard_adapter import get_yellowcard_edges
from coinnect.routing.engine import build_quote

router = APIRouter(prefix="/v1")


def _get_client_ip(request: Request) -> str:
    """Extract real client IP — respects Cloudflare CF-Connecting-IP, then X-Forwarded-For."""
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip.strip()
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _rate_limit_error(info: dict) -> HTTPException:
    """Build a 429 with a helpful human-readable message."""
    tier   = info.get("tier", "anonymous")
    limit  = info.get("limit", 0)
    reason = info.get("reason", "limit_reached")

    if reason == "hourly_limit":
        detail = (
            f"You can only make {limit} searches per hour on the {tier} plan. "
            "Try again at the top of the next hour. "
            "Get a free API key at coinnect.bot/#pricing — 1,000/day, 100/hour, no signup."
        )
    elif reason == "daily_limit":
        detail = (
            f"You can only make {limit} searches per day on the {tier} plan. "
            "Try again tomorrow. "
            "Get a free API key at coinnect.bot/#pricing — 1,000/day, no signup."
        )
    else:
        detail = "Rate limit reached. Get a free API key at coinnect.bot/#pricing — no signup required."

    return HTTPException(status_code=429, detail=detail)


async def _log_search(from_c, to_c, amount, routes_found, api_key, user_agent, source):
    import asyncio as _aio
    loop = _aio.get_event_loop()
    from coinnect.db.analytics import log_search
    await loop.run_in_executor(None, log_search, from_c, to_c, amount, routes_found, api_key, user_agent, source)


# ── Response models ────────────────────────────────────────────────────────────

class StepOut(BaseModel):
    step: int
    from_currency: str
    to_currency: str
    via: str
    fee_pct: float
    estimated_minutes: int
    instructions: str
    min_amount: float | None = None
    max_amount: float | None = None


class RouteOut(BaseModel):
    rank: int
    label: str
    total_cost_pct: float
    total_time_minutes: int
    you_send: float
    they_receive: float
    they_receive_currency: str
    steps: list[StepOut]


class QuoteOut(BaseModel):
    from_currency: str
    to_currency: str
    amount: float
    generated_at: datetime
    routes: list[RouteOut]


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/quote", response_model=QuoteOut, summary="Get ranked transfer routes")
async def quote(
    request: Request,
    from_: str = Query(..., alias="from", description="Source currency, e.g. USD"),
    to: str = Query(..., description="Destination currency, e.g. NGN"),
    amount: float = Query(..., gt=0, description="Amount in source currency"),
    x_api_key: str | None = Header(None),
    user_agent: str | None = Header(None),
):
    """
    Find the cheapest routes to send money from one currency to another.

    Returns routes ranked by total cost. Each route may have multiple steps
    across different exchanges. Coinnect never executes transfers — it only
    shows you the path.

    Safe to call from AI agents as a tool/function.
    """
    from_ = from_.upper()
    to = to.upper()

    # ── Rate limiting ────────────────────────────────────────────────────────
    from coinnect.db.keys import check_rate_limit, check_anonymous
    if x_api_key:
        allowed, info = check_rate_limit(x_api_key)
        if not allowed:
            raise _rate_limit_error(info)
    else:
        ip = _get_client_ip(request)
        allowed, info = check_anonymous(ip)
        if not allowed:
            raise _rate_limit_error(info)

    # ── Fetch edges & build quote ────────────────────────────────────────────
    from coinnect.exchanges.remittance_adapter import get_remittance_edges
    crypto_edges, wise_edges, trad_edges, yc_edges, remit_edges = await asyncio.gather(
        get_all_edges(),
        get_wise_edges(),
        get_traditional_edges(),
        get_yellowcard_edges(),
        get_remittance_edges(),
    )
    all_edges = crypto_edges + wise_edges + trad_edges + yc_edges + remit_edges

    if not all_edges:
        raise HTTPException(503, "Exchange data temporarily unavailable")

    result = build_quote(all_edges, from_, to, amount)

    if not result.routes:
        raise HTTPException(
            404,
            f"No routes found for {from_} → {to}. "
            "This corridor may not be supported yet. "
            "Check /v1/corridors for supported pairs."
        )

    source = "api" if x_api_key else "web"
    asyncio.create_task(_log_search(from_, to, amount, len(result.routes), x_api_key, user_agent, source))

    return QuoteOut(
        from_currency=result.from_currency,
        to_currency=result.to_currency,
        amount=result.amount,
        generated_at=result.generated_at,
        routes=[
            RouteOut(
                rank=r.rank,
                label=r.label,
                total_cost_pct=r.total_cost_pct,
                total_time_minutes=r.total_time_minutes,
                you_send=r.you_send,
                they_receive=r.they_receive,
                they_receive_currency=r.they_receive_currency,
                steps=[StepOut(**s.__dict__) for s in r.steps],
            )
            for r in result.routes
        ],
    )


@router.get("/exchanges", summary="List integrated exchanges")
async def exchanges():
    """List all exchanges currently integrated into Coinnect."""
    return {
        "exchanges": [
            {"name": name.capitalize(), "type": "crypto_exchange", "api": "ccxt"}
            for name in SUPPORTED_EXCHANGES
        ] + [
            {"name": "Wise", "type": "fiat_transfer", "api": "wise"},
            {"name": "Yellow Card", "type": "crypto_to_fiat", "api": "yellowcard", "region": "Africa"},
        ]
    }


@router.get("/corridors", summary="List active currency corridors")
async def corridors():
    """Returns the most commonly used currency pairs."""
    return {
        "corridors": [
            {"from": "USD", "to": "MXN", "via": ["Wise", "Coinbase+USDC+Bitso", "SPEI"]},
            {"from": "USD", "to": "BRL", "via": ["Wise", "Coinbase+USDC", "PIX"]},
            {"from": "USD", "to": "NGN", "via": ["Coinbase+USDC+Yellow Card", "Kraken+USDC+Yellow Card", "Wise"]},
            {"from": "USD", "to": "KES", "via": ["Coinbase+USDC+Yellow Card", "Wise"]},
            {"from": "USD", "to": "GHS", "via": ["Coinbase+USDC+Yellow Card", "Wise"]},
            {"from": "USD", "to": "PHP", "via": ["Wise", "Binance+USDC"]},
            {"from": "USD", "to": "INR", "via": ["Wise", "Coinbase+USDC"]},
            {"from": "USD", "to": "ARS", "via": ["Binance+USDC", "Wise"]},
            {"from": "EUR", "to": "USD", "via": ["Wise", "Kraken"]},
            {"from": "MXN", "to": "USD", "via": ["Wise", "Bitso+USDC"]},
        ]
    }


@router.get("/history", summary="Historical fee rates for a corridor")
async def history(
    from_: str = Query(..., alias="from", description="Source currency, e.g. USD"),
    to: str = Query(..., description="Destination currency, e.g. NGN"),
    days: int = Query(None, ge=1, le=365),
    minutes: int = Query(None, ge=15, le=43200),
):
    """
    Returns time-series of the best route's fee% and received amount for a corridor.
    Snapshots captured every 3 minutes for key corridors.
    """
    from coinnect.db.history import get_history, get_stats
    if minutes is not None:
        minutes_back = minutes
    elif days is not None:
        minutes_back = days * 24 * 60
    else:
        minutes_back = 7 * 24 * 60

    points = get_history(from_.upper(), to.upper(), minutes_back)
    stats = get_stats(from_.upper(), to.upper(), minutes_back)
    return {
        "from_currency": from_.upper(),
        "to_currency": to.upper(),
        "minutes": minutes_back,
        "points": points,
        "stats": stats,
    }


@router.get("/history/providers", summary="Per-provider rate history for a corridor")
async def history_providers(
    from_: str = Query(..., alias="from"),
    to: str = Query(...),
    days: int = Query(None, ge=1, le=365),
    minutes: int = Query(None, ge=15, le=43200),
):
    """
    Returns historical cost_pct per provider/route for a given corridor.
    Use this to compare e.g. Wise vs Binance P2P vs Strike over time for USD→MXN.
    """
    from coinnect.db.history import get_provider_history
    if minutes is not None:
        minutes_back = minutes
    elif days is not None:
        minutes_back = days * 24 * 60
    else:
        minutes_back = 7 * 24 * 60
    data = get_provider_history(from_.upper(), to.upper(), minutes_back)
    return {
        "from_currency": from_.upper(),
        "to_currency": to.upper(),
        "minutes": minutes_back,
        "providers": data,
    }


@router.get("/snapshot/daily", summary="Full daily rate snapshot (CSV) — open data")
async def snapshot_daily(
    date: str | None = Query(None, description="YYYY-MM-DD, defaults to today UTC"),
):
    """
    Download a full-day CSV snapshot of best-route rates for all tracked corridors.

    Each row = one 3-minute capture: corridor, amount, best cost %, received amount, provider path.

    Free, no key required. Intended for researchers, bots, and bulk analysis.
    Publish the data: cite as Coinnect Open Rate Data (coinnect.bot).
    """
    import io, csv
    from coinnect.db.history import DB_PATH, _connect, _normalize_ts

    if date:
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(400, "date must be YYYY-MM-DD")
        day = date
    else:
        day = datetime.now(UTC).strftime("%Y-%m-%d")

    ts = _normalize_ts("captured_at")
    with _connect() as conn:
        rows = conn.execute(f"""
            SELECT captured_at, from_currency, to_currency, amount,
                   best_cost_pct, best_time_min, they_receive, best_via
            FROM rate_snapshots
            WHERE substr({ts}, 1, 10) = ?
            ORDER BY captured_at ASC
        """, (day,)).fetchall()

    if not rows:
        raise HTTPException(404, f"No data for {day} yet. Snapshots are captured every 3 minutes for key corridors.")

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["captured_at_utc","from_currency","to_currency","amount","best_cost_pct","best_time_min","they_receive","best_via"])
    for r in rows:
        w.writerow([r["captured_at"], r["from_currency"], r["to_currency"], r["amount"],
                    r["best_cost_pct"], r["best_time_min"], r["they_receive"], r["best_via"]])

    from fastapi.responses import Response
    filename = f"coinnect-rates-{day}.csv"
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/snapshot/{snapshot_id}", summary="Permalink for a specific rate snapshot")
async def snapshot_permalink(snapshot_id: int):
    """
    Returns the full route data for a specific snapshot ID.

    Use this to deep-link a specific rate comparison: `/rates/{id}` renders a
    human-readable page. The snapshot is immutable — it records exactly what
    rates were available at capture time (UTC).
    """
    from coinnect.db.history import get_snapshot_by_id
    snap = get_snapshot_by_id(snapshot_id)
    if not snap:
        raise HTTPException(404, f"Snapshot #{snapshot_id} not found.")
    return snap


@router.get("/snapshot/meta", summary="Available daily snapshots — open data")
async def snapshot_meta():
    """List available dates with row counts. Use with /v1/snapshot/daily?date=YYYY-MM-DD."""
    from coinnect.db.history import _connect, _normalize_ts
    ts = _normalize_ts("captured_at")
    with _connect() as conn:
        rows = conn.execute(f"""
            SELECT substr({ts}, 1, 10) as day, COUNT(*) as rows
            FROM rate_snapshots
            GROUP BY day
            ORDER BY day DESC
            LIMIT 90
        """).fetchall()
    return {
        "dataset": "Coinnect Open Rate Data",
        "description": "Best-route fee% and received amount for key corridors, captured every 3 minutes.",
        "license": "CC-BY 4.0",
        "cite_as": "Coinnect (coinnect.bot) Open Rate Data",
        "download": "/v1/snapshot/daily?date=YYYY-MM-DD",
        "available_days": [{"date": r["day"], "rows": r["rows"]} for r in rows],
    }


@router.get("/health", summary="API health check")
async def health():
    return {
        "ok": True,
        "status": "live",
        "version": "2026.03.22.1",
        "exchanges_online": len(SUPPORTED_EXCHANGES) + 2,
        "checked_at": datetime.now(UTC).isoformat(),
    }


# ── API Key endpoints ─────────────────────────────────────────────────────────

# Rate limit key creation: max 5 keys per IP per hour
_key_create_timestamps: dict[str, list[float]] = defaultdict(list)
_KEY_CREATE_MAX_PER_HOUR = 5


@router.post("/keys", summary="Generate a self-serve API key", tags=["API Keys"])
async def create_key(request: Request, label: str | None = Query(None, max_length=80)):
    """
    Generate an API key instantly — no signup, no email, no password.

    The key is issued in the **free** tier (1,000 requests/day, 100/hour).
    Store it safely: it cannot be recovered if lost (generate a new one).

    Use it as the `X-Api-Key` header:
    ```
    curl -H "X-Api-Key: cn_..." https://coinnect.bot/v1/quote?from=USD&to=MXN&amount=500
    ```
    """
    # Rate limit key creation by IP
    ip = _get_client_ip(request)
    now = time.monotonic()
    timestamps = _key_create_timestamps[ip]
    _key_create_timestamps[ip] = [t for t in timestamps if now - t < 3600]
    if len(_key_create_timestamps[ip]) >= _KEY_CREATE_MAX_PER_HOUR:
        raise HTTPException(429, "Too many keys created — max 5 per hour. Try again later.")
    _key_create_timestamps[ip].append(now)

    from coinnect.db.keys import create_key as _create_key, TIER_LIMITS
    api_key = _create_key(tier="free", label=label)
    limits = TIER_LIMITS["free"]
    return {
        "api_key": api_key,
        "tier": "free",
        "limit_per_day": limits["day"],
        "limit_per_hour": limits["hour"],
        "message": "Store this key — it cannot be recovered. Generate a new one if lost.",
        "usage": "GET /v1/keys/usage  with header  X-Api-Key: <your key>",
    }


@router.get("/keys/usage", summary="Check usage for a key", tags=["API Keys"])
async def key_usage(x_api_key: str = Header(..., description="Your Coinnect API key (cn_...)")):
    """
    Returns today's request count and remaining quota.
    Pass the key in the `X-Api-Key` header — never in the URL.
    """
    from coinnect.db.keys import get_usage
    result = get_usage(x_api_key)
    if "error" in result:
        raise HTTPException(404, "Key not found")
    return result
