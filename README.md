# Coinnect

> The open routing layer for global money.

**coinnect.bot** · Non-profit · Open source · Bot-friendly

---

## What is Coinnect?

Coinnect finds the cheapest path to send money between any two currencies — across traditional remittance services, crypto exchanges, and regional P2P platforms.

You tell it where money needs to go. It tells you how to get there, ranked by cost and time. It never touches your funds.

```
GET https://api.coinnect.bot/v1/quote?from=USD&to=NGN&amount=500
```

```json
{
  "routes": [
    {
      "rank": 1,
      "label": "Cheapest",
      "total_cost_pct": 1.4,
      "total_time_minutes": 60,
      "steps": [
        { "from": "USD", "to": "USDC", "via": "Kraken",     "fee_pct": 0.5 },
        { "from": "USDC", "to": "NGN",  "via": "YellowCard", "fee_pct": 0.9 }
      ],
      "you_send": 500.00,
      "they_receive": 762450,
      "vs_western_union_saving_usd": 21.50
    }
  ]
}
```

## Why non-profit?

Every comparison platform faces the same problem: the business model eventually compromises the product. Affiliate commissions, promoted listings, premium placements — these are not malicious choices, they are business necessities. But they introduce bias into what should be a purely informational service.

Coinnect accepts no commission from any exchange, ever. It is funded by voluntary donations from users who save money using it.

## For humans and machines

**Humans** use the web interface at [coinnect.bot](https://coinnect.bot): enter amount, origin, destination — get a ranked table of routes with step-by-step instructions.

**Machines** query the public REST API directly. Coinnect is designed to be called as a tool by AI agents, chatbots, and automated systems. Full OpenAPI spec in [`/docs/api`](./docs/api/).

**AI agents via MCP** — Coinnect ships with a native MCP server that exposes three tools from day one:

| Tool | Description |
|------|-------------|
| `coinnect_quote` | Find cheapest/fastest routes between any two currencies |
| `coinnect_corridors` | List supported currency pairs |
| `coinnect_explain_route` | Natural language explanation of a route |

To use with Claude Code or Claude Desktop, add to your MCP config:

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

Or run directly: `COINNECT_API=https://coinnect.bot python -m coinnect.mcp_server`

## The problem we solve

Global money flows through dozens of closed ecosystems — M-Pesa, GCash, bKash, UPI, Alipay, Western Union, regional P2P platforms — that don't speak to each other. Moving money between them requires knowing which path exists, which is cheapest today, and how many steps it takes.

That information exists. It's just fragmented, opaque, and — when someone organizes it — monetized through referral fees that bias the result.

Coinnect organizes it without bias. No referral fees. No promoted routes. No equity. No exit.

## Status

🚧 **Pre-launch** — targeting May 1, 2026

- [x] White paper (v0.3)
- [x] Quote engine — Kraken, Binance, Coinbase, Bitso, Wise, Yellow Card, Western Union, MoneyGram
- [x] Web UI (coinnect.bot)
- [x] Public API (`/v1/quote`, `/v1/exchanges`, `/v1/corridors`, `/v1/health`)
- [x] MCP server (`coinnect-mcp`) — AI agent integration from day 1
- [ ] OpenAPI spec (publish at `/docs`)
- [ ] Rate limiting (slowapi)
- [ ] GitHub repo public

## White paper

Full white paper in [`/docs/whitepaper.md`](./docs/whitepaper.md).

## Contributing

Coinnect is open source. Contributions welcome — exchange integrations, routing improvements, translations, and documentation.

See [`CONTRIBUTING.md`](./CONTRIBUTING.md).

## Founder

Miguel Valencia Villaseñor — former COO at Airtm (2018–2025).

Built Coinnect because the problem is real, the solution is simple, and no one was building it without a business model attached.

Public donation wallet: *forthcoming at coinnect.bot*

## License

MIT — free to use, fork, and build on.
