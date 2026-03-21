# Coinnect — ClawHub Skill (Draft, pre-publish)

> **Status:** Ready to publish. Waiting for coinnect.bot public launch (May 1, 2026).
> **Action:** Submit to ClawHub when live. Keep this file as the canonical skill definition.

---

## Skill metadata

```yaml
name: coinnect
display_name: "Coinnect — Money Routing"
description: >
  Find the cheapest multi-step path to send money between any two currencies —
  fiat, crypto, P2P, or mixed. Non-profit, no affiliate fees, no KYC required.
  Returns ranked routes with fees, exchange rates, step-by-step instructions,
  and sender/recipient requirements.
version: "0.3.0"
author: miguelvalenciav
homepage: https://coinnect.bot
license: MIT
tags: [finance, remittances, crypto, routing, money-transfer]
```

---

## Skill definition (Claude Code format)

```markdown
---
name: coinnect
description: Find the cheapest routes to send money between currencies. Calls the Coinnect API to compare traditional remittance, crypto exchanges, and P2P routes. Returns ranked options with total fees, exchange rates, and step-by-step instructions.
---

Use this skill when the user wants to:
- Send money internationally
- Compare exchange rates or transfer fees
- Find the cheapest crypto-to-fiat conversion
- Know how to get USD to NGN, MXN, PHP, BRL, KES, etc.

## How to use

Call the Coinnect API:
GET https://coinnect.bot/v1/quote?from={FROM}&to={TO}&amount={AMOUNT}

Response includes routes ranked by cost, each with steps, fees, and time.

## Key corridors
USD → MXN, BRL, ARS, COP, PEN (LatAm)
USD → NGN, KES, GHS (Africa)
USD → PHP, INR, IDR, VND, THB (Asia)
BTC/ETH/USDC → any fiat (crypto-to-fiat)

## Example
"I need to send $500 to my family in Nigeria."
→ GET /v1/quote?from=USD&to=NGN&amount=500
→ Returns: cheapest route via Binance+USDT+Yellow Card at 0.86%, recipient gets ~NGN 672,737
```

---

## MCP server config (for Claude Desktop / Claude Code)

```json
{
  "mcpServers": {
    "coinnect": {
      "command": "python",
      "args": ["-m", "coinnect.mcp_server"],
      "env": {
        "COINNECT_API": "https://coinnect.bot"
      }
    }
  }
}
```

**Self-hosted:**
```json
{
  "mcpServers": {
    "coinnect-local": {
      "command": "python",
      "args": ["-m", "coinnect.mcp_server"],
      "env": {
        "COINNECT_API": "http://localhost:8100"
      }
    }
  }
}
```

---

## Tools exposed via MCP

| Tool | Description |
|------|-------------|
| `coinnect_quote` | Get ranked routes between any two currencies |
| `coinnect_corridors` | List supported currency pairs |
| `coinnect_explain_route` | Natural language explanation of a route |

---

## Publish checklist

- [ ] coinnect.bot live and stable (May 1, 2026)
- [ ] GitHub repo public (miguelvalenciav/coinnect)
- [ ] ClawHub account created
- [ ] Skill submitted for review
- [ ] Add badge to README: `[![Available on ClawHub](https://clawhub.io/badge/coinnect)]`
