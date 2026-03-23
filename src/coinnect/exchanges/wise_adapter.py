"""
Wise adapter — fiat-to-fiat corridors with live exchange rates.
Exchange rates from Wise API (public /v1/rates endpoint) with fallback
to open.er-api.com when Wise is unavailable.
"""

import logging
import httpx
from coinnect.routing.engine import Edge

logger = logging.getLogger(__name__)

RATES_URL = "https://open.er-api.com/v6/latest/{base}"
WISE_RATES_URL = "https://wise.com/rates/live"
WISE_HEADERS = {"User-Agent": "Coinnect/1.0 (coinnect.bot)"}

# Fee + spread estimates per corridor — sourced from wise.com/pricing (updated manually)
# Format: (from, to, fee_pct, estimated_minutes)
WISE_CORRIDORS: list[tuple] = [
    # Latin America
    ("USD", "MXN",  2.30, 60),
    ("USD", "ARS",  4.20, 60),
    ("USD", "BRL",  2.80, 60),
    ("USD", "COP",  2.60, 60),
    ("USD", "PEN",  2.90, 60),
    # Africa
    ("USD", "NGN",  3.10, 120),
    ("USD", "KES",  3.00, 120),
    ("USD", "GHS",  3.50, 120),
    ("USD", "TZS",  3.20, 120),
    ("USD", "UGX",  3.40, 120),
    # Asia
    ("USD", "PHP",  2.10, 60),
    ("USD", "INR",  1.80, 60),
    ("USD", "BDT",  2.50, 120),
    ("USD", "PKR",  2.80, 120),
    ("USD", "LKR",  2.60, 120),
    ("USD", "NPR",  2.90, 120),
    ("USD", "IDR",  2.20, 60),
    ("USD", "VND",  2.40, 60),
    ("USD", "THB",  2.00, 60),
    # Europe/Fiat
    ("EUR", "USD",  1.90, 60),
    ("GBP", "USD",  1.80, 60),
    ("EUR", "MXN",  2.50, 60),
    ("EUR", "PHP",  2.30, 60),
    ("EUR", "INR",  2.00, 60),
    ("SGD", "PHP",  1.90, 60),
    ("SGD", "INR",  1.80, 60),
    ("SGD", "BDT",  2.30, 120),
    ("AUD", "PHP",  2.20, 60),
    ("AUD", "INR",  2.00, 60),
    ("CAD", "PHP",  2.30, 60),
    ("MXN", "USD",  2.80, 60),
    ("MXN", "EUR",  3.00, 60),
    ("BRL", "USD",  3.20, 60),
    ("COP", "USD",  3.00, 60),
    ("INR", "USD",  2.20, 60),
    ("PHP", "USD",  2.50, 60),
    ("NGN", "USD",  4.00, 120),
    ("KES", "USD",  3.50, 120),
]

# Western Union / MoneyGram — approximate fees for comparison baseline
TRADITIONAL_CORRIDORS: list[tuple] = [
    # (from, to, service, fee_pct, minutes)
    ("USD", "MXN",  "Western Union", 5.50, 10),
    ("USD", "MXN",  "MoneyGram",     5.20, 10),
    ("USD", "NGN",  "Western Union", 6.80, 30),
    ("USD", "PHP",  "Western Union", 4.80, 10),
    ("USD", "PHP",  "MoneyGram",     4.50, 10),
    ("USD", "INR",  "Western Union", 4.50, 10),
    ("USD", "IDR",  "Western Union", 5.00, 30),
    ("USD", "VND",  "Western Union", 5.20, 30),
    ("USD", "BDT",  "Western Union", 5.50, 30),
    ("USD", "PKR",  "Western Union", 5.80, 30),
    ("USD", "ARS",  "Western Union", 7.20, 30),
    ("USD", "BRL",  "Western Union", 5.80, 30),
]

# Rate cache keyed by base currency, with TTL
import asyncio
import time

_rate_cache: dict[str, tuple[float, dict]] = {}  # base -> (timestamp, rates)
_RATE_CACHE_TTL = 300  # 5 minutes

# Wise-specific rate cache keyed by "FROM-TO" pair
_wise_rate_cache: dict[str, tuple[float, float]] = {}  # "USD-MXN" -> (timestamp, rate)
_WISE_RATE_CACHE_TTL = 129600  # 36 hours — long cache to avoid rate limiting from Wise

# Track whether we've already logged a Wise block warning this cycle
_wise_block_warned: bool = False
_wise_block_warned_at: float = 0.0
_WISE_BLOCK_WARN_INTERVAL = 300  # Only warn once every 5 minutes

# Rate limiting for Wise API: batch size and delay
_WISE_BATCH_SIZE = 5
_WISE_BATCH_DELAY = 0.5  # seconds between batches


async def _fetch_rates(base: str, client: httpx.AsyncClient) -> dict[str, float]:
    """Fetch live exchange rates for a base currency."""
    now = time.monotonic()
    if base in _rate_cache:
        cached_at, rates = _rate_cache[base]
        if now - cached_at < _RATE_CACHE_TTL:
            return rates
    try:
        r = await client.get(RATES_URL.format(base=base), timeout=5)
        data = r.json()
        if data.get("result") == "success":
            rates = data.get("rates", {})
            _rate_cache[base] = (now, rates)
            return rates
    except Exception as e:
        logger.warning(f"Failed to fetch rates for {base}: {e}")
        if base in _rate_cache:
            return _rate_cache[base][1]
    return {}


