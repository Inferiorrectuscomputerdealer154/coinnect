"""
Direct API adapters — live rates from exchanges without CCXT support.
Bitso (LatAm), Buda (Chile/Colombia/Peru), CoinGecko (emerging market reference),
Flutterwave (African corridors), Yadio (LatAm P2P), VALR (South Africa),
CoinDCX/WazirX (India), SatoshiTango (Argentina), FloatRates (FX fallback).
"""

import asyncio
import logging
import os
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

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
_bluelytics_cache: dict = {"edges": [], "ts": 0.0}
_dolarsi_cache: dict = {"edges": [], "ts": 0.0}
_criptoya_cache: dict = {"edges": [], "ts": 0.0}
_bcb_cache: dict = {"edges": [], "ts": 0.0}
_banxico_cache: dict = {"edges": [], "ts": 0.0}
_trm_cache: dict = {"edges": [], "ts": 0.0}
_lirarate_cache: dict = {"edges": [], "ts": 0.0}
_yadio_cache: dict = {"edges": [], "ts": 0.0}
_valr_cache: dict = {"edges": [], "ts": 0.0}
_coindcx_cache: dict = {"edges": [], "ts": 0.0}
_wazirx_cache: dict = {"edges": [], "ts": 0.0}
_satoshitango_cache: dict = {"edges": [], "ts": 0.0}
_floatrates_cache: dict = {"edges": [], "ts": 0.0}
_binance_p2p_cache: dict = {"edges": [], "ts": 0.0}
_tcmb_cache: dict = {"edges": [], "ts": 0.0}
_nrb_cache: dict = {"edges": [], "ts": 0.0}
_nbp_cache: dict = {"edges": [], "ts": 0.0}
_cnb_cache: dict = {"edges": [], "ts": 0.0}
_nbu_cache: dict = {"edges": [], "ts": 0.0}
_nbg_cache: dict = {"edges": [], "ts": 0.0}
_boi_cache: dict = {"edges": [], "ts": 0.0}
_bnr_cache: dict = {"edges": [], "ts": 0.0}
_cbr_cache: dict = {"edges": [], "ts": 0.0}
_uphold_cache: dict = {"edges": [], "ts": 0.0}
_ofx_cache: dict = {"edges": [], "ts": 0.0}

