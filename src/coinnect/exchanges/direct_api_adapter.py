"""
Direct API adapters — live rates from exchanges without CCXT support.
Bitso (LatAm), Buda (Chile/Colombia/Peru), CoinGecko (emerging market reference),
Flutterwave (African corridors).
"""

import asyncio
import logging
import os
import time

import httpx

from coinnect.routing.engine import Edge

logger = logging.getLogger(__name__)

# ── TTL caches ───────────────────────────────────────────────────────────────

_bitso_cache: dict = {"edges": [], "ts": 0.0}
_buda_cache: dict = {"edges": [], "ts": 0.0}
_coingecko_cache: dict = {"edges": [], "ts": 0.0}
_strike_cache: dict = {"edges": [], "ts": 0.0}
_frankfurter_cache: dict = {"edges": [], "ts": 0.0}
_currencyapi_cache: dict = {"edges": [], "ts": 0.0}
_flutterwave_cache: dict = {"edges": [], "ts": 0.0}

BITSO_TTL = 180       # 3 minutes
BUDA_TTL = 180        # 3 minutes
COINGECKO_TTL = 300   # 5 minutes
STRIKE_TTL = 180      # 3 minutes
FRANKFURTER_TTL = 1800  # 30 minutes (ECB updates daily)
CURRENCYAPI_TTL = 1800  # 30 minutes
FLUTTERWAVE_TTL = 300   # 5 minutes

HEADERS = {"User-Agent": "Coinnect/1.0 (coinnect.bot)"}


# ── Bitso ────────────────────────────────────────────────────────────────────

BITSO_BOOKS = {
    "btc_mxn", "eth_mxn", "usdc_mxn", "usdt_mxn",
    "btc_ars", "usdt_ars",
    "btc_brl", "usdt_brl",
    "btc_cop",
}
BITSO_FEE = 0.60


async def get_bitso_edges() -> list[Edge]:
    """Fetch live rates from Bitso public ticker API."""
    now = time.monotonic()
    if _bitso_cache["edges"] and (now - _bitso_cache["ts"]) < BITSO_TTL:
        return _bitso_cache["edges"]

    edges: list[Edge] = []
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            resp = await client.get("https://api.bitso.com/v3/ticker/")
            resp.raise_for_status()
            data = resp.json()

        for ticker in data.get("payload", []):
            book = ticker.get("book", "")
            if book not in BITSO_BOOKS:
                continue
            last = float(ticker.get("last", 0))
            if not last:
                continue

            base, quote = book.split("_")
            base = base.upper()
            quote = quote.upper()

            edges.append(Edge(
                from_currency=base,
                to_currency=quote,
                via="Bitso",
                fee_pct=BITSO_FEE,
                estimated_minutes=15,
                instructions=f"Sell {base} for {quote} on Bitso",
                exchange_rate=last,
            ))
            edges.append(Edge(
                from_currency=quote,
                to_currency=base,
                via="Bitso",
                fee_pct=BITSO_FEE,
                estimated_minutes=15,
                instructions=f"Buy {base} with {quote} on Bitso",
                exchange_rate=1.0 / last,
            ))

        _bitso_cache["edges"] = edges
        _bitso_cache["ts"] = now
        logger.info(f"Bitso: loaded {len(edges)} edges from {len(BITSO_BOOKS)} books")
    except Exception as e:
        logger.warning(f"Bitso adapter failed: {e}")
        return _bitso_cache["edges"]  # stale cache on error

    return edges


# ── Buda ─────────────────────────────────────────────────────────────────────

BUDA_MARKETS = [
    "btc-clp", "eth-clp", "usdc-clp",
    "btc-cop", "usdc-cop",
    "btc-pen", "usdc-pen",
]
BUDA_FEE = 0.80


