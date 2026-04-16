"""
SEO pages — server-rendered corridor and country pages for search engine indexing.

Generates lightweight HTML with inline CSS, JSON-LD structured data, OG tags,
canonical URLs, and hreflang tags. No JavaScript required to render content.
"""

import html
import json
import time
import logging
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from coinnect.routing.engine import Edge, build_quote, QuoteResult

logger = logging.getLogger(__name__)

BASE_URL = "https://coinnect.bot"

# ── Corridor definitions ─────────────────────────────────────────────────────

TOP_CORRIDORS: list[tuple[str, str]] = [
    ("USD", "MXN"), ("USD", "INR"), ("USD", "PHP"), ("USD", "NGN"), ("USD", "BRL"),
    ("USD", "COP"), ("USD", "PKR"), ("USD", "BDT"), ("USD", "KES"), ("USD", "GHS"),
    ("EUR", "MXN"), ("EUR", "NGN"), ("EUR", "PHP"), ("EUR", "INR"), ("EUR", "TRY"),
    ("GBP", "INR"), ("GBP", "PHP"), ("GBP", "NGN"), ("GBP", "PKR"),
    ("AED", "INR"), ("AED", "PHP"), ("AED", "PKR"),
    ("CAD", "PHP"), ("CAD", "INR"),
    ("USD", "PYG"), ("USD", "UYU"), ("PYG", "USD"), ("UYU", "USD"),
    ("MXN", "USD"), ("BRL", "USD"), ("PHP", "USD"), ("INR", "USD"),
    ("NGN", "USD"), ("KES", "USD"),
]

# Default amounts for corridor pages (realistic transfer sizes)
DEFAULT_AMOUNTS: dict[str, float] = {
    "USD": 500, "EUR": 500, "GBP": 400, "CAD": 600, "AED": 2000,
    "MXN": 10000, "BRL": 2500, "PHP": 25000, "INR": 40000,
    "NGN": 500000, "KES": 50000, "PYG": 5000000, "UYU": 5000,
}

# ── Country definitions ───────────────────────────────────────────────────────

COUNTRY_DATA: dict[str, dict[str, Any]] = {
    "mexico": {
        "name": "Mexico", "currency": "MXN", "flag": "MX",
        "inbound": [("USD", "MXN"), ("EUR", "MXN"), ("GBP", "MXN"), ("CAD", "MXN")],
        "outbound": [("MXN", "USD"), ("MXN", "EUR")],
    },
    "india": {
        "name": "India", "currency": "INR", "flag": "IN",
        "inbound": [("USD", "INR"), ("EUR", "INR"), ("GBP", "INR"), ("AED", "INR"), ("CAD", "INR")],
        "outbound": [("INR", "USD")],
    },
    "philippines": {
        "name": "Philippines", "currency": "PHP", "flag": "PH",
        "inbound": [("USD", "PHP"), ("EUR", "PHP"), ("GBP", "PHP"), ("AED", "PHP"), ("CAD", "PHP")],
        "outbound": [("PHP", "USD")],
    },
    "nigeria": {
        "name": "Nigeria", "currency": "NGN", "flag": "NG",
        "inbound": [("USD", "NGN"), ("EUR", "NGN"), ("GBP", "NGN")],
        "outbound": [("NGN", "USD")],
    },
    "brazil": {
        "name": "Brazil", "currency": "BRL", "flag": "BR",
        "inbound": [("USD", "BRL"), ("EUR", "BRL")],
        "outbound": [("BRL", "USD")],
    },
    "colombia": {
        "name": "Colombia", "currency": "COP", "flag": "CO",
        "inbound": [("USD", "COP"), ("EUR", "COP")],
        "outbound": [("COP", "USD")],
    },
    "pakistan": {
        "name": "Pakistan", "currency": "PKR", "flag": "PK",
        "inbound": [("USD", "PKR"), ("GBP", "PKR"), ("AED", "PKR")],
        "outbound": [("PKR", "USD")],
    },
    "bangladesh": {
        "name": "Bangladesh", "currency": "BDT", "flag": "BD",
        "inbound": [("USD", "BDT")],
        "outbound": [("BDT", "USD")],
    },
    "kenya": {
        "name": "Kenya", "currency": "KES", "flag": "KE",
        "inbound": [("USD", "KES"), ("EUR", "KES"), ("GBP", "KES")],
        "outbound": [("KES", "USD")],
    },
    "ghana": {
        "name": "Ghana", "currency": "GHS", "flag": "GH",
        "inbound": [("USD", "GHS"), ("EUR", "GHS"), ("GBP", "GHS")],
        "outbound": [("GHS", "USD")],
    },
    "turkey": {
        "name": "Turkey", "currency": "TRY", "flag": "TR",
        "inbound": [("USD", "TRY"), ("EUR", "TRY")],
        "outbound": [("TRY", "USD"), ("TRY", "EUR")],
    },
    "argentina": {
        "name": "Argentina", "currency": "ARS", "flag": "AR",
        "inbound": [("USD", "ARS"), ("EUR", "ARS")],
        "outbound": [("ARS", "USD")],
    },
    "uk": {
        "name": "United Kingdom", "currency": "GBP", "flag": "GB",
        "inbound": [("USD", "GBP"), ("EUR", "GBP")],
        "outbound": [("GBP", "INR"), ("GBP", "PHP"), ("GBP", "NGN"), ("GBP", "PKR")],
    },
    "usa": {
        "name": "United States", "currency": "USD", "flag": "US",
        "inbound": [("MXN", "USD"), ("BRL", "USD"), ("PHP", "USD"), ("INR", "USD"), ("NGN", "USD"), ("KES", "USD")],
        "outbound": [("USD", "MXN"), ("USD", "INR"), ("USD", "PHP"), ("USD", "NGN"), ("USD", "BRL"),
                     ("USD", "COP"), ("USD", "PKR"), ("USD", "BDT"), ("USD", "KES"), ("USD", "GHS")],
    },
    "canada": {
        "name": "Canada", "currency": "CAD", "flag": "CA",
        "inbound": [("USD", "CAD")],
        "outbound": [("CAD", "PHP"), ("CAD", "INR")],
    },
    "uae": {
        "name": "UAE", "currency": "AED", "flag": "AE",
        "inbound": [("USD", "AED")],
        "outbound": [("AED", "INR"), ("AED", "PHP"), ("AED", "PKR")],
    },
    "germany": {
        "name": "Germany", "currency": "EUR", "flag": "DE",
        "inbound": [("USD", "EUR")],
        "outbound": [("EUR", "MXN"), ("EUR", "NGN"), ("EUR", "PHP"), ("EUR", "INR"), ("EUR", "TRY")],
    },
    "france": {
        "name": "France", "currency": "EUR", "flag": "FR",
        "inbound": [("USD", "EUR")],
        "outbound": [("EUR", "MXN"), ("EUR", "NGN"), ("EUR", "PHP"), ("EUR", "INR"), ("EUR", "TRY")],
    },
    "japan": {
        "name": "Japan", "currency": "JPY", "flag": "JP",
        "inbound": [("USD", "JPY")],
        "outbound": [("JPY", "USD"), ("JPY", "PHP")],
    },
    "south-africa": {
        "name": "South Africa", "currency": "ZAR", "flag": "ZA",
        "inbound": [("USD", "ZAR"), ("GBP", "ZAR")],
        "outbound": [("ZAR", "USD")],
    },
    "hong-kong": {
        "name": "Hong Kong", "currency": "HKD", "flag": "HK",
        "inbound": [("USD", "HKD"), ("GBP", "HKD"), ("EUR", "HKD")],
        "outbound": [("HKD", "USD"), ("HKD", "EUR")],
    },
    "singapore": {
        "name": "Singapore", "currency": "SGD", "flag": "SG",
        "inbound": [("USD", "SGD"), ("GBP", "SGD"), ("AUD", "SGD")],
        "outbound": [("SGD", "USD"), ("SGD", "INR"), ("SGD", "PHP")],
    },
    "indonesia": {
        "name": "Indonesia", "currency": "IDR", "flag": "ID",
        "inbound": [("USD", "IDR"), ("SGD", "IDR")],
        "outbound": [("IDR", "USD")],
    },
    "thailand": {
        "name": "Thailand", "currency": "THB", "flag": "TH",
        "inbound": [("USD", "THB"), ("GBP", "THB")],
        "outbound": [("THB", "USD")],
    },
    "vietnam": {
        "name": "Vietnam", "currency": "VND", "flag": "VN",
        "inbound": [("USD", "VND"), ("EUR", "VND")],
        "outbound": [("VND", "USD")],
    },
    "australia": {
        "name": "Australia", "currency": "AUD", "flag": "AU",
        "inbound": [("USD", "AUD"), ("GBP", "AUD")],
        "outbound": [("AUD", "USD"), ("AUD", "INR"), ("AUD", "PHP")],
    },
    "paraguay": {
        "name": "Paraguay", "currency": "PYG", "flag": "PY",
        "inbound": [("USD", "PYG"), ("EUR", "PYG"), ("BRL", "PYG"), ("ARS", "PYG")],
        "outbound": [("PYG", "USD"), ("PYG", "EUR"), ("PYG", "BRL"), ("PYG", "ARS")],
    },
    "uruguay": {
        "name": "Uruguay", "currency": "UYU", "flag": "UY",
        "inbound": [("USD", "UYU"), ("EUR", "UYU"), ("BRL", "UYU"), ("ARS", "UYU")],
        "outbound": [("UYU", "USD"), ("UYU", "EUR"), ("UYU", "BRL"), ("UYU", "ARS")],
    },
    "chile": {
        "name": "Chile", "currency": "CLP", "flag": "CL",
        "inbound": [("USD", "CLP"), ("EUR", "CLP")],
        "outbound": [("CLP", "USD")],
    },
    "peru": {
        "name": "Peru", "currency": "PEN", "flag": "PE",
        "inbound": [("USD", "PEN"), ("EUR", "PEN")],
        "outbound": [("PEN", "USD")],
    },
    "egypt": {
        "name": "Egypt", "currency": "EGP", "flag": "EG",
        "inbound": [("USD", "EGP"), ("EUR", "EGP"), ("GBP", "EGP")],
        "outbound": [],
    },
}

