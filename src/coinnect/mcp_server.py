"""
Coinnect MCP Server — exposes routing tools to AI agents.

Run standalone:
    python -m coinnect.mcp_server          # stdio transport (Claude Desktop / Claude Code)
    python -m coinnect.mcp_server --http   # HTTP/SSE on port 8101

Tools:
    coinnect_quote          — ranked routes between two currencies
    coinnect_corridors      — list supported currency pairs
    coinnect_explain_route  — natural language explanation of a route
"""

import asyncio
import json
import sys
import os
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Default API base: localhost when running alongside the FastAPI server,
# or override via COINNECT_API env var.
API_BASE = os.environ.get("COINNECT_API", "http://localhost:8100").rstrip("/")

app = Server("coinnect")


# ── Tool definitions ────────────────────────────────────────────────────────


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="coinnect_quote",
            description=(
                "Find the cheapest and fastest routes to send money between any two currencies. "
                "Returns ranked routes with total fees, exchange rates, transfer time, and "
                "step-by-step instructions. Each route may combine multiple exchanges. "
                "Coinnect never executes transfers — it only shows you the path. "
                "Currencies: USD, EUR, GBP, MXN, BRL, ARS, COP, PEN, NGN, KES, GHS, "
                "PHP, INR, IDR, VND, THB, PKR, USDC, USDT, BTC, ETH, and more."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "from_currency": {
                        "type": "string",
                        "description": "Source currency ISO 4217 code (e.g. USD, EUR, MXN) or crypto ticker (USDC, BTC)"
                    },
                    "to_currency": {
                        "type": "string",
                        "description": "Destination currency ISO 4217 code (e.g. NGN, PHP, BRL) or crypto ticker"
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount to send in from_currency (e.g. 500)"
                    }
                },
                "required": ["from_currency", "to_currency", "amount"]
            }
        ),
        Tool(
            name="coinnect_corridors",
            description=(
                "List the most commonly used currency corridors supported by Coinnect. "
                "Useful before calling coinnect_quote to check if a pair is likely to have routes."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="coinnect_explain_route",
            description=(
                "Given a quote result from coinnect_quote, explain the best route in plain language. "
                "Describes each step, why this route is optimal, and what the sender and recipient need to do."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "from_currency": {"type": "string", "description": "Source currency"},
                    "to_currency": {"type": "string", "description": "Destination currency"},
                    "amount": {"type": "number", "description": "Amount in source currency"},
                    "route": {
                        "type": "object",
                        "description": "A single route object from coinnect_quote response"
                    }
                },
                "required": ["from_currency", "to_currency", "amount", "route"]
            }
        ),
    ]


