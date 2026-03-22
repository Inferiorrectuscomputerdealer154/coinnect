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
    from coinnect.routing.engine import build_quote

    crypto_edges, wise_edges, trad_edges, yc_edges, remit_edges = await asyncio.gather(
        get_all_edges(force_refresh=force),
        get_wise_edges(),
        get_traditional_edges(),
        get_yellowcard_edges(),
        get_remittance_edges(),
    )
    all_edges = crypto_edges + wise_edges + trad_edges + yc_edges + remit_edges

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
        "**Non-profit. No affiliate fees. No custody. Free forever.**\n\n"
        "**For AI agents:** call `/v1/quote` as a tool with `from`, `to`, and `amount` parameters. "
        "Or use the MCP server (`python -m coinnect.mcp_server`) for Claude/MCP-compatible agents.\n\n"
        "Rate limits: 20 req/day / 50/hr anonymous (beta) · 1,000/day free key · "
        "5,000/day agent key · see coinnect.bot/#pricing"
    ),
    version="2026.03.22.1",
    contact={"name": "Coinnect", "url": "https://coinnect.bot"},
    license_info={"name": "MIT"},
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


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
    return FileResponse(STATIC_DIR / "sitemap.xml", media_type="application/xml")


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


@app.get("/rates/{snapshot_id}", include_in_schema=False)
async def snapshot_page(snapshot_id: int):
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
      <svg width="24" height="24" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="16" cy="16" r="14" stroke="#06b6d4" stroke-width="2"/>
        <text x="16" y="21" font-size="13" text-anchor="middle" fill="#F7931A" font-family="monospace" font-weight="bold">₿</text>
        <text x="16" y="13" font-size="10" text-anchor="middle" fill="#06b6d4" font-family="monospace">$</text>
      </svg>
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
      <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="16" cy="16" r="14" stroke="#06b6d4" stroke-width="2"/>
        <text x="16" y="21" font-size="13" text-anchor="middle" fill="#F7931A" font-family="monospace" font-weight="bold">₿</text>
        <text x="16" y="13" font-size="10" text-anchor="middle" fill="#06b6d4" font-family="monospace">$</text>
      </svg>
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