# ── Currency display names ────────────────────────────────────────────────────

CURRENCY_NAMES: dict[str, str] = {
    "USD": "US Dollar", "EUR": "Euro", "GBP": "British Pound", "CAD": "Canadian Dollar",
    "AED": "UAE Dirham", "MXN": "Mexican Peso", "BRL": "Brazilian Real",
    "INR": "Indian Rupee", "PHP": "Philippine Peso", "NGN": "Nigerian Naira",
    "COP": "Colombian Peso", "PKR": "Pakistani Rupee", "BDT": "Bangladeshi Taka",
    "KES": "Kenyan Shilling", "GHS": "Ghanaian Cedi", "TRY": "Turkish Lira",
    "HKD": "Hong Kong Dollar", "SGD": "Singapore Dollar", "IDR": "Indonesian Rupiah",
    "THB": "Thai Baht", "VND": "Vietnamese Dong", "AUD": "Australian Dollar",
    "CLP": "Chilean Peso", "PEN": "Peruvian Sol", "EGP": "Egyptian Pound",
    "ARS": "Argentine Peso", "JPY": "Japanese Yen", "ZAR": "South African Rand",
    "PYG": "Paraguayan Guaraní", "UYU": "Uruguayan Peso",
}

# ── HTML cache ────────────────────────────────────────────────────────────────

_html_cache: dict[str, tuple[float, str]] = {}
CACHE_TTL = 180  # 3 minutes

# ── Reference provider filter (keep in sync with api/routes.py) ──────────────

REFERENCE_PROVIDERS = {
    # FX reference data (not transfer services)
    "Market rate", "ECB (reference)", "FloatRates", "x-rates.com (mid-market)",
    "Yadio (P2P)", "CoinGecko (market)",
    # Central bank official rates (reference only, not transfer services)
    "BCB PTAX (BR)", "Banxico (MX)", "TRM (CO)", "TCMB (TR)", "NBP (PL)", "CNB (CZ)",
    "NBU (UA)", "NBG (GE)", "BOI (IL)", "BNR (RO)", "NRB (NP)",
    # Argentina parallel market rates
    "Blue market (AR)", "Official (AR)", "Dolar Blue (AR)", "MEP (AR)", "CCL (AR)",
    # Other
    "Parallel (LB)",
}


def _is_reference_provider(via: str) -> bool:
    """Check if a provider is reference-only (pure data source, not a transfer service)."""
    if via in REFERENCE_PROVIDERS:
        return True
    # CriptoYa individual exchanges: e.g. "ripio (AR)", "belo (AR)", etc.
    if via.endswith(" (AR)"):
        return True
    return False


def _filter_real_edges(edges: list[Edge]) -> list[Edge]:
    """Remove reference-only providers — they should not appear as user-facing routes."""
    return [e for e in edges if not _is_reference_provider(e.via)]


def _cache_get(key: str) -> str | None:
    if key in _html_cache:
        ts, content = _html_cache[key]
        if time.monotonic() - ts < CACHE_TTL:
            return content
        del _html_cache[key]
    return None


