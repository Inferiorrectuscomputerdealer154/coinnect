"""
FastAPI routes — /v1/quote, /v1/exchanges, /v1/corridors, /v1/health
"""

import asyncio
from datetime import datetime, UTC

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from coinnect.exchanges.ccxt_adapter import get_all_edges, SUPPORTED_EXCHANGES
from coinnect.exchanges.wise_adapter import get_wise_edges
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

    crypto_edges, wise_edges = await asyncio.gather(
        get_all_edges(),
        get_wise_edges(),
    )
    all_edges = crypto_edges + wise_edges

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
        ]
    }


@router.get("/corridors", summary="List active currency corridors")
async def corridors():
    """Returns the most commonly used currency pairs."""
    return {
        "corridors": [
            {"from": "USD", "to": "MXN", "via": ["Wise", "Bitso+USDC"]},
            {"from": "USD", "to": "NGN", "via": ["Kraken+YellowCard"]},
            {"from": "USD", "to": "PHP", "via": ["Wise", "Binance+GCash"]},
            {"from": "USD", "to": "ARS", "via": ["Binance+Lemon"]},
            {"from": "EUR", "to": "USD", "via": ["Wise", "Kraken"]},
        ]
    }


@router.get("/health", summary="API health check")
async def health():
    return {
        "ok": True,
        "status": "live",
        "exchanges_online": len(SUPPORTED_EXCHANGES) + 1,
        "checked_at": datetime.now(UTC).isoformat(),
    }
