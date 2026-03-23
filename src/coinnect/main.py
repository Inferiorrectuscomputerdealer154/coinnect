"""
Coinnect API — entry point
"""

import asyncio
import html
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse

from coinnect.api.routes import router
from coinnect.api.admin_routes import admin_router, suggest_router
from coinnect.db.history import init_db, record_snapshot, prune_old, TRACKED_CORRIDORS
from coinnect.db.keys import init_keys_db
from coinnect.db.analytics import init_analytics_db
from coinnect.seo_pages import (
    render_corridor_page, render_country_page, generate_sitemap_xml,
    TOP_CORRIDORS, COUNTRY_DATA, _cache_get, _cache_set,
)

logger = logging.getLogger(__name__)
STATIC_DIR = Path(__file__).parent / "static"
DOCS_DIR = Path(__file__).parent.parent.parent / "docs"


# ── Background rate refresh ─────────────────────────────────────────────────

async def _refresh_once(force: bool = False) -> int:
    """Refresh all exchange edges, store history snapshots. Returns edge count."""
    from coinnect.exchanges.ccxt_adapter import get_all_edges
    from coinnect.exchanges.wise_adapter import get_wise_edges, get_traditional_edges
    from coinnect.exchanges.yellowcard_adapter import get_yellowcard_edges
    from coinnect.exchanges.remittance_adapter import get_remittance_edges
    from coinnect.exchanges.direct_api_adapter import (
        get_bitso_edges, get_buda_edges, get_coingecko_edges,
        get_strike_edges, get_frankfurter_edges, get_currencyapi_edges,
        get_flutterwave_edges,
        get_bluelytics_edges, get_dolarsi_edges, get_criptoya_edges,
        get_bcb_edges, get_trm_edges, get_lirarate_edges,
        get_yadio_edges, get_valr_edges, get_coindcx_edges,
        get_wazirx_edges, get_satoshitango_edges, get_floatrates_edges,
        get_binance_p2p_edges,
    )
    from coinnect.exchanges.calculator_adapter import get_calculator_edges
    from coinnect.routing.engine import build_quote

    (
        crypto_edges, wise_edges, trad_edges, yc_edges, remit_edges,
        bitso_edges, buda_edges, cg_edges,
        strike_edges, frank_edges, curapi_edges, fw_edges,
        bluelytics_edges, dolarsi_edges, criptoya_edges,
        bcb_edges, trm_edges, lirarate_edges,
        yadio_edges, valr_edges, coindcx_edges,
        wazirx_edges, satoshitango_edges, floatrates_edges,
        binance_p2p_edges,
        calc_edges,
    ) = await asyncio.gather(
        get_all_edges(force_refresh=force),
        get_wise_edges(),
        get_traditional_edges(),
        get_yellowcard_edges(),
        get_remittance_edges(),
        get_bitso_edges(),
        get_buda_edges(),
        get_coingecko_edges(),
        get_strike_edges(),
        get_frankfurter_edges(),
        get_currencyapi_edges(),
        get_flutterwave_edges(),
        get_bluelytics_edges(),
        get_dolarsi_edges(),
        get_criptoya_edges(),
        get_bcb_edges(),
        get_trm_edges(),
        get_lirarate_edges(),
        get_yadio_edges(),
        get_valr_edges(),
        get_coindcx_edges(),
        get_wazirx_edges(),
        get_satoshitango_edges(),
        get_floatrates_edges(),
        get_binance_p2p_edges(),
        get_calculator_edges(),
    )
    all_edges = (
        crypto_edges + wise_edges + trad_edges + yc_edges + remit_edges
        + bitso_edges + buda_edges + cg_edges
        + strike_edges + frank_edges + curapi_edges + fw_edges
        + bluelytics_edges + dolarsi_edges + criptoya_edges
        + bcb_edges + trm_edges + lirarate_edges
        + yadio_edges + valr_edges + coindcx_edges
        + wazirx_edges + satoshitango_edges + floatrates_edges
        + binance_p2p_edges
        + calc_edges
    )

    if not all_edges:
        logger.warning("Refresh returned 0 edges")
        return 0

    # Record snapshot for each tracked corridor
    for from_c, to_c, amount in TRACKED_CORRIDORS:
        try:
            result = build_quote(all_edges, from_c, to_c, amount)
            if result.routes:
                await record_snapshot(from_c, to_c, amount, result.routes)
        except Exception as e:
            logger.debug(f"Snapshot failed {from_c}→{to_c}: {e}")

    return len(all_edges)


async def _refresh_loop() -> None:
    """Background task: refresh rates every 3 minutes, prune DB weekly."""
    prune_counter = 0
    quest_counter = 0
    while True:
        try:
            count = await _refresh_once(force=True)
            logger.info(f"Rate refresh: {count} edges loaded")
        except Exception as e:
            logger.error(f"Rate refresh failed: {e}")

        prune_counter += 1
        if prune_counter >= 336:  # ~7 days at 3-min intervals
            try:
                deleted = prune_old(keep_days=30)
                logger.info(f"History pruned: {deleted} old rows removed")
                prune_counter = 0
            except Exception as e:
                logger.error(f"Prune failed: {e}")

        quest_counter += 1
        if quest_counter >= 20:  # ~1 hour at 3-min intervals
            try:
                from coinnect.db.analytics import generate_quests
                created = generate_quests()
                if created:
                    logger.info(f"Generated {created} new quests")
                quest_counter = 0
            except Exception as e:
                logger.error(f"Quest generation failed: {e}")

        await asyncio.sleep(180)  # 3 minutes


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    init_keys_db()
    init_analytics_db()
    # Do one immediate refresh (no force — use cache if warm)
    asyncio.create_task(_refresh_once(force=False))
    # Start background loop
    refresh_task = asyncio.create_task(_refresh_loop())
    logger.info("Coinnect started — background refresh active (3 min interval)")
    yield
    # Shutdown
    refresh_task.cancel()
    try:
        await refresh_task
    except asyncio.CancelledError:
        pass


# ── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Coinnect API",
    description=(
        "The open map for global money.\n\n"
        "Finds the cheapest path between any two currencies — "
        "across traditional remittance, crypto exchanges, and P2P platforms.\n\n"
        "**Non-profit. No affiliate fees. No custody. Free for personal use.**\n\n"
        "**For AI agents:** call `/v1/quote` as a tool with `from`, `to`, and `amount` parameters. "
        "Or use the MCP server (`python -m coinnect.mcp_server`) for Claude/MCP-compatible agents.\n\n"
        "Rate limits: 20 req/day / 50/hr anonymous (beta) · 1,000/day free key · "
        "5,000/day agent key · see coinnect.bot/#pricing"
    ),
    version="2026.03.23",
    contact={"name": "Coinnect", "url": "https://coinnect.bot"},
    license_info={"name": "MIT"},
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://coinnect.bot", "http://localhost:8100"],
    allow_methods=["GET", "POST", "HEAD"],
    allow_headers=["*"],
)


