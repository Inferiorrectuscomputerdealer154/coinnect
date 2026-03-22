"""
Wise adapter — fiat-to-fiat corridors with live exchange rates.
Rates from open.er-api.com (free, no auth).
"""

import logging
import httpx
from coinnect.routing.engine import Edge

logger = logging.getLogger(__name__)

RATES_URL = "https://open.er-api.com/v6/latest/{base}"

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
import time

_rate_cache: dict[str, tuple[float, dict]] = {}  # base → (timestamp, rates)
_RATE_CACHE_TTL = 300  # 5 minutes


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


async def get_wise_edges() -> list[Edge]:
    """Return Wise fiat corridor edges with live exchange rates."""
    edges = []
    bases_needed = {from_ for from_, _, _, _ in WISE_CORRIDORS}

    async with httpx.AsyncClient() as client:
        import asyncio
        rate_maps = dict(zip(
            bases_needed,
            await asyncio.gather(*[_fetch_rates(b, client) for b in bases_needed])
        ))

    for from_, to_, fee, minutes in WISE_CORRIDORS:
        rates = rate_maps.get(from_, {})
        rate = rates.get(to_, 1.0)
        if rate == 0:
            rate = 1.0
        edges.append(Edge(
            from_currency=from_,
            to_currency=to_,
            via="Wise",
            fee_pct=fee,
            estimated_minutes=minutes,
            instructions=f"Send {from_} via Wise — recipient gets {to_} in ~{max(1, minutes//60)}h",
            exchange_rate=rate,
        ))
    return edges


async def get_traditional_edges() -> list[Edge]:
    """Return traditional remittance edges as comparison baseline."""
    edges = []
    bases_needed = {from_ for from_, _, _, _, _ in TRADITIONAL_CORRIDORS}

    async with httpx.AsyncClient() as client:
        import asyncio
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
            instructions=f"Send via {service} — fees approx {fee}% of amount",
            exchange_rate=rate,
        ))
    return edges
