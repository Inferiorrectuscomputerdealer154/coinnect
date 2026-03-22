"""
FastAPI routes — /v1/quote, /v1/exchanges, /v1/corridors, /v1/health, /v1/history,
                 /v1/keys (POST), /v1/keys/usage (GET, X-Api-Key header)
"""

import asyncio
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


@router.get("/health", summary="API health check")
async def health():
    from coinnect.db.history import DB_PATH
    return {
        "ok": True,
        "status": "live",
        "version": "2026.03.21.1",
        "exchanges_online": len(SUPPORTED_EXCHANGES) + 2,
        "history_db": str(DB_PATH),
        "checked_at": datetime.now(UTC).isoformat(),
    }


# ── API Key endpoints ─────────────────────────────────────────────────────────

@router.post("/keys", summary="Generate a self-serve API key", tags=["API Keys"])
async def create_key(label: str | None = Query(None, max_length=80)):
    """
    Generate an API key instantly — no signup, no email, no password.

    The key is issued in the **free** tier (1,000 requests/day, 100/hour).
    Store it safely: it cannot be recovered if lost (generate a new one).

    Use it as the `X-Api-Key` header:
    ```
    curl -H "X-Api-Key: cn_..." https://coinnect.bot/v1/quote?from=USD&to=MXN&amount=500
    ```
    """
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