@app.middleware("http")
async def handle_head_requests(request: Request, call_next):
    """Convert HEAD requests to GET — UptimeRobot and similar tools use HEAD."""
    if request.method == "HEAD":
        request._method = "GET"
        request.scope["method"] = "GET"
    return await call_next(request)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://www.googletagmanager.com; "
        "connect-src 'self' https://www.google-analytics.com https://region1.google-analytics.com; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "frame-ancestors 'none'"
    )
    if "Via" in response.headers:
        del response.headers["Via"]
    return response


app.include_router(router)
app.include_router(admin_router, include_in_schema=False)
app.include_router(suggest_router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap():
    from fastapi.responses import Response
    cached = _cache_get("sitemap")
    if cached:
        return Response(content=cached, media_type="application/xml")
    xml = generate_sitemap_xml()
    _cache_set("sitemap", xml)
    return Response(content=xml, media_type="application/xml")


@app.get("/robots.txt", include_in_schema=False)
async def robots():
    return PlainTextResponse(
        "User-agent: *\n"
        "Allow: /\n"
        "Sitemap: https://coinnect.bot/sitemap.xml\n"
    )


@app.get("/llms.txt", include_in_schema=False)
async def llms_txt():
    return FileResponse(STATIC_DIR / "llms.txt", media_type="text/plain")


@app.get("/.well-known/security.txt", include_in_schema=False)
async def security_txt():
    content = (
        "Contact: mailto:miguel@coinnect.bot\n"
        "Scope: https://coinnect.bot\n"
        "Policy: https://coinnect.bot/#pricing\n"
        "Preferred-Languages: en, es\n"
        "Expires: 2027-01-01T00:00:00Z\n"
    )
    return PlainTextResponse(content)


async def _get_all_edges_cached() -> list:
    """Fetch all edges from all adapters (uses each adapter's internal cache)."""
    from coinnect.exchanges.ccxt_adapter import get_all_edges
    from coinnect.exchanges.wise_adapter import get_wise_edges, get_traditional_edges
    from coinnect.exchanges.yellowcard_adapter import get_yellowcard_edges
    from coinnect.exchanges.remittance_adapter import get_remittance_edges
    from coinnect.exchanges.direct_api_adapter import (
        get_bitso_edges, get_buda_edges, get_coingecko_edges,
        get_strike_edges, get_frankfurter_edges, get_currencyapi_edges,
        get_flutterwave_edges,
        get_bluelytics_edges, get_dolarsi_edges, get_criptoya_edges,
        get_bcb_edges, get_trm_edges, get_lirarate_edges,
        get_yadio_edges, get_valr_edges, get_coindcx_edges,
        get_wazirx_edges, get_satoshitango_edges, get_floatrates_edges,
        get_binance_p2p_edges,
    )
    from coinnect.exchanges.calculator_adapter import get_calculator_edges
    results = await asyncio.gather(
        get_all_edges(),
        get_wise_edges(),
        get_traditional_edges(),
        get_yellowcard_edges(),
        get_remittance_edges(),
        get_bitso_edges(),
        get_buda_edges(),
        get_coingecko_edges(),
        get_strike_edges(),
        get_frankfurter_edges(),
        get_currencyapi_edges(),
        get_flutterwave_edges(),
        get_bluelytics_edges(),
        get_dolarsi_edges(),
        get_criptoya_edges(),
        get_bcb_edges(),
        get_trm_edges(),
        get_lirarate_edges(),
        get_yadio_edges(),
        get_valr_edges(),
        get_coindcx_edges(),
        get_wazirx_edges(),
        get_satoshitango_edges(),
        get_floatrates_edges(),
        get_binance_p2p_edges(),
        get_calculator_edges(),
    )
    all_edges = []
    for batch in results:
        all_edges.extend(batch)
    return all_edges


@app.get("/explore", include_in_schema=False)
async def explore_index():
    """Index page listing all SEO corridor and country pages."""
    from coinnect.seo_pages import TOP_CORRIDORS, COUNTRY_DATA
    corridors_html = "\n".join(
        f'<li><a href="/send/{fc.lower()}-to-{tc.lower()}">{fc} → {tc}</a></li>'
        for fc, tc in TOP_CORRIDORS
    )
    countries_html = "\n".join(
        f'<li><a href="/rates/{slug}">{data["name"]} ({", ".join(data.get("currencies",[]))})</a></li>'
        for slug, data in sorted(COUNTRY_DATA.items(), key=lambda x: x[1]["name"])
    )
    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Explore — All Corridors &amp; Countries | Coinnect</title>
<link rel="icon" type="image/svg+xml" href="/static/logo.svg">
<style>
body{{font-family:system-ui,sans-serif;max-width:800px;margin:2rem auto;padding:0 1rem;color:#111827;background:#f9fafb;line-height:1.6}}
a{{color:#0891b2;text-decoration:none}} a:hover{{text-decoration:underline}}
h1{{font-size:1.5rem;margin-bottom:.5rem}} h2{{font-size:1.1rem;margin-top:2rem;color:#6b7280}}
ul{{columns:2;column-gap:2rem;list-style:none;padding:0}} li{{padding:.25rem 0;font-size:.9rem}}
.back{{display:inline-block;margin-bottom:1rem;font-size:.85rem;color:#6b7280}}
</style></head><body>
<a href="/" class="back">← Back to Coinnect</a>
<h1>Explore All Routes</h1>
<p style="color:#6b7280;font-size:.9rem">30 corridors and 20 countries with live rate comparisons.</p>
<h2>Corridors</h2>
<ul>{corridors_html}</ul>
<h2>Countries</h2>
<ul>{countries_html}</ul>
<p style="margin-top:2rem;font-size:.75rem;color:#9ca3af">Data updates every 3 minutes · <a href="/v1/snapshot/meta">Open data API</a> · <a href="https://huggingface.co/datasets/coinnect-dev/coinnect-rates">Hugging Face</a></p>
</body></html>""")


@app.get("/get-listed", include_in_schema=False)
async def get_listed_page():
    """Page for providers who want to be listed on Coinnect."""
    return HTMLResponse("""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Get Listed on Coinnect</title>
<link rel="icon" type="image/svg+xml" href="/static/logo.svg">
<style>
body{font-family:system-ui,sans-serif;max-width:700px;margin:2rem auto;padding:0 1rem;color:#111827;background:#f9fafb;line-height:1.7}
a{color:#0891b2;text-decoration:none} a:hover{text-decoration:underline}
h1{font-size:1.5rem;margin-bottom:.25rem} h2{font-size:1.1rem;margin-top:2rem;color:#374151}
.back{display:inline-block;margin-bottom:1rem;font-size:.85rem;color:#6b7280}
.req{background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:1.25rem;margin:.75rem 0}
.req h3{font-size:.95rem;margin:0 0 .5rem;color:#111827}
.req p{font-size:.85rem;color:#6b7280;margin:0}
.cta{display:inline-block;margin-top:1.5rem;background:#0891b2;color:#fff;padding:.75rem 1.5rem;border-radius:10px;font-weight:600;font-size:.9rem}
.cta:hover{background:#0e7490;text-decoration:none}
code{background:#f1f5f9;padding:.15rem .4rem;border-radius:4px;font-size:.85rem}
</style></head><body>
<a href="/" class="back">← Back to Coinnect</a>
<h1>Get Listed on Coinnect</h1>
<p style="color:#6b7280;font-size:.9rem">Coinnect compares 30+ providers to find the cheapest money transfer routes. Listing is free, neutral, and based on data — not partnerships.</p>

<h2>Requirements</h2>

<div class="req">
  <h3>1. Public pricing</h3>
  <p>Your fees and exchange rates must be publicly accessible without login. A pricing page URL or published API is required.</p>
</div>

<div class="req">
  <h3>2. Corridor data</h3>
  <p>Provide your supported currency pairs with: <code>from</code>, <code>to</code>, <code>min/max amount</code>, <code>payment methods</code>, and <code>estimated time</code>.</p>
</div>

<div class="req">
  <h3>3. Rate source (one of)</h3>
  <p><strong>Best:</strong> A public REST API returning live quotes (you get a "LIVE" badge).<br>
  <strong>Good:</strong> A public calculator page we can reference.<br>
  <strong>Minimum:</strong> Published fee tables (listed as "ESTIMATED").</p>
</div>

<div class="req">
  <h3>4. Regulated in at least one jurisdiction</h3>
  <p>No credible fraud or insolvency history. Providers must comply with applicable regulations in their operating jurisdictions.</p>
</div>

<h2>What you get</h2>
<ul style="font-size:.9rem;color:#374151">
  <li>Neutral ranking by cost — we never favor paying partners</li>
  <li>Visibility across 50+ SEO-optimized corridor pages</li>
  <li>Listed in our open dataset on <a href="https://huggingface.co/datasets/coinnect-dev/coinnect-rates">Hugging Face</a></li>
  <li>Discoverable by AI agents via MCP server and REST API</li>
  <li>Badge: LIVE (with API) or ESTIMATED (fee tables)</li>
</ul>

<h2>How rankings work</h2>
<p style="font-size:.9rem;color:#6b7280">Routes are ranked by total cost to the recipient (fees + exchange rate spread). We do not accept affiliate commissions, paid placements, or sponsored rankings. Ever. <a href="https://github.com/coinnect-dev/coinnect/blob/main/docs/LISTING_STANDARD.md">Full listing standard →</a></p>

<a href="mailto:miguel@coinnect.bot?subject=Get%20listed%20on%20Coinnect&body=Provider%20name:%0ACorridor(s):%0APricing%20page%20URL:%0AAPI%20docs%20(if%20available):" class="cta">Apply to get listed</a>
<p style="font-size:.8rem;color:#9ca3af;margin-top:.5rem">Or email miguel@coinnect.bot with your provider name, corridors, and pricing page URL.</p>

</body></html>""")


@app.get("/suggest", include_in_schema=False)
async def suggest_page():
    """Standalone page for suggesting and voting on corridors/providers."""
    return HTMLResponse("""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Suggest a Corridor or Provider | Coinnect</title>
  <meta name="description" content="Help Coinnect add the money routes you need. Suggest corridors and providers, vote on community requests.">
  <link rel="icon" type="image/svg+xml" href="/static/logo.svg">
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:system-ui,-apple-system,sans-serif;background:#f8fafc;color:#1a1a1a;line-height:1.6}
    @media(prefers-color-scheme:dark){
      body{background:#0f172a;color:#e2e8f0}
      .card{background:#1e293b;border-color:#334155}
      .topnav{background:rgba(15,23,42,.95);border-color:#334155}
      select,input{background:#0f172a;color:#e2e8f0;border-color:#475569}
      .sg-item{background:#1e293b;border-color:#334155}
      .vote-btn{border-color:#475569}
      .vote-btn:hover{border-color:#06b6d4;background:rgba(6,182,212,.1)}
      .submit-btn{background:#0891b2}
      .submit-btn:hover{background:#0e7490}
      .note-text{color:#94a3b8}
      .admin-note{background:rgba(245,158,11,.08);border-color:#92400e;color:#fbbf24}
      .api-note{background:#1e293b;border-color:#334155;color:#94a3b8}
      .status-msg{color:#67e8f9}
      h1,h2,.sg-name{color:#f1f5f9}
      .subtitle,.meta-text{color:#94a3b8}
    }

    .topnav{position:sticky;top:0;background:rgba(255,255,255,.95);backdrop-filter:blur(8px);
             border-bottom:1px solid #e2e8f0;display:flex;align-items:center;
             justify-content:space-between;padding:.75rem 1.5rem;z-index:100}
    .logo{display:flex;align-items:center;gap:.5rem;text-decoration:none;color:#1a1a1a;font-weight:700}
    @media(prefers-color-scheme:dark){.logo{color:#f1f5f9}}
    .back{text-decoration:none;color:#6b7280;font-size:.85rem;padding:.35rem .8rem;
           border:1px solid #e2e8f0;border-radius:8px;background:#fff}
    @media(prefers-color-scheme:dark){.back{background:#1e293b;border-color:#475569;color:#94a3b8}}
    .back:hover{color:#06b6d4;border-color:#06b6d4}

    .container{max-width:640px;margin:0 auto;padding:2rem 1rem 4rem}

    h1{font-size:1.5rem;font-weight:700;margin-bottom:.25rem}
    .subtitle{color:#6b7280;font-size:.9rem;margin-bottom:2rem}

    /* Form card */
    .card{background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:1.5rem;margin-bottom:2rem;
          box-shadow:0 1px 3px rgba(0,0,0,.04)}
    .form-row{display:flex;gap:.75rem;align-items:flex-end;flex-wrap:wrap;margin-bottom:1rem}
    .form-group{flex:1;min-width:120px}
    .form-group label{display:block;font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;color:#6b7280;margin-bottom:.3rem;font-weight:600}
    select,input[type="text"]{width:100%;padding:.55rem .75rem;border:1px solid #d1d5db;border-radius:10px;
           font-size:.88rem;background:#fff;color:#1a1a1a;transition:border-color .15s}
    select:focus,input:focus{outline:none;border-color:#06b6d4;box-shadow:0 0 0 2px rgba(6,182,212,.15)}
    .arrow{color:#9ca3af;font-size:1.1rem;padding-bottom:.35rem;flex-shrink:0}
    .submit-btn{padding:.55rem 1.25rem;background:#06b6d4;color:#fff;border:none;border-radius:10px;
                font-size:.88rem;font-weight:600;cursor:pointer;transition:background .15s;white-space:nowrap}
    .submit-btn:hover{background:#0891b2}
    .submit-btn:disabled{opacity:.5;cursor:not-allowed}

    .match-hint{font-size:.8rem;color:#f59e0b;padding:.5rem .75rem;background:#fefce8;border:1px solid #fde68a;
                border-radius:8px;margin-bottom:1rem;display:none}
    @media(prefers-color-scheme:dark){.match-hint{background:rgba(245,158,11,.08);border-color:#92400e;color:#fbbf24}}
    .status-msg{font-size:.85rem;color:#06b6d4;margin-top:.5rem;min-height:1.3rem}

    /* Suggestions list */
    h2{font-size:1.1rem;font-weight:700;margin-bottom:.75rem;color:#374151}
    .sg-item{display:flex;gap:.75rem;align-items:flex-start;background:#fff;border:1px solid #e2e8f0;
             border-radius:12px;padding:.85rem 1rem;margin-bottom:.5rem;transition:border-color .15s}
    .sg-item:hover{border-color:#cbd5e1}
    .vote-btn{display:flex;flex-direction:column;align-items:center;gap:.15rem;flex-shrink:0;width:2.5rem;
              padding:.4rem 0;border-radius:8px;border:1px solid #e2e8f0;background:none;cursor:pointer;
              transition:all .15s}
    .vote-btn:hover{border-color:#06b6d4;background:rgba(6,182,212,.05)}
    .vote-btn .arrow-up{color:#9ca3af;font-size:.7rem;line-height:1;transition:color .15s}
    .vote-btn:hover .arrow-up{color:#06b6d4}
    .vote-btn .count{font-size:.9rem;font-weight:700;color:#374151;line-height:1}
    @media(prefers-color-scheme:dark){.vote-btn .count{color:#e2e8f0}}
    .vote-btn.voted{border-color:#06b6d4;background:rgba(6,182,212,.08)}
    .vote-btn.voted .arrow-up{color:#06b6d4}
    .sg-name{font-weight:600;font-size:.9rem;color:#1a1a1a}
    .note-text{font-size:.78rem;color:#6b7280;margin-top:.15rem}
    .admin-note{margin-top:.4rem;font-size:.78rem;color:#b45309;background:#fffbeb;border:1px solid #fde68a;
                border-radius:6px;padding:.3rem .6rem;display:flex;align-items:flex-start;gap:.4rem}

    /* Status badges */
    .badge{display:inline-block;font-size:.65rem;font-weight:700;padding:.15rem .5rem;border-radius:999px;
           text-transform:uppercase;letter-spacing:.03em;margin-left:.4rem;vertical-align:middle}
    .badge-open{background:#f3f4f6;color:#6b7280}
    .badge-considering{background:#dbeafe;color:#1d4ed8}
    .badge-integrated{background:#d1fae5;color:#059669}
    .badge-needs-api{background:#fef3c7;color:#b45309}
    .badge-accepted{background:#d1fae5;color:#059669}
    .badge-rejected{background:#fee2e2;color:#dc2626}
    @media(prefers-color-scheme:dark){
      .badge-open{background:#374151;color:#9ca3af}
      .badge-considering{background:rgba(59,130,246,.15);color:#60a5fa}
      .badge-integrated{background:rgba(16,185,129,.15);color:#34d399}
      .badge-needs-api{background:rgba(245,158,11,.15);color:#fbbf24}
      .badge-accepted{background:rgba(16,185,129,.15);color:#34d399}
      .badge-rejected{background:rgba(239,68,68,.15);color:#f87171}
    }

    .api-note{margin-top:2rem;font-size:.78rem;color:#9ca3af;background:#f8fafc;border:1px solid #e2e8f0;
              border-radius:10px;padding:.85rem 1rem}
    .api-note code{background:#e2e8f0;padding:.15rem .4rem;border-radius:4px;font-size:.8rem}
    @media(prefers-color-scheme:dark){.api-note code{background:#334155}}
    .meta-text{font-size:.75rem;color:#9ca3af;margin-top:1.5rem;text-align:center}
    .meta-text a{color:#06b6d4;text-decoration:none}

    .empty-state{text-align:center;padding:2rem;color:#9ca3af;font-size:.85rem}

    @media(max-width:480px){
      .form-row{flex-direction:column;align-items:stretch}
      .arrow{text-align:center;padding:0;margin:-.25rem 0}
      .submit-btn{width:100%}
    }
  </style>
</head>
<body>
  <nav class="topnav">
    <a href="/" class="logo">
      <svg width="24" height="24" viewBox="0 0 44 44" xmlns="http://www.w3.org/2000/svg"><circle cx="16" cy="22" r="11" fill="none" stroke="#06b6d4" stroke-width="2.5"/><circle cx="28" cy="22" r="11" fill="none" stroke="#06b6d4" stroke-width="2.5"/><path d="M8 22 L36 22" stroke="#06b6d4" stroke-width="2" stroke-linecap="round"/><path d="M32 18 L36 22 L32 26" fill="none" stroke="#06b6d4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="8" cy="22" r="2" fill="#06b6d4"/></svg>
      Coinnect
    </a>
    <a href="/" class="back">&larr; Back to Coinnect</a>
  </nav>

  <div class="container">
    <h1>Suggest a Corridor or Provider</h1>
    <p class="subtitle">Help us add the routes you need.</p>

    <!-- Submit form -->
    <div class="card">
      <div class="form-row">
        <div class="form-group">
          <label>From</label>
          <select id="sgFrom">
            <option value="">(any)</option>
            <optgroup label="Crypto">
              <option value="BTC">BTC &mdash; Bitcoin</option>
              <option value="ETH">ETH &mdash; Ethereum</option>
              <option value="USDC">USDC &mdash; USD Coin</option>
              <option value="USDT">USDT &mdash; Tether</option>
            </optgroup>
            <optgroup label="Major Fiat">
              <option value="USD">USD &mdash; US Dollar</option>
              <option value="EUR">EUR &mdash; Euro</option>
              <option value="GBP">GBP &mdash; Pound</option>
              <option value="CAD">CAD &mdash; Canadian Dollar</option>
              <option value="AUD">AUD &mdash; Australian Dollar</option>
              <option value="JPY">JPY &mdash; Japanese Yen</option>
              <option value="CHF">CHF &mdash; Swiss Franc</option>
            </optgroup>
            <optgroup label="Latin America">
              <option value="MXN">MXN &mdash; Mexican Peso</option>
              <option value="BRL">BRL &mdash; Brazilian Real</option>
              <option value="COP">COP &mdash; Colombian Peso</option>
              <option value="ARS">ARS &mdash; Argentine Peso</option>
              <option value="PEN">PEN &mdash; Peruvian Sol</option>
              <option value="CLP">CLP &mdash; Chilean Peso</option>
              <option value="VES">VES &mdash; Venezuelan Bolivar</option>
            </optgroup>
            <optgroup label="Asia">
              <option value="INR">INR &mdash; Indian Rupee</option>
              <option value="PHP">PHP &mdash; Philippine Peso</option>
              <option value="THB">THB &mdash; Thai Baht</option>
              <option value="IDR">IDR &mdash; Indonesian Rupiah</option>
              <option value="VND">VND &mdash; Vietnamese Dong</option>
              <option value="PKR">PKR &mdash; Pakistani Rupee</option>
              <option value="BDT">BDT &mdash; Bangladeshi Taka</option>
            </optgroup>
            <optgroup label="Africa">
              <option value="NGN">NGN &mdash; Nigerian Naira</option>
              <option value="KES">KES &mdash; Kenyan Shilling</option>
              <option value="GHS">GHS &mdash; Ghanaian Cedi</option>
              <option value="ZAR">ZAR &mdash; South African Rand</option>
            </optgroup>
            <optgroup label="Middle East">
              <option value="AED">AED &mdash; UAE Dirham</option>
              <option value="SAR">SAR &mdash; Saudi Riyal</option>
              <option value="TRY">TRY &mdash; Turkish Lira</option>
            </optgroup>
            <optgroup label="Europe">
              <option value="UAH">UAH &mdash; Ukrainian Hryvnia</option>
              <option value="PLN">PLN &mdash; Polish Zloty</option>
              <option value="RON">RON &mdash; Romanian Leu</option>
              <option value="CZK">CZK &mdash; Czech Koruna</option>
              <option value="HUF">HUF &mdash; Hungarian Forint</option>
            </optgroup>
          </select>
        </div>
        <span class="arrow">&rarr;</span>
        <div class="form-group">
          <label>To</label>
          <select id="sgTo">
            <option value="">(any)</option>
            <optgroup label="Latin America">
              <option value="MXN">MXN &mdash; Mexico</option>
              <option value="BRL">BRL &mdash; Brazil</option>
              <option value="COP">COP &mdash; Colombia</option>
              <option value="ARS">ARS &mdash; Argentina</option>
              <option value="PEN">PEN &mdash; Peru</option>
              <option value="CLP">CLP &mdash; Chile</option>
              <option value="VES">VES &mdash; Venezuela</option>
            </optgroup>
            <optgroup label="Asia">
              <option value="PHP">PHP &mdash; Philippines</option>
              <option value="INR">INR &mdash; India</option>
              <option value="IDR">IDR &mdash; Indonesia</option>
              <option value="VND">VND &mdash; Vietnam</option>
              <option value="THB">THB &mdash; Thailand</option>
              <option value="BDT">BDT &mdash; Bangladesh</option>
              <option value="PKR">PKR &mdash; Pakistan</option>
            </optgroup>
            <optgroup label="Africa">
              <option value="NGN">NGN &mdash; Nigeria</option>
              <option value="KES">KES &mdash; Kenya</option>
              <option value="GHS">GHS &mdash; Ghana</option>
              <option value="ZAR">ZAR &mdash; South Africa</option>
              <option value="TZS">TZS &mdash; Tanzania</option>
              <option value="UGX">UGX &mdash; Uganda</option>
            </optgroup>
            <optgroup label="Middle East">
              <option value="AED">AED &mdash; UAE</option>
              <option value="SAR">SAR &mdash; Saudi Arabia</option>
              <option value="TRY">TRY &mdash; Turkey</option>
            </optgroup>
            <optgroup label="Europe">
              <option value="UAH">UAH &mdash; Ukraine</option>
              <option value="PLN">PLN &mdash; Poland</option>
              <option value="RON">RON &mdash; Romania</option>
              <option value="CZK">CZK &mdash; Czech Republic</option>
              <option value="HUF">HUF &mdash; Hungary</option>
            </optgroup>
            <optgroup label="Major Fiat">
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
              <option value="GBP">GBP</option>
              <option value="CAD">CAD</option>
              <option value="AUD">AUD</option>
              <option value="JPY">JPY</option>
            </optgroup>
            <optgroup label="Crypto">
              <option value="USDC">USDC</option>
              <option value="USDT">USDT</option>
              <option value="BTC">BTC</option>
              <option value="ETH">ETH</option>
            </optgroup>
          </select>
        </div>
        <div class="form-group" style="min-width:160px">
          <label>Provider name (optional)</label>
          <input type="text" id="sgProvider" maxlength="100" placeholder="e.g. M-Pesa, GCash, Nequi...">
        </div>
        <button class="submit-btn" id="sgSubmitBtn" onclick="submitSuggestion()">Submit</button>
      </div>
      <div id="matchHint" class="match-hint"></div>
      <div id="sgMsg" class="status-msg"></div>
    </div>

    <!-- Existing suggestions -->
    <h2>Existing suggestions</h2>
    <div id="suggestionsList">
      <div class="empty-state">Loading suggestions...</div>
    </div>

    <!-- API note for bots -->
    <div class="api-note">
      <strong>Bots:</strong> use <code>POST /v1/suggestions</code> with <code>{"name": "...", "fingerprint": "..."}</code>.
      Upvote with <code>POST /v1/suggestions/{id}/upvote</code> with <code>{"fingerprint": "..."}</code>.
    </div>

    <p class="meta-text">
      Coinnect is non-profit and open source &middot; <a href="/">Live rates</a> &middot; <a href="/whitepaper">Whitepaper</a>
    </p>
  </div>

  <script>
    // ---- Fingerprint ----
    function getFingerprint(){
      let fp=localStorage.getItem('_fp');
      if(fp)return fp;
      const arr=new Uint8Array(16);
      crypto.getRandomValues(arr);
      fp=Array.from(arr).map(b=>b.toString(16).padStart(2,'0')).join('');
      localStorage.setItem('_fp',fp);
      return fp;
    }

    // ---- Escape HTML ----
    function esc(s){if(s==null)return'';const d=document.createElement('div');d.textContent=String(s);return d.innerHTML;}

    // ---- Status badges ----
    const BADGE_MAP={
      'open':['Open','badge-open'],
      'considering':['Considering','badge-considering'],
      'integrated':['Integrated','badge-integrated'],
      'needs-api':['Needs API','badge-needs-api'],
      'accepted':['Accepted','badge-accepted'],
      'rejected':['Rejected','badge-rejected'],
    };
    function badge(status){
      const [label,cls]=BADGE_MAP[status]||BADGE_MAP['open'];
      return `<span class="badge ${cls}">${label}</span>`;
    }

    // ---- State ----
    let allSuggestions=[];

    // ---- Load suggestions ----
    async function loadSuggestions(){
      try{
        const r=await fetch('/v1/suggestions?status=all');
        const d=await r.json();
        allSuggestions=d.suggestions||[];
        renderSuggestions(allSuggestions);
      }catch(e){
        document.getElementById('suggestionsList').innerHTML='<div class="empty-state">Could not load suggestions.</div>';
      }
    }

    function renderSuggestions(list){
      const el=document.getElementById('suggestionsList');
      if(!list.length){el.innerHTML='<div class="empty-state">No suggestions yet &mdash; be the first!</div>';return;}
      el.innerHTML=list.map(s=>`
        <div class="sg-item">
          <button onclick="voteSuggestion(${s.id},this)" class="vote-btn" title="Upvote this suggestion">
            <span class="arrow-up">&#9650;</span>
            <span class="count">${s.votes}</span>
          </button>
          <div style="flex:1;min-width:0">
            <div>
              <span class="sg-name">${esc(s.name)}</span>
              ${badge(s.status)}
            </div>
            ${s.note?`<div class="note-text">${esc(s.note)}</div>`:''}
            ${s.admin_note?`<div class="admin-note"><span style="flex-shrink:0">&#8505;&#65039;</span><span>${esc(s.admin_note)}</span></div>`:''}
          </div>
        </div>
      `).join('');
    }

    // ---- Auto-check for duplicates ----
    function buildName(){
      const from=document.getElementById('sgFrom').value;
      const to=document.getElementById('sgTo').value;
      const prov=document.getElementById('sgProvider').value.trim();
      let parts=[];
      if(from&&to) parts.push(from+' to '+to);
      else if(from) parts.push(from);
      else if(to) parts.push(to);
      if(prov) parts.push(prov);
      return parts.join(' — ');
    }

    function checkDuplicates(){
      const hint=document.getElementById('matchHint');
      const from=document.getElementById('sgFrom').value.toUpperCase();
      const to=document.getElementById('sgTo').value.toUpperCase();
      const prov=document.getElementById('sgProvider').value.trim().toLowerCase();

      if(!from&&!to&&!prov){hint.style.display='none';return;}

      const matches=allSuggestions.filter(s=>{
        const n=s.name.toLowerCase();
        if(prov&&n.includes(prov))return true;
        if(from&&to&&n.includes(from.toLowerCase())&&n.includes(to.toLowerCase()))return true;
        return false;
      });

      if(matches.length){
        hint.style.display='block';
        hint.innerHTML='Already suggested: '+matches.map(m=>
          `<strong>${esc(m.name)}</strong> (${m.votes} vote${m.votes!==1?'s':''}) &mdash; vote instead?`
        ).join(', ');
      }else{
        hint.style.display='none';
      }
    }

    document.getElementById('sgFrom').addEventListener('change',checkDuplicates);
    document.getElementById('sgTo').addEventListener('change',checkDuplicates);
    document.getElementById('sgProvider').addEventListener('input',checkDuplicates);

    // ---- Submit ----
    async function submitSuggestion(){
      const name=buildName();
      const msg=document.getElementById('sgMsg');
      if(!name){msg.textContent='Please select currencies or enter a provider name.';return;}

      const btn=document.getElementById('sgSubmitBtn');
      btn.disabled=true;
      btn.textContent='Submitting...';
      const fp=getFingerprint();
      try{
        const r=await fetch('/v1/suggestions',{
          method:'POST',
          headers:{'Content-Type':'application/json'},
          body:JSON.stringify({name:name,fingerprint:fp})
        });
        if(r.ok){
          document.getElementById('sgFrom').value='';
          document.getElementById('sgTo').value='';
          document.getElementById('sgProvider').value='';
          document.getElementById('matchHint').style.display='none';
          msg.textContent='Submitted! Thanks for the suggestion.';
          setTimeout(()=>{msg.textContent='';},4000);
          loadSuggestions();
        }else{
          const d=await r.json();
          msg.textContent=d.detail||'Error submitting.';
        }
      }catch(e){
        msg.textContent='Network error. Try again.';
      }
      btn.disabled=false;
      btn.textContent='Submit';
    }

    // ---- Vote ----
    async function voteSuggestion(id,btn){
      const fp=getFingerprint();
      try{
        const r=await fetch('/v1/suggestions/'+id+'/upvote',{
          method:'POST',
          headers:{'Content-Type':'application/json'},
          body:JSON.stringify({fingerprint:fp})
        });
        const d=await r.json();
        if(d.votes!==undefined){
          btn.querySelector('.count').textContent=d.votes;
          btn.classList.add('voted');
          btn.disabled=true;
        }else if(d.detail){
          btn.classList.add('voted');
          btn.disabled=true;
        }
      }catch(e){}
    }

    // ---- Init ----
    loadSuggestions();
  </script>
</body>
</html>""")


@app.get("/send/{corridor}", include_in_schema=False)
async def corridor_page(corridor: str):
    """SEO corridor page: /send/usd-to-mxn"""
    corridor = corridor.lower().strip()
    parts = corridor.split("-to-")
    if len(parts) != 2:
        return HTMLResponse("<html><body><h2>Invalid corridor</h2><p><a href='/'>Back</a></p></body></html>", status_code=404)

    from_c, to_c = parts[0].upper(), parts[1].upper()
    cache_key = f"corridor:{from_c}:{to_c}"
    cached = _cache_get(cache_key)
    if cached:
        return HTMLResponse(cached)

    edges = await _get_all_edges_cached()
    if not edges:
        return HTMLResponse("<html><body><h2>Exchange data temporarily unavailable</h2><p><a href='/'>Back</a></p></body></html>", status_code=503)

    page_html = render_corridor_page(from_c, to_c, edges)
    _cache_set(cache_key, page_html)
    return HTMLResponse(page_html)


@app.get("/rates/{slug}", include_in_schema=False)
async def rates_page(slug: str):
    """Country page (/rates/mexico) or snapshot page (/rates/123)."""
    # If slug is numeric, serve the snapshot page
    if slug.isdigit():
        return await snapshot_page_inner(int(slug))
    # Otherwise treat as country slug
    cache_key = f"country:{slug}"
    cached = _cache_get(cache_key)
    if cached:
        return HTMLResponse(cached)

    if slug not in COUNTRY_DATA:
        return HTMLResponse(
            "<html><body><h2>Country not found</h2>"
            "<p><a href='/'>Back to Coinnect</a></p></body></html>",
            status_code=404,
        )

    edges = await _get_all_edges_cached()
    if not edges:
        return HTMLResponse("<html><body><h2>Exchange data temporarily unavailable</h2><p><a href='/'>Back</a></p></body></html>", status_code=503)

    page_html = render_country_page(slug, edges)
    if not page_html:
        return HTMLResponse("<html><body><h2>Country not found</h2><p><a href='/'>Back</a></p></body></html>", status_code=404)

    _cache_set(cache_key, page_html)
    return HTMLResponse(page_html)


async def snapshot_page_inner(snapshot_id: int):
    """Human-readable permalink for a rate snapshot."""
    from coinnect.db.history import get_snapshot_by_id
    snap = get_snapshot_by_id(snapshot_id)
    if not snap:
        return HTMLResponse("<html><body><h2>Snapshot not found</h2><p><a href='/'>← Back</a></p></body></html>", status_code=404)

    ts = html.escape(str(snap.get("captured_at", "")))
    from_c = html.escape(str(snap.get("from_currency", "")))
    to_c = html.escape(str(snap.get("to_currency", "")))
    amount = snap.get("amount", 0)
    routes = snap.get("routes", [])

    def color_for_rank(i: int) -> str:
        if i == 0: return "#059669"   # emerald
        if i == 1: return "#2563eb"   # blue
        return "#6b7280"

    rows_html = ""
    for i, r in enumerate(routes):
        via = html.escape(str(r.get("via", "—")))
        cost = r.get("total_cost_pct", 0)
        recv = r.get("they_receive", 0)
        label = html.escape(str(r.get("label", f"Option {i+1}")))
        mins = r.get("total_time_minutes", 0)
        h = mins // 60
        m = mins % 60
        time_str = f"{h}h {m}m" if h else f"{m}m"
        badge_color = color_for_rank(i)
        rows_html += f"""
        <tr>
          <td><span style="display:inline-block;padding:.2rem .6rem;border-radius:12px;background:{badge_color};color:#fff;font-size:.78rem;font-weight:600">{label}</span></td>
          <td style="font-family:monospace">{via}</td>
          <td style="text-align:right;font-weight:600;color:{badge_color}">{cost:.2f}%</td>
          <td style="text-align:right">{recv:,.2f} {to_c}</td>
          <td style="text-align:right;color:#6b7280">{time_str}</td>
        </tr>"""

    api_url = f"https://coinnect.bot/v1/snapshot/{snapshot_id}"
    ts_display = ts[:19].replace("T", " ") + " UTC" if ts else "unknown"

    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Rate snapshot #{snapshot_id} — {from_c}→{to_c} {amount:g} | Coinnect</title>
  <meta name="description" content="Archived rate comparison: {amount:g} {from_c} to {to_c} captured {ts_display}. Open data by Coinnect.">
  <meta property="og:title" content="Coinnect: {amount:g} {from_c}→{to_c} snapshot #{snapshot_id}">
  <meta property="og:description" content="Best route: {routes[0].get('total_cost_pct',0):.2f}% via {routes[0].get('via','?')} — captured {ts_display}">
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:system-ui,sans-serif;background:#f8fafc;color:#1a1a1a;line-height:1.6}}
    .topnav{{position:sticky;top:0;background:rgba(255,255,255,.95);backdrop-filter:blur(8px);
             border-bottom:1px solid #e2e8f0;display:flex;align-items:center;
             justify-content:space-between;padding:.75rem 1.5rem}}
    .logo{{display:flex;align-items:center;gap:.5rem;text-decoration:none;color:#1a1a1a;font-weight:700}}
    .back{{text-decoration:none;color:#6b7280;font-size:.85rem;padding:.35rem .8rem;
           border:1px solid #e2e8f0;border-radius:8px;background:#fff}}
    .back:hover{{color:#06b6d4;border-color:#06b6d4}}
    .card{{max-width:700px;margin:2rem auto;background:#fff;border-radius:16px;
           box-shadow:0 1px 4px rgba(0,0,0,.06);overflow:hidden}}
    .card-header{{padding:1.5rem 1.5rem 1rem;border-bottom:1px solid #f1f5f9}}
    .badge-snap{{display:inline-block;padding:.2rem .7rem;border-radius:999px;
                background:#f0fdfe;color:#0891b2;font-size:.75rem;font-weight:600;
                border:1px solid #bae6fd;margin-bottom:.8rem}}
    h1{{font-size:1.6rem;font-weight:700;margin-bottom:.3rem}}
    .meta{{color:#6b7280;font-size:.85rem}}
    .meta a{{color:#06b6d4;text-decoration:none}}
    .meta a:hover{{text-decoration:underline}}
    table{{width:100%;border-collapse:collapse;font-size:.88rem}}
    th{{background:#f8fafc;padding:.7rem 1rem;text-align:left;color:#6b7280;font-weight:600;
        font-size:.78rem;text-transform:uppercase;letter-spacing:.04em;border-bottom:2px solid #e2e8f0}}
    th:not(:first-child){{text-align:right}}
    td{{padding:.75rem 1rem;border-bottom:1px solid #f1f5f9;vertical-align:middle}}
    tr:last-child td{{border-bottom:none}}
    .footer{{padding:1rem 1.5rem;background:#f8fafc;font-size:.8rem;color:#9ca3af;display:flex;
             justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.5rem}}
    .copy-btn{{cursor:pointer;background:none;border:1px solid #e2e8f0;border-radius:6px;
              padding:.25rem .6rem;font-size:.75rem;color:#6b7280}}
    .copy-btn:hover{{border-color:#06b6d4;color:#06b6d4}}
    @media(max-width:500px){{h1{{font-size:1.25rem}}th,td{{padding:.5rem .75rem}}}}
  </style>
</head>
<body>
  <nav class="topnav">
    <a href="/" class="logo">
      <svg width="24" height="24" viewBox="0 0 44 44" xmlns="http://www.w3.org/2000/svg"><circle cx="16" cy="22" r="11" fill="none" stroke="#06b6d4" stroke-width="2.5"/><circle cx="28" cy="22" r="11" fill="none" stroke="#06b6d4" stroke-width="2.5"/><path d="M8 22 L36 22" stroke="#06b6d4" stroke-width="2" stroke-linecap="round"/><path d="M32 18 L36 22 L32 26" fill="none" stroke="#06b6d4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="8" cy="22" r="2" fill="#06b6d4"/></svg>
      Coinnect
    </a>
    <a href="/" class="back">← Live rates</a>
  </nav>

  <div class="card">
    <div class="card-header">
      <div class="badge-snap">📸 Archived snapshot #{snapshot_id}</div>
      <h1>{amount:g} {from_c} → {to_c}</h1>
      <p class="meta">Captured <strong>{ts_display}</strong> &nbsp;·&nbsp;
        <a href="{api_url}" target="_blank">JSON data ↗</a> &nbsp;·&nbsp;
        <button class="copy-btn" onclick="navigator.clipboard.writeText(location.href).then(()=>this.textContent='Copied!')">Copy link</button>
      </p>
    </div>
    <table>
      <thead>
        <tr>
          <th>Route</th><th>Provider path</th><th>Fee %</th><th>Recipient gets</th><th>Time</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
    <div class="footer">
      <span>Open data · CC-BY 4.0 · <a href="https://coinnect.bot" style="color:#06b6d4">coinnect.bot</a></span>
      <span>Rates are historical — verify live at coinnect.bot before sending</span>
    </div>
  </div>
</body>
</html>""")


@app.get("/whitepaper", include_in_schema=False)
async def whitepaper():
    import markdown as md_lib
    text = (DOCS_DIR / "whitepaper.md").read_text()
    body = md_lib.markdown(text, extensions=["tables", "fenced_code", "nl2br"])
    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Coinnect Whitepaper — The Open Routing Layer for Global Money</title>
  <meta name="description" content="Coinnect white paper: open-source money routing layer. Finds cheapest path between any currencies via fiat, crypto, and P2P networks. Non-profit, no affiliate fees.">
  <style>
    *{{box-sizing:border-box;}}
    body{{margin:0;font-family:Georgia,serif;line-height:1.75;color:#1a1a1a;background:#fff;}}

    /* Sticky top nav */
    .topnav{{position:sticky;top:0;z-index:100;background:rgba(255,255,255,0.95);backdrop-filter:blur(8px);border-bottom:1px solid #e2e8f0;display:flex;align-items:center;justify-content:space-between;padding:.75rem 2rem;font-family:system-ui,sans-serif;}}
    .topnav-logo{{display:flex;align-items:center;gap:.6rem;text-decoration:none;color:#1a1a1a;font-weight:700;font-size:.95rem;}}
    .topnav-logo svg{{width:28px;height:28px;}}
    .topnav-back{{display:inline-flex;align-items:center;gap:.4rem;text-decoration:none;color:#6b7280;font-size:.85rem;padding:.4rem .9rem;border:1px solid #e2e8f0;border-radius:8px;transition:all .15s;background:#fff;}}
    .topnav-back:hover{{color:#06b6d4;border-color:#06b6d4;background:#f0fdfe;}}

    /* Content */
    .content{{max-width:760px;margin:0 auto;padding:2.5rem 1.5rem 4rem;}}
    h1,h2,h3{{font-family:system-ui,sans-serif;margin-top:2.5rem;}}
    h1{{font-size:2rem;border-bottom:2px solid #06b6d4;padding-bottom:.6rem;margin-top:0;}}
    h2{{font-size:1.35rem;margin-top:3rem;color:#0891b2;}}
    h3{{font-size:1.05rem;color:#374151;}}
    p{{margin:.9rem 0;}}
    code{{background:#f1f5f9;padding:.15em .45em;border-radius:4px;font-size:.88em;}}
    pre{{background:#f1f5f9;padding:1.1rem;border-radius:8px;overflow-x:auto;border:1px solid #e2e8f0;}}
    pre code{{background:none;padding:0;font-size:.85em;}}
    hr{{border:none;border-top:1px solid #e2e8f0;margin:2.5rem 0;}}
    a{{color:#06b6d4;}}
    li{{margin:.4rem 0;}}
    blockquote{{margin:1.5rem 0;padding:.8rem 1.2rem;border-left:3px solid #06b6d4;background:#f0fdfe;color:#374151;font-style:italic;}}
    table{{border-collapse:collapse;width:100%;margin:1.5rem 0;font-family:system-ui;font-size:.88rem;}}
    th{{background:#0891b2;color:#fff;text-align:left;padding:.55rem .8rem;}}
    td{{padding:.55rem .8rem;border-bottom:1px solid #e2e8f0;}}
    tr:nth-child(even) td{{background:#f8fafc;}}

    /* Reading progress bar */
    .progress{{position:fixed;top:0;left:0;height:2px;background:linear-gradient(90deg,#06b6d4,#3b82f6);width:0%;z-index:200;transition:width .1s;}}
  </style>
</head>
<body>
  <div class="progress" id="prog"></div>

  <nav class="topnav" role="navigation" aria-label="Site navigation">
    <a href="/" class="topnav-logo" aria-label="Coinnect home">
      <svg width="28" height="28" viewBox="0 0 44 44" xmlns="http://www.w3.org/2000/svg"><circle cx="16" cy="22" r="11" fill="none" stroke="#06b6d4" stroke-width="2.5"/><circle cx="28" cy="22" r="11" fill="none" stroke="#06b6d4" stroke-width="2.5"/><path d="M8 22 L36 22" stroke="#06b6d4" stroke-width="2" stroke-linecap="round"/><path d="M32 18 L36 22 L32 26" fill="none" stroke="#06b6d4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="8" cy="22" r="2" fill="#06b6d4"/></svg>
      Coinnect
    </a>
    <a href="/" class="topnav-back" aria-label="Back to Coinnect app">← Back to app</a>
  </nav>

  <main class="content" role="main">
    {body}
  </main>

  <script>
    const prog=document.getElementById('prog');
    window.addEventListener('scroll',()=>{{
      const h=document.documentElement;
      const pct=(h.scrollTop/(h.scrollHeight-h.clientHeight))*100;
      prog.style.width=Math.min(pct,100)+'%';
    }},{{passive:true}});
  </script>
</body>
</html>""")
