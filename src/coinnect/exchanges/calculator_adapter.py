"""
Live calculator adapters — scrape semi-public calculator/estimate endpoints.

These are the internal API endpoints that remittance provider websites use for
their own calculators. They may break without notice, require sessions, or
return 403. Each adapter is designed to fail gracefully and return [].

Tested 2026-03-22. Results per provider:
  - Remitly:     attempts /us/en/api/v3/calculator/estimate (may need session cookie)
  - Wise:        /gateway/v3/quotes — requires auth, but /gateway/v1/quotes may work
  - TransferGo:  my.transfergo.com/api/quotes — may return JSON quotes
  - Xe/x-rates:  x-rates.com HTML scrape for mid-market rate
  - WU/MG/Pangea: all require JS rendering or session tokens — skipped in code,
                   kept as stubs for future re-testing

All adapters use a 5-minute TTL cache and return list[Edge].
"""

import asyncio
import logging
import re
import time
from dataclasses import dataclass

import httpx

from coinnect.routing.engine import Edge

logger = logging.getLogger(__name__)

# ── Shared ────────────────────────────────────────────────────────────────────

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

CALC_TTL = 300  # 5 minutes for all calculator caches

_remitly_cache: dict = {"edges": [], "ts": 0.0}
_wise_calc_cache: dict = {"edges": [], "ts": 0.0}
_transfergo_cache: dict = {"edges": [], "ts": 0.0}
_xrates_cache: dict = {"edges": [], "ts": 0.0}


def _cache_fresh(cache: dict) -> bool:
    return bool(cache["edges"]) and (time.monotonic() - cache["ts"]) < CALC_TTL


# ── 1. Remitly Calculator ─────────────────────────────────────────────────────
# Endpoint: GET /us/en/api/v3/calculator/estimate
# Known behavior: may return JSON with exchange_rate, fee, receive_amount
# or may redirect / return HTML if session cookie is missing.
# We try two URL patterns.

REMITLY_CORRIDORS = [
    ("US", "MX", "USD", "MXN", 500),
    ("US", "PH", "USD", "PHP", 500),
    ("US", "IN", "USD", "INR", 500),
    ("US", "NG", "USD", "NGN", 500),
    ("US", "BR", "USD", "BRL", 500),
    ("US", "CO", "USD", "COP", 500),
    ("US", "GT", "USD", "GTQ", 500),
    ("US", "SV", "USD", "USD", 500),  # El Salvador uses USD
    ("GB", "PH", "GBP", "PHP", 400),
    ("GB", "IN", "GBP", "INR", 400),
    ("CA", "PH", "CAD", "PHP", 500),
    ("CA", "IN", "CAD", "INR", 500),
]

REMITLY_URLS = [
    # Pattern 1: website-internal API
    "https://www.remitly.com/{from_lower}/en/api/v3/calculator/estimate"
    "?from_country_code={from_country}&to_country_code={to_country}"
    "&send_amount={amount}",
    # Pattern 2: separate API host
    "https://api.remitly.io/v3/calculator/estimate"
    "?from={from_country}&to={to_country}&amount={amount}",
]


async def _fetch_remitly_corridor(
    client: httpx.AsyncClient,
    from_country: str, to_country: str,
    from_ccy: str, to_ccy: str, amount: int,
) -> Edge | None:
    """Try Remitly calculator for one corridor. Return Edge or None."""
    for url_template in REMITLY_URLS:
        url = url_template.format(
            from_lower=from_country.lower(),
            from_country=from_country,
            to_country=to_country,
            amount=amount,
        )
        try:
            r = await client.get(url, headers=BROWSER_HEADERS, timeout=10)
            if r.status_code != 200:
                continue
            ct = r.headers.get("content-type", "")
            if "json" not in ct:
                continue
            data = r.json()

            # Remitly returns various JSON shapes; try common field names
            exchange_rate = (
                data.get("exchange_rate")
                or data.get("exchangeRate")
                or data.get("rate")
            )
            fee = data.get("fee") or data.get("transfer_fee") or data.get("totalFee")
            receive = (
                data.get("receive_amount")
                or data.get("receiveAmount")
                or data.get("destination_amount")
            )

            if exchange_rate and float(exchange_rate) > 0:
                exchange_rate = float(exchange_rate)
                fee_val = float(fee) if fee else 0
                # Calculate effective fee as percentage of send amount
                fee_pct = (fee_val / amount) * 100 if fee_val else 0
                # Also factor in rate spread vs mid-market (we can't know mid-market here,
                # so just report the explicit fee)
                # If fee is very low, Remitly likely bakes spread into rate — add 1% estimate
                if fee_pct < 0.5:
                    fee_pct += 1.0

                return Edge(
                    from_currency=from_ccy,
                    to_currency=to_ccy,
                    via="Remitly (live)",
                    fee_pct=round(fee_pct, 2),
                    estimated_minutes=1440,  # economy tier
                    instructions=(
                        f"Remitly live quote: send {amount} {from_ccy}, "
                        f"receive ~{receive or round(amount * exchange_rate, 2)} {to_ccy}. "
                        f"Rate: {exchange_rate:.4f}"
                    ),
                    exchange_rate=exchange_rate,
                    min_amount=1.0,
                    max_amount=10_000.0,
                )
        except Exception:
            continue
    return None