async def _fetch_wise_rate(
    from_c: str, to_c: str, client: httpx.AsyncClient
) -> float | None:
    """Fetch live exchange rate from Wise public API. Returns rate or None.

    When Wise returns a block response, logs a single warning (not per-corridor)
    and returns None so the fallback FX rate kicks in.
    """
    global _wise_block_warned, _wise_block_warned_at
    key = f"{from_c}-{to_c}"
    now = time.monotonic()
    if key in _wise_rate_cache:
        cached_at, rate = _wise_rate_cache[key]
        if now - cached_at < _WISE_RATE_CACHE_TTL:
            return rate
    try:
        r = await client.get(
            WISE_RATES_URL,
            params={"source": from_c, "target": to_c},
            headers=WISE_HEADERS,
            timeout=5,
        )
        data = r.json()
        # Response: {"source":"USD","target":"MXN","value":17.9156,"time":...}
        if isinstance(data, dict) and "value" in data:
            rate = float(data["value"])
            if rate > 0:
                _wise_rate_cache[key] = (now, rate)
                logger.debug("Wise live rate %s->%s: %s", from_c, to_c, rate)
                return rate

        # Detect block response: {"response": "block"} or any non-rate response
        is_block = isinstance(data, dict) and data.get("response") == "block"
        if is_block or (isinstance(data, dict) and "value" not in data):
            # Log only once per warn interval to avoid spamming logs for all 38 corridors
            if not _wise_block_warned or (now - _wise_block_warned_at > _WISE_BLOCK_WARN_INTERVAL):
                reason = "blocked by Wise API" if is_block else f"unexpected response: {data}"
                logger.warning("Wise API %s -- all corridors will use fallback FX rates", reason)
                _wise_block_warned = True
                _wise_block_warned_at = now
            return None

        logger.warning("Unexpected Wise rates response for %s->%s: %s", from_c, to_c, data)
    except Exception as e:
        logger.warning("Failed to fetch Wise rate for %s->%s: %s", from_c, to_c, e)
        # Return stale cache if available
        if key in _wise_rate_cache:
            return _wise_rate_cache[key][1]
    return None


async def get_wise_edges() -> list[Edge]:
    """Return Wise fiat corridor edges with live exchange rates.

    Fetches rates from the Wise public API first, in batches of 5 with 0.5s
    delay between batches to avoid rate limiting. For any corridor where the
    Wise API doesn't return a rate, falls back to open.er-api.com.
    """
    edges = []
    corridors = [(from_, to_, fee, minutes) for from_, to_, fee, minutes in WISE_CORRIDORS]

    async with httpx.AsyncClient() as client:
        # 1. Try Wise live rates for all corridors (batched to avoid rate limiting)
        wise_rates: list[float | None] = []
        for batch_start in range(0, len(corridors), _WISE_BATCH_SIZE):
            batch = corridors[batch_start:batch_start + _WISE_BATCH_SIZE]
            batch_results = await asyncio.gather(
                *[_fetch_wise_rate(from_, to_, client) for from_, to_, _, _ in batch]
            )
            wise_rates.extend(batch_results)
            # Delay between batches (but not after the last batch)
            if batch_start + _WISE_BATCH_SIZE < len(corridors):
                await asyncio.sleep(_WISE_BATCH_DELAY)

        # 2. For corridors where Wise API failed, fetch fallback rates from open.er-api.com
        fallback_bases = set()
        for i, rate in enumerate(wise_rates):
            if rate is None:
                fallback_bases.add(corridors[i][0])

        fallback_maps: dict[str, dict] = {}
        if fallback_bases:
            fetched = await asyncio.gather(
                *[_fetch_rates(b, client) for b in fallback_bases]
            )
            fallback_maps = dict(zip(fallback_bases, fetched))

    for i, (from_, to_, fee, minutes) in enumerate(corridors):
        rate = wise_rates[i]
        if rate is None:
            # Fallback to open.er-api.com
            rate = fallback_maps.get(from_, {}).get(to_, 1.0)
            if rate == 0:
                rate = 1.0
            logger.debug("Using fallback rate for %s->%s: %s", from_, to_, rate)
        edges.append(Edge(
            from_currency=from_,
            to_currency=to_,
            via="Wise",
            fee_pct=fee,
            estimated_minutes=minutes,
            instructions=f"Send {from_} via Wise -- recipient gets {to_} in ~{max(1, minutes//60)}h",
            exchange_rate=rate,
        ))
    return edges


async def get_traditional_edges() -> list[Edge]:
    """Return traditional remittance edges as comparison baseline."""
    edges = []
    bases_needed = {from_ for from_, _, _, _, _ in TRADITIONAL_CORRIDORS}

    async with httpx.AsyncClient() as client:
        rate_maps = dict(zip(
            bases_needed,
            await asyncio.gather(*[_fetch_rates(b, client) for b in bases_needed])
        ))

    for from_, to_, service, fee, minutes in TRADITIONAL_CORRIDORS:
        rates = rate_maps.get(from_, {})
        rate = rates.get(to_, 1.0)
        if rate == 0:
            rate = 1.0
        edges.append(Edge(
            from_currency=from_,
            to_currency=to_,
            via=service,
            fee_pct=fee,
            estimated_minutes=minutes,
            instructions=f"Send via {service} -- fees approx {fee}% of amount",
            exchange_rate=rate,
        ))
    return edges
