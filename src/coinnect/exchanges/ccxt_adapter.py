"""
CCXT adapter — fetches live rates from crypto exchanges.
Converts them into Edge objects for the routing engine.
"""

import asyncio
import logging
from datetime import datetime, UTC

import ccxt.async_support as ccxt

from coinnect.routing.engine import Edge

logger = logging.getLogger(__name__)

# Exchanges we support at launch
SUPPORTED_EXCHANGES = {
    "kraken":   {"class": ccxt.kraken,   "fee_pct": 0.26},
    "binance":  {"class": ccxt.binance,  "fee_pct": 0.10},
    "coinbase": {"class": ccxt.coinbase, "fee_pct": 0.60},
    "bitso":    {"class": ccxt.bitso,    "fee_pct": 0.65},
}

# Stablecoin used as routing intermediary
BRIDGE = "USDC"

# Cache: edges refreshed every 3 minutes
_cache: dict = {"edges": [], "updated_at": None}
CACHE_TTL_SECONDS = 180


async def fetch_edges_from_exchange(name: str, config: dict) -> list[Edge]:
    """Fetch available conversion edges from a single exchange."""
    edges = []
    exchange = config["class"]({"enableRateLimit": True})
    fee = config["fee_pct"]

    try:
        tickers = await exchange.fetch_tickers()
        for symbol, ticker in tickers.items():
            if "/" not in symbol:
                continue
            base, quote = symbol.split("/", 1)
            bid = ticker.get("bid")
            ask = ticker.get("ask")
            if not bid or not ask:
                continue

            spread_pct = ((ask - bid) / ask) * 100
            total_cost = round(fee + spread_pct, 3)
            minutes = 10 if name in ("binance", "kraken") else 20

            # base → quote
            edges.append(Edge(
                from_currency=base,
                to_currency=quote,
                via=name.capitalize(),
                fee_pct=total_cost,
                estimated_minutes=minutes,
                instructions=f"Sell {base} for {quote} on {name.capitalize()}",
            ))
            # quote → base
            edges.append(Edge(
                from_currency=quote,
                to_currency=base,
                via=name.capitalize(),
                fee_pct=total_cost,
                estimated_minutes=minutes,
                instructions=f"Buy {base} with {quote} on {name.capitalize()}",
            ))
    except Exception as e:
        logger.warning(f"Failed to fetch from {name}: {e}")
    finally:
        await exchange.close()

    return edges


async def get_all_edges(force_refresh: bool = False) -> list[Edge]:
    """Return cached edges, refreshing if stale."""
    now = datetime.now(UTC).timestamp()
    updated = _cache["updated_at"]

    if not force_refresh and updated and (now - updated) < CACHE_TTL_SECONDS:
        return _cache["edges"]

    logger.info("Refreshing exchange rates...")
    tasks = [
        fetch_edges_from_exchange(name, config)
        for name, config in SUPPORTED_EXCHANGES.items()
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    edges = []
    for result in results:
        if isinstance(result, list):
            edges.extend(result)

    _cache["edges"] = edges
    _cache["updated_at"] = now
    logger.info(f"Loaded {len(edges)} edges from {len(SUPPORTED_EXCHANGES)} exchanges")
    return edges