async def get_remitly_calc_edges() -> list[Edge]:
    """Fetch live Remitly calculator quotes for key corridors."""
    if _cache_fresh(_remitly_cache):
        return _remitly_cache["edges"]

    edges: list[Edge] = []
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            tasks = [
                _fetch_remitly_corridor(client, fc, tc, fcy, tcy, amt)
                for fc, tc, fcy, tcy, amt in REMITLY_CORRIDORS
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, Edge):
                    edges.append(r)
    except Exception as e:
        logger.debug(f"Remitly calculator failed: {e}")

    if edges:
        _remitly_cache["edges"] = edges
        _remitly_cache["ts"] = time.monotonic()
        logger.info(f"Remitly calculator: {len(edges)} live edges")
    else:
        logger.debug("Remitly calculator: 0 edges (endpoints may require session)")

    return edges


# ── 2. Western Union ──────────────────────────────────────────────────────────
# SKIPPED — all tested endpoints require JavaScript rendering, CSRF tokens, or
# return 403/redirect to the main site. Tested URLs:
#   GET  /wuconnect/rest/api/v1.0/EstimateFee → 403 or HTML redirect
#   POST /gateway/api/estimate → requires x-csrf-token + session cookie
# The WU website loads its calculator via a React SPA that fetches a session
# token first. Not feasible for simple HTTP scraping.


# ── 3. MoneyGram ──────────────────────────────────────────────────────────────
# SKIPPED — tested endpoints:
#   GET  /mgo/api/v1/estimate → 403 Forbidden
#   POST /api/moneygram.com/v1/estimate → 404
# MoneyGram's calculator is embedded in their SPA and requires cookies/session
# from loading the main page first. Not feasible without browser automation.


# ── 4. Wise Quotes (amount-specific fees) ────────────────────────────────────
# The public /v1/rates endpoint gives mid-market rates but NOT fees.
# The /gateway/v3/quotes endpoint requires authentication (returns 401).
# We try the anonymous compare endpoint instead.

WISE_CALC_CORRIDORS = [
    ("USD", "MXN", 500),
    ("USD", "PHP", 500),
    ("USD", "INR", 500),
    ("USD", "NGN", 500),
    ("USD", "BRL", 500),
    ("USD", "COP", 500),
    ("GBP", "INR", 400),
    ("GBP", "PHP", 400),
    ("EUR", "MXN", 500),
    ("EUR", "INR", 500),
]

WISE_COMPARE_URL = (
    "https://wise.com/gb/compare/?sourceCurrency={from_ccy}"
    "&targetCurrency={to_ccy}&sendAmount={amount}"
)
WISE_GATEWAY_URL = (
    "https://wise.com/gateway/v3/quotes/"
    "?sourceCurrency={from_ccy}&targetCurrency={to_ccy}&sourceAmount={amount}"
)
# Alternative: the price comparison JSON that the compare page fetches
WISE_PRICE_URL = (
    "https://wise.com/gateway/v1/price/comparison/"
    "?sourceCurrency={from_ccy}&targetCurrency={to_ccy}&sendAmount={amount}"
)