async def get_buda_edges() -> list[Edge]:
    """Fetch live rates from Buda.com public ticker API."""
    now = time.monotonic()
    if _buda_cache["edges"] and (now - _buda_cache["ts"]) < BUDA_TTL:
        return _buda_cache["edges"]

    edges: list[Edge] = []
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            for market_id in BUDA_MARKETS:
                try:
                    url = f"https://www.buda.com/api/v2/markets/{market_id}/ticker"
                    resp = await client.get(url)
                    resp.raise_for_status()
                    ticker = resp.json().get("ticker", {})

                    last_price_raw = ticker.get("last_price", [])
                    if isinstance(last_price_raw, list) and len(last_price_raw) >= 1:
                        last = float(last_price_raw[0])
                    elif isinstance(last_price_raw, (int, float, str)):
                        last = float(last_price_raw)
                    else:
                        continue

                    if not last:
                        continue

                    base, quote = market_id.split("-")
                    base = base.upper()
                    quote = quote.upper()

                    edges.append(Edge(
                        from_currency=base,
                        to_currency=quote,
                        via="Buda",
                        fee_pct=BUDA_FEE,
                        estimated_minutes=20,
                        instructions=f"Sell {base} for {quote} on Buda.com",
                        exchange_rate=last,
                    ))
                    edges.append(Edge(
                        from_currency=quote,
                        to_currency=base,
                        via="Buda",
                        fee_pct=BUDA_FEE,
                        estimated_minutes=20,
                        instructions=f"Buy {base} with {quote} on Buda.com",
                        exchange_rate=1.0 / last,
                    ))
                except Exception as e:
                    logger.warning(f"Buda market {market_id} failed: {e}")

        _buda_cache["edges"] = edges
        _buda_cache["ts"] = now
        logger.info(f"Buda: loaded {len(edges)} edges from {len(BUDA_MARKETS)} markets")
    except Exception as e:
        logger.warning(f"Buda adapter failed: {e}")
        return _buda_cache["edges"]

    return edges


# ── CoinGecko ────────────────────────────────────────────────────────────────

COINGECKO_IDS = "bitcoin,ethereum,usd-coin,tether"
COINGECKO_VS = "ngn,kes,ghs,tzs,ugx,zar,php,inr,bdt,pkr,idr,vnd,thb,aed,sar,try,uah,xof,xaf"

# Map CoinGecko coin ids → standard ticker symbols
CG_SYMBOL_MAP = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "usd-coin": "USDC",
    "tether": "USDT",
}


async def get_coingecko_edges() -> list[Edge]:
    """Fetch crypto→fiat reference rates from CoinGecko (single batched request)."""
    now = time.monotonic()
    if _coingecko_cache["edges"] and (now - _coingecko_cache["ts"]) < COINGECKO_TTL:
        return _coingecko_cache["edges"]

    edges: list[Edge] = []
    try:
        url = (
            "https://api.coingecko.com/api/v3/simple/price"
            f"?ids={COINGECKO_IDS}&vs_currencies={COINGECKO_VS}"
        )
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        for coin_id, prices in data.items():
            crypto = CG_SYMBOL_MAP.get(coin_id)
            if not crypto:
                continue
            for fiat_lower, price in prices.items():
                if not price:
                    continue
                fiat = fiat_lower.upper()
                rate = float(price)

                edges.append(Edge(
                    from_currency=crypto,
                    to_currency=fiat,
                    via="CoinGecko (market)",
                    fee_pct=0.0,
                    estimated_minutes=0,
                    instructions="Reference market rate — not a direct transfer provider",
                    exchange_rate=rate,
                ))
                edges.append(Edge(
                    from_currency=fiat,
                    to_currency=crypto,
                    via="CoinGecko (market)",
                    fee_pct=0.0,
                    estimated_minutes=0,
                    instructions="Reference market rate — not a direct transfer provider",
                    exchange_rate=1.0 / rate,
                ))

        _coingecko_cache["edges"] = edges
        _coingecko_cache["ts"] = now
        logger.info(f"CoinGecko: loaded {len(edges)} reference edges")
    except Exception as e:
        logger.warning(f"CoinGecko adapter failed: {e}")
        return _coingecko_cache["edges"]

    return edges


# ── Strike ──────────────────────────────────────────────────────────────────

STRIKE_FEE = 0.50


