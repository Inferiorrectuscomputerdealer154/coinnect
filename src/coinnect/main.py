"""
Coinnect API — entry point
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

from coinnect.api.routes import router
from coinnect.db.history import init_db, record_snapshot, prune_old, TRACKED_CORRIDORS

logger = logging.getLogger(__name__)
STATIC_DIR = Path(__file__).parent / "static"
DOCS_DIR = Path(__file__).parent.parent.parent / "docs"


# ── Background rate refresh ─────────────────────────────────────────────────

async def _refresh_once(force: bool = False) -> int:
    """Refresh all exchange edges, store history snapshots. Returns edge count."""
    from coinnect.exchanges.ccxt_adapter import get_all_edges
    from coinnect.exchanges.wise_adapter import get_wise_edges, get_traditional_edges
    from coinnect.exchanges.yellowcard_adapter import get_yellowcard_edges
    from coinnect.routing.engine import build_quote

    crypto_edges, wise_edges, trad_edges, yc_edges = await asyncio.gather(
        get_all_edges(force_refresh=force),
        get_wise_edges(),
        get_traditional_edges(),
        get_yellowcard_edges(),
    )
    all_edges = crypto_edges + wise_edges + trad_edges + yc_edges

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
        "The open routing layer for global money.\n\n"
        "Finds the cheapest path to send money between any two currencies — "
        "across traditional remittance, crypto exchanges, and P2P platforms.\n\n"
        "**Non-profit. No affiliate fees. No custody. No KYC.**\n\n"
        "**For AI agents:** call `/v1/quote` as a tool with `from`, `to`, and `amount` parameters. "
        "Or use the MCP server (`python -m coinnect.mcp_server`) for Claude/MCP-compatible agents.\n\n"
        "Rate limits: 100 req/day anonymous · No auth required for basic use."
    ),
    version="0.3.0",
    contact={"name": "Coinnect", "url": "https://coinnect.bot"},
    license_info={"name": "MIT"},
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(STATIC_DIR / "index.html")


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
  <title>Coinnect Whitepaper</title>
  <style>
    body {{ max-width: 760px; margin: 0 auto; padding: 2rem 1.5rem; font-family: Georgia, serif; line-height: 1.7; color: #1a1a1a; }}
    h1,h2,h3 {{ font-family: system-ui, sans-serif; margin-top: 2rem; }}
    h1 {{ font-size: 2rem; border-bottom: 2px solid #06b6d4; padding-bottom: .5rem; margin-top: 0; }}
    h2 {{ font-size: 1.4rem; margin-top: 2.5rem; color: #0891b2; }}
    h3 {{ font-size: 1.1rem; color: #374151; }}
    code {{ background: #f1f5f9; padding: .1em .4em; border-radius: 3px; font-size: .9em; }}
    pre {{ background: #f1f5f9; padding: 1rem; border-radius: 6px; overflow-x: auto; }}
    pre code {{ background: none; padding: 0; }}
    hr {{ border: none; border-top: 1px solid #e2e8f0; margin: 2rem 0; }}
    a {{ color: #06b6d4; }}
    li {{ margin: .3rem 0; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1.5rem 0; font-family: system-ui; font-size: .9rem; }}
    th {{ background: #0891b2; color: white; text-align: left; padding: .5rem .75rem; }}
    td {{ padding: .5rem .75rem; border-bottom: 1px solid #e2e8f0; }}
    tr:nth-child(even) td {{ background: #f8fafc; }}
    .back {{ display: inline-block; margin-bottom: 2rem; font-family: system-ui; font-size: .9rem; text-decoration: none; color: #6b7280; }}
    .back:hover {{ color: #06b6d4; }}
  </style>
</head>
<body>
  <a class="back" href="/">← Back to Coinnect</a>
  {body}
</body>
</html>""")
