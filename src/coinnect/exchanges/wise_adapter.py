"""
Wise API adapter — fiat-to-fiat corridors.
Uses Wise's public price comparison endpoint (no auth required for quotes).
"""

import logging
import httpx
from coinnect.routing.engine import Edge

logger = logging.getLogger(__name__)

WISE_URL = "https://api.wise.com/v1/rates"

# Wise fee approximation by corridor (actual fees vary — updated periodically)
# Source: wise.com/us/pricing/
WISE_FEES: dict[str, float] = {
    "USD_MXN": 2.3,
    "USD_NGN": 3.1,
    "USD_PHP": 2.1,
    "USD_INR": 1.8,
    "USD_BDT": 2.5,
    "USD_KES": 3.0,
    "USD_GHS": 3.5,
    "EUR_USD": 1.9,
    "GBP_USD": 1.8,
}


async def get_wise_edges() -> list[Edge]:
    """Fetch Wise rates and return as edges."""
    edges = []
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(WISE_URL)
            resp.raise_for_status()
            rates = resp.json()

        rate_map = {f"{r['source']}_{r['target']}": r["rate"] for r in rates}

        for pair, fee in WISE_FEES.items():
            src, tgt = pair.split("_")
            if pair in rate_map:
                edges.append(Edge(
                    from_currency=src,
                    to_currency=tgt,
                    via="Wise",
                    fee_pct=fee,
                    estimated_minutes=60,
                    instructions=f"Send {src} via Wise — recipient receives {tgt} in ~1 hour",
                ))

    except Exception as e:
        logger.warning(f"Wise API error: {e}")

    return edges
