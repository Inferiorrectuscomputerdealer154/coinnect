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
_trm_cache: dict = {"edges": [], "ts": 0.0}
_lirarate_cache: dict = {"edges": [], "ts": 0.0}
_yadio_cache: dict = {"edges": [], "ts": 0.0}
_valr_cache: dict = {"edges": [], "ts": 0.0}
_coindcx_cache: dict = {"edges": [], "ts": 0.0}
_wazirx_cache: dict = {"edges": [], "ts": 0.0}
_satoshitango_cache: dict = {"edges": [], "ts": 0.0}
_floatrates_cache: dict = {"edges": [], "ts": 0.0}

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
TRM_TTL = 3600          # 60 minutes
LIRARATE_TTL = 1800     # 30 minutes
YADIO_TTL = 300         # 5 minutes
VALR_TTL = 180          # 3 minutes
COINDCX_TTL = 180       # 3 minutes
WAZIRX_TTL = 180        # 3 minutes
SATOSHITANGO_TTL = 300  # 5 minutes
FLOATRATES_TTL = 3600   # 60 minutes (daily data)

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
                    fee_pct=0.0,
                    estimated_minutes=0,
                    instructions="P2P market rate — reference only",
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
                    fee_pct=0.0,
                    estimated_minutes=0,
                    instructions="P2P market rate — reference only",
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
                via="FloatRates",
                fee_pct=0.0,
                estimated_minutes=0,
                instructions="Market reference rate — daily FX data",
                exchange_rate=float(rate),
            ))

        _floatrates_cache["edges"] = edges
        _floatrates_cache["ts"] = now
        logger.info(f"FloatRates: loaded {len(edges)} reference edges")
    except Exception as e:
        logger.warning(f"FloatRates adapter failed: {e}")
        return _floatrates_cache["edges"]

    return edges
