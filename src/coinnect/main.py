"""
Coinnect API — entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from coinnect.api.routes import router

app = FastAPI(
    title="Coinnect API",
    description=(
        "The open routing layer for global money.\n\n"
        "Finds the cheapest path to send money between any two currencies — "
        "across traditional remittance, crypto exchanges, and P2P platforms.\n\n"
        "Non-profit. No affiliate fees. No custody. No KYC.\n\n"
        "**For AI agents:** call `/v1/quote` as a tool with `from`, `to`, and `amount` parameters."
    ),
    version="0.1.0",
    contact={"name": "Coinnect", "url": "https://coinnect.bot"},
    license_info={"name": "MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "name": "Coinnect",
        "tagline": "The open routing layer for global money",
        "docs": "/docs",
        "quote": "/v1/quote?from=USD&to=NGN&amount=500",
        "source": "https://coinnect.bot",
    }
