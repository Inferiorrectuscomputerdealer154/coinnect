# Coinnect: The Open Route Guide for Global Money

**Version:** 0.5 (March 2026)
**Author:** [Miguel V.](https://www.linkedin.com/in/miguelvalenciav/)
**Domain:** coinnect.bot · **Status:** Live — public beta
**Code:** [github.com/coinnect-dev/coinnect](https://github.com/coinnect-dev/coinnect) · MIT License

---

## Abstract

Every year, people and machines move trillions of dollars across borders. The infrastructure exists. The exchanges are open. The corridors are live. But the information is fragmented, opaque, and — when it isn't — controlled by platforms that profit from sending you the wrong way.

Coinnect is the route guide for global money. It tells you how to get from A to B at the lowest cost, in the least time, using any combination of exchanges, wallets, and networks — without touching your money, without charging a commission, and without any interest in the route you take.

Like a road map, it doesn't drive. Like a compass, it doesn't choose the destination. It just shows you all the paths — and which one is cheapest today.

---

## 1. The Problem

### 1.1 The invisible tax on moving money

A nurse in the Philippines sends $300 to her family every month. She has done this for twelve years. She uses the same service her cousin recommended in 2012. She has never compared prices. She doesn't know that another route — two steps instead of one, through a stablecoin she's never heard of — would save her $18 every month. That's $216 a year. Over twelve years, that's more than $2,500 — quietly extracted through ignorance, not fraud.

No one deceived her. The information just wasn't easy to find. And the services that could show her are paid by the exchanges they recommend.

This is the core problem Coinnect solves: **not the cost of moving money, but the cost of not knowing the cheapest way to move it.**

### 1.2 The comparison gap

| Service | Scope | Model | Neutral? |
|---------|-------|-------|---------|
| Monito.com | Global fiat remittance | For-profit, affiliate commissions | No — paid per referral |
| Yadio.io | LatAm P2P crypto rates | For-profit, price tracker | Partial — single-step only |
| Wise | Direct fiat transfer | For-profit, they are a route | No — also a listed route |
| Google "send money" | Surface-level | Commercial agreements | No |
| Coinnect | Global, fiat + crypto + P2P | Non-profit, donation-funded | **Yes** |

The difference is structural, not ethical. Affiliate platforms may have good intentions — but if Exchange A pays them and Exchange B doesn't, the incentive exists to favor A. Coinnect removes that incentive entirely by accepting no commission from any exchange, ever.

### 1.3 Closed worlds that don't speak to each other

The deeper problem is fragmentation. Global money flows through dozens of separate ecosystems:

- **M-Pesa** (Kenya, Tanzania, 8 African countries) — 50 million users, SMS-based
- **GCash** (Philippines) — 80 million users, telco-backed
- **bKash** (Bangladesh) — 65 million users, national financial backbone
- **UPI** (India) — government protocol, 400 million users across PhonePe, Paytm, Google Pay
- **Wave** (West Africa) — Senegal, Mali, Côte d'Ivoire
- **El Dorado** (Latin America) — digital dollar P2P for currency-unstable markets

Stablecoins like USDC are technically capable of linking these worlds — but they sit inside closed platforms. **Coinnect is the routing layer** above all of them: not replacing any platform, not competing with any of them — just finding the optimal path between any two points.

### 1.4 The machine gap

As of 2026, AI agents are beginning to make financial decisions autonomously. There is no open, neutral API an agent can query to find the cheapest path between two currencies across the full spectrum — from traditional remittance to crypto to regional P2P. Coinnect fills that gap.

---

## 2. The Solution

### 2.1 What Coinnect does

Coinnect aggregates real-time pricing from exchanges, calculates all viable routes, and returns them ranked by total cost and time — with no preference for any provider.

**Input:** "I want to send 500 USD to Nigeria."

**Output:**
```json
{
  "routes": [{
    "rank": 1,
    "label": "Cheapest",
    "total_cost_pct": 1.4,
    "total_time_minutes": 60,
    "steps": [
      {"from": "USD",  "to": "USDC", "via": "Kraken",      "fee_pct": 0.5},
      {"from": "USDC", "to": "NGN",  "via": "Yellow Card", "fee_pct": 0.9}
    ],
    "you_send": 500.00,
    "they_receive": 762450,
    "they_receive_currency": "NGN"
  }]
}
```

Coinnect does not execute the transfer. It does not hold funds. It does not require KYC. It shows the map. You drive.

### 2.2 The routing layer

The internet moves data through routers. Routers don't read your emails. They just find the fastest path and hand it off.

Coinnect is the router for money. It doesn't touch the transfer. It finds the path.

**The value is in the information, not the transaction.** Because Coinnect never touches transactions, it needs no money transmitter license and carries minimal regulatory risk under current interpretations, and has no reason — structural or financial — to favor any ecosystem.

### 2.3 For humans, machines, and self-hosters

**For humans:** coinnect.bot — enter amount, origin, destination. No account required.

**For machines:** Public REST API returning JSON. Any AI agent or automated system can query Coinnect as a tool.

```
GET https://coinnect.bot/v1/quote?from=USD&to=NGN&amount=500
```

**For agents (MCP):** A Model Context Protocol server exposes three tools — `coinnect_quote`, `coinnect_corridors`, `coinnect_explain_route` — compatible with Claude Code, Claude Desktop, and any MCP client.

```bash
python -m coinnect.mcp_server
```

**For self-hosters:** The full stack runs as a single Python process. Clone, install, run. No cloud services required.

---

## 3. System Architecture

![Coinnect System Architecture](/static/architecture.svg)

### 3.1 Quote engine

The engine runs a shortest-path algorithm across a live graph:

- **Nodes** = currencies (USD, MXN, USDC, NGN, PHP…)
- **Edges** = exchange pairs with real-time fee and rate data
- **Weight** = total cost (fees + spread) or total time

Two-phase approach:
1. **Direct routes** — all single-step provider edges for the corridor, ranked by cost.
2. **Multi-hop routes** — two Dijkstra passes (cost-optimized, time-optimized) find paths like USD → USDC via Coinbase → NGN via Yellow Card.

Results are merged, deduplicated by path signature, and returned as up to 30 ranked routes. Routes within 0.1% of each other are shown as tied.

### 3.2 Rate refresh

Exchange rates refresh every 3 minutes via a background asyncio task:

- **CCXT** — live order book data from Binance, Kraken, Coinbase, Bitso, Luno, Bitstamp, Gemini
- **Wise API** — live fiat rates for 80+ currencies
- **Yellow Card API** — live Africa crypto→fiat rates
- **open.er-api.com** — FX cross-rates for fiat pairs
- **Published fee tables** — 15+ remittance providers (labeled `~est.`)

### 3.3 Rate history & open data

Every 3-minute refresh stores a snapshot for 18 tracked corridors in SQLite. This powers:

- **Sparkline charts** on the web UI (15m / 1h / 1d / 7d / 28d / 1y windows)
- **Per-provider comparison chart** — fee % over time for the same corridor (Wise vs. Binance P2P vs. Strike, etc.)
- **Open data download** — full daily CSV exports at `/v1/snapshot/daily`, licensed CC-BY 4.0

### 3.4 API

```
GET  /v1/quote                 Ranked routes for a transfer
GET  /v1/history               Time-series best rate for a corridor
GET  /v1/history/providers     Per-provider rate history for a corridor
GET  /v1/snapshot/{id}         Permalink for a specific rate snapshot
GET  /v1/snapshot/daily        Full-day CSV export (CC-BY 4.0, no key needed)
GET  /v1/snapshot/meta         Available snapshot dates
GET  /v1/exchanges             List all integrated providers
GET  /v1/corridors             Most active currency pairs
GET  /v1/health                API status
POST /v1/keys                  Generate a self-serve API key (no signup)
GET  /v1/keys/usage            Today's usage for a key
GET  /v1/suggestions           Community provider suggestions
POST /v1/suggestions           Submit a new suggestion
```

Human-readable snapshots at `coinnect.bot/rates/{id}` — shareable, archivable, CC-BY 4.0.

Full OpenAPI specification at `/docs`.

### 3.5 API keys — userless by design

- `POST /v1/keys` generates a `cn_...` key instantly — no email, no account
- Rate counting is in-memory (O(1) per request)
- Lost key? Generate a new one. No recovery, no support ticket.

| Tier | Requests/day | Requests/hour |
|------|-------------|--------------|
| Anonymous (no key) | 20 | 50 (beta) |
| Free key | 1,000 | 100 |
| Agent 🤖 | 5,000 | 200 |
| Pro | 50,000 | 2,000 |
| Self-hosted | unlimited | unlimited |

### 3.6 Machine-readable by design

| Standard | Supported |
|----------|-----------|
| OpenAPI 3.0 | ✓ `/docs` |
| JSON Schema | ✓ |
| MCP (Model Context Protocol) | ✓ `coinnect.mcp_server` |
| OpenAI Tool format | ✓ compatible |
| Anthropic Tool Use | ✓ compatible |
| llms.txt | ✓ `/llms.txt` |

### 3.7 No custody, no KYC

Coinnect never holds funds, never processes payments, never collects identity information. Each provider handles its own KYC. Coinnect is purely informational — legally and technically.

### 3.8 Backoffice & observability

A password-protected admin panel at `/admin` provides search analytics, provider management (pause/enable without redeploy), and recent query logs. Every `/v1/quote` call is logged asynchronously.

---

## 4. x402 — Machine-to-Machine Payments for API Access

### 4.1 The problem with free tiers

Free API tiers have a structural flaw: they require account creation, email verification, abuse monitoring, and a support system. They punish honest users (rate limits, quotas) and reward abusers (throwaway accounts). For an AI agent operating autonomously, even generating an API key is friction.

The x402 protocol solves this. It extends HTTP with a payment layer: instead of a 401 Unauthorized, a server returns a 402 Payment Required with a machine-readable price. The client pays automatically in USDC on Base L2 (Ethereum Layer 2), and the server unlocks the response. No accounts. No keys. No friction.

### 4.2 How it works

```
Agent → GET /v1/quote?from=USD&to=NGN&amount=500
Server ← 402 Payment Required
         X-Payment-Required: {amount: "0.001", currency: "USDC", network: "base",
                               recipient: "0xf0813041b9b017a88f28B8600E73a695E2B02e0A",
                               description: "Coinnect quote — 1 request"}
Agent → GET /v1/quote?from=USD&to=NGN&amount=500
         X-Payment: <signed USDC Base transaction>
Server ← 200 OK + route data
```

Each request costs approximately **$0.001 USDC** (~0.1 cents). A typical AI agent session making 100 queries costs $0.10 — comparable to a fraction of a cent per search in electricity. On Base L2, each transaction costs less than $0.001 in gas.

### 4.3 Why Base L2?

- **Gas fees:** $0.0003–0.001 per transaction (vs. $2–20 on Ethereum mainnet)
- **Settlement:** ~2 seconds, Ethereum-secured
- **USDC:** native on Base, issued by Circle — no bridge risk
- **Wallet compatibility:** MetaMask, Coinbase Wallet, any EVM wallet

Our receiving address (`0xf0813041b9b017a88f28B8600E73a695E2B02e0A`) is an EVM address — the same one that accepts ETH, USDC, BNB, and DAI donations. It works on Base natively; no separate setup is needed.

### 4.4 x402 tiers on Coinnect

| Access mode | How | Cost | Limit |
|-------------|-----|------|-------|
| Browser (anonymous) | IP-based | Free | 20/day, 50/hr |
| Free key | POST /v1/keys | Free | 1,000/day |
| Agent key | Request at coinnect.bot | Free | 5,000/day |
| x402 (micropayment) | Auto-pay $0.001/req | $0.001/req | Unlimited |
| Pro key | Contact | Subscription | 50,000/day |

x402 is designed for fully autonomous AI agents that operate without human oversight. They pay as they go, wallets permitting, with no account management required.

### 4.5 Mexico-specific note

If you are operating from Mexico and want to top up a Base L2 wallet:

1. **Coinbase (recommended):** Available in Mexico since 2023. Buy USDC directly with MXN via SPEI or bank transfer. No MSB license required on your end — you're a retail buyer. Withdraw USDC to Base L2 within the same app.
2. **Bitso → Coinbase:** Convert MXN → USDC on Bitso (native Mexican exchange), then send to a Coinbase-linked Base address or any Base-compatible wallet.
3. **Wallet:** MetaMask supports Base natively. Switch network to "Base" and your existing address (`0xf0813…`) receives and sends USDC on Base.

Since Coinnect is purely an informational service (no money transmission), operating from Mexico requires no special financial licensing. x402 income would be classified as digital services revenue — taxable as RESICO or general regime depending on your setup.

### 4.6 Current status

x402 is in the Coinnect roadmap for Q3 2026. The receiving address is already configured. Implementation requires integrating the [x402-python](https://github.com/coinbase/x402) middleware (FastAPI-compatible) into the `/v1/quote` route and deploying with a Base RPC endpoint.

The [Coinbase x402 SDK](https://github.com/coinbase/x402) is MIT-licensed and maintained by Coinbase. It handles payment verification, replay prevention, and automatic response unlocking.

---

## 5. Why Non-Profit

### 5.1 The alignment problem

Every for-profit comparison platform faces the same structural problem: the business model eventually compromises the product. Affiliate commissions, promoted listings, premium placements — these aren't malicious choices, they're business necessities. But they introduce bias into what should be a purely informational service.

A non-profit doesn't have this problem. The only metric that matters is accuracy.

### 5.2 Sustainability

Coinnect is funded entirely by voluntary donations from users who save money using the platform. If we save you $20 on a transfer, a $1 donation is a 2000% return for you and keeps the service running for everyone.

No advertising. No affiliate fees. No investor expectations. No exit.

Open Collective (fiscal host: Open Source Collective) accepts donations in fiat and crypto. The project treasury uses a Gnosis Safe multisig on Polygon.

### 5.3 Transparent compensation

The founder's compensation and all operational expenses are published publicly in [SUSTAINABILITY.md](https://github.com/coinnect-dev/coinnect/blob/main/docs/SUSTAINABILITY.md). The founding statutes cap founder compensation at 10% of total annual budget, starting at $2,500/month and scaling only with organizational revenue. Financial reports are published quarterly.

### 5.4 Infrastructure cost

The current deployment runs on a single Linux server: FastAPI, three SQLite databases, and a static frontend. No serverless, no CDN required at current scale. As traffic grows, the architecture is designed for straightforward horizontal scaling: the quote engine is stateless, SQLite history can migrate to libSQL/Turso for edge distribution, and the frontend can move to any CDN.

---

## 6. Providers — Inclusion Criteria

1. **Publicly documented pricing** — real-time API or published fee tables
2. **Regulated in at least one jurisdiction** — reduces counterparty risk
3. **No credible fraud or insolvency history**

We do not charge providers to be listed. We do not accept payment for rankings. Any provider that meets the criteria is included; any that fails is excluded — regardless of who they are.

Providers without a live public API are included with fees from published pricing pages, clearly labeled as **~est.** in route instructions.

### 6.1 Integrated providers (March 2026)

**Crypto exchanges (live rates via CCXT):** Binance, Kraken, Coinbase, Bitso, Luno (Africa), Bitstamp (EU), Gemini (US)

**Fiat/crypto bridges (live APIs):** Wise (80+ currencies), Yellow Card (Africa, 8 countries)

**Remittance (published fee estimates):**

| Provider | Coverage | Est. fee range |
|----------|----------|----------------|
| Remitly | 170+ countries | 1.2–3.8% |
| WorldRemit | 130+ countries | 2.2–4.2% |
| Ria | 165+ countries | 2.8–4.5% |
| Sendwave | Africa, W. Africa | 1.5–2.0% |
| Xoom (PayPal) | 160+ countries | 2.8–5.0% |
| Paysend | 160+ countries | 2.0–3.6% |
| OFX | Major currencies | 0.5–0.7% |
| TransferGo | Europe focus | 1.1–2.5% |
| Strike | Bitcoin-native | ~1.0% |
| XE | Global | 1.5–3.0% |
| Global66 | LatAm | 1.0–2.5% |
| Atlantic Money | EU corridors | 0.4–0.6% |
| Intermex | USA→LatAm | 2.5–4.0% |
| Western Union | ~200 countries | 3.0–8.0% |
| MoneyGram | ~200 countries | 3.0–7.0% |

Western Union and MoneyGram are included as baselines. When Coinnect shows a USDC route saves you $22 versus Western Union on the same corridor, the value is immediate and concrete. Completeness is honesty.

---

## 7. Disclaimer & Rate Accuracy

Rates displayed on Coinnect are sourced from provider APIs and published pricing pages. Live-rate providers refresh every 3 minutes. Estimated-fee providers (labeled **~est.**) use manually verified ranges.

**Coinnect makes no warranty about rate accuracy.** Rates change in seconds. Always verify directly with the provider before executing any transfer. Coinnect is an information service — it does not execute transfers, hold funds, or act as a financial intermediary.

---

## 8. Legal & Regulatory

### 8.1 What Coinnect is not

- A money transfer operator (MTO)
- A payment processor
- A cryptocurrency exchange
- A financial advisor
- A custodian of any kind

### 8.2 Regulatory position

A service that provides publicly available pricing information and routing recommendations — without executing, facilitating, or touching transactions — does not require a money services business (MSB) license in most jurisdictions.

This mirrors the legal position of Google Flights (shows prices without being an airline) or Monito (compares fees without being a remittance service).

### 8.3 Data privacy

Coinnect does not collect personal information. Quote requests include only currency types and amounts. Analytics logs capture aggregate usage (corridor, amount range, source type) with no user identity, wallet addresses, or IP addresses in persistent storage. GA4 analytics can be opted out via `/?notrack`.

---

## 9. Roadmap

| Phase | Timeline | Milestone |
|-------|----------|-----------|
| Public beta | Q1 2026 ✓ | GitHub public, open data API, rate history, snapshot permalinks |
| Community | Q2 2026 | x402 pay-per-use API (USDC/Base), PWA, provider suggestion board |
| Ecosystem | Q4 2026 | Stellar anchors (M-Pesa, Wave, GCash), `pip install coinnect-tool` |
| Global | 2027 | 30+ providers, 60+ currencies, Africa + Asia full coverage |

---

## 10. The Founder

[Miguel V.](https://www.linkedin.com/in/miguelvalenciav/) built Coinnect because the problem is real, the solution is simple, and nobody was building it without a business model attached.

His compensation is capped by the founding statutes and published quarterly. He has no equity to sell, no investors to answer to, and no exit to plan.

---

## 11. Vision

Before GPS, every driver carried a road atlas. It didn't drive. It didn't own the roads. It had no preference for which highway you took. You trusted it precisely because it had no stake in your route — it just knew every path and showed you all of them.

Then came Waze: the same neutrality, but live, collaborative, self-updating — and eventually, consulted by autonomous vehicles without any human in the loop.

That is the arc of Coinnect.

Today: we show you the map.
Tomorrow: the map updates itself with community data.
Eventually: machines consult it automatically, and money moves at its natural cost — without anyone extracting a tax from ignorance.

**The money already knows how to move. Coinnect shows it the cheapest way.**

---

*Version 0.5 · March 2026 · feedback: miguel@coinnect.bot*
