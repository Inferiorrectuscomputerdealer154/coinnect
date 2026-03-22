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
    ("MXN", "USD"), ("BRL", "USD"), ("PHP", "USD"), ("INR", "USD"),
    ("NGN", "USD"), ("KES", "USD"),
]

# Default amounts for corridor pages (realistic transfer sizes)
DEFAULT_AMOUNTS: dict[str, float] = {
    "USD": 500, "EUR": 500, "GBP": 400, "CAD": 600, "AED": 2000,
    "MXN": 10000, "BRL": 2500, "PHP": 25000, "INR": 40000,
    "NGN": 500000, "KES": 50000,
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
}

# ── Currency display names ────────────────────────────────────────────────────

CURRENCY_NAMES: dict[str, str] = {
    "USD": "US Dollar", "EUR": "Euro", "GBP": "British Pound", "CAD": "Canadian Dollar",
    "AED": "UAE Dirham", "MXN": "Mexican Peso", "BRL": "Brazilian Real",
    "INR": "Indian Rupee", "PHP": "Philippine Peso", "NGN": "Nigerian Naira",
    "COP": "Colombian Peso", "PKR": "Pakistani Rupee", "BDT": "Bangladeshi Taka",
    "KES": "Kenyan Shilling", "GHS": "Ghanaian Cedi", "TRY": "Turkish Lira",
    "ARS": "Argentine Peso", "JPY": "Japanese Yen", "ZAR": "South African Rand",
}

# ── Supported languages for hreflang ──────────────────────────────────────────

HREFLANG_LANGS = [
    "en", "es", "fr", "de", "pt", "hi", "ur", "bn", "tl", "tr", "ar", "sw", "ja", "zh", "ko",
]

# ── HTML cache ────────────────────────────────────────────────────────────────

_html_cache: dict[str, tuple[float, str]] = {}
CACHE_TTL = 180  # 3 minutes


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
    tags = []
    for lang in HREFLANG_LANGS:
        tags.append(f'  <link rel="alternate" hreflang="{lang}" href="{BASE_URL}{path}">')
    tags.append(f'  <link rel="alternate" hreflang="x-default" href="{BASE_URL}{path}">')
    return "\n".join(tags)


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
  <p>Non-profit. No affiliate fees. Open data (CC-BY 4.0).</p>
  <p><a href="/">Home</a> &middot; <a href="/whitepaper">Whitepaper</a> &middot;
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
<p style="margin-top:.8rem">Coinnect is non-profit, open-source, and takes no affiliate fees. <a href="/whitepaper">Read the whitepaper</a>.</p>
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
<p>Yes. Non-profit, no affiliate fees, open source. <a href="/">Use the interactive search</a> for any amount.</p>
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

    now_str = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

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
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="Send {html.escape(from_c)} to {html.escape(to_c)} — Coinnect">
  <meta name="twitter:description" content="{html.escape(og_desc)}">
  <script type="application/ld+json">{json.dumps(json_ld)}</script>
  <script type="application/ld+json">{json.dumps(faq_ld)}</script>
  <style>{_base_style()}</style>
</head>
<body>
{_nav_html()}
<main class="container">
  <nav class="breadcrumb">
    <a href="/">Home</a> &rsaquo; <a href="/send/{from_c.lower()}-to-{to_c.lower()}">Send {html.escape(from_c)} to {html.escape(to_c)}</a>
  </nav>
  <h1>Send {from_name} ({html.escape(from_c)}) to {to_name} ({html.escape(to_c)})</h1>
  <p class="subtitle">Compare the cheapest routes to convert {html.escape(from_c)} to {html.escape(to_c)} — updated every 3 minutes across 15+ providers.</p>

  {table_html}
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
        "dateModified": datetime.now(UTC).isoformat(),
    }

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
  <meta name="twitter:card" content="summary">
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
  <p class="subtitle">Live rates for all corridors involving {currency} ({country_name}) — updated every 3 minutes.</p>

  {sections_html}
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