# ── Tool handlers ───────────────────────────────────────────────────────────


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "coinnect_quote":
        return await _handle_quote(arguments)
    elif name == "coinnect_corridors":
        return await _handle_corridors()
    elif name == "coinnect_explain_route":
        return [TextContent(type="text", text=_explain_route(arguments))]
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def _handle_quote(args: dict) -> list[TextContent]:
    from_c = str(args.get("from_currency", "")).upper()
    to_c = str(args.get("to_currency", "")).upper()
    amount = float(args.get("amount", 0))

    if not from_c or not to_c or amount <= 0:
        return [TextContent(type="text", text="Error: from_currency, to_currency, and amount > 0 are required.")]

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(f"{API_BASE}/v1/quote", params={"from": from_c, "to": to_c, "amount": amount})

        if r.status_code == 404:
            data = r.json()
            return [TextContent(type="text", text=f"No routes found for {from_c} → {to_c}. {data.get('detail', '')}")]
        if r.status_code != 200:
            return [TextContent(type="text", text=f"API error {r.status_code}: {r.text[:200]}")]

        data = r.json()
        routes = data.get("routes", [])

        if not routes:
            return [TextContent(type="text", text=f"No routes found for {from_c} → {to_c}.")]

        # Format output for LLM consumption
        lines = [
            f"Coinnect quote: {from_c} {amount:,.2f} → {to_c}",
            f"Generated at: {data['generated_at']}",
            f"Found {len(routes)} route(s):",
            ""
        ]

        for r_obj in routes:
            lines.append(f"[{r_obj['rank']}] {r_obj['label']}")
            lines.append(f"  Fee: {r_obj['total_cost_pct']}% · Time: {_fmt_time(r_obj['total_time_minutes'])}")
            lines.append(f"  You send: {from_c} {r_obj['you_send']:,.2f}")
            lines.append(f"  They receive: {to_c} {r_obj['they_receive']:,.2f}")
            for step in r_obj["steps"]:
                lines.append(f"  Step {step['step']}: {step['from_currency']} → {step['to_currency']} via {step['via']} ({step['fee_pct']}% · {_fmt_time(step['estimated_minutes'])})")
                if step.get("instructions"):
                    lines.append(f"    → {step['instructions']}")
            lines.append("")

        # Append raw JSON for agents that want to parse it
        lines.append("--- Raw JSON ---")
        lines.append(json.dumps(data, indent=2))

        return [TextContent(type="text", text="\n".join(lines))]

    except httpx.ConnectError:
        return [TextContent(type="text", text=f"Could not connect to Coinnect API at {API_BASE}. Is the server running?")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error fetching quote: {e}")]


async def _handle_corridors() -> list[TextContent]:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{API_BASE}/v1/corridors")

        if r.status_code != 200:
            return [TextContent(type="text", text=f"API error {r.status_code}")]

        data = r.json()
        lines = ["Supported currency corridors:", ""]
        for c in data.get("corridors", []):
            via = ", ".join(c.get("via", []))
            lines.append(f"  {c['from']} → {c['to']}  (via {via})")

        lines += [
            "",
            "Note: Coinnect can route any pair reachable through a chain of supported exchanges.",
            "Use coinnect_quote to find routes for any pair not listed here."
        ]
        return [TextContent(type="text", text="\n".join(lines))]

    except Exception as e:
        return [TextContent(type="text", text=f"Error fetching corridors: {e}")]


def _explain_route(args: dict) -> str:
    from_c = str(args.get("from_currency", "")).upper()
    to_c = str(args.get("to_currency", "")).upper()
    amount = float(args.get("amount", 0))
    route = args.get("route", {})

    if not route:
        return "No route provided."

    label = route.get("label", "")
    cost_pct = route.get("total_cost_pct", 0)
    minutes = route.get("total_time_minutes", 0)
    they_receive = route.get("they_receive", 0)
    steps = route.get("steps", [])

    fee_usd_equiv = amount * cost_pct / 100
    exchanges = list(dict.fromkeys(s["via"] for s in steps))

    lines = [
        f"Route explanation: {label} — {from_c} {amount:,.2f} → {to_c}",
        "",
        f"This route sends {from_c} {amount:,.2f} and delivers {to_c} {they_receive:,.2f} "
        f"to the recipient, with a total cost of {cost_pct}% (~{from_c} {fee_usd_equiv:.2f} in fees). "
        f"Expected transfer time: {_fmt_time(minutes)}.",
        "",
        "How it works, step by step:",
    ]

    for step in steps:
        who = "Sender" if step["step"] < len(steps) else "Recipient"
        lines.append(
            f"  {step['step']}. {step['instructions']} "
            f"(fee: {step['fee_pct']}%, ~{_fmt_time(step['estimated_minutes'])})"
        )

    lines += [
        "",
        f"Exchanges used: {', '.join(exchanges)}",
        "",
        "Why this route?",
    ]

    if label == "Cheapest":
        lines.append(
            f"This is the lowest-fee path currently available for {from_c} → {to_c}. "
            f"It routes through {' and '.join(exchanges)} to minimize the total percentage lost to fees and spread."
        )
    elif label == "Fastest":
        lines.append(
            f"This is the fastest path currently available, estimated to arrive in {_fmt_time(minutes)}. "
            f"Speed comes at a slightly higher fee ({cost_pct}%) compared to the cheapest option."
        )
    elif label == "Balanced":
        lines.append(
            f"This route balances cost and speed — it's not the absolute cheapest or fastest, "
            f"but offers a good trade-off: {cost_pct}% fee in {_fmt_time(minutes)}."
        )
    else:
        lines.append(
            f"This is an alternative path with {cost_pct}% total fees and {_fmt_time(minutes)} estimated time."
        )

    lines += [
        "",
        "Important: Coinnect only shows you the route. Each exchange handles its own KYC and execution.",
        "Coinnect never holds your funds.",
    ]

    return "\n".join(lines)


def _fmt_time(minutes: int) -> str:
    if minutes < 60:
        return f"~{minutes}m"
    h = minutes // 60
    m = minutes % 60
    return f"~{h}h {m}m" if m else f"~{h}h"


# ── Entry point ─────────────────────────────────────────────────────────────


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