async def _fetch_wise_quote(
    client: httpx.AsyncClient,
    from_ccy: str, to_ccy: str, amount: int,
) -> Edge | None:
    """Try Wise's anonymous quote/comparison endpoints."""
    urls = [
        WISE_PRICE_URL.format(from_ccy=from_ccy, to_ccy=to_ccy, amount=amount),
        WISE_GATEWAY_URL.format(from_ccy=from_ccy, to_ccy=to_ccy, amount=amount),
    ]
    for url in urls:
        try:
            r = await client.get(url, headers=BROWSER_HEADERS, timeout=10)
            if r.status_code != 200:
                continue
            ct = r.headers.get("content-type", "")
            if "json" not in ct:
                continue
            data = r.json()

            # The comparison endpoint may return a list of providers
            # or a single quote object
            if isinstance(data, list):
                # Find the Wise entry
                for item in data:
                    name = (item.get("name") or item.get("provider") or "").lower()
                    if "wise" in name or "transferwise" in name:
                        data = item
                        break
                else:
                    # Use first item if no Wise-specific one found
                    if data:
                        data = data[0]
                    else:
                        continue

            rate = (
                data.get("rate") or data.get("exchangeRate")
                or data.get("midMarketRate") or data.get("exchange_rate")
            )
            fee = (
                data.get("fee") or data.get("totalFee")
                or data.get("transferFee") or data.get("total_fee")
            )
            receive = (
                data.get("receivedAmount") or data.get("targetAmount")
                or data.get("receive_amount")
            )

            if rate and float(rate) > 0:
                rate = float(rate)
                fee_val = float(fee) if fee else 0
                fee_pct = (fee_val / amount) * 100 if fee_val else 0
                recv_display = receive or round(amount * rate, 2)

                return Edge(
                    from_currency=from_ccy,
                    to_currency=to_ccy,
                    via="Wise (live quote)",
                    fee_pct=round(fee_pct, 2) if fee_pct > 0 else 0.45,
                    estimated_minutes=60,
                    instructions=(
                        f"Wise live: send {amount} {from_ccy}, "
                        f"receive ~{recv_display} {to_ccy}. "
                        f"Fee: {fee_val:.2f} {from_ccy}, Rate: {rate:.4f}"
                    ),
                    exchange_rate=rate,
                    min_amount=1.0,
                    max_amount=1_000_000.0,
                )
        except Exception:
            continue
    return None


async def get_wise_calc_edges() -> list[Edge]:
    """Fetch live Wise quotes with actual fees for specific amounts."""
    if _cache_fresh(_wise_calc_cache):
        return _wise_calc_cache["edges"]

    edges: list[Edge] = []
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            tasks = [
                _fetch_wise_quote(client, fc, tc, amt)
                for fc, tc, amt in WISE_CALC_CORRIDORS
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, Edge):
                    edges.append(r)
    except Exception as e:
        logger.debug(f"Wise calculator failed: {e}")

    if edges:
        _wise_calc_cache["edges"] = edges
        _wise_calc_cache["ts"] = time.monotonic()
        logger.info(f"Wise calculator: {len(edges)} live edges")
    else:
        logger.debug("Wise calculator: 0 edges (may require auth)")

    return edges


# ── 5. Xe / x-rates.com ──────────────────────────────────────────────────────
# xe.com/api/protected/* requires authentication (returns 401).
# x-rates.com/calculator/ returns HTML with the rate embedded in the page.
# We parse the HTML to extract the mid-market rate.

XRATES_PAIRS = [
    ("USD", "MXN"), ("USD", "PHP"), ("USD", "INR"), ("USD", "NGN"),
    ("USD", "BRL"), ("USD", "COP"), ("USD", "ARS"), ("USD", "IDR"),
    ("EUR", "MXN"), ("EUR", "PHP"), ("EUR", "INR"),
    ("GBP", "INR"), ("GBP", "PHP"), ("GBP", "NGN"),
    ("CAD", "PHP"), ("CAD", "INR"),
    ("AUD", "PHP"), ("AUD", "INR"),
]

XRATES_URL = "https://www.x-rates.com/calculator/?from={from_ccy}&to={to_ccy}&amount=1"