BITSO_TTL = 180       # 3 minutes
BUDA_TTL = 180        # 3 minutes
COINGECKO_TTL = 300   # 5 minutes
STRIKE_TTL = 180      # 3 minutes
FRANKFURTER_TTL = 1800  # 30 minutes (ECB updates daily)
CURRENCYAPI_TTL = 1800  # 30 minutes
FLUTTERWAVE_TTL = 300   # 5 minutes
BLUELYTICS_TTL = 900    # 15 minutes
DOLARSI_TTL = 900       # 15 minutes
CRIPTOYA_TTL = 300      # 5 minutes
BCB_TTL = 3600          # 60 minutes (updates once daily)
BANXICO_TTL = 3600      # 60 minutes (updates once daily)
TRM_TTL = 3600          # 60 minutes
LIRARATE_TTL = 1800     # 30 minutes
YADIO_TTL = 300         # 5 minutes
VALR_TTL = 180          # 3 minutes
COINDCX_TTL = 180       # 3 minutes
WAZIRX_TTL = 180        # 3 minutes
SATOSHITANGO_TTL = 300  # 5 minutes
FLOATRATES_TTL = 3600   # 60 minutes (daily data)
BINANCE_P2P_TTL = 300   # 5 minutes
TCMB_TTL = 3600         # 60 minutes (updates once daily)
NRB_TTL = 3600          # 60 minutes (updates once daily)
NBP_TTL = 3600          # 60 minutes (updates once daily)
CNB_TTL = 3600          # 60 minutes (updates once daily)
NBU_TTL = 3600          # 60 minutes (updates once daily)
NBG_TTL = 3600          # 60 minutes (updates once daily)
BOI_TTL = 3600          # 60 minutes (updates once daily)
BNR_TTL = 3600          # 60 minutes (updates once daily)
CBR_TTL = 3600          # 60 minutes (updates once daily)
UPHOLD_TTL = 300        # 5 minutes
OFX_TTL = 300           # 5 minutes

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
                    via="Market rate",
                    fee_pct=0.5,
                    estimated_minutes=0,
                    instructions="Market rate conversion — verify actual cost with your bank or exchange (~est. 0.5% typical spread)",
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
                    via="Market rate",
                    fee_pct=0.5,
                    estimated_minutes=0,
                    instructions="Market rate conversion — verify actual cost with your bank or exchange (~est. 0.5% typical spread)",
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
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            # Fetch USD-based rates
            resp = await client.get(
                "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json"
            )
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
                    fee_pct=0.5,
                    estimated_minutes=0,
                    instructions="Market rate conversion — verify actual cost with your bank or exchange (~est. 0.5% typical spread)",
                    exchange_rate=float(rate),
                ))

            # Fetch EUR-based rates for broader corridor coverage
            resp_eur = await client.get(
                "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/eur.json"
            )
            resp_eur.raise_for_status()
            eur_data = resp_eur.json()

            eur_rates = eur_data.get("eur", {})
            for currency, rate in eur_rates.items():
                if not rate or currency == "eur":
                    continue
                edges.append(Edge(
                    from_currency="EUR",
                    to_currency=currency.upper(),
                    via="Market rate",
                    fee_pct=0.5,
                    estimated_minutes=0,
                    instructions="Market rate conversion — verify actual cost with your bank or exchange (~est. 0.5% typical spread)",
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


# ── Bluelytics (Argentina parallel rates) ─────────────────────────────────


async def get_bluelytics_edges() -> list[Edge]:
    """Fetch Argentine blue/official dollar and euro rates from Bluelytics."""
    now = time.monotonic()
    if _bluelytics_cache["edges"] and (now - _bluelytics_cache["ts"]) < BLUELYTICS_TTL:
        return _bluelytics_cache["edges"]

    edges: list[Edge] = []
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            resp = await client.get("https://api.bluelytics.com.ar/v2/latest")
            resp.raise_for_status()
            data = resp.json()

        blue = data.get("blue", {})
        oficial = data.get("oficial", {})
        blue_euro = data.get("blue_euro", {})

        blue_avg = blue.get("value_avg")
        if blue_avg:
            edges.append(Edge(
                from_currency="USD",
                to_currency="ARS",
                via="Blue market (AR)",
                fee_pct=0.0,
                estimated_minutes=0,
                instructions="Argentine parallel market rate — reference only",
                exchange_rate=float(blue_avg),
            ))

        oficial_avg = oficial.get("value_avg")
        if oficial_avg:
            edges.append(Edge(
                from_currency="USD",
                to_currency="ARS",
                via="Official (AR)",
                fee_pct=0.0,
                estimated_minutes=0,
                instructions="Argentine parallel market rate — reference only",
                exchange_rate=float(oficial_avg),
            ))

        blue_euro_avg = blue_euro.get("value_avg")
        if blue_euro_avg:
            edges.append(Edge(
                from_currency="EUR",
                to_currency="ARS",
                via="Blue market (AR)",
                fee_pct=0.0,
                estimated_minutes=0,
                instructions="Argentine parallel market rate — reference only",
                exchange_rate=float(blue_euro_avg),
            ))

        _bluelytics_cache["edges"] = edges
        _bluelytics_cache["ts"] = now
        logger.info(f"Bluelytics: loaded {len(edges)} edges")
    except Exception as e:
        logger.warning(f"Bluelytics adapter failed: {e}")
        return _bluelytics_cache["edges"]

    return edges


# ── DolarSi (Argentina all dollar variants) ───────────────────────────────

# Map DolarSi names to display names
_DOLARSI_NAME_MAP = {
    "Dolar Blue": "Dolar Blue (AR)",
    "Dolar Oficial": "Dolar Oficial (AR)",
    "Dolar Bolsa": "MEP (AR)",
    "Dolar Contado con Liqui": "CCL (AR)",
}


def _parse_ar_number(s: str) -> float | None:
    """Parse an Argentine-formatted number (comma as decimal separator)."""
    if not s:
        return None
    try:
        # "1.280,50" → "1280.50"  or  "1280,50" → "1280.50"
        cleaned = s.replace(".", "").replace(",", ".")
        return float(cleaned)
    except (ValueError, TypeError):
        return None


async def get_dolarsi_edges() -> list[Edge]:
    """Fetch all Argentine dollar variants from DolarSi."""
    now = time.monotonic()
    if _dolarsi_cache["edges"] and (now - _dolarsi_cache["ts"]) < DOLARSI_TTL:
        return _dolarsi_cache["edges"]

    edges: list[Edge] = []
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            resp = await client.get(
                "https://www.dolarsi.com/api/api.php?type=valoresprincipales"
            )
            resp.raise_for_status()
            data = resp.json()

        for item in data:
            casa = item.get("casa", {})
            nombre = casa.get("nombre", "")
            via = _DOLARSI_NAME_MAP.get(nombre)
            if not via:
                continue

            venta = _parse_ar_number(casa.get("venta", ""))
            if not venta:
                continue

            edges.append(Edge(
                from_currency="USD",
                to_currency="ARS",
                via=via,
                fee_pct=0.0,
                estimated_minutes=0,
                instructions="Argentine parallel market rate — reference only",
                exchange_rate=venta,
            ))

        _dolarsi_cache["edges"] = edges
        _dolarsi_cache["ts"] = now
        logger.info(f"DolarSi: loaded {len(edges)} edges")
    except Exception as e:
        logger.warning(f"DolarSi adapter failed: {e}")
        return _dolarsi_cache["edges"]

    return edges


# ── CriptoYa (Argentina crypto exchange rates) ────────────────────────────


async def get_criptoya_edges() -> list[Edge]:
    """Fetch USDT/ARS rates from Argentine crypto exchanges via CriptoYa."""
    now = time.monotonic()
    if _criptoya_cache["edges"] and (now - _criptoya_cache["ts"]) < CRIPTOYA_TTL:
        return _criptoya_cache["edges"]

    edges: list[Edge] = []
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            resp = await client.get("https://criptoya.com/api/usdt/ars")
            resp.raise_for_status()
            data = resp.json()

        for exchange, info in data.items():
            if not isinstance(info, dict):
                continue
            ask = info.get("ask")
            if not ask:
                continue

            edges.append(Edge(
                from_currency="USDT",
                to_currency="ARS",
                via=f"{exchange} (AR)",
                fee_pct=0.5,
                estimated_minutes=5,
                instructions=f"Sell USDT for ARS on {exchange}",
                exchange_rate=float(ask),
            ))

        _criptoya_cache["edges"] = edges
        _criptoya_cache["ts"] = now
        logger.info(f"CriptoYa: loaded {len(edges)} edges from {len(data)} exchanges")
    except Exception as e:
        logger.warning(f"CriptoYa adapter failed: {e}")
        return _criptoya_cache["edges"]

    return edges


# ── BCB PTAX (Brazil official rate) ────────────────────────────────────────


async def get_bcb_edges() -> list[Edge]:
    """Fetch official USD/BRL PTAX rate from the Brazilian Central Bank."""
    now = time.monotonic()
    if _bcb_cache["edges"] and (now - _bcb_cache["ts"]) < BCB_TTL:
        return _bcb_cache["edges"]

    edges: list[Edge] = []
    try:
        today = datetime.now(timezone.utc).strftime("%m-%d-%Y")
        url = (
            "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
            f"CotacaoDolarDia(dataCotacao=@dataCotacao)"
            f"?@dataCotacao='{today}'&$format=json"
        )
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        values = data.get("value", [])
        if values:
            cotacao_venda = values[0].get("cotacaoVenda")
            if cotacao_venda:
                edges.append(Edge(
                    from_currency="USD",
                    to_currency="BRL",
                    via="BCB PTAX (BR)",
                    fee_pct=0.0,
                    estimated_minutes=0,
                    instructions="Brazilian Central Bank official rate — reference only",
                    exchange_rate=float(cotacao_venda),
                ))

        _bcb_cache["edges"] = edges
        _bcb_cache["ts"] = now
        logger.info(f"BCB: loaded {len(edges)} edges")
    except Exception as e:
        logger.warning(f"BCB adapter failed: {e}")
        return _bcb_cache["edges"]

    return edges


# ── Banxico (Mexico official rate) ─────────────────────────────────────────


async def get_banxico_edges() -> list[Edge]:
    """Fetch official USD/MXN FIX rate from Banco de México (SIE API).

    Requires BMX_TOKEN env var (free token from banxico.org.mx/SieAPIRest/).
    Series SF43718 = Tipo de cambio pesos por dólar E.U.A. (FIX).
    """
    now = time.monotonic()
    if _banxico_cache["edges"] and (now - _banxico_cache["ts"]) < BANXICO_TTL:
        return _banxico_cache["edges"]

    edges: list[Edge] = []
    token = os.environ.get("BMX_TOKEN", "")
    if not token:
        logger.warning("Banxico: BMX_TOKEN not set — skipping")
        return _banxico_cache["edges"]

    try:
        url = (
            "https://www.banxico.org.mx/SieAPIRest/service/v1/"
            "series/SF43718/datos/oportuno"
        )
        headers = {**HEADERS, "Bmx-Token": token, "Accept": "application/json"}
        async with httpx.AsyncClient(headers=headers, timeout=15) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        # Response shape:
        # {"bmx":{"series":[{"idSerie":"SF43718","titulo":"...","datos":[{"fecha":"dd/mm/yyyy","dato":"19.1234"}]}]}}
        series = data.get("bmx", {}).get("series", [])
        if series:
            datos = series[0].get("datos", [])
            if datos:
                dato = datos[-1].get("dato", "")
                # dato can be "N/E" on non-business days
                if dato and dato != "N/E":
                    rate = float(dato.replace(",", ""))
                    if rate > 0:
                        edges.append(Edge(
                            from_currency="USD",
                            to_currency="MXN",
                            via="Banxico (MX)",
                            fee_pct=0.0,
                            estimated_minutes=0,
                            instructions="Banco de México official FIX rate — reference only",
                            exchange_rate=rate,
                        ))

        _banxico_cache["edges"] = edges
        _banxico_cache["ts"] = now
        logger.info(f"Banxico: loaded {len(edges)} edges")
    except Exception as e:
        logger.warning(f"Banxico adapter failed: {e}")
        return _banxico_cache["edges"]

    return edges


# ── TRM (Colombia official rate) ───────────────────────────────────────────


async def get_trm_edges() -> list[Edge]:
    """Fetch official USD/COP TRM rate from Colombia's datos.gov.co."""
    now = time.monotonic()
    if _trm_cache["edges"] and (now - _trm_cache["ts"]) < TRM_TTL:
        return _trm_cache["edges"]

    edges: list[Edge] = []
    try:
        url = (
            "https://www.datos.gov.co/resource/32sa-8pi3.json"
            "?$order=vigenciadesde%20DESC&$limit=1"
        )
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        if data and isinstance(data, list):
            valor = data[0].get("valor")
            if valor:
                edges.append(Edge(
                    from_currency="USD",
                    to_currency="COP",
                    via="TRM (CO)",
                    fee_pct=0.0,
                    estimated_minutes=0,
                    instructions="Colombian official TRM rate — reference only",
                    exchange_rate=float(valor),
                ))

        _trm_cache["edges"] = edges
        _trm_cache["ts"] = now
        logger.info(f"TRM: loaded {len(edges)} edges")
    except Exception as e:
        logger.warning(f"TRM adapter failed: {e}")
        return _trm_cache["edges"]

    return edges


# ── LiraRate (Lebanon parallel rate) ───────────────────────────────────────


async def get_lirarate_edges() -> list[Edge]:
    """Fetch USD/LBP parallel rate from LiraRate."""
    now = time.monotonic()
    if _lirarate_cache["edges"] and (now - _lirarate_cache["ts"]) < LIRARATE_TTL:
        return _lirarate_cache["edges"]

    edges: list[Edge] = []
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            resp = await client.get(
                "https://lirarate.org/wp-json/starter/v1/rates"
            )
            resp.raise_for_status()
            data = resp.json()

        # Response structure may vary; try common patterns
        rate = None
        if isinstance(data, dict):
            # Try direct "usd" or "USD" key
            for key in ("usd", "USD", "buy", "sell"):
                val = data.get(key)
                if val and isinstance(val, (int, float, str)):
                    try:
                        rate = float(str(val).replace(",", ""))
                        break
                    except (ValueError, TypeError):
                        continue
            # Try nested structure
            if rate is None:
                for key, val in data.items():
                    if isinstance(val, dict):
                        for subkey in ("buy", "sell", "rate", "value"):
                            sv = val.get(subkey)
                            if sv:
                                try:
                                    rate = float(str(sv).replace(",", ""))
                                    break
                                except (ValueError, TypeError):
                                    continue
                    if rate:
                        break

        if rate and rate > 1000:  # sanity check — LBP should be in thousands
            edges.append(Edge(
                from_currency="USD",
                to_currency="LBP",
                via="Parallel (LB)",
                fee_pct=0.0,
                estimated_minutes=0,
                instructions="Lebanese parallel market rate — reference only",
                exchange_rate=rate,
            ))

        _lirarate_cache["edges"] = edges
        _lirarate_cache["ts"] = now
        logger.info(f"LiraRate: loaded {len(edges)} edges")
    except Exception as e:
        logger.warning(f"LiraRate adapter failed: {e}")
        return _lirarate_cache["edges"]

    return edges


# ── Yadio (LatAm P2P rates) ─────────────────────────────────────────────


async def get_yadio_edges() -> list[Edge]:
    """Fetch P2P/parallel market rates from Yadio (126 currencies, LatAm specialty)."""
    now = time.monotonic()
    if _yadio_cache["edges"] and (now - _yadio_cache["ts"]) < YADIO_TTL:
        return _yadio_cache["edges"]

    edges: list[Edge] = []
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            # Fetch USD-based rates
            resp_usd = await client.get("https://api.yadio.io/exrates/USD")
            resp_usd.raise_for_status()
            usd_data = resp_usd.json()

            usd_rates = usd_data.get("USD", {})
            for currency, rate in usd_rates.items():
                if not rate or currency == "USD":
                    continue
                edges.append(Edge(
                    from_currency="USD",
                    to_currency=currency.upper(),
                    via="Yadio (P2P)",
                    fee_pct=0.3,
                    estimated_minutes=0,
                    instructions="P2P market rate — verify actual cost with your local P2P provider (~est. 0.3% spread)",
                    exchange_rate=float(rate),
                ))

            # Fetch EUR-based rates
            resp_eur = await client.get("https://api.yadio.io/exrates/EUR")
            resp_eur.raise_for_status()
            eur_data = resp_eur.json()

            eur_rates = eur_data.get("EUR", {})
            for currency, rate in eur_rates.items():
                if not rate or currency == "EUR":
                    continue
                edges.append(Edge(
                    from_currency="EUR",
                    to_currency=currency.upper(),
                    via="Yadio (P2P)",
                    fee_pct=0.3,
                    estimated_minutes=0,
                    instructions="P2P market rate — verify actual cost with your local P2P provider (~est. 0.3% spread)",
                    exchange_rate=float(rate),
                ))

        _yadio_cache["edges"] = edges
        _yadio_cache["ts"] = now
        logger.info(f"Yadio: loaded {len(edges)} P2P reference edges")
    except Exception as e:
        logger.warning(f"Yadio adapter failed: {e}")
        return _yadio_cache["edges"]

    return edges


# ── VALR (South Africa) ─────────────────────────────────────────────────

VALR_ZAR_PAIRS = {"BTCZAR", "ETHZAR", "USDCZAR", "USDTZAR"}
VALR_FEE = 0.75


async def get_valr_edges() -> list[Edge]:
    """Fetch ZAR trading pairs from VALR (South Africa)."""
    now = time.monotonic()
    if _valr_cache["edges"] and (now - _valr_cache["ts"]) < VALR_TTL:
        return _valr_cache["edges"]

    edges: list[Edge] = []
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            resp = await client.get("https://api.valr.com/v1/public/marketsummary")
            resp.raise_for_status()
            data = resp.json()

        for item in data:
            pair = item.get("currencyPair", "")
            if pair not in VALR_ZAR_PAIRS:
                continue
            last = item.get("lastTradedPrice")
            if not last:
                continue
            last = float(last)
            if not last:
                continue

            # Split pair: e.g. "BTCZAR" → BTC, ZAR
            base = pair[:-3]
            quote = pair[-3:]

            edges.append(Edge(
                from_currency=base,
                to_currency=quote,
                via="VALR",
                fee_pct=VALR_FEE,
                estimated_minutes=15,
                instructions=f"Sell {base} for {quote} on VALR",
                exchange_rate=last,
            ))
            edges.append(Edge(
                from_currency=quote,
                to_currency=base,
                via="VALR",
                fee_pct=VALR_FEE,
                estimated_minutes=15,
                instructions=f"Buy {base} with {quote} on VALR",
                exchange_rate=1.0 / last,
            ))

        _valr_cache["edges"] = edges
        _valr_cache["ts"] = now
        logger.info(f"VALR: loaded {len(edges)} edges")
    except Exception as e:
        logger.warning(f"VALR adapter failed: {e}")
        return _valr_cache["edges"]

    return edges


# ── CoinDCX (India) ─────────────────────────────────────────────────────

COINDCX_INR_MARKETS = {"BTCINR", "ETHINR", "USDTINR", "USDCINR"}
COINDCX_FEE = 0.50


async def get_coindcx_edges() -> list[Edge]:
    """Fetch INR trading pairs from CoinDCX (India)."""
    now = time.monotonic()
    if _coindcx_cache["edges"] and (now - _coindcx_cache["ts"]) < COINDCX_TTL:
        return _coindcx_cache["edges"]

    edges: list[Edge] = []
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            resp = await client.get("https://api.coindcx.com/exchange/ticker")
            resp.raise_for_status()
            data = resp.json()

        for item in data:
            market = item.get("market", "")
            if market not in COINDCX_INR_MARKETS:
                continue
            last = item.get("last_price")
            if not last:
                continue
            last = float(last)
            if not last:
                continue

            # Split: "BTCINR" → BTC, INR
            base = market[:-3]
            quote = market[-3:]

            edges.append(Edge(
                from_currency=base,
                to_currency=quote,
                via="CoinDCX",
                fee_pct=COINDCX_FEE,
                estimated_minutes=15,
                instructions=f"Sell {base} for {quote} on CoinDCX",
                exchange_rate=last,
            ))
            edges.append(Edge(
                from_currency=quote,
                to_currency=base,
                via="CoinDCX",
                fee_pct=COINDCX_FEE,
                estimated_minutes=15,
                instructions=f"Buy {base} with {quote} on CoinDCX",
                exchange_rate=1.0 / last,
            ))

        _coindcx_cache["edges"] = edges
        _coindcx_cache["ts"] = now
        logger.info(f"CoinDCX: loaded {len(edges)} edges")
    except Exception as e:
        logger.warning(f"CoinDCX adapter failed: {e}")
        return _coindcx_cache["edges"]

    return edges


# ── WazirX (India) ───────────────────────────────────────────────────────

WAZIRX_INR_SYMBOLS = {"btcinr", "ethinr", "usdtinr"}
WAZIRX_FEE = 0.40


async def get_wazirx_edges() -> list[Edge]:
    """Fetch INR trading pairs from WazirX (India)."""
    now = time.monotonic()
    if _wazirx_cache["edges"] and (now - _wazirx_cache["ts"]) < WAZIRX_TTL:
        return _wazirx_cache["edges"]

    edges: list[Edge] = []
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            resp = await client.get("https://api.wazirx.com/sapi/v1/tickers/24hr")
            resp.raise_for_status()
            data = resp.json()

        for item in data:
            symbol = item.get("symbol", "")
            if symbol not in WAZIRX_INR_SYMBOLS:
                continue
            last = item.get("lastPrice")
            if not last:
                continue
            last = float(last)
            if not last:
                continue

            # Split: "btcinr" → BTC, INR
            base = symbol[:-3].upper()
            quote = symbol[-3:].upper()

            edges.append(Edge(
                from_currency=base,
                to_currency=quote,
                via="WazirX",
                fee_pct=WAZIRX_FEE,
                estimated_minutes=15,
                instructions=f"Sell {base} for {quote} on WazirX",
                exchange_rate=last,
            ))
            edges.append(Edge(
                from_currency=quote,
                to_currency=base,
                via="WazirX",
                fee_pct=WAZIRX_FEE,
                estimated_minutes=15,
                instructions=f"Buy {base} with {quote} on WazirX",
                exchange_rate=1.0 / last,
            ))

        _wazirx_cache["edges"] = edges
        _wazirx_cache["ts"] = now
        logger.info(f"WazirX: loaded {len(edges)} edges")
    except Exception as e:
        logger.warning(f"WazirX adapter failed: {e}")
        return _wazirx_cache["edges"]

    return edges


# ── SatoshiTango (Argentina) ─────────────────────────────────────────────

SATOSHITANGO_ASSETS = ["BTC", "ETH", "USDT", "USDC", "DAI"]
SATOSHITANGO_FEE = 1.0


async def get_satoshitango_edges() -> list[Edge]:
    """Fetch crypto/ARS rates from SatoshiTango (Argentina)."""
    now = time.monotonic()
    if _satoshitango_cache["edges"] and (now - _satoshitango_cache["ts"]) < SATOSHITANGO_TTL:
        return _satoshitango_cache["edges"]

    edges: list[Edge] = []
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            resp = await client.get("https://api.satoshitango.com/v3/ticker/ARS")
            resp.raise_for_status()
            data = resp.json()

        ticker = data.get("data", {}).get("ticker", {})
        for asset in SATOSHITANGO_ASSETS:
            info = ticker.get(asset)
            if not info:
                continue
            ask = info.get("ask")
            if not ask:
                continue
            rate = float(ask)
            if not rate:
                continue

            edges.append(Edge(
                from_currency=asset,
                to_currency="ARS",
                via="SatoshiTango",
                fee_pct=SATOSHITANGO_FEE,
                estimated_minutes=10,
                instructions=f"Sell {asset} for ARS on SatoshiTango",
                exchange_rate=rate,
            ))
            edges.append(Edge(
                from_currency="ARS",
                to_currency=asset,
                via="SatoshiTango",
                fee_pct=SATOSHITANGO_FEE,
                estimated_minutes=10,
                instructions=f"Buy {asset} with ARS on SatoshiTango",
                exchange_rate=1.0 / rate,
            ))

        _satoshitango_cache["edges"] = edges
        _satoshitango_cache["ts"] = now
        logger.info(f"SatoshiTango: loaded {len(edges)} edges")
    except Exception as e:
        logger.warning(f"SatoshiTango adapter failed: {e}")
        return _satoshitango_cache["edges"]

    return edges


# ── FloatRates (FX fallback) ─────────────────────────────────────────────


async def get_floatrates_edges() -> list[Edge]:
    """Fetch daily FX rates from FloatRates (additional fallback)."""
    now = time.monotonic()
    if _floatrates_cache["edges"] and (now - _floatrates_cache["ts"]) < FLOATRATES_TTL:
        return _floatrates_cache["edges"]

    edges: list[Edge] = []
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            resp = await client.get("https://www.floatrates.com/daily/usd.json")
            resp.raise_for_status()
            data = resp.json()

        for currency_lower, info in data.items():
            if not isinstance(info, dict):
                continue
            rate = info.get("rate")
            if not rate:
                continue
            edges.append(Edge(
                from_currency="USD",
                to_currency=currency_lower.upper(),
                via="Market rate",
                fee_pct=0.5,
                estimated_minutes=0,
                instructions="Market rate conversion — verify actual cost with your bank or exchange (~est. 0.5% typical spread)",
                exchange_rate=float(rate),
            ))

        _floatrates_cache["edges"] = edges
        _floatrates_cache["ts"] = now
        logger.info(f"FloatRates: loaded {len(edges)} reference edges")
    except Exception as e:
        logger.warning(f"FloatRates adapter failed: {e}")
        return _floatrates_cache["edges"]

    return edges


# ── Binance P2P (live rates) ─────────────────────────────────────────────

BINANCE_P2P_FIATS = ["MXN", "ARS", "NGN", "COP", "VES", "BRL", "KES", "GHS", "PKR", "BDT", "TRY", "UAH"]
BINANCE_P2P_URL = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
BINANCE_P2P_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


def _median(values: list[float]) -> float:
    """Return the median of a sorted list of floats."""
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2


async def _fetch_binance_p2p_prices(
    client: httpx.AsyncClient, fiat: str, trade_type: str,
) -> float | None:
    """Fetch top-5 P2P prices for a fiat/tradeType and return the median price."""
    try:
        body = {
            "fiat": fiat,
            "page": 1,
            "rows": 5,
            "tradeType": trade_type,
            "asset": "USDT",
            "payTypes": [],
            "publisherType": None,
        }
        resp = await client.post(BINANCE_P2P_URL, json=body)
        resp.raise_for_status()
        data = resp.json()

        prices = []
        for item in data.get("data", []):
            adv = item.get("adv", {})
            price = adv.get("price")
            if price:
                prices.append(float(price))

        if not prices:
            return None
        return _median(prices)
    except Exception as e:
        logger.debug(f"Binance P2P {fiat} {trade_type} failed: {e}")
        return None


async def get_binance_p2p_edges() -> list[Edge]:
    """Fetch live P2P USDT rates from Binance for emerging market currencies."""
    now = time.monotonic()
    if _binance_p2p_cache["edges"] and (now - _binance_p2p_cache["ts"]) < BINANCE_P2P_TTL:
        return _binance_p2p_cache["edges"]

    edges: list[Edge] = []
    try:
        async with httpx.AsyncClient(headers=BINANCE_P2P_HEADERS, timeout=20) as client:
            # Fetch BUY and SELL prices for all fiats in parallel
            tasks = []
            for fiat in BINANCE_P2P_FIATS:
                tasks.append(_fetch_binance_p2p_prices(client, fiat, "BUY"))
                tasks.append(_fetch_binance_p2p_prices(client, fiat, "SELL"))

            results = await asyncio.gather(*tasks, return_exceptions=True)

        # results: [MXN_BUY, MXN_SELL, ARS_BUY, ARS_SELL, ...]
        for i, fiat in enumerate(BINANCE_P2P_FIATS):
            buy_price = results[i * 2] if not isinstance(results[i * 2], Exception) else None
            sell_price = results[i * 2 + 1] if not isinstance(results[i * 2 + 1], Exception) else None

            # BUY price = price users pay in FIAT to buy USDT → FIAT→USDT edge
            if buy_price and buy_price > 0:
                edges.append(Edge(
                    from_currency=fiat,
                    to_currency="USDT",
                    via="Binance P2P (live)",
                    fee_pct=0.0,
                    estimated_minutes=30,
                    instructions=f"Buy USDT with {fiat} on Binance P2P",
                    exchange_rate=1.0 / buy_price,
                ))

            # SELL price = price users get in FIAT for selling USDT → USDT→FIAT edge
            if sell_price and sell_price > 0:
                edges.append(Edge(
                    from_currency="USDT",
                    to_currency=fiat,
                    via="Binance P2P (live)",
                    fee_pct=0.0,
                    estimated_minutes=30,
                    instructions=f"Sell USDT for {fiat} on Binance P2P",
                    exchange_rate=sell_price,
                ))

        _binance_p2p_cache["edges"] = edges
        _binance_p2p_cache["ts"] = now
        logger.info(f"Binance P2P: loaded {len(edges)} edges for {len(BINANCE_P2P_FIATS)} fiats")
    except Exception as e:
        logger.warning(f"Binance P2P adapter failed: {e}")
        return _binance_p2p_cache["edges"]

    return edges


# ── TCMB (Turkey Central Bank) ─────────────────────────────────────────────


async def get_tcmb_edges() -> list[Edge]:
    """Fetch official USD/TRY rate from Turkey Central Bank XML feed."""
    now = time.monotonic()
    if _tcmb_cache["edges"] and (now - _tcmb_cache["ts"]) < TCMB_TTL:
        return _tcmb_cache["edges"]

    edges: list[Edge] = []
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            resp = await client.get("https://www.tcmb.gov.tr/kurlar/today.xml")
            resp.raise_for_status()

        root = ET.fromstring(resp.text)
        # XML structure: <Tarih_Date> > <Currency CurrencyCode="USD"> > <ForexSelling>
        for currency in root.findall(".//Currency"):
            code = currency.get("CurrencyCode", "")
            if code != "USD":
                continue
            forex_selling = currency.findtext("ForexSelling")
            if forex_selling:
                rate = float(forex_selling.replace(",", "."))
                if rate > 0:
                    edges.append(Edge(
                        from_currency="USD",
                        to_currency="TRY",
                        via="TCMB (TR)",
                        fee_pct=0.0,
                        estimated_minutes=0,
                        instructions="Turkish Central Bank official rate — reference only",
                        exchange_rate=rate,
                    ))
                    break

        _tcmb_cache["edges"] = edges
        _tcmb_cache["ts"] = now
        logger.info(f"TCMB: loaded {len(edges)} edges")
    except Exception as e:
        logger.warning(f"TCMB adapter failed: {e}")
        return _tcmb_cache["edges"]

    return edges


# ── NRB (Nepal Rastra Bank) ────────────────────────────────────────────────


async def get_nrb_edges() -> list[Edge]:
    """Fetch official USD/NPR rate from Nepal Rastra Bank JSON API."""
    now = time.monotonic()
    if _nrb_cache["edges"] and (now - _nrb_cache["ts"]) < NRB_TTL:
        return _nrb_cache["edges"]

    edges: list[Edge] = []
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            resp = await client.get(
                "https://www.nrb.org.np/api/forex/v1/rates",
                params={"per_page": 5, "page": 1},
            )
            resp.raise_for_status()
            data = resp.json()

        usd_rate = None

        # Deep-search for USD rate in any nested structure
        def _find_usd_rate(obj, depth=0):
            """Recursively search for USD exchange rate in nested JSON."""
            if depth > 5:
                return None
            if isinstance(obj, dict):
                # Check if this dict itself is a USD rate entry
                for key in ("iso3", "code", "currency_code", "charCode", "cc"):
                    if obj.get(key) == "USD" or (isinstance(obj.get(key), dict) and obj[key].get("iso3") == "USD"):
                        for rate_key in ("sell", "buy", "selling", "buying", "rate", "mid", "value"):
                            val = obj.get(rate_key)
                            if val:
                                try:
                                    return float(str(val).replace(",", ""))
                                except (ValueError, TypeError):
                                    continue
                # Check if "name" contains "Dollar"
                name = obj.get("name", "") or obj.get("currency", "")
                if isinstance(name, str) and "dollar" in name.lower() and "us" in name.lower():
                    for rate_key in ("sell", "buy", "selling", "buying", "rate", "mid", "value"):
                        val = obj.get(rate_key)
                        if val:
                            try:
                                return float(str(val).replace(",", ""))
                            except (ValueError, TypeError):
                                continue
                # Recurse into values
                for v in obj.values():
                    result = _find_usd_rate(v, depth + 1)
                    if result:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = _find_usd_rate(item, depth + 1)
                    if result:
                        return result
            return None

        usd_rate = _find_usd_rate(data)

        if usd_rate and usd_rate > 0:
            edges.append(Edge(
                from_currency="USD",
                to_currency="NPR",
                via="NRB (NP)",
                fee_pct=0.0,
                estimated_minutes=0,
                instructions="Nepal Rastra Bank official rate — reference only",
                exchange_rate=usd_rate,
            ))
        else:
            logger.debug(f"NRB: could not find USD rate in response keys={list(data.keys()) if isinstance(data, dict) else type(data)}")

        _nrb_cache["edges"] = edges
        _nrb_cache["ts"] = now
        logger.info(f"NRB: loaded {len(edges)} edges")
    except Exception as e:
        logger.warning(f"NRB adapter failed: {e}")
        return _nrb_cache["edges"]

    return edges


# ── NBP (National Bank of Poland) ──────────────────────────────────────────


async def get_nbp_edges() -> list[Edge]:
    """Fetch official USD/PLN and EUR/PLN rates from National Bank of Poland."""
    now = time.monotonic()
    if _nbp_cache["edges"] and (now - _nbp_cache["ts"]) < NBP_TTL:
        return _nbp_cache["edges"]

    edges: list[Edge] = []
    try:
        # NBP Table A = average exchange rates
        async with httpx.AsyncClient(headers={**HEADERS, "Accept": "application/json"}, timeout=15) as client:
            resp = await client.get(
                "https://api.nbp.pl/api/exchangerates/tables/A/?format=json"
            )
            resp.raise_for_status()
            data = resp.json()

        # Response: [{"table":"A","no":"...","effectiveDate":"...","rates":[{"currency":"...","code":"USD","mid":4.1234}]}]
        if data and isinstance(data, list):
            rates = data[0].get("rates", [])
            for rate_entry in rates:
                code = rate_entry.get("code", "")
                mid = rate_entry.get("mid")
                if code in ("USD", "EUR", "GBP", "CHF") and mid:
                    rate = float(mid)
                    if rate > 0:
                        edges.append(Edge(
                            from_currency=code,
                            to_currency="PLN",
                            via="NBP (PL)",
                            fee_pct=0.0,
                            estimated_minutes=0,
                            instructions="National Bank of Poland official rate — reference only",
                            exchange_rate=rate,
                        ))

        _nbp_cache["edges"] = edges
        _nbp_cache["ts"] = now
        logger.info(f"NBP: loaded {len(edges)} edges")
    except Exception as e:
        logger.warning(f"NBP adapter failed: {e}")
        return _nbp_cache["edges"]

    return edges


# ── CNB (Czech National Bank) ──────────────────────────────────────────────


async def get_cnb_edges() -> list[Edge]:
    """Fetch official USD/CZK and EUR/CZK rates from Czech National Bank."""
    now = time.monotonic()
    if _cnb_cache["edges"] and (now - _cnb_cache["ts"]) < CNB_TTL:
        return _cnb_cache["edges"]

    edges: list[Edge] = []
    try:
        # CNB daily rates text format (pipe-delimited)
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            resp = await client.get(
                "https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/denni_kurz.txt"
            )
            resp.raise_for_status()

        # Format: header lines, then "country|currency|amount|code|rate"
        # e.g. "USA|dolar|1|USD|23,456"
        wanted = {"USD", "EUR", "GBP", "CHF"}
        for line in resp.text.strip().split("\n")[2:]:  # skip date + header
            parts = line.split("|")
            if len(parts) >= 5:
                code = parts[3].strip()
                if code in wanted:
                    amount = int(parts[2].strip())
                    rate_str = parts[4].strip().replace(",", ".")
                    rate = float(rate_str) / amount
                    if rate > 0:
                        edges.append(Edge(
                            from_currency=code,
                            to_currency="CZK",
                            via="CNB (CZ)",
                            fee_pct=0.0,
                            estimated_minutes=0,
                            instructions="Czech National Bank official rate — reference only",
                            exchange_rate=rate,
                        ))

        _cnb_cache["edges"] = edges
        _cnb_cache["ts"] = now
        logger.info(f"CNB: loaded {len(edges)} edges")
    except Exception as e:
        logger.warning(f"CNB adapter failed: {e}")
        return _cnb_cache["edges"]

    return edges


# ── NBU (National Bank of Ukraine) ─────────────────────────────────────────


async def get_nbu_edges() -> list[Edge]:
    """Fetch official USD/UAH rate from National Bank of Ukraine JSON API."""
    now = time.monotonic()
    if _nbu_cache["edges"] and (now - _nbu_cache["ts"]) < NBU_TTL:
        return _nbu_cache["edges"]

    edges: list[Edge] = []
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            resp = await client.get(
                "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"
            )
            resp.raise_for_status()
            data = resp.json()

        # Response: [{"r030":840,"txt":"Долар США","rate":41.2345,"cc":"USD","exchangedate":"23.03.2026"}, ...]
        wanted = {"USD", "EUR", "GBP", "CHF", "PLN"}
        if isinstance(data, list):
            for entry in data:
                cc = entry.get("cc", "")
                if cc in wanted:
                    rate = entry.get("rate")
                    if rate and float(rate) > 0:
                        edges.append(Edge(
                            from_currency=cc,
                            to_currency="UAH",
                            via="NBU (UA)",
                            fee_pct=0.0,
                            estimated_minutes=0,
                            instructions="National Bank of Ukraine official rate — reference only",
                            exchange_rate=float(rate),
                        ))

        _nbu_cache["edges"] = edges
        _nbu_cache["ts"] = now
        logger.info(f"NBU: loaded {len(edges)} edges")
    except Exception as e:
        logger.warning(f"NBU adapter failed: {e}")
        return _nbu_cache["edges"]

    return edges


# ── NBG (National Bank of Georgia) ─────────────────────────────────────────


async def get_nbg_edges() -> list[Edge]:
    """Fetch official USD/GEL rate from National Bank of Georgia JSON API."""
    now = time.monotonic()
    if _nbg_cache["edges"] and (now - _nbg_cache["ts"]) < NBG_TTL:
        return _nbg_cache["edges"]

    edges: list[Edge] = []
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True) as client:
            # Try the newer API endpoint first
            resp = await client.get(
                f"https://nbg.gov.ge/gw/api/ct/monetarypolicy/currencies/en/json/?date={today}"
            )
            if resp.status_code != 200:
                # Fallback to older endpoint
                resp = await client.get(
                    "https://nbg.gov.ge/gw/api/ct/monetarypolicy/currencies/en/json/"
                )
            resp.raise_for_status()
            data = resp.json()

        # Response: [{"currencies":[{"code":"USD","quantity":1,"rate":2.7123,...}],...}]
        # or flat: [{"code":"USD","quantity":1,"rate":2.7123,...}]
        wanted = {"USD", "EUR", "GBP"}
        currencies = []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    # Nested structure
                    if "currencies" in item:
                        currencies.extend(item["currencies"])
                    # Flat structure
                    elif "code" in item:
                        currencies.append(item)

        for entry in currencies:
            code = entry.get("code", "")
            if code in wanted:
                rate = entry.get("rate")
                quantity = entry.get("quantity", 1)
                if rate and quantity:
                    effective_rate = float(rate) / int(quantity)
                    if effective_rate > 0:
                        edges.append(Edge(
                            from_currency=code,
                            to_currency="GEL",
                            via="NBG (GE)",
                            fee_pct=0.0,
                            estimated_minutes=0,
                            instructions="National Bank of Georgia official rate — reference only",
                            exchange_rate=effective_rate,
                        ))

        _nbg_cache["edges"] = edges
        _nbg_cache["ts"] = now
        logger.info(f"NBG: loaded {len(edges)} edges")
    except Exception as e:
        logger.warning(f"NBG adapter failed: {e}")
        return _nbg_cache["edges"]

    return edges


# ── BOI (Bank of Israel) ───────────────────────────────────────────────────


async def get_boi_edges() -> list[Edge]:
    """Fetch official USD/ILS rate from Bank of Israel XML feed."""
    now = time.monotonic()
    if _boi_cache["edges"] and (now - _boi_cache["ts"]) < BOI_TTL:
        return _boi_cache["edges"]

    edges: list[Edge] = []
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            resp = await client.get(
                "https://www.boi.org.il/PublicApi/GetExchangeRates?asXml=false"
            )
            resp.raise_for_status()
            data = resp.json()

        # Response: {"exchangeRates": [{"key":"USD","currentExchangeRate":3.6123,...}, ...]}
        wanted = {"USD", "EUR", "GBP"}
        ex_rates = data.get("exchangeRates", [])
        for entry in ex_rates:
            code = entry.get("key", "")
            if code in wanted:
                rate = entry.get("currentExchangeRate")
                unit = entry.get("unit", 1)
                if rate and unit:
                    effective_rate = float(rate) / int(unit)
                    if effective_rate > 0:
                        edges.append(Edge(
                            from_currency=code,
                            to_currency="ILS",
                            via="BOI (IL)",
                            fee_pct=0.0,
                            estimated_minutes=0,
                            instructions="Bank of Israel official rate — reference only",
                            exchange_rate=effective_rate,
                        ))

        _boi_cache["edges"] = edges
        _boi_cache["ts"] = now
        logger.info(f"BOI: loaded {len(edges)} edges")
    except Exception as e:
        logger.warning(f"BOI adapter failed: {e}")
        return _boi_cache["edges"]

    return edges


# ── BNR (National Bank of Romania) ─────────────────────────────────────────


async def get_bnr_edges() -> list[Edge]:
    """Fetch official USD/RON and EUR/RON rates from National Bank of Romania XML."""
    now = time.monotonic()
    if _bnr_cache["edges"] and (now - _bnr_cache["ts"]) < BNR_TTL:
        return _bnr_cache["edges"]

    edges: list[Edge] = []
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            resp = await client.get(
                "https://www.bnr.ro/nbrfxrates.xml"
            )
            resp.raise_for_status()

        root = ET.fromstring(resp.text)
        # Namespace: {http://www.bnr.ro/xsd}
        ns = {"bnr": "http://www.bnr.ro/xsd"}
        wanted = {"USD", "EUR", "GBP", "CHF"}
        for rate_elem in root.findall(".//bnr:Rate", ns):
            code = rate_elem.get("currency", "")
            if code in wanted and rate_elem.text:
                multiplier = int(rate_elem.get("multiplier", "1"))
                rate = float(rate_elem.text) / multiplier
                if rate > 0:
                    edges.append(Edge(
                        from_currency=code,
                        to_currency="RON",
                        via="BNR (RO)",
                        fee_pct=0.0,
                        estimated_minutes=0,
                        instructions="National Bank of Romania official rate — reference only",
                        exchange_rate=rate,
                    ))

        _bnr_cache["edges"] = edges
        _bnr_cache["ts"] = now
        logger.info(f"BNR: loaded {len(edges)} edges")
    except Exception as e:
        logger.warning(f"BNR adapter failed: {e}")
        return _bnr_cache["edges"]

    return edges


# ── CBR (Central Bank of Russia) ───────────────────────────────────────────


async def get_cbr_edges() -> list[Edge]:
    """Fetch official USD/RUB rate from Central Bank of Russia (via JSON mirror)."""
    now = time.monotonic()
    if _cbr_cache["edges"] and (now - _cbr_cache["ts"]) < CBR_TTL:
        return _cbr_cache["edges"]

    edges: list[Edge] = []
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            # Use the well-known JSON mirror (official XML blocks non-browser agents)
            resp = await client.get(
                "https://www.cbr-xml-daily.ru/daily_json.js"
            )
            resp.raise_for_status()
            data = resp.json()

        # Response: {"Date":"...","Valute":{"USD":{"ID":"...","NumCode":"840","CharCode":"USD","Nominal":1,"Name":"...","Value":84.1234,"Previous":...},...}}
        valute = data.get("Valute", {})
        wanted = {"USD", "EUR", "GBP", "CNY"}
        for code in wanted:
            entry = valute.get(code)
            if entry:
                nominal = entry.get("Nominal", 1)
                value = entry.get("Value")
                if value and nominal:
                    rate = float(value) / int(nominal)
                    if rate > 0:
                        edges.append(Edge(
                            from_currency=code,
                            to_currency="RUB",
                            via="CBR (RU)",
                            fee_pct=0.0,
                            estimated_minutes=0,
                            instructions="Central Bank of Russia official rate — reference only",
                            exchange_rate=rate,
                        ))

        _cbr_cache["edges"] = edges
        _cbr_cache["ts"] = now
        logger.info(f"CBR: loaded {len(edges)} edges")
    except Exception as e:
        logger.warning(f"CBR adapter failed: {e}")
        return _cbr_cache["edges"]

    return edges


# ── Uphold ──────────────────────────────────────────────────────────────────

UPHOLD_BASE_CURRENCIES = {"USD", "EUR", "GBP"}
UPHOLD_FEE = 1.20


async def get_uphold_edges() -> list[Edge]:
    """Fetch live rates from Uphold public ticker API (no auth required)."""
    now = time.monotonic()
    if _uphold_cache["edges"] and (now - _uphold_cache["ts"]) < UPHOLD_TTL:
        return _uphold_cache["edges"]

    edges: list[Edge] = []
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            resp = await client.get("https://api.uphold.com/v0/ticker")
            resp.raise_for_status()
            data = resp.json()

        for ticker in data:
            pair = ticker.get("pair", "")
            if len(pair) < 6:
                continue
            # Pair format: "USDMXN" — first 3 chars = base, rest = quote
            base = pair[:3]
            quote = pair[3:]
            if base not in UPHOLD_BASE_CURRENCIES:
                continue
            ask = float(ticker.get("ask", 0))
            bid = float(ticker.get("bid", 0))
            if not ask or not bid:
                continue

            # base → quote at ask price
            edges.append(Edge(
                from_currency=base,
                to_currency=quote,
                via="Uphold",
                fee_pct=UPHOLD_FEE,
                estimated_minutes=30,
                instructions=f"Convert {base} to {quote} on Uphold",
                exchange_rate=ask,
            ))
            # quote → base at 1/bid
            edges.append(Edge(
                from_currency=quote,
                to_currency=base,
                via="Uphold",
                fee_pct=UPHOLD_FEE,
                estimated_minutes=30,
                instructions=f"Convert {quote} to {base} on Uphold",
                exchange_rate=1.0 / bid,
            ))

        _uphold_cache["edges"] = edges
        _uphold_cache["ts"] = now
        logger.info(f"Uphold: loaded {len(edges)} edges")
    except Exception as e:
        logger.warning(f"Uphold adapter failed: {e}")
        return _uphold_cache["edges"]

    return edges


# ── OFX ─────────────────────────────────────────────────────────────────────

OFX_FEE = 0.50


_ofx_token_cache: dict = {"token": "", "ts": 0.0}
_OFX_TOKEN_TTL = 3000  # ~50 min (tokens last 60 min)


async def _ofx_get_token(client: httpx.AsyncClient) -> str | None:
    """Get OFX OAuth2 access token using client credentials."""
    now = time.monotonic()
    if _ofx_token_cache["token"] and (now - _ofx_token_cache["ts"]) < _OFX_TOKEN_TTL:
        return _ofx_token_cache["token"]
    cid = os.environ.get("OFX_CLIENT_ID", "")
    secret = os.environ.get("OFX_CLIENT_SECRET", "")
    if not cid or not secret:
        return None
    try:
        resp = await client.post(
            "https://sandbox.api.ofx.com/v1/oauth/token",
            data={"grant_type": "client_credentials",
                  "client_id": cid, "client_secret": secret,
                  "scope": "ofxrates"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )
        resp.raise_for_status()
        token = resp.json().get("access_token", "")
        if token:
            _ofx_token_cache["token"] = token
            _ofx_token_cache["ts"] = now
        return token
    except Exception as e:
        logger.warning(f"OFX token failed: {e}")
        return None


async def get_ofx_edges() -> list[Edge]:
    """Fetch live rates from OFX Rates API (OAuth2).
    Requires OFX_CLIENT_ID + OFX_CLIENT_SECRET env vars.
    Register free at https://developer.ofx.com/rates-api
    """
    # OFX disabled until production API access is approved (sandbox returns 401 on rates)
    # Re-enable by setting OFX_ENABLED=1 in .env
    if not os.environ.get("OFX_ENABLED"):
        return []
    cid = os.environ.get("OFX_CLIENT_ID", "")
    if not cid:
        return []

    now = time.monotonic()
    if _ofx_cache["edges"] and (now - _ofx_cache["ts"]) < OFX_TTL:
        return _ofx_cache["edges"]

    edges: list[Edge] = []
    corridors = [
        ("USD", "MXN"), ("USD", "EUR"), ("USD", "GBP"), ("USD", "AUD"),
        ("USD", "CAD"), ("USD", "INR"), ("USD", "PHP"), ("USD", "BRL"),
        ("USD", "NGN"), ("USD", "KES"), ("USD", "ZAR"), ("USD", "SGD"),
        ("EUR", "GBP"), ("EUR", "USD"), ("EUR", "MXN"), ("EUR", "INR"),
        ("GBP", "USD"), ("GBP", "EUR"), ("GBP", "INR"),
        ("AUD", "USD"), ("AUD", "GBP"), ("CAD", "USD"),
    ]
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            token = await _ofx_get_token(client)
            if not token:
                logger.warning("OFX: no token — skipping")
                return _ofx_cache.get("edges", [])

            for source, dest in corridors:
                try:
                    resp = await client.get(
                        f"https://sandbox.api.ofx.com/v1/rates/spot?CCYPair={source}{dest}",
                        headers={"Authorization": f"Bearer {token}"},
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    rate = float(data.get("rate", 0) or data.get("customerRate", 0) or 0)
                    if not rate:
                        continue
                    edges.append(Edge(
                        from_currency=source,
                        to_currency=dest,
                        via="OFX",
                        fee_pct=0.4,
                        estimated_minutes=1440,
                        instructions=f"Transfer {source} to {dest} via OFX — ~1 business day",
                        exchange_rate=rate,
                    ))
                    edges.append(Edge(
                        from_currency=dest,
                        to_currency=source,
                        via="OFX",
                        fee_pct=0.4,
                        estimated_minutes=1440,
                        instructions=f"Transfer {dest} to {source} via OFX — ~1 business day",
                        exchange_rate=1.0 / rate,
                    ))
                except Exception as inner_e:
                    logger.warning(f"OFX {source}->{dest} failed: {inner_e}")

        _ofx_cache["edges"] = edges
        _ofx_cache["ts"] = now
        logger.info(f"OFX: loaded {len(edges)} edges")
    except Exception as e:
        logger.warning(f"OFX adapter failed: {e}")
        return _ofx_cache["edges"]

    return edges
# Bridge edges enabled 2026-03-23T17:10