def _cache_set(key: str, content: str) -> None:
    _html_cache[key] = (time.monotonic(), content)


# ── Shared HTML fragments ─────────────────────────────────────────────────────

COINNECT_LOGO_SVG = (
    '<svg width="24" height="24" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">'
    '<circle cx="16" cy="16" r="14" stroke="#06b6d4" stroke-width="2"/>'
    '<text x="16" y="21" font-size="13" text-anchor="middle" fill="#F7931A" '
    'font-family="monospace" font-weight="bold">&#x20bf;</text>'
    '<text x="16" y="13" font-size="10" text-anchor="middle" fill="#06b6d4" '
    'font-family="monospace">$</text></svg>'
)


def _hreflang_tags(path: str) -> str:
    """Only declare en + x-default (no false multilingual claims)."""
    return (
        f'  <link rel="alternate" hreflang="en" href="{BASE_URL}{path}">\n'
        f'  <link rel="alternate" hreflang="x-default" href="{BASE_URL}{path}">'
    )


def _base_style() -> str:
    return """
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:system-ui,-apple-system,sans-serif;background:#f8fafc;color:#1a1a1a;line-height:1.6}
    .topnav{position:sticky;top:0;background:rgba(255,255,255,.95);backdrop-filter:blur(8px);
             border-bottom:1px solid #e2e8f0;display:flex;align-items:center;
             justify-content:space-between;padding:.75rem 1.5rem;z-index:10}
    .logo{display:flex;align-items:center;gap:.5rem;text-decoration:none;color:#1a1a1a;font-weight:700}
    .cta{text-decoration:none;color:#fff;font-size:.85rem;padding:.45rem 1rem;
         border-radius:8px;background:#06b6d4;font-weight:600}
    .cta:hover{background:#0891b2}
    .container{max-width:800px;margin:0 auto;padding:1.5rem}
    h1{font-size:1.8rem;font-weight:800;margin-bottom:.5rem;color:#0f172a}
    h2{font-size:1.3rem;font-weight:700;margin:2rem 0 .8rem;color:#0f172a}
    h3{font-size:1.05rem;font-weight:600;margin:1.5rem 0 .5rem;color:#334155}
    p{margin:.5rem 0;color:#475569}
    .subtitle{font-size:1.05rem;color:#64748b;margin-bottom:1.5rem}
    table{width:100%;border-collapse:collapse;font-size:.88rem;margin:.8rem 0 1.5rem}
    th{background:#f1f5f9;padding:.6rem .8rem;text-align:left;color:#64748b;font-weight:600;
       font-size:.78rem;text-transform:uppercase;letter-spacing:.04em;border-bottom:2px solid #e2e8f0}
    td{padding:.6rem .8rem;border-bottom:1px solid #f1f5f9;vertical-align:middle}
    tr:hover td{background:#f8fafc}
    .badge{display:inline-block;padding:.15rem .5rem;border-radius:10px;font-size:.72rem;font-weight:600;color:#fff}
    .badge-green{background:#059669}
    .badge-blue{background:#2563eb}
    .badge-gray{background:#6b7280}
    .card{background:#fff;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,.06);padding:1.5rem;margin-bottom:1.5rem}
    .footer{text-align:center;padding:2rem 1rem;color:#94a3b8;font-size:.8rem;border-top:1px solid #e2e8f0;margin-top:2rem}
    .footer a{color:#06b6d4;text-decoration:none}
    .breadcrumb{font-size:.82rem;color:#94a3b8;margin-bottom:1rem}
    .breadcrumb a{color:#06b6d4;text-decoration:none}
    .corridor-link{display:inline-block;padding:.3rem .7rem;margin:.25rem;border:1px solid #e2e8f0;
                   border-radius:8px;text-decoration:none;color:#334155;font-size:.85rem;background:#fff}
    .corridor-link:hover{border-color:#06b6d4;color:#06b6d4;background:#f0fdfe}
    @media(max-width:600px){h1{font-size:1.4rem}.container{padding:1rem}th,td{padding:.4rem .5rem}}
    """


def _nav_html() -> str:
    return f"""<nav class="topnav">
  <a href="/" class="logo">{COINNECT_LOGO_SVG} Coinnect</a>
  <a href="/" class="cta">Compare rates now</a>
</nav>"""


def _footer_html() -> str:
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<footer class="footer">
  <p>Rates updated every 3 minutes. Last render: {html.escape(now)}</p>
  <p>Mission-driven. No affiliate fees. Open data (CC-BY 4.0).</p>
  <p><a href="/">Home</a> &middot; <a href="/exchanges">Exchanges</a> &middot;
     <a href="/explore">Corridors</a> &middot; <a href="/whitepaper">Whitepaper</a> &middot;
     <a href="/docs">API Docs</a> &middot; <a href="/sitemap.xml">Sitemap</a></p>
  <p>&copy; {datetime.now(UTC).year} <a href="{BASE_URL}">Coinnect</a> — The open map for global money</p>
</footer>"""


# ── Corridor page rendering ──────────────────────────────────────────────────

def _route_rows_html(result: QuoteResult, to_currency: str) -> str:
    rows = ""
    for r in result.routes:
        via_parts = " &rarr; ".join(html.escape(s.via) for s in r.steps)
        badge_cls = "badge-green" if r.rank == 1 else ("badge-blue" if r.rank == 2 else "badge-gray")
        label = html.escape(r.label)
        h = r.total_time_minutes // 60
        m = r.total_time_minutes % 60
        time_str = f"{h}h {m}m" if h else f"{m}m"
        rows += f"""<tr>
  <td><span class="badge {badge_cls}">{label}</span></td>
  <td>{via_parts}</td>
  <td style="text-align:right;font-weight:600">{r.total_cost_pct:.2f}%</td>
  <td style="text-align:right">{r.they_receive:,.2f} {html.escape(to_currency)}</td>
  <td style="text-align:right;color:#6b7280">{time_str}</td>
</tr>"""
    return rows


def render_corridor_page(
    from_c: str, to_c: str, edges: list[Edge],
) -> str:
    """Render a full SSR corridor page for /send/{from}-to-{to}."""
    from_c = from_c.upper()
    to_c = to_c.upper()
    amount = DEFAULT_AMOUNTS.get(from_c, 500)
    from_name = html.escape(CURRENCY_NAMES.get(from_c, from_c))
    to_name = html.escape(CURRENCY_NAMES.get(to_c, to_c))
    path = f"/send/{from_c.lower()}-to-{to_c.lower()}"
    canonical = f"{BASE_URL}{path}"

    # Filter out reference-only providers (CoinGecko, Yadio, etc.)
    edges = _filter_real_edges(edges)

    # Build quote
    result = build_quote(edges, from_c, to_c, amount)
    has_routes = bool(result.routes)

    # Build routes table
    if has_routes:
        rows_html = _route_rows_html(result, to_c)
        best = result.routes[0]
        best_cost = f"{best.total_cost_pct:.2f}%"
        best_via = html.escape(" > ".join(s.via for s in best.steps))
        best_receive = f"{best.they_receive:,.2f}"
        table_html = f"""<div class="card">