async def get_strike_edges() -> list[Edge]:
    """Fetch BTC/USD rate from Strike public ticker (Lightning Network)."""
    now = time.monotonic()
    if _strike_cache["edges"] and (now - _strike_cache["ts"]) < STRIKE_TTL:
        return _strike_cache["edges"]

    edges: list[Edge] = []
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            resp = await client.get("https://api.strike.me/v1/rates/ticker")
            resp.raise_for_status()
            data = resp.json()

        # data is a list of rate objects; find BTC/USD
        btc_usd_rate = None
        for rate in data if isinstance(data, list) else []:
            amount = rate.get("amount")
            source = rate.get("sourceCurrency", "").upper()
            target = rate.get("targetCurrency", "").upper()
            if source == "BTC" and target == "USD" and amount:
                btc_usd_rate = float(amount)
                break

        if btc_usd_rate:
            edges.append(Edge(
                from_currency="BTC",
                to_currency="USD",
                via="Strike",
                fee_pct=STRIKE_FEE,
                estimated_minutes=5,
                instructions="Sell BTC for USD via Strike (Lightning Network)",
                exchange_rate=btc_usd_rate,
            ))
            edges.append(Edge(
                from_currency="USD",
                to_currency="BTC",
                via="Strike",
                fee_pct=STRIKE_FEE,
                estimated_minutes=5,
                instructions="Buy BTC with USD via Strike (Lightning Network)",
                exchange_rate=1.0 / btc_usd_rate,
            ))

        _strike_cache["edges"] = edges
        _strike_cache["ts"] = now
        logger.info(f"Strike: loaded {len(edges)} edges")
    except Exception as e:
        logger.warning(f"Strike adapter failed: {e}")
        return _strike_cache["edges"]

    return edges


# ── Frankfurter (ECB reference rates) ──────────────────────────────────────


async def get_frankfurter_edges() -> list[Edge]:
    """Fetch FX reference rates from Frankfurter (ECB data), USD and EUR bases."""
    now = time.monotonic()
    if _frankfurter_cache["edges"] and (now - _frankfurter_cache["ts"]) < FRANKFURTER_TTL:
        return _frankfurter_cache["edges"]

    edges: list[Edge] = []
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            # Fetch USD-based rates
            resp_usd = await client.get("https://api.frankfurter.app/latest?from=USD")
            resp_usd.raise_for_status()
            usd_data = resp_usd.json()

            for currency, rate in usd_data.get("rates", {}).items():
                if not rate:
                    continue
                edges.append(Edge(
                    from_currency="USD",
                    to_currency=currency.upper(),
                    via="ECB (reference)",
                    fee_pct=0.0,
                    estimated_minutes=0,
                    instructions="ECB reference rate — not a transfer provider",
                    exchange_rate=float(rate),
                ))

            # Fetch EUR-based rates
            resp_eur = await client.get("https://api.frankfurter.app/latest?from=EUR")
            resp_eur.raise_for_status()
            eur_data = resp_eur.json()

            for currency, rate in eur_data.get("rates", {}).items():
                if not rate:
                    continue
                edges.append(Edge(
                    from_currency="EUR",
                    to_currency=currency.upper(),
                    via="ECB (reference)",
                    fee_pct=0.0,
                    estimated_minutes=0,
                    instructions="ECB reference rate — not a transfer provider",
                    exchange_rate=float(rate),
                ))

        _frankfurter_cache["edges"] = edges
        _frankfurter_cache["ts"] = now
        logger.info(f"Frankfurter: loaded {len(edges)} ECB reference edges")
    except Exception as e:
        logger.warning(f"Frankfurter adapter failed: {e}")
        return _frankfurter_cache["edges"]

    return edges


# ── Currency API (fawazahmed0 CDN fallback) ────────────────────────────────


