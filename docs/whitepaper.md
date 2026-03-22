# Coinnect: The Open Route Guide for Global Money

**Version:** 0.1 (March 2026)
**Author:** [Miguel V.](https://www.linkedin.com/in/miguelvalenciav/)
**Domain:** coinnect.bot
**Status:** Live — public beta

---

## Abstract

Every year, people and machines move trillions of dollars across borders. The infrastructure exists. The exchanges exist. The corridors are open. But the information is fragmented, opaque, and — when it isn't — controlled by platforms that profit from sending you the wrong way.

Coinnect is the route guide for global money. It tells you how to get from A to B at the lowest cost, in the least time, using any combination of exchanges, wallets, and networks — without touching your money, without charging a commission, and without any interest in the route you take.

Like a road map, it doesn't drive. Like a compass, it doesn't choose the destination. It just shows you all the paths — and which one is shortest today.

---

## 1. The Problem

### 1.1 The invisible tax on moving money

A nurse in the Philippines sends $300 to her family every month. She has done this for twelve years. She uses the same service her cousin recommended in 2012. She has never compared prices. She doesn't know that another route — two steps instead of one, through a stablecoin she's never heard of — would save her $18 every month. That's $216 a year. Over twelve years, that's more than $2,500 — quietly extracted through ignorance, not fraud.

No one deceived her. The information just wasn't easy to find. And the services that could show her are paid by the exchanges they recommend.

This is the core problem Coinnect solves: **not the cost of moving money, but the cost of not knowing the cheapest way to move it.**

### 1.2 The comparison gap

A handful of services today attempt to compare money transfer options:

| Service | Scope | Model | Neutral? |
|---------|-------|-------|---------|
| Monito.com | Global fiat remittance | For-profit, affiliate commissions | No — paid per referral |
| Yadio.io | LatAm P2P crypto rates | For-profit, price tracker | No — single-step, no routing |
| Wise | Direct fiat transfer | For-profit, they are a route | No — also a listed route |
| Google "send money" | Surface-level | Commercial agreements | No |
| Coinnect | Global, fiat + crypto + P2P | Non-profit, donation-funded | **Yes** |

The difference is structural, not ethical. Monito may have good intentions — but if Exchange A pays them a commission and Exchange B doesn't, the incentive exists to favor A. Coinnect removes that incentive entirely by accepting no commission from any exchange, ever.

### 1.3 Closed worlds that don't speak to each other

The deeper problem isn't just cost — it's fragmentation. Global money doesn't flow through one system. It flows through dozens of separate ecosystems, each with its own users, its own liquidity, and its own rules:

- **M-Pesa** (Kenya, Tanzania, 8 African countries) — 50 million users operating via SMS, no smartphone required
- **GCash** (Philippines) — 80 million users, telco-backed, entirely self-contained
- **bKash** (Bangladesh) — 65 million users, the financial backbone of an entire country
- **UPI** (India) — a government protocol with 400 million users across PhonePe, Paytm, Google Pay
- **Wave** (West Africa) — Senegal, Mali, Côte d'Ivoire, growing fast
- **El Dorado** (Latin America) — digital dollar P2P network built to work around local currency instability

Each of these is a planet with its own gravity. A freelancer in Venezuela can't pay a supplier in Kenya directly. A family in the Philippines can't receive from a relative in Bangladesh without going through three intermediaries, each taking a cut.

The connective tissue that exists today — stablecoins like USDC — is technically capable of linking these worlds. But it sits locked inside closed platforms that built it for their own users, not for the open internet.

**Coinnect is the routing layer** that sits above all of them: not replacing any platform, not competing with any of them, but finding the optimal path between any two points — whatever ecosystems those points happen to live in.

### 1.4 The machine gap

As of March 2026, AI agents are beginning to make financial decisions autonomously. Stripe's Machine Payment Protocol represents the first serious attempt to standardize payments between machines. But it serves the corporate, card-based world.

There is no open, neutral API that an AI agent can query to find the cheapest path between two currencies across the full spectrum of exchanges — from traditional remittance services to crypto networks to regional P2P platforms.

Coinnect is built to fill that gap.

---

## 2. The Solution

### 2.1 What Coinnect does

Coinnect aggregates real-time pricing data from exchanges, calculates all viable routes between two currencies, and returns them ranked by total cost and time — with no preference for any exchange.

**Input:**
> "I want to send 500 USD to someone in Nigeria."

**Output:**
```json
{
  "routes": [
    {
      "rank": 1,
      "label": "Cheapest",
      "total_cost_pct": 1.4,
      "total_time_minutes": 60,
      "steps": [
        {"from": "USD", "to": "USDC", "via": "Kraken",     "fee_pct": 0.5},
        {"from": "USDC", "to": "NGN",  "via": "Yellow Card", "fee_pct": 0.9}
      ],
      "you_send": 500.00,
      "they_receive": 762450,
      "they_receive_currency": "NGN"
    }
  ]
}
```

Coinnect does not execute the transfer. It does not hold funds. It does not require KYC. It shows the map. You drive.

### 2.2 The routing layer

The internet moves data through routers. Routers don't read your emails. They don't care what you're sending. They just find the fastest path from A to B and hand it off to the next node.

Coinnect is the router for money. It doesn't touch the transfer. It finds the path.

**The value is in the information, not the transaction.** And because Coinnect never touches transactions, it needs no money transmitter license, holds no regulatory risk, and has no reason — structural or financial — to favor any ecosystem over another.

### 2.3 For humans and machines

Coinnect has two interfaces built from day one:

**For humans:** A simple web interface at coinnect.bot. Enter amount, origin currency, destination currency. Get a ranked list of routes with exchange logos, step-by-step instructions, and requirements. No account required.

**For machines:** A public REST API returning the same data as JSON. Any AI agent, chatbot, or automated system can query Coinnect as a tool and route payments optimally without human intervention.

```
GET https://coinnect.bot/v1/quote?from=USD&to=NGN&amount=500
```

**For agents (MCP):** A Model Context Protocol server (`python -m coinnect.mcp_server`) exposes three tools — `coinnect_quote`, `coinnect_corridors`, `coinnect_explain_route` — compatible with Claude Code, Claude Desktop, and any MCP client.

---

## 3. Why Non-Profit

### 3.1 The alignment problem

Every for-profit comparison platform faces the same structural problem: the business model eventually compromises the product. Affiliate commissions, promoted listings, premium placements — these are not malicious choices, they are business necessities. But they introduce bias into what should be a purely informational service.

A non-profit doesn't have this problem. The only metric that matters is accuracy.

### 3.2 Sustainability through donations

Coinnect is funded entirely by voluntary donations from users who save money using the platform. The logic is simple: if we save you $20 on a transfer, a $1 donation is a 2000% return for you and keeps the service running for everyone.

No advertising. No affiliate fees. No investor expectations. No exit.

### 3.3 Infrastructure

Coinnect is designed to run at minimal cost. The current deployment runs on a single Linux server serving the FastAPI application, SQLite databases for rate history and analytics, and the static web frontend. No serverless, no CDN required at current scale.

As traffic grows, the architecture is trivially horizontally scalable: the quote engine is stateless, the SQLite history store can be migrated to libSQL/Turso for edge distribution, and the static frontend can be moved to any CDN.

### 3.4 Transparent compensation

The founder's compensation and all operational expenses are published publicly. The founding statutes establish a hard cap on founder compensation tied to the organization's annual budget. Financial reports are published quarterly.

---

## 4. Providers — Inclusion Criteria

Coinnect includes providers that meet these criteria:

1. **Publicly documented pricing** — either via a real-time API or published fee tables
2. **Regulated in at least one jurisdiction** — reduces counterparty risk for users
3. **No credible fraud or insolvency history** — basic user protection

We do not charge providers to be listed. We do not accept payment for rankings. Any provider that meets the criteria is included; any that fails is excluded — regardless of who they are.

Providers without a live public API are included with fees sourced from their published pricing pages, clearly labeled as **~estimated** in route instructions. Users are always advised to verify on the provider's official site before transacting.

### 4.1 Integrated providers (as of March 2026)

**Crypto exchanges (live rates via CCXT):**

| Provider | Type | Key corridors |
|----------|------|---------------|
| Binance | Crypto exchange | Global, largest USDC/USDT liquidity |
| Kraken | Crypto exchange | USD, EUR, major crypto |
| Coinbase | Crypto exchange | USD, EUR, regulated US anchor |
| Bitso | LatAm crypto | MXN, ARS, BRL — SPEI delivery |

**Specialized fiat/crypto bridges:**

| Provider | Type | Key corridors |
|----------|------|---------------|
| Yellow Card | Africa crypto→fiat | NGN, GHS, KES, UGX, TZS, ZAR, XAF, RWF |
| Wise | Global fiat transfer | 80+ currencies, live rate API |

**Remittance networks (estimated fees from published pricing):**

| Provider | Coverage | Est. fee range | Notes |
|----------|----------|----------------|-------|
| Remitly | 170+ countries | 1.2–3.8% | Strong LatAm, Asia, Africa |
| WorldRemit | 130+ countries | 2.2–4.2% | Strong Africa |
| Ria | 165+ countries | 2.8–4.5% | 490k+ agent locations |
| Sendwave | Africa, W. Africa | 1.5–2.0% | No transfer fee, FX spread only |
| Xoom (PayPal) | 160+ countries | 2.8–5.0% | Large US diaspora user base |
| Paysend | 160+ countries | 2.0–3.6% | Card-to-card delivery |
| OFX | Major currencies | 0.5–0.7% | Best for large transfers (min ~$250) |
| TransferGo | Europe focus | 1.1–2.5% | Eastern Europe corridors |
| Skrill | 120+ countries | 2.7–4.5% | E-wallet, gaming/freelancer use |
| Revolut | Global (app) | 1.1–2.0% | Standard plan limits apply |

**Comparison baseline:**

| Provider | Type | Notes |
|----------|------|-------|
| Western Union | Traditional | ~200 countries, cash or bank |
| MoneyGram | Traditional | ~200 countries, cash or bank |

**Why include Western Union and MoneyGram?** Because the comparison only makes sense when you can see the full spectrum. When Coinnect shows that a USDC route saves you $22 versus Western Union on the same corridor, the value proposition is immediate and concrete. We include them not to attack them — but because completeness is honesty.

---

## 5. Technical Architecture

### 5.1 The quote engine

At its core, Coinnect runs a shortest-path algorithm across a live graph where:
- **Nodes** = currencies (USD, MXN, USDC, NGN, PHP, etc.)
- **Edges** = exchange pairs with real-time fee and rate data
- **Weight** = total cost (fees + spread) or total time, depending on user preference

The engine uses a two-phase approach:

1. **Direct routes** — all single-step provider edges for the requested corridor are collected and ranked by cost. This ensures every provider is surfaced, not just the cheapest one.
2. **Multi-step routes** — two Dijkstra runs (cost-optimized and time-optimized) find the best multi-hop paths (e.g., USD → USDC via Coinbase → NGN via Yellow Card).

Results are merged, deduplicated by path signature, and returned as up to 12 ranked routes. The top three receive featured labels (Cheapest, Balanced, Fastest); the rest appear as numbered options.

### 5.2 Rate refresh

Exchange rates refresh every 3 minutes via a background asyncio task. Rates are sourced from:
- **CCXT** for crypto exchange pairs (Binance, Kraken, Coinbase, Bitso)
- **open.er-api.com** for fiat cross-rates (free, no auth, ~hourly updates)
- **Provider pricing pages** for static remittance corridors (updated manually)

### 5.3 Rate history

Every 3-minute refresh stores a snapshot for 18 tracked corridors in a SQLite database. This powers the dual sparkline charts on the web UI, showing how the effective exchange rate (not just the fee %) has moved over 15m / 1h / 1d / 7d / 28d / 1y windows.

The timestamp comparison bug common in SQLite (ISO 8601 with timezone vs. `datetime('now')` format mismatch) is handled by normalizing stored timestamps to `YYYY-MM-DD HH:MM:SS` format before comparison.

### 5.4 API design

```
GET  /v1/quote              — Ranked routes for a transfer
GET  /v1/history            — Time-series rate data for a corridor (?from=&to=&minutes=)
GET  /v1/exchanges          — List all integrated providers
GET  /v1/corridors          — Most active currency pairs
GET  /v1/health             — API status
POST /v1/keys               — Generate a self-serve API key (no signup)
GET  /v1/keys/{key}/usage   — Today's usage for a key
GET  /v1/suggestions        — Community-submitted provider suggestions
POST /v1/suggestions        — Submit a new provider suggestion
POST /v1/suggestions/{id}/upvote — Upvote (fingerprint-gated, one vote per device)
```

Full OpenAPI specification available at `/docs`.

### 5.5 API keys — userless by design

Coinnect's key system is deliberately stateless on the user side:

- `POST /v1/keys` generates a `cn_...` UUID key instantly — no email, no account, no OAuth
- The key is stored in SQLite with a tier (`free`: 1,000 req/day) and optional label
- Rate counting is in-memory (O(1) per request, dict keyed by API key)
- Memory is backed by SQLite and survives restarts via cache warm-up
- Lost key? Generate a new one. No recovery, no support ticket.

Anonymous access (no key) allows 100 req/day. Key holders get 1,000 req/day. Self-hosters get unlimited.

### 5.6 Machine-readable by design

Coinnect is built for the emerging world of autonomous agents making financial decisions.

| Standard | What it is | Supported |
|----------|-----------|-----------|
| **OpenAPI 3.0** | Machine-readable API spec | ✓ `/docs` |
| **JSON Schema** | Data structure validation | ✓ |
| **MCP (Model Context Protocol)** | AI↔tool connections | ✓ `coinnect.mcp_server` |
| **OpenAI Tool format** | Function definition for AI agents | ✓ compatible |
| **Anthropic Tool Use** | Claude's tool format | ✓ compatible |
| **llms.txt** | Site summary for LLM crawlers | Planned |

**Example MCP tool call:**
```
User: "I need to send $500 to my sister in Kenya."
Agent: → calls coinnect_quote(from="USD", to="KES", amount=500)
Agent: "The cheapest route is via Coinbase + Yellow Card at 1.3% total cost,
        delivering ~66,500 KES in about 20 minutes. Sendwave is also a great
        option at 1.5% with no transfer fee."
```

### 5.7 No custody, no KYC

Coinnect never holds funds, never processes payments, and never collects user identity information. Each provider handles its own KYC requirements. Coinnect is purely informational — legally and technically.

### 5.8 Backoffice & observability

A password-protected admin panel at `/admin` provides:
- **Search analytics** — total queries today, split by web vs. API, top corridors, 7-day trend
- **Provider management** — pause or re-enable any provider without a code deploy
- **Recent searches** — last 50 queries with corridor, amount, and source

Every `/v1/quote` call is logged asynchronously (non-blocking) to the analytics SQLite table, capturing corridor, amount, API key prefix, source type, and route count.

---

## 6. Disclaimer & Rate Accuracy

Exchange rates and fees displayed on Coinnect are sourced from provider APIs and published pricing pages. Live-rate providers (Binance, Kraken, Coinbase, Bitso, Wise, Yellow Card) refresh every 3 minutes. Estimated-fee providers (labeled **~est.**) use manually verified fee ranges from published pricing.

**Coinnect makes no warranty about rate accuracy.** Rates change in seconds. Always verify the current rate directly with the provider before executing any transfer. Coinnect is an information service only — it does not execute transfers, hold funds, or act as a financial intermediary. Any decision made based on information shown here is at the user's sole risk.

---

## 7. Legal & Regulatory

### 7.1 What Coinnect is not

Coinnect is a **price comparison and routing information service**. It is not:

- A money transfer operator (MTO)
- A payment processor
- A cryptocurrency exchange
- A financial advisor
- A custodian of any kind

### 7.2 Regulatory classification

In most jurisdictions, a service that provides publicly available pricing information and routing recommendations — without executing, facilitating, or touching transactions — does not require a money services business (MSB) license or equivalent.

This mirrors the legal position of price comparison services like Google Flights (which shows flight prices without being an airline) or Monito (which compares transfer fees without being a remittance service).

### 7.3 Data privacy

Coinnect does not collect personal information. Quote requests include only currency types and amounts. Analytics logs capture aggregate usage (corridor, amount range, source type) but no user identity, wallet addresses, or IP addresses in persistent storage. Optional GA4 analytics can be opted out via `/?notrack`.

---

## 8. Roadmap

| Phase | Timeline | Milestone |
|-------|----------|-----------|
| Public launch | Q2 2026 | GitHub repo public, rate limiting enforced, Remitly live API |
| Community | Q3 2026 | Provider suggestion board, rate accuracy feedback, user reviews |
| Ecosystem | Q4 2026 | Stellar anchors (M-Pesa, Wave, GCash), `pip install coinnect-tool` |
| Global | 2027 | 30+ providers, 60+ currencies, Africa + Asia full coverage |

---

## 9. The Founder

[Miguel V.](https://www.linkedin.com/in/miguelvalenciav/) built Coinnect because the problem is real, the solution is simple, and nobody was building it without a business model attached.

His public donation wallet is listed on coinnect.bot. His compensation is capped by the founding statutes and published quarterly. He has no equity to sell, no investors to answer to, and no exit to plan.

He intends to do this for as long as it is useful.

---

## 10. Vision

Before GPS, every driver carried a road atlas. It didn't drive. It didn't own the roads. It had no preference for which highway you took. You trusted it precisely because it had no stake in your route — it just knew every path and showed you all of them.

Then came Waze: the same neutrality, but live, collaborative, self-updating — and eventually, consulted by autonomous vehicles without any human in the loop.

That is the arc of Coinnect.

Today: we show you the map.
Tomorrow: the map updates itself with community data.
Eventually: machines consult it automatically, and money moves at its natural cost — without anyone being able to extract a tax from ignorance.

**The money already knows how to move. Coinnect shows it the cheapest way.**

---

*This document is version 0.4. Updated as the project evolves.*
*Feedback: miguel@coinnect.bot*