<h2>Best routes for {amount:g} {html.escape(from_c)} to {html.escape(to_c)} today</h2>
<table>
  <thead><tr><th>Route</th><th>Path</th><th>Fee</th><th>Recipient gets</th><th>Time</th></tr></thead>
  <tbody>{rows_html}</tbody>
</table>
</div>"""
        meta_desc = (
            f"Send {html.escape(from_c)} to {html.escape(to_c)} cheaply. "
            f"Best rate today: {best_cost} fee via {best_via}. "
            f"{amount:g} {html.escape(from_c)} = {best_receive} {html.escape(to_c)}. "
            f"Compare {len(result.routes)} routes across crypto, Wise, and remittance providers."
        )
        og_desc = (
            f"Cheapest: {best_cost} via {best_via}. "
            f"Send {amount:g} {html.escape(from_c)}, receive {best_receive} {html.escape(to_c)}."
        )
    else:
        table_html = f"""<div class="card">
<h2>Routes for {html.escape(from_c)} to {html.escape(to_c)}</h2>
<p>No live routes available right now. Rates refresh every 3 minutes — check back soon or
<a href="/?from={html.escape(from_c)}&to={html.escape(to_c)}">try the interactive search</a>.</p>
</div>"""
        meta_desc = (
            f"Send {html.escape(from_c)} to {html.escape(to_c)} — compare routes across "
            f"crypto exchanges, Wise, and traditional remittance. Updated every 3 minutes."
        )
        og_desc = meta_desc
        best_cost = "N/A"
        best_receive = "N/A"

    # JSON-LD structured data
    json_ld = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": f"Send {from_c} to {to_c} — Cheapest Routes Today",
        "description": meta_desc,
        "url": canonical,
        "provider": {
            "@type": "Organization",
            "name": "Coinnect",
            "url": BASE_URL,
        },
        "dateModified": datetime.now(UTC).isoformat(),
    }
    if has_routes:
        json_ld["mainEntity"] = {
            "@type": "FinancialProduct",
            "name": f"{from_c} to {to_c} money transfer",
            "description": f"Compare routes to send {from_c} to {to_c}",
            "feesAndCommissionsSpecification": f"Best rate: {best_cost} total fee",
        }

    # Related corridors
    related = []
    for fc, tc in TOP_CORRIDORS:
        if (fc, tc) != (from_c, to_c):
            related.append((fc, tc))
    related = related[:12]
    related_html = '<div class="card"><h3>Other popular corridors</h3><p>'
    for fc, tc in related:
        slug = f"{fc.lower()}-to-{tc.lower()}"
        related_html += f'<a class="corridor-link" href="/send/{slug}">{fc} &rarr; {tc}</a> '
    related_html += "</p></div>"

    # How it works section
    howto_html = f"""<div class="card">
<h2>How to send {html.escape(from_c)} to {html.escape(to_c)} cheaply</h2>
<ol style="padding-left:1.5rem;color:#475569">
<li style="margin:.5rem 0"><strong>Compare routes above</strong> — Coinnect checks crypto exchanges, Wise, Western Union, and more every 3 minutes.</li>
<li style="margin:.5rem 0"><strong>Pick the cheapest path</strong> — Some routes use crypto as a bridge (e.g. buy USDC, send, sell). Others are direct bank transfers.</li>
<li style="margin:.5rem 0"><strong>Execute it yourself</strong> — Coinnect never touches your money. Follow the step-by-step instructions for your chosen route.</li>
</ol>
<p style="margin-top:.8rem">Coinnect is mission-driven, open-source, and takes no affiliate fees. <a href="/whitepaper">Read the whitepaper</a>.</p>
</div>"""

    # FAQ section for SEO
    faq_html = f"""<div class="card">
