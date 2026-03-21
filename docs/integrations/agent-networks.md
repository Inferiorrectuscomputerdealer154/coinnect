# Coinnect — Agent Network Integrations (Draft, pre-launch)

> **Status:** Research phase. Prepare integrations, publish after May 1, 2026 launch.

---

## Why agent networks matter for Coinnect

In 2026, AI agents are beginning to make financial decisions autonomously.
An agent helping a user send remittances needs a neutral, open, machine-queryable
source of truth for exchange rates and optimal routes. Coinnect is that source.

The goal: be the default money routing tool in every major agent framework
and discovery platform from day one.

---

## Target platforms (in priority order)

### 1. MCP (Model Context Protocol) — Anthropic
- **Status:** ✅ Implemented (`src/coinnect/mcp_server.py`)
- **Distribution:** ClawHub (pending launch), npm/pip registry
- **Audience:** Claude Code, Claude Desktop, any MCP-compatible agent
- **Action:** Publish to ClawHub on May 1

### 2. LangChain / LangGraph
- **What:** Python tool wrapper for LangChain agents
- **Package:** `pip install coinnect-tool` (pending PyPI)
- **Format:**
  ```python
  from coinnect import CoinnectTool
  tools = [CoinnectTool()]  # LangChain-compatible
  ```
- **Action:** Create `coinnect-tool` PyPI package post-launch

### 3. OpenAI Assistants / Function Calling
- **What:** Tool definition for GPT-4o and compatible models
- **File:** `docs/integrations/openai-tool.json` (create before launch)
- **Action:** Publish tool definition + test with GPT-4o

### 4. Fetch.ai / AgentVerse
- **What:** uAgents framework for autonomous economic agents
- **URL:** https://agentverse.ai
- **Fit:** Excellent — Fetch.ai is focused on financial automation and agent-to-agent payments
- **Action:** Create a Fetch.ai agent that wraps Coinnect's quote API
- **Priority:** High (Q3 2026)

### 5. AutoGen (Microsoft)
- **What:** Multi-agent conversation framework
- **Format:** Tool function registration
- **Action:** Add to docs/integrations/ post-launch

### 6. Agent social networks (emerging, 2026)
- **Twitter/X AI agents:** Several AI agents have Twitter presences and interact with each other.
  Coinnect should have a presence where it can respond to "@coinnect quote BTC to NGN" style mentions.
- **Telegram bots:** Already in roadmap. Highest priority for LatAm/Africa distribution.
  One Telegram message: "send 500 USD to Nigeria" → bot replies with cheapest route.
- **Discord bots:** Tech community presence for crypto corridors.

### 7. Stripe Machine Payment Protocol (MPC)
- **What:** Stripe's protocol for machine-to-machine payments
- **Fit:** Complementary — Coinnect handles the routing intelligence,
  Stripe MPC handles the card/fiat execution layer
- **Action:** Document how agents can use Coinnect to find the route,
  then Stripe to execute the fiat leg

### 8. x402 Protocol (Coinbase/Base)
- **What:** HTTP-native micropayments via USDC on Base
- **Fit:** Coinnect could expose a `/v1/quote` endpoint that accepts
  x402 micropayments (e.g., 0.001 USDC per query) as an alternative to
  rate limiting for high-volume agent use
- **Action:** Research and prototype (Q4 2026)

---

## Telegram bot spec (priority — Q2 2026)

A Telegram bot that wraps the Coinnect API for conversational use.

**Commands:**
- `/quote 500 USD to NGN` → returns top 3 routes
- `/rate BTC USD` → current BTC/USD rate
- `/corridors` → list supported pairs
- `/help` → usage guide

**Infrastructure:**
- Python bot using `python-telegram-bot`
- Connects to `https://coinnect.bot/v1/`
- Can run on ash (systemd service) or bob
- No user data stored

---

## PyPI package spec (`coinnect-tool`)

```python
# Usage in any agent framework:
from coinnect import get_quote, get_corridors

# Returns same JSON as /v1/quote
routes = await get_quote("USD", "NGN", 500)

# LangChain tool
from coinnect.langchain import CoinnectTool
# AutoGen tool
from coinnect.autogen import CoinnectFunction
# OpenAI function
from coinnect.openai import COINNECT_FUNCTIONS
```

**Publish checklist:**
- [ ] Create `coinnect-tool` package (post-launch)
- [ ] Register on PyPI
- [ ] Add to LangChain Hub
- [ ] Add to llms.txt standard

---

## llms.txt (emerging standard)

Add `/llms.txt` to coinnect.bot describing the API for LLM discovery:

```
# Coinnect
> The open routing layer for global money.

## API
GET /v1/quote?from=USD&to=NGN&amount=500
GET /v1/corridors
GET /v1/history?from=USD&to=NGN&days=7

## MCP
python -m coinnect.mcp_server
Tools: coinnect_quote, coinnect_corridors, coinnect_explain_route

## Usage policy
100 req/day anonymous. Unlimited for self-hosted instances. MIT license.
```

---

## TODO (add to project backlog)

- [ ] Create Telegram bot (Q2 2026)
- [ ] `pip install coinnect-tool` PyPI package (Q2 2026)
- [ ] Fetch.ai agent wrapper (Q3 2026)
- [ ] `/llms.txt` endpoint on coinnect.bot (before May 1)
- [ ] x402 micropayments research (Q4 2026)
- [ ] Koadro integration (internal Miguel dashboard)
