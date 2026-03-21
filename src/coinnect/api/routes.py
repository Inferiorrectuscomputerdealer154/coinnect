"""
FastAPI routes — /v1/quote, /v1/exchanges, /v1/corridors, /v1/health, /v1/history
"""

import asyncio
from datetime import datetime, UTC

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from coinnect.exchanges.ccxt_adapter import get_all_edges, SUPPORTED_EXCHANGES
from coinnect.exchanges.wise_adapter import get_wise_edges, get_traditional_edges
from coinnect.exchanges.yellowcard_adapter import get_yellowcard_edges
from coinnect.routing.engine import build_quote, QuoteResult

router = APIRouter(prefix="/v1")


# ── Response models ────────────────────────────────────────────────────────────

class StepOut(BaseModel):
    step: int
    from_currency: str
    to_currency: str
    via: str
    fee_pct: float
    estimated_minutes: int
    instructions: str


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
    from_: str = Query(..., alias="from", description="Source currency, e.g. USD"),
    to: str = Query(..., description="Destination currency, e.g. NGN"),
    amount: float = Query(..., gt=0, description="Amount in source currency"),
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

    crypto_edges, wise_edges, trad_edges, yc_edges = await asyncio.gather(
        get_all_edges(),
        get_wise_edges(),
        get_traditional_edges(),
        get_yellowcard_edges(),
    )
    all_edges = crypto_edges + wise_edges + trad_edges + yc_edges

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
    days: int = Query(7, ge=1, le=30, description="Number of days of history"),
):
    """
    Returns time-series of the best route's fee% and received amount for a currency corridor.

    Snapshots are captured automatically every 3 minutes for key corridors.
    Use this to display sparkline charts or detect fee trends.
    """
    from coinnect.db.history import get_history, get_stats
    points = get_history(from_.upper(), to.upper(), days)
    stats = get_stats(from_.upper(), to.upper(), days)
    return {
        "from_currency": from_.upper(),
        "to_currency": to.upper(),
        "days": days,
        "points": points,
        "stats": stats,
    }


@router.get("/health", summary="API health check")
async def health():
    from coinnect.db.history import DB_PATH
    return {
        "ok": True,
        "status": "live",
        "version": "0.3.0",
        "exchanges_online": len(SUPPORTED_EXCHANGES) + 2,  # +Bitso +YellowCard
        "history_db": str(DB_PATH),
        "checked_at": datetime.now(UTC).isoformat(),
    }