<h2>FAQ: {html.escape(from_c)} to {html.escape(to_c)}</h2>
<h3>What is the cheapest way to send {html.escape(from_c)} to {html.escape(to_c)}?</h3>
<p>It changes every few minutes. Right now the cheapest route has a {best_cost} fee. Coinnect compares all options automatically.</p>
<h3>Does Coinnect transfer my money?</h3>
<p>No. Coinnect is a comparison engine. It finds the cheapest route and gives you step-by-step instructions to execute it yourself on the actual platforms (Wise, Binance, Coinbase, etc.).</p>
<h3>How often are rates updated?</h3>
<p>Every 3 minutes. Rates are pulled live from 15+ exchanges and remittance providers.</p>
<h3>Is Coinnect free?</h3>
<p>Yes. Free for personal use, no affiliate fees, open source. <a href="/">Use the interactive search</a> for any amount.</p>
</div>"""

    # FAQ JSON-LD
    faq_ld = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": f"What is the cheapest way to send {from_c} to {to_c}?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f"It changes every few minutes. Coinnect compares all options automatically across crypto exchanges, Wise, and traditional remittance providers. Currently the best route has a {best_cost} fee.",
                },
            },
            {
                "@type": "Question",
                "name": "Does Coinnect transfer my money?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "No. Coinnect is a comparison engine. It finds the cheapest route and gives step-by-step instructions to execute on the actual platforms.",
                },
            },
            {
                "@type": "Question",
                "name": "How often are rates updated?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Every 3 minutes. Rates are pulled live from 15+ exchanges and remittance providers.",
                },
            },
        ],
    }

    now_dt = datetime.now(UTC)
    now_str = now_dt.strftime("%Y-%m-%d %H:%M UTC")
    now_iso = now_dt.isoformat()

    # Quick answer box (above the fold, before routes table)
    if not has_routes:
        best_via = ""
    if has_routes:
        answer_box = (
            f'<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:12px;'
            f'padding:16px 20px;margin-bottom:24px">\n'
            f'  <p style="font-size:18px;font-weight:700;color:#166534;margin:0">\n'
            f'    Right now: The cheapest route is {best_via} &mdash; {best_cost} fee.\n'
            f'  </p>\n'
            f'  <p style="font-size:14px;color:#4b5563;margin:8px 0 0">\n'
            f'    Send {amount:g} {html.escape(from_c)}, recipient gets {best_receive} '
            f'{html.escape(to_c)}. Updated {now_str}.\n'
            f'  </p>\n'
            f'</div>'
        )
    else:
        answer_box = ""

    # Methodology section (after routes table)
    methodology_html = (
        '<div class="card">\n'
        '<h2>How we calculate these rates</h2>\n'
        '<p>Coinnect pulls live rates from exchange APIs (Binance, Kraken, Coinbase, Wise, and others) '
        'every 3 minutes. For providers without live APIs, we use published fee schedules verified '
        'quarterly against World Bank data. Total cost includes exchange rate markup + transfer fees. '
        'Routes are ranked by total cost to the recipient &mdash; never by partnerships or commissions. '
        '<a href="/whitepaper">Read our methodology</a>.</p>\n'
        '</div>'
    )

    # BreadcrumbList JSON-LD
    breadcrumb_ld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Coinnect", "item": f"{BASE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": "Send Money", "item": f"{BASE_URL}/send/"},
            {"@type": "ListItem", "position": 3, "name": f"{from_c} to {to_c}", "item": canonical},
        ],
    }

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Send {html.escape(from_c)} to {html.escape(to_c)} — Cheapest Routes Today | Coinnect</title>
  <meta name="description" content="{html.escape(meta_desc)}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{canonical}">
{_hreflang_tags(path)}
  <meta property="og:type" content="website">
  <meta property="og:title" content="Send {html.escape(from_c)} to {html.escape(to_c)} — Coinnect">
  <meta property="og:description" content="{html.escape(og_desc)}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:site_name" content="Coinnect">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Send {html.escape(from_c)} to {html.escape(to_c)} — Coinnect">
  <meta name="twitter:description" content="{html.escape(og_desc)}">
  <script type="application/ld+json">{json.dumps(json_ld)}</script>
  <script type="application/ld+json">{json.dumps(faq_ld)}</script>
  <script type="application/ld+json">{json.dumps(breadcrumb_ld)}</script>
  <style>{_base_style()}</style>
</head>
<body>
{_nav_html()}
<main class="container">
  <nav class="breadcrumb">
    <a href="/">Home</a> &rsaquo; <a href="/send/{from_c.lower()}-to-{to_c.lower()}">Send {html.escape(from_c)} to {html.escape(to_c)}</a>
  </nav>
  <h1>Send {from_name} ({html.escape(from_c)}) to {to_name} ({html.escape(to_c)})</h1>
  <time datetime="{now_iso}" style="font-size:12px;color:#9ca3af">Last updated: {now_str} &middot; Refreshes every 3 minutes</time>
  <p class="subtitle">Compare the cheapest routes to convert {html.escape(from_c)} to {html.escape(to_c)} — updated every 3 minutes across 15+ providers.</p>

  {answer_box}
  {table_html}

  <div style="text-align:center;margin:1.5rem 0">
    <a href="/?from={html.escape(from_c)}&to={html.escape(to_c)}&amount={amount:g}" class="cta"
       style="display:inline-block;padding:.7rem 2rem;font-size:1.05rem;border-radius:10px">
      Try it yourself &mdash; search {html.escape(from_c)} &rarr; {html.escape(to_c)}
    </a>
    <p style="font-size:.82rem;color:#94a3b8;margin-top:.5rem">Enter any amount. Live results. No sign-up.</p>
  </div>

  {methodology_html}
  {howto_html}
  {faq_html}
  {related_html}

  <div class="card" style="text-align:center">
    <p style="font-size:1.05rem;font-weight:600;margin-bottom:.5rem">Want a custom amount?</p>
    <p><a href="/?from={html.escape(from_c)}&to={html.escape(to_c)}" class="cta" style="display:inline-block;padding:.6rem 1.5rem;font-size:1rem">Search {html.escape(from_c)} &rarr; {html.escape(to_c)} on Coinnect</a></p>
  </div>
</main>
{_footer_html()}
</body>
</html>"""


# ── Country page rendering ───────────────────────────────────────────────────