async def _fetch_xrate(
    client: httpx.AsyncClient,
    from_ccy: str, to_ccy: str,
) -> Edge | None:
    """Scrape x-rates.com for a mid-market rate."""
    url = XRATES_URL.format(from_ccy=from_ccy, to_ccy=to_ccy)
    try:
        r = await client.get(url, headers=BROWSER_HEADERS, timeout=10)
        if r.status_code != 200:
            return None

        # The result is in HTML like: <span class="ccOutputRs">20.345678</span>
        # or in a pattern like "1.00 USD = 20.3456 MXN"
        text = r.text

        # Try pattern: class="ccOutputRs">NUMBER</span>
        match = re.search(r'class="ccOutputRs">\s*([\d.,]+)\s*</span>', text)
        if not match:
            # Try pattern: "1 USD = NUMBER MXN"
            match = re.search(
                rf'1(?:\.00?)?\s*{re.escape(from_ccy)}\s*=\s*([\d.,]+)\s*{re.escape(to_ccy)}',
                text
            )
        if not match:
            # Try generic number near the output area
            match = re.search(r'ccOutputTxt[^>]*>.*?([\d]+\.[\d]{2,6})', text, re.DOTALL)

        if match:
            rate_str = match.group(1).replace(",", "")
            rate = float(rate_str)
            if rate > 0:
                return Edge(
                    from_currency=from_ccy,
                    to_currency=to_ccy,
                    via="x-rates.com (mid-market)",
                    fee_pct=0.0,  # mid-market reference, no fee
                    estimated_minutes=0,
                    instructions=(
                        f"Mid-market reference rate from x-rates.com: "
                        f"1 {from_ccy} = {rate:.4f} {to_ccy}. "
                        f"Not a transfer service — use as benchmark."
                    ),
                    exchange_rate=rate,
                    min_amount=0.01,
                    max_amount=1_000_000_000.0,
                )
    except Exception:
        pass
    return None


