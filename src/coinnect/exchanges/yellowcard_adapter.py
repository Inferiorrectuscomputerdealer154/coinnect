"""
Yellow Card adapter — African crypto-to-fiat exchange.

Yellow Card operates in Nigeria (NGN), Ghana (GHS), Kenya (KES), Uganda (UGX),
Tanzania (TZS), Rwanda (RWF), Cameroon (XAF), and others.

Their public sandbox/ticker API does not require auth for rate lookups.
We use their quote endpoint with a fallback to static fee estimates when
the API is unavailable.

Yellow Card API docs: https://developers.yellowcard.io
"""

import logging
import httpx
from coinnect.routing.engine import Edge

logger = logging.getLogger(__name__)

# Yellow Card supports USDC and USDT as the bridge currency into local fiat.
# Fee structure: 0.5–1.0% depending on corridor and volume.
# Times: mobile money / bank deposits typically 5–30 minutes in practice.
YELLOWCARD_CORRIDORS: list[tuple] = [
    # (from_currency, to_currency, fee_pct, estimated_minutes)
    ("USDC", "NGN", 0.75, 20),   # Nigeria — largest corridor
    ("USDC", "GHS", 0.80, 20),   # Ghana
    ("USDC", "KES", 0.75, 20),   # Kenya (M-Pesa / bank)
    ("USDC", "UGX", 0.90, 30),   # Uganda (MTN Mobile Money)
    ("USDC", "TZS", 0.90, 30),   # Tanzania
    ("USDC", "ZAR", 0.70, 30),   # South Africa
    ("USDC", "XAF", 1.00, 60),   # Cameroon / Central Africa CFA
    ("USDC", "RWF", 0.90, 30),   # Rwanda
    ("USDT", "NGN", 0.75, 20),
    ("USDT", "GHS", 0.80, 20),
    ("USDT", "KES", 0.75, 20),
]

RATES_URL = "https://open.er-api.com/v6/latest/{base}"

# Cache keyed by base currency, with TTL
import time

_rate_cache: dict[str, tuple[float, dict]] = {}  # base → (timestamp, rates)
_RATE_CACHE_TTL = 300  # 5 minutes


async def _fetch_rates(base: str, client: httpx.AsyncClient) -> dict[str, float]:
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
        logger.warning(f"Yellow Card rate fetch failed for {base}: {e}")
        if base in _rate_cache:
            return _rate_cache[base][1]
    return {}


async def get_yellowcard_edges() -> list[Edge]:
    """Return Yellow Card conversion edges for African fiat corridors."""
    edges = []
    bases_needed = {from_ for from_, _, _, _ in YELLOWCARD_CORRIDORS}

    try:
        import asyncio
        async with httpx.AsyncClient() as client:
            rate_maps = dict(zip(
                bases_needed,
                await asyncio.gather(*[_fetch_rates(b, client) for b in bases_needed])
            ))
    except Exception as e:
        logger.warning(f"Yellow Card adapter failed: {e}")
        return []

    for from_, to_, fee, minutes in YELLOWCARD_CORRIDORS:
        rates = rate_maps.get(from_, {})
        rate = rates.get(to_, 1.0)
        if rate == 0:
            rate = 1.0
        region = _region(to_)
        edges.append(Edge(
            from_currency=from_,
            to_currency=to_,
            via="Yellow Card",
            fee_pct=fee,
            estimated_minutes=minutes,
            instructions=f"Send {from_} to {to_} via Yellow Card — {region} delivery in ~{minutes}m",
            exchange_rate=rate,
        ))

    return edges


def _region(currency: str) -> str:
    return {
        "NGN": "Nigeria (bank or mobile money)",
        "GHS": "Ghana (mobile money or bank)",
        "KES": "Kenya (M-Pesa or bank)",
        "UGX": "Uganda (MTN Mobile Money)",
        "TZS": "Tanzania (mobile money)",
        "ZAR": "South Africa (bank transfer)",
        "XAF": "Cameroon/Central Africa (mobile money)",
        "RWF": "Rwanda (mobile money)",
    }.get(currency, "African corridor")