def render_country_page(
    country_slug: str, edges: list[Edge],
) -> str | None:
    """Render a country page for /rates/{country}. Returns None if unknown country."""
    data = COUNTRY_DATA.get(country_slug)
    if not data:
        return None

    country_name = html.escape(data["name"])
    currency = html.escape(data["currency"])
    path = f"/rates/{country_slug}"
    canonical = f"{BASE_URL}{path}"

    # Filter out reference-only providers (CoinGecko, Yadio, etc.)
    edges = _filter_real_edges(edges)

    # Build quotes for all corridors
    sections_html = ""

    # Inbound (sending TO this country)
    if data["inbound"]:
        sections_html += f'<h2>Send money to {country_name}</h2>\n'
        for from_c, to_c in data["inbound"]:
            amount = DEFAULT_AMOUNTS.get(from_c, 500)
            result = build_quote(edges, from_c, to_c, amount)
            slug = f"{from_c.lower()}-to-{to_c.lower()}"
            sections_html += f'<div class="card">\n'
            sections_html += f'<h3><a href="/send/{slug}" style="color:#0f172a;text-decoration:none">{html.escape(from_c)} &rarr; {html.escape(to_c)}</a> <span style="font-weight:400;color:#64748b;font-size:.85rem">({amount:g} {html.escape(from_c)})</span></h3>\n'
            if result.routes:
                top3 = result.routes[:3]
                sections_html += '<table><thead><tr><th>Route</th><th>Path</th><th>Fee</th><th>Receives</th><th>Time</th></tr></thead><tbody>'
                sections_html += _route_rows_html_limited(top3, to_c)
                sections_html += '</tbody></table>'
                if len(result.routes) > 3:
                    sections_html += f'<p style="font-size:.85rem"><a href="/send/{slug}">See all {len(result.routes)} routes &rarr;</a></p>\n'
            else:
                sections_html += '<p style="color:#94a3b8">No live routes. Check back in a few minutes.</p>\n'
            sections_html += '</div>\n'

    # Outbound (sending FROM this country)
    if data["outbound"]:
        sections_html += f'<h2>Send money from {country_name}</h2>\n'
        for from_c, to_c in data["outbound"]:
            amount = DEFAULT_AMOUNTS.get(from_c, 500)
            result = build_quote(edges, from_c, to_c, amount)
            slug = f"{from_c.lower()}-to-{to_c.lower()}"
            sections_html += f'<div class="card">\n'
            sections_html += f'<h3><a href="/send/{slug}" style="color:#0f172a;text-decoration:none">{html.escape(from_c)} &rarr; {html.escape(to_c)}</a> <span style="font-weight:400;color:#64748b;font-size:.85rem">({amount:g} {html.escape(from_c)})</span></h3>\n'
            if result.routes:
                top3 = result.routes[:3]
                sections_html += '<table><thead><tr><th>Route</th><th>Path</th><th>Fee</th><th>Receives</th><th>Time</th></tr></thead><tbody>'
                sections_html += _route_rows_html_limited(top3, to_c)
                sections_html += '</tbody></table>'
                if len(result.routes) > 3:
                    sections_html += f'<p style="font-size:.85rem"><a href="/send/{slug}">See all {len(result.routes)} routes &rarr;</a></p>\n'
            else:
                sections_html += '<p style="color:#94a3b8">No live routes. Check back in a few minutes.</p>\n'
            sections_html += '</div>\n'

    # Related countries
    other_countries = [s for s in COUNTRY_DATA if s != country_slug][:12]
    related_html = '<div class="card"><h3>Other countries</h3><p>'
    for slug in other_countries:
        cname = html.escape(COUNTRY_DATA[slug]["name"])
        related_html += f'<a class="corridor-link" href="/rates/{slug}">{cname}</a> '
    related_html += '</p></div>'

    meta_desc = (
        f"Compare money transfer rates to and from {country_name} ({currency}). "
        f"Live rates updated every 3 minutes across crypto, Wise, and remittance providers."
    )

    now_dt = datetime.now(UTC)
    now_str = now_dt.strftime("%Y-%m-%d %H:%M UTC")
    now_iso = now_dt.isoformat()

    json_ld = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": f"Money Transfer Rates — {data['name']}",
        "description": meta_desc,
        "url": canonical,
        "provider": {
            "@type": "Organization",
            "name": "Coinnect",
            "url": BASE_URL,
        },
        "dateModified": now_iso,
    }

    # Methodology section
    methodology_html = (
        '<div class="card">\n'
        '<h2>How we calculate these rates</h2>\n'
        '<p>Coinnect pulls live rates from exchange APIs (Binance, Kraken, Coinbase, Wise, and others) '
        'every 3 minutes. For providers without live APIs, we use published fee schedules verified '
        'quarterly against World Bank data. Total cost includes exchange rate markup + transfer fees. '
        'Routes are ranked by total cost to the recipient &mdash; never by partnerships or commissions. '
        '<a href="/whitepaper">Read our methodology</a>.</p>\n'
        '</div>'
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Money Transfer Rates — {country_name} ({currency}) | Coinnect</title>
  <meta name="description" content="{html.escape(meta_desc)}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{canonical}">
{_hreflang_tags(path)}
  <meta property="og:type" content="website">
  <meta property="og:title" content="Money Transfer Rates — {country_name} | Coinnect">
  <meta property="og:description" content="{html.escape(meta_desc)}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:site_name" content="Coinnect">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Money Transfer Rates — {country_name} | Coinnect">
  <meta name="twitter:description" content="{html.escape(meta_desc)}">
  <script type="application/ld+json">{json.dumps(json_ld)}</script>
  <style>{_base_style()}</style>
</head>
<body>
{_nav_html()}
<main class="container">
  <nav class="breadcrumb">
    <a href="/">Home</a> &rsaquo; <a href="/rates/{country_slug}">Rates: {country_name}</a>
  </nav>
  <h1>Money Transfer Rates: {country_name}</h1>
  <time datetime="{now_iso}" style="font-size:12px;color:#9ca3af">Last updated: {now_str} &middot; Refreshes every 3 minutes</time>
  <p class="subtitle">Live rates for all corridors involving {currency} ({country_name}) — updated every 3 minutes.</p>

  {sections_html}
  {methodology_html}
  {related_html}

  <div class="card" style="text-align:center">
    <p style="font-size:1.05rem;font-weight:600;margin-bottom:.5rem">Need a different corridor?</p>
    <p><a href="/" class="cta" style="display:inline-block;padding:.6rem 1.5rem;font-size:1rem">Search any corridor on Coinnect</a></p>
  </div>
</main>
{_footer_html()}
</body>
</html>"""


def _route_rows_html_limited(routes: list, to_currency: str) -> str:
    rows = ""
    for r in routes:
        via_parts = " &rarr; ".join(html.escape(s.via) for s in r.steps)
        badge_cls = "badge-green" if r.rank == 1 else ("badge-blue" if r.rank == 2 else "badge-gray")
        label = html.escape(r.label)
        h = r.total_time_minutes // 60
        m = r.total_time_minutes % 60
        time_str = f"{h}h {m}m" if h else f"{m}m"
        rows += f"""<tr>
  <td><span class="badge {badge_cls}">{label}</span></td>
  <td>{via_parts}</td>
  <td style="text-align:right;font-weight:600">{r.total_cost_pct:.2f}%</td>
  <td style="text-align:right">{r.they_receive:,.2f} {html.escape(to_currency)}</td>
  <td style="text-align:right;color:#6b7280">{time_str}</td>
</tr>"""
    return rows


# ── Sitemap generation ────────────────────────────────────────────────────────

def generate_sitemap_xml() -> str:
    """Generate a complete sitemap including all corridor and country pages."""
    now = datetime.now(UTC).strftime("%Y-%m-%d")
    urls = []

    # Static pages
    urls.append(("https://coinnect.bot/", "daily", "1.0"))
    urls.append(("https://coinnect.bot/whitepaper", "monthly", "0.8"))
    urls.append(("https://coinnect.bot/docs", "weekly", "0.8"))
    urls.append(("https://coinnect.bot/llms.txt", "monthly", "0.5"))

    # Corridor pages
    for from_c, to_c in TOP_CORRIDORS:
        slug = f"{from_c.lower()}-to-{to_c.lower()}"
        urls.append((f"https://coinnect.bot/send/{slug}", "hourly", "0.9"))

    # Country pages
    for country_slug in COUNTRY_DATA:
        urls.append((f"https://coinnect.bot/rates/{country_slug}", "hourly", "0.85"))

    # Country-based corridor pages (e.g. /send/united-states/mexico)
    _seen_pairs = set()
    for from_slug, from_data in COUNTRY_DATA.items():
        from_kebab = from_data["name"].lower().replace(" ", "-")
        for to_slug, to_data in COUNTRY_DATA.items():
            if from_slug == to_slug:
                continue
            pair_key = (from_data["currency"], to_data["currency"])
            if pair_key in _seen_pairs:
                continue
            # Only add if this is a real corridor (appears in outbound/inbound)
            for fc, tc in from_data.get("outbound", []):
                if tc == to_data["currency"]:
                    to_kebab = to_data["name"].lower().replace(" ", "-")
                    urls.append((f"https://coinnect.bot/send/{from_kebab}/{to_kebab}", "hourly", "0.85"))
                    _seen_pairs.add(pair_key)
                    break

    # Exchange directory and profile pages
    urls.append(("https://coinnect.bot/exchanges", "weekly", "0.8"))
    try:
        import json as _json
        _profiles_path = Path(__file__).parent.parent.parent / "data" / "exchange_profiles.json"
        with open(_profiles_path) as _f:
            _exchange_data = _json.load(_f)
        for _ex in _exchange_data.get("exchanges", []):
            urls.append((f"https://coinnect.bot/exchange/{_ex['slug']}", "weekly", "0.7"))
    except Exception:
        pass

    xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_parts.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for loc, freq, priority in urls:
        xml_parts.append(f"  <url>")
        xml_parts.append(f"    <loc>{loc}</loc>")
        xml_parts.append(f"    <lastmod>{now}</lastmod>")
        xml_parts.append(f"    <changefreq>{freq}</changefreq>")
        xml_parts.append(f"    <priority>{priority}</priority>")
        xml_parts.append(f"  </url>")
    xml_parts.append("</urlset>")

    return "\n".join(xml_parts)


# ── Exchange profile data loading ─────────────────────────────────────────────

def _load_exchange_profiles() -> list[dict]:
    """Load exchange profiles from data/exchange_profiles.json."""
    profiles_path = Path(__file__).parent.parent.parent / "data" / "exchange_profiles.json"
    try:
        with open(profiles_path) as f:
            data = json.load(f)
        return data.get("exchanges", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _find_exchange(slug: str) -> dict | None:
    """Find a single exchange by slug."""
    for ex in _load_exchange_profiles():
        if ex["slug"] == slug:
            return ex
    return None


# ── Exchange profile page ─────────────────────────────────────────────────────

def generate_exchange_page(slug: str) -> str | None:
    """Render a full SSR exchange profile page for /exchange/{slug}.

    Returns None if the exchange is not found.
    Uses the same design language as corridor/country pages (light mode, inline CSS,
    same nav/footer, Schema.org JSON-LD).
    """
    exchange = _find_exchange(slug)
    if not exchange:
        return None

    name = html.escape(exchange["name"])
    hq = exchange.get("headquarters", {})
    hq_city = html.escape(hq.get("city", ""))
    hq_country = html.escape(hq.get("country", ""))
    hq_str = f"{hq_city}, {hq_country}" if hq_city else ""
    founded = exchange.get("founded", "")
    website = html.escape(exchange.get("website", ""))
    api_docs = html.escape(exchange.get("api_docs", "") or "")
    fee_model = html.escape(exchange.get("fee_model", ""))
    speed = html.escape(exchange.get("speed", ""))
    supported_currencies = exchange.get("supported_currencies", "")
    supported_countries = exchange.get("supported_countries", "")
    status = exchange.get("integration_status", "planned")
    data_source = html.escape(exchange.get("coinnect_data_source", ""))

    # Transfer methods
    methods = exchange.get("transfer_methods", [])
    methods_str = ", ".join(html.escape(m.replace("_", " ").title()) for m in methods)

    # Status badge
    status_map = {
        "live": ("badge-green", "Live on Coinnect"),
        "estimated": ("badge-blue", "Estimated rates"),
        "planned": ("badge-gray", "Planned"),
    }
    badge_cls, badge_label = status_map.get(status, ("badge-gray", "Unknown"))

    # Regulation list
    regulated = exchange.get("regulated_in", [])
    regulated_html = ""
    if regulated:
        items = "".join(f"<li>{html.escape(r)}</li>" for r in regulated)
        regulated_html = f'<div class="card"><h3>Regulation &amp; Licenses</h3><ul style="padding-left:1.5rem;color:#475569;font-size:.88rem">{items}</ul></div>'

    # Key facts
    facts = exchange.get("interesting_facts", [])
    facts_html = ""
    if facts:
        items = "".join(f"<li style=\"margin:.4rem 0\">{html.escape(f)}</li>" for f in facts)
        facts_html = f'<div class="card"><h3>Key Facts</h3><ul style="padding-left:1.5rem;color:#475569;font-size:.88rem">{items}</ul></div>'

    # App store links
    app_stores = exchange.get("app_stores", {})
    app_links_html = ""
    if app_stores:
        links = []
        if app_stores.get("ios"):
            links.append(f'<a href="{html.escape(app_stores["ios"])}" target="_blank" rel="noopener" style="color:#06b6d4">iOS App Store</a>')
        if app_stores.get("android"):
            links.append(f'<a href="{html.escape(app_stores["android"])}" target="_blank" rel="noopener" style="color:#06b6d4">Google Play</a>')
        if links:
            app_links_html = f'<p style="font-size:.88rem;color:#475569">Download: {" &middot; ".join(links)}</p>'

    # API docs link
    api_docs_html = ""
    if api_docs:
        api_docs_html = f'<p style="font-size:.88rem"><span style="color:#64748b">API docs:</span> <a href="{api_docs}" target="_blank" rel="noopener" style="color:#06b6d4">{api_docs}</a></p>'

    path = f"/exchange/{slug}"
    canonical = f"{BASE_URL}{path}"
    meta_desc = (
        f"{exchange['name']} on Coinnect: factual profile, regulation, fees, "
        f"supported currencies, and integration status. Free, neutral, no affiliate fees."
    )

    # JSON-LD
    json_ld = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": exchange["name"],
        "url": exchange.get("website", ""),
        "foundingDate": str(founded),
        "address": {
            "@type": "PostalAddress",
            "addressLocality": hq.get("city", ""),
            "addressCountry": hq.get("country", ""),
        },
    }

    breadcrumb_ld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Coinnect", "item": f"{BASE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": "Exchanges", "item": f"{BASE_URL}/exchanges"},
            {"@type": "ListItem", "position": 3, "name": exchange["name"], "item": canonical},
        ],
    }

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name} — Coinnect Exchange Profile</title>
  <meta name="description" content="{html.escape(meta_desc)}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{canonical}">
{_hreflang_tags(path)}
  <meta property="og:type" content="website">
  <meta property="og:title" content="{name} — Coinnect Exchange Profile">
  <meta property="og:description" content="{html.escape(meta_desc)}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:site_name" content="Coinnect">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{name} — Coinnect Exchange Profile">
  <meta name="twitter:description" content="{html.escape(meta_desc)}">
  <script type="application/ld+json">{json.dumps(json_ld)}</script>
  <script type="application/ld+json">{json.dumps(breadcrumb_ld)}</script>
  <style>{_base_style()}</style>
</head>
<body>
{_nav_html()}
<main class="container">
  <nav class="breadcrumb">
    <a href="/">Home</a> &rsaquo; <a href="/exchanges">Exchanges</a> &rsaquo; {name}
  </nav>

  <h1>{name}</h1>
  <p class="subtitle">Founded {founded} &middot; {hq_str}</p>
  <p><span class="badge {badge_cls}">{html.escape(badge_label)}</span>
     <span style="font-size:.78rem;color:#94a3b8;margin-left:.5rem">{data_source}</span></p>

  <div class="card" style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem">
    <div>
      <h3 style="margin-top:0">Supported currencies</h3>
      <p>{supported_currencies}</p>
      <h3>Supported countries</h3>
      <p>{supported_countries}</p>
      <h3>Transfer methods</h3>
      <p>{methods_str or '&mdash;'}</p>
      <h3>Typical speed</h3>
      <p>{speed or '&mdash;'}</p>
    </div>
    <div>
      <h3 style="margin-top:0">Fee model</h3>
      <p>{fee_model or '&mdash;'}</p>
      <h3>Website</h3>
      <p><a href="{website}" target="_blank" rel="noopener" style="color:#06b6d4">{website or '&mdash;'}</a></p>
      {api_docs_html}
      {app_links_html}
    </div>
  </div>

  {regulated_html}
  {facts_html}

  <div class="card" style="text-align:center">
    <p style="font-size:1.05rem;font-weight:600;margin-bottom:.5rem">See {name} rates on Coinnect</p>
    <p><a href="/" class="cta" style="display:inline-block;padding:.6rem 1.5rem;font-size:1rem">Compare rates now</a></p>
  </div>

  <div style="font-size:.78rem;color:#94a3b8;margin-top:1.5rem;padding-top:1rem;border-top:1px solid #e2e8f0">
    <p>This profile contains publicly available, factual information only. Coinnect is not affiliated with,
    endorsed by, or sponsored by {name}. Data sourced from official websites, press releases, and regulatory filings.</p>
  </div>
</main>
{_footer_html()}
</body>
</html>"""


# ── Exchange directory page ───────────────────────────────────────────────────

def generate_exchanges_directory() -> str:
    """Render the /exchanges listing page with all exchange profiles."""
    exchanges = _load_exchange_profiles()
    exchanges_sorted = sorted(exchanges, key=lambda x: x["name"])

    cards_html = ""
    for ex in exchanges_sorted:
        slug = html.escape(ex["slug"])
        name = html.escape(ex["name"])
        status = ex.get("integration_status", "planned")
        hq = ex.get("headquarters", {})
        hq_str = html.escape(f"{hq.get('city', '')}, {hq.get('country', '')}") if hq.get("city") else ""
        founded = ex.get("founded", "")
        currencies = ex.get("supported_currencies", "?")
        countries = ex.get("supported_countries", "?")

        status_map = {
            "live": ("badge-green", "Live"),
            "estimated": ("badge-blue", "Estimated"),
            "planned": ("badge-gray", "Planned"),
        }
        badge_cls, badge_label = status_map.get(status, ("badge-gray", "Unknown"))

        cards_html += f"""<a href="/exchange/{slug}" class="corridor-link"
   style="display:block;padding:.8rem 1rem;margin:.4rem 0;border-radius:10px;text-decoration:none">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:.25rem">
    <span style="font-weight:600;color:#0f172a;font-size:.92rem">{name}</span>
    <span class="badge {badge_cls}" style="font-size:.68rem">{html.escape(badge_label)}</span>
  </div>
  <p style="font-size:.78rem;color:#64748b;margin:0">{hq_str} &middot; Founded {founded}</p>
  <p style="font-size:.75rem;color:#94a3b8;margin:.2rem 0 0">{currencies} currencies &middot; {countries} countries</p>
</a>"""

    path = "/exchanges"
    canonical = f"{BASE_URL}{path}"
    meta_desc = (
        "Factual profiles of money transfer providers and exchanges on Coinnect. "
        "Neutral, no affiliate fees, open data."
    )

    json_ld = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "Exchange Directory",
        "description": meta_desc,
        "url": canonical,
        "provider": {
            "@type": "Organization",
            "name": "Coinnect",
            "url": BASE_URL,
        },
    }

    breadcrumb_ld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Coinnect", "item": f"{BASE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": "Exchanges", "item": canonical},
        ],
    }

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Exchange Directory — Coinnect</title>
  <meta name="description" content="{html.escape(meta_desc)}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{canonical}">
{_hreflang_tags(path)}
  <meta property="og:type" content="website">
  <meta property="og:title" content="Exchange Directory — Coinnect">
  <meta property="og:description" content="{html.escape(meta_desc)}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:site_name" content="Coinnect">
  <meta name="twitter:card" content="summary_large_image">
  <script type="application/ld+json">{json.dumps(json_ld)}</script>
  <script type="application/ld+json">{json.dumps(breadcrumb_ld)}</script>
  <style>{_base_style()}</style>