async def get_xrates_edges() -> list[Edge]:
    """Fetch mid-market rates from x-rates.com as benchmark reference."""
    if _cache_fresh(_xrates_cache):
        return _xrates_cache["edges"]

    edges: list[Edge] = []
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            # Fetch in small batches to be polite
            for i in range(0, len(XRATES_PAIRS), 4):
                batch = XRATES_PAIRS[i:i + 4]
                tasks = [_fetch_xrate(client, fc, tc) for fc, tc in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for r in results:
                    if isinstance(r, Edge):
                        edges.append(r)
                if i + 4 < len(XRATES_PAIRS):
                    await asyncio.sleep(0.5)  # rate-limit politeness
    except Exception as e:
        logger.debug(f"x-rates.com scrape failed: {e}")

    if edges:
        _xrates_cache["edges"] = edges
        _xrates_cache["ts"] = time.monotonic()
        logger.info(f"x-rates.com: {len(edges)} mid-market reference edges")
    else:
        logger.debug("x-rates.com: 0 edges")

    return edges


# ── 6. TransferGo Calculator ─────────────────────────────────────────────────
# my.transfergo.com/api/quotes may return JSON quotes without auth.
# If it requires a session, it will return 401/403 and we skip.

TRANSFERGO_CORRIDORS = [
    ("GBP", "INR", "GB", "IN", 500),
    ("GBP", "PLN", "GB", "PL", 500),
    ("GBP", "UAH", "GB", "UA", 500),
    ("GBP", "PHP", "GB", "PH", 500),
    ("EUR", "PLN", "DE", "PL", 500),
    ("EUR", "UAH", "DE", "UA", 500),
    ("EUR", "INR", "DE", "IN", 500),
    ("EUR", "PHP", "DE", "PH", 500),
    ("EUR", "RON", "DE", "RO", 500),
]

TRANSFERGO_URL = (
    "https://my.transfergo.com/api/quotes"
    "?from={from_ccy}&to={to_ccy}&fromCountry={from_country}"
    "&toCountry={to_country}&amount={amount}&paymentMethod=bank"
)
# Alternative URL pattern
TRANSFERGO_URL_V2 = (
    "https://my.transfergo.com/api/transfers/quote"
    "?calculationBase=sendAmount&amount={amount}"
    "&fromCurrencyCode={from_ccy}&toCurrencyCode={to_ccy}"
    "&fromCountryCode={from_country}&toCountryCode={to_country}"
)


async def _fetch_transfergo_quote(
    client: httpx.AsyncClient,
    from_ccy: str, to_ccy: str,
    from_country: str, to_country: str,
    amount: int,
) -> Edge | None:
    """Try TransferGo quote endpoint."""
    urls = [
        TRANSFERGO_URL.format(
            from_ccy=from_ccy, to_ccy=to_ccy,
            from_country=from_country, to_country=to_country,
            amount=amount,
        ),
        TRANSFERGO_URL_V2.format(
            from_ccy=from_ccy, to_ccy=to_ccy,
            from_country=from_country, to_country=to_country,
            amount=amount,
        ),
    ]
    for url in urls:
        try:
            r = await client.get(url, headers=BROWSER_HEADERS, timeout=10)
            if r.status_code != 200:
                continue
            ct = r.headers.get("content-type", "")
            if "json" not in ct:
                continue
            data = r.json()

            # TransferGo may return a list of delivery options or a single object
            if isinstance(data, list) and data:
                # Pick the cheapest / standard option
                data = data[0]

            rate = (
                data.get("rate") or data.get("exchangeRate")
                or data.get("exchange_rate")
            )
            fee = (
                data.get("fee") or data.get("totalFee")
                or data.get("transferFee")
            )
            receive = (
                data.get("receivedAmount") or data.get("payoutAmount")
                or data.get("toAmount")
            )

            if rate and float(rate) > 0:
                rate = float(rate)
                fee_val = float(fee) if fee else 0
                fee_pct = (fee_val / amount) * 100 if fee_val else 1.5  # default estimate
                recv_display = receive or round(amount * rate, 2)

                return Edge(
                    from_currency=from_ccy,
                    to_currency=to_ccy,
                    via="TransferGo (live)",
                    fee_pct=round(fee_pct, 2),
                    estimated_minutes=60,
                    instructions=(
                        f"TransferGo live: send {amount} {from_ccy}, "
                        f"receive ~{recv_display} {to_ccy}. "
                        f"Rate: {rate:.4f}"
                    ),
                    exchange_rate=rate,
                    min_amount=1.0,
                    max_amount=50_000.0,
                )
        except Exception:
            continue
    return None


async def get_transfergo_calc_edges() -> list[Edge]:
    """Fetch live TransferGo quotes."""
    if _cache_fresh(_transfergo_cache):
        return _transfergo_cache["edges"]

    edges: list[Edge] = []
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            tasks = [
                _fetch_transfergo_quote(client, fc, tc, fco, tco, amt)
                for fc, tc, fco, tco, amt in TRANSFERGO_CORRIDORS
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, Edge):
                    edges.append(r)
    except Exception as e:
        logger.debug(f"TransferGo calculator failed: {e}")

    if edges:
        _transfergo_cache["edges"] = edges
        _transfergo_cache["ts"] = time.monotonic()
        logger.info(f"TransferGo calculator: {len(edges)} live edges")
    else:
        logger.debug("TransferGo calculator: 0 edges (may require auth)")

    return edges


# ── 7. Pangea (LatAm specialist) ─────────────────────────────────────────────
# SKIPPED — api.gopangea.com returns 403 or requires API key.
# The website calculator loads via React SPA with session management.
# Not feasible for simple HTTP scraping.


# ── Aggregate ─────────────────────────────────────────────────────────────────

async def get_calculator_edges() -> list[Edge]:
    """Fetch all live calculator edges from all working providers.

    Each sub-adapter fails gracefully and returns [].
    """
    results = await asyncio.gather(
        get_remitly_calc_edges(),
        get_wise_calc_edges(),
        get_xrates_edges(),
        get_transfergo_calc_edges(),
        return_exceptions=True,
    )

    all_edges: list[Edge] = []
    names = ["Remitly-calc", "Wise-calc", "x-rates", "TransferGo-calc"]
    for name, batch in zip(names, results):
        if isinstance(batch, Exception):
            logger.warning(f"Calculator adapter {name} raised: {batch}")
            continue
        if isinstance(batch, list):
            all_edges.extend(batch)

    if all_edges:
        logger.info(f"Calculator adapters total: {len(all_edges)} live edges")
    return all_edges