async def get_currencyapi_edges() -> list[Edge]:
    """Fetch 150+ currency rates from fawazahmed0 CDN (fallback for exotic currencies)."""
    now = time.monotonic()
    if _currencyapi_cache["edges"] and (now - _currencyapi_cache["ts"]) < CURRENCYAPI_TTL:
        return _currencyapi_cache["edges"]

    edges: list[Edge] = []
    try:
        url = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json"
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        rates = data.get("usd", {})
        for currency, rate in rates.items():
            if not rate or currency == "usd":
                continue
            edges.append(Edge(
                from_currency="USD",
                to_currency=currency.upper(),
                via="Market rate",
                fee_pct=0.0,
                estimated_minutes=0,
                instructions="Market reference rate",
                exchange_rate=float(rate),
            ))

        _currencyapi_cache["edges"] = edges
        _currencyapi_cache["ts"] = now
        logger.info(f"CurrencyAPI: loaded {len(edges)} reference edges")
    except Exception as e:
        logger.warning(f"CurrencyAPI adapter failed: {e}")
        return _currencyapi_cache["edges"]

    return edges


# ── Flutterwave (African corridors) ─────────────────────────────────────────

FLUTTERWAVE_CORRIDORS = [
    # (from, to, amount) — amount=500 for fiat, amount=1 for crypto
    ("USD", "NGN", 500), ("USD", "GHS", 500), ("USD", "KES", 500),
    ("USD", "ZAR", 500), ("USD", "UGX", 500), ("USD", "TZS", 500),
    ("USD", "RWF", 500),
    ("EUR", "NGN", 500), ("EUR", "GHS", 500), ("EUR", "KES", 500),
    ("GBP", "NGN", 500), ("GBP", "KES", 500),
    # Reverse corridors
    ("NGN", "USD", 500), ("KES", "USD", 500), ("GHS", "USD", 500),
    ("ZAR", "USD", 500),
]
FLUTTERWAVE_FEE_PCT = 1.5  # estimated spread vs mid-market


async def _fetch_flutterwave_rate(
    client: httpx.AsyncClient, from_c: str, to_c: str, amount: int,
) -> Edge | None:
    """Fetch a single corridor rate from Flutterwave."""
    try:
        resp = await client.get(
            "https://api.flutterwave.com/v3/rates",
            params={"from": from_c, "to": to_c, "amount": amount},
        )
        resp.raise_for_status()
        body = resp.json()
        if body.get("status") != "success":
            return None

        rate = body.get("data", {}).get("rate")
        if not rate:
            return None

        return Edge(
            from_currency=from_c,
            to_currency=to_c,
            via="Flutterwave",
            fee_pct=FLUTTERWAVE_FEE_PCT,
            estimated_minutes=30,
            instructions="Flutterwave — bank transfer or mobile money",
            exchange_rate=float(rate),
        )
    except Exception as e:
        logger.debug(f"Flutterwave {from_c}→{to_c} failed: {e}")
        return None


async def get_flutterwave_edges() -> list[Edge]:
    """Fetch live rates from Flutterwave for African corridors."""
    api_key = os.environ.get("FLUTTERWAVE_PUBLIC_KEY")
    if not api_key:
        return []

    now = time.monotonic()
    if _flutterwave_cache["edges"] and (now - _flutterwave_cache["ts"]) < FLUTTERWAVE_TTL:
        return _flutterwave_cache["edges"]

    edges: list[Edge] = []
    try:
        headers = {**HEADERS, "Authorization": f"Bearer {api_key}"}
        async with httpx.AsyncClient(headers=headers, timeout=20) as client:
            results = await asyncio.gather(
                *[
                    _fetch_flutterwave_rate(client, fc, tc, amt)
                    for fc, tc, amt in FLUTTERWAVE_CORRIDORS
                ],
                return_exceptions=True,
            )

        for result in results:
            if isinstance(result, Edge):
                edges.append(result)

        _flutterwave_cache["edges"] = edges
        _flutterwave_cache["ts"] = now
        logger.info(f"Flutterwave: loaded {len(edges)} edges from {len(FLUTTERWAVE_CORRIDORS)} corridors")
    except Exception as e:
        logger.warning(f"Flutterwave adapter failed: {e}")
        return _flutterwave_cache["edges"]  # stale cache on error

    return edges