</head>
<body>
{_nav_html()}
<main class="container">
  <nav class="breadcrumb">
    <a href="/">Home</a> &rsaquo; Exchanges
  </nav>

  <h1>Exchange Directory</h1>
  <p class="subtitle">Factual profiles of the providers Coinnect compares. No reviews, no scores, no affiliate fees &mdash; just public data.</p>

  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:.5rem">
    {cards_html}
  </div>

  <div style="font-size:.78rem;color:#94a3b8;margin-top:2rem">
    <p>All information is sourced from official websites, press releases, and regulatory filings.
    Coinnect is not affiliated with any listed provider.</p>
  </div>
</main>
{_footer_html()}
</body>
</html>"""


# ── Country-to-currency mapping (for /send/{from_country}/{to_country}) ───────

COUNTRY_TO_SLUG: dict[str, str] = {}
for _slug, _cdata in COUNTRY_DATA.items():
    # Build mapping from various name forms to country slug
    # e.g. "united-states" -> "usa", "mexico" -> "mexico"
    COUNTRY_TO_SLUG[_slug] = _slug
    # Also add kebab-case version of the full name
    _kebab = _cdata["name"].lower().replace(" ", "-")
    COUNTRY_TO_SLUG[_kebab] = _slug


def resolve_country_corridor(from_country: str, to_country: str) -> tuple[str, str] | None:
    """Resolve country slugs to a (from_currency, to_currency) pair.

    Accepts both country data keys ('usa', 'mexico') and kebab-case names
    ('united-states', 'south-africa').
    Returns None if either country is unknown.
    """
    from_slug = COUNTRY_TO_SLUG.get(from_country.lower())
    to_slug = COUNTRY_TO_SLUG.get(to_country.lower())
    if not from_slug or not to_slug:
        return None
    from_data = COUNTRY_DATA[from_slug]
    to_data = COUNTRY_DATA[to_slug]
    from_currency = from_data["currency"]
    to_currency = to_data["currency"]
    return (from_currency, to_currency)
