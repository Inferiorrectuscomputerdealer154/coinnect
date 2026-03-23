# Coinnect: The Open Route Guide for Global Money

**Version:** 0.7 (March 2026)
**Author:** Miguel
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
| Wise | Direct fiat transfer | For-profit, also a provider | Partial — also a listed route |
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

**Input:** "I want to send 50,000 INR to the UK."

**Output:**
```json
{
  "routes": [{
    "rank": 1,
    "label": "Cheapest",
    "total_cost_pct": 0.76,
    "total_time_minutes": 60,
    "steps": [
      {"from": "INR",  "to": "USDT", "via": "CoinDCX",  "fee_pct": 0.5},
      {"from": "USDT", "to": "BTC",  "via": "MEXC",     "fee_pct": 0.1},
      {"from": "BTC",  "to": "GBP",  "via": "Kraken",   "fee_pct": 0.16}
    ],
    "you_send": 50000,
    "they_receive": 397,
    "they_receive_currency": "GBP"
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
GET https://coinnect.bot/v1/quote?from=INR&to=GBP&amount=50000
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

The engine models the global money transfer landscape as a **weighted directed graph**:

- **Nodes** = currencies (USD, MXN, USDC, NGN, BTC, ETB, XOF…)
- **Edges** = conversion paths between currencies, each carrying: `exchange_rate`, `fee_pct`, `estimated_minutes`, and `provider`
- **Weight** = total cost (compound fees + exchange rate spread) or total time

![Routing Diagram](/static/routing-diagram.svg)

#### Edge types

| Type | Source | Fee | Badge | Example |
|------|--------|-----|-------|---------|
| **Live exchange** | CCXT order book, Wise API | Real bid/ask spread | LIVE | Binance BTC→MXN at 0.12% |
| **Estimated provider** | Published fee tables | Static % | ESTIMATED | Wise INR→GBP at ~2.8% |
| **Market rate bridge** | FX reference APIs | ~0.5% spread | ESTIMATED | USD→ETB via CurrencyAPI |
| **P2P market** | Binance P2P, Yadio | Median of offers | LIVE/REFERENCE | USDT→PHP at 0.3% |

#### How paths are found

Two-phase approach:
1. **Direct routes** — all single-step provider edges for the corridor, ranked by cost.
2. **Multi-hop routes** — two Dijkstra passes (cost-optimized, time-optimized) find paths up to **4 hops**, like: INR → USDT (CoinDCX, 0.5%) → BTC (MEXC, 0.1%) → GBP (Kraken, 0.16%) = 0.76% total — **73% cheaper** than a direct Wise transfer at 2.8%.

#### Bridge edges

For exotic corridors where no direct provider exists (e.g., ZAR→ETB), the engine uses **bridge edges** from reference FX sources (CurrencyAPI, Frankfurter, FloatRates). These carry a conservative 0.5% spread estimate and are labeled ESTIMATED. When a real provider is added for that corridor, it automatically wins the ranking.

This means Coinnect can route virtually **any fiat-to-fiat pair** through a combination of crypto exchanges and market rate bridges. The graph currently has 29,000+ edges covering 50+ currencies.

#### Constraints

- **Circular route prevention:** the engine skips any exchange already used in the current path, ensuring no provider appears twice.
- **Amount filtering:** edges are filtered by `min_amount` and `max_amount` for the requested transfer size.
- **Cost calculation:** compound formula per MRP spec: `total_cost = 1 - ∏(1 - fee_i/100)` — correctly handles multi-hop fee stacking.

Results are merged, deduplicated by path signature, and returned as up to 30 ranked routes. Routes within 0.1% of each other are shown as tied.

### 3.2 Rate refresh

Exchange rates refresh every 3 minutes via a background asyncio task, pulling from 30+ live data sources:

- **CCXT (21 exchanges)** — live order book data from Binance, Kraken, Coinbase, OKX, Bybit, KuCoin, Gate, Bitget, MEXC, HTX, Crypto.com, Luno, Bitstamp, Gemini, Bithumb, Bitflyer, BtcTurk, IndependentReserve, WhiteBIT
- **Binance P2P (live)** — real-time P2P USDT rates for 12 emerging market currencies (MXN, ARS, NGN, COP, VES, BRL, KES, GHS, PKR, BDT, TRY, UAH)
- **Wise API** — live fiat rates for 80+ currencies
- **Direct exchange APIs** — Bitso (LatAm), Buda (Chile/Colombia/Peru), VALR (South Africa), CoinDCX (India), WazirX (India), SatoshiTango (Argentina)
- **Central bank official rates (9)** — BCB (Brazil), TRM (Colombia), Bluelytics (Argentina), TCMB (Turkey), NBP (Poland), CNB (Czech Republic), NBU (Ukraine), NBG (Georgia), BOI (Israel), BNR (Romania)
- **Reference rates** — CoinGecko, Yadio (LatAm P2P), Frankfurter (ECB), FloatRates, CurrencyAPI, CriptoYa (Argentina)
- **Calculator** — x-rates.com
- **Published fee tables** — 21 remittance providers (labeled `~est.`)

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
POST /v1/verify                Report a real rate you observed (community calibration)
GET  /v1/quests                Open rate verification bounties
POST /v1/quests/{id}/claim     Claim a quest with your rate report
GET  /v1/suggestions           Community provider suggestions
POST /v1/suggestions           Submit a new suggestion
```

Human-readable snapshots at `coinnect.bot/rates/{id}` — shareable, archivable, CC-BY 4.0.

Full OpenAPI specification at `/docs`.

### 3.5 API keys — userless by design

- `POST /v1/keys` generates a `cn_...` key instantly — no email, no account
- Rate counting is in-memory (O(1) per request)
- Lost key? Generate a new one. No recovery, no support ticket.

| Tier | Requests/day | Notes |
|------|-------------|-------|
| Anonymous (no key) | 20 | IP-based |
| Personal (free key) | 1,000 | No signup required |
| Pro / Bots | 5,000 | Free during beta; paid plans when demand grows |
| x402 micropayment | Unlimited | $0.002/request, USDC on Base L2 |
| Self-hosted | Unlimited | Run your own instance |

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
Agent → GET /v1/quote?from=INR&to=GBP&amount=50000
Server ← 402 Payment Required
         X-Payment-Required: {amount: "0.002", currency: "USDC", network: "base",
                               recipient: "0xf0813041b9b017a88f28B8600E73a695E2B02e0A",
                               description: "Coinnect quote — 1 request"}
Agent → GET /v1/quote?from=INR&to=GBP&amount=50000
         X-Payment: <signed USDC Base transaction>
Server ← 200 OK + route data
```

Each request costs **$0.002 USDC** (~0.2 cents). A typical AI agent session making 100 queries costs $0.20 — comparable to a fraction of a cent per search in electricity. On Base L2, each transaction costs less than $0.001 in gas.

### 4.3 Why Base L2?

- **Gas fees:** $0.0003–0.001 per transaction (vs. $2–20 on Ethereum mainnet)
- **Settlement:** ~2 seconds, Ethereum-secured
- **USDC:** native on Base, issued by Circle — no bridge risk
- **Wallet compatibility:** MetaMask, Coinbase Wallet, any EVM wallet

Our receiving address (`0xf0813041b9b017a88f28B8600E73a695E2B02e0A`) is an EVM address — the same one that accepts ETH, USDC, BNB, and DAI donations. It works on Base natively; no separate setup is needed.

### 4.4 x402 tiers on Coinnect

| Access mode | How | Cost | Limit |
|-------------|-----|------|-------|
| Browser (anonymous) | IP-based | Free | 20/day |
| Personal key | POST /v1/keys | Free | 1,000/day |
| Pro / Bot key | POST /v1/keys | Free (beta) | 5,000/day |
| x402 (micropayment) | Auto-pay $0.002/req | $0.002/req | Unlimited |
| Self-hosted | Clone + run | Free | Unlimited |

x402 is designed for fully autonomous AI agents that operate without human oversight. They pay as they go, wallets permitting, with no account management required.

### 4.5 Current status

x402 is **live** on Coinnect. The [x402-python](https://github.com/coinbase/x402) middleware (FastAPI-compatible) is deployed on the `/v1/quote` route, accepting USDC on Base L2 at **$0.002 per request**. Any agent that sends a valid x402 payment header bypasses all rate limits — no key required.

The [Coinbase x402 SDK](https://github.com/coinbase/x402) is MIT-licensed and maintained by Coinbase. It handles payment verification, replay prevention, and automatic response unlocking.

---

## 5. Why Non-Profit

### 5.1 The alignment problem

Every for-profit comparison platform faces the same structural problem: the business model eventually compromises the product. Affiliate commissions, promoted listings, premium placements — these aren't malicious choices, they're business necessities. But they introduce bias into what should be a purely informational service.

A non-profit doesn't have this problem. The only metric that matters is accuracy.

### 5.2 Sustainability

Coinnect is **free for personal use**. If usage patterns change or costs require it, paid tiers may be introduced for high-volume commercial use — with a minimum 90-day notice before any change takes effect.

The project is funded by voluntary donations from users who save money using the platform, and by x402 micropayments from autonomous agents. If we save you $20 on a transfer, a $1 donation is a 2000% return for you and keeps the service running for everyone.

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

**Crypto exchanges (21 live via CCXT):** Binance, Kraken, Coinbase, OKX, Bybit, KuCoin, Gate, Bitget, MEXC, HTX, Crypto.com, Luno, Bitstamp, Gemini, Bithumb, Bitflyer, BtcTurk, IndependentReserve, WhiteBIT

**Crypto exchanges (live via direct API):** Bitso (LatAm), Buda (Chile/Colombia/Peru), VALR (South Africa), CoinDCX (India), WazirX (India), SatoshiTango (Argentina)

**P2P live rates:** Binance P2P (12 emerging market currencies: MXN, ARS, NGN, COP, VES, BRL, KES, GHS, PKR, BDT, TRY, UAH), Yadio (LatAm P2P)

**Fiat transfer (live API):** Wise (80+ currencies)

**Central bank official rates (9):** BCB (Brazil), TRM (Colombia), Bluelytics (Argentina blue rate), TCMB (Turkey), NBP (Poland), CNB (Czech Republic), NBU (Ukraine), NBG (Georgia), BOI (Israel), BNR (Romania)

**Reference rates:** CoinGecko, Frankfurter (ECB), FloatRates, CurrencyAPI, CriptoYa (Argentina), x-rates.com

**Community verification:** Users and bots can report real rates via `POST /v1/verify`. Open quests at `GET /v1/quests` incentivize coverage of under-observed corridors. Reports feed the adaptive fee calibration system (Section 11).

**Remittance (21 providers, published fee estimates):**

| Provider | Coverage | Est. fee range |
|----------|----------|----------------|
| Remitly | 170+ countries | 1.2–3.8% |
| Wise | 80+ currencies | 0.4–1.5% |
| WorldRemit | 130+ countries | 2.2–4.2% |
| Ria | 165+ countries | 2.8–4.5% |
| Sendwave | Africa, W. Africa | 1.5–2.0% |
| Nala | East Africa, UK corridors | 0.5–1.5% |
| Taptap Send | Africa, UK/EU/US corridors | 0.5–1.2% |
| Xoom (PayPal) | 160+ countries | 2.8–5.0% |
| Paysend | 160+ countries | 2.0–3.6% |
| OFX | Major currencies | 0.5–0.7% |
| TransferGo | Europe focus | 1.1–2.5% |
| Strike | Bitcoin-native | ~1.0% |
| XE | Global | 1.5–3.0% |
| Global66 | LatAm | 1.0–2.5% |
| Atlantic Money | EU corridors | 0.4–0.6% |
| Intermex | USA→LatAm | 2.5–4.0% |
| Flutterwave | African corridors | 1.5–3.0% |
| Yellow Card | Africa crypto→fiat | 1.0–2.5% |
| Azimo | EU→Global | 1.5–3.0% |
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

| Phase | Focus |
|-------|-------|
| Now | 21 CCXT exchanges, 21 remittance providers, 9 central banks, x402 live, quests, MCP, Telegram bot, 50+ SEO pages, Hugging Face dataset |
| Next | More live-rate providers, community verification at scale, delivery method filters |
| Later | MTP ([mtp.bot](https://mtp.bot)), Stellar anchors, SDKs |

This is a beta. Priorities shift based on user feedback. See [`ROADMAP.md`](./ROADMAP.md) for details.

---

## 10. Rate Accuracy Model

Every route in Coinnect carries an **accuracy score** (0.0–1.0) reflecting the confidence in the displayed rate:

| Source type | Score | Meaning |
|-------------|-------|---------|
| Live exchange API (order book) | 1.0 | Real-time bid/ask from exchange |
| Live FX API (Wise, etc.) | 0.95 | Provider's own rate, refreshed every 3 min |
| Central bank reference | 0.90 | Official rate, updated daily |
| P2P market monitor | 0.80 | Aggregated from multiple P2P listings |
| Published fee table + live FX | 0.60 | Known fee structure applied to live mid-market rate |
| Static estimate | 0.40 | Manual research, verified quarterly |

The accuracy score is computed as:

```
accuracy = source_freshness × source_reliability × fee_confidence
```

Where:
- `source_freshness` decays linearly from 1.0 (just fetched) to 0.5 (at TTL expiry)
- `source_reliability` is the historical hit rate of the source (% of successful fetches in last 24h)
- `fee_confidence` is 1.0 for known fees (API-reported) and 0.6 for estimated fees

This score is exposed in the API response and used internally to weight route rankings when multiple routes have similar total costs.

---

## 11. Adaptive Fee Calibration

Static fee estimates (~est.) are inherently inaccurate — provider fees change without notice, and exchange rate spreads vary by corridor and time of day.

Coinnect addresses this through an **adaptive calibration loop**:

1. **Observation:** When a provider with live API data covers the same corridor as an estimated provider, both rates are recorded in parallel.

2. **Comparison:** The system computes the error between the estimated rate and any available ground truth:
   - Live API quotes for the same corridor
   - World Bank Remittance Prices Worldwide (quarterly benchmark)
   - User-reported rates (future: community verification via MTP)

3. **Adjustment:** Fee estimates are adjusted using exponential moving average:
   ```
   adjusted_fee = α × observed_fee + (1 - α) × current_estimate
   ```
   where α = 0.3 (slow adaptation to avoid overreacting to outliers).

4. **Confidence tracking:** Each adjustment narrows or widens the confidence interval. Corridors with frequent ground truth observations converge to high accuracy; corridors with sparse data maintain wider uncertainty bands.

This creates a self-improving system: as more data sources come online and more users report real rates, the estimated providers converge toward actual costs — without requiring manual updates.

The calibration state is persisted in SQLite and published as part of the open data exports, enabling external researchers to audit and improve the model.

---

## 12. Scalability

### Current architecture

Coinnect runs as a single Python process (FastAPI + SQLite) on a single server. With 4 workers, it handles ~50 requests/second for live quotes and serves static assets via Cloudflare CDN.

This is sufficient for tens of thousands of daily users. The quote engine is stateless — all state lives in SQLite and in-memory edge caches that rebuild every 3 minutes.

### Scaling path

| Load | Architecture | Estimated cost |
|------|-------------|----------------|
| 1-50K users/day | Single server (current) | ~$30/month |
| 50K-500K | Add Cloudflare cache on /v1/quote (60s TTL) | ~$30/month |
| 500K-5M | Horizontal: 2-3 servers behind load balancer | ~$100-300/month |
| 5M+ | Edge compute (Cloudflare Workers) + libSQL/Turso for distributed SQLite | ~$500-1000/month |

### Distributed data collection

The most valuable form of distributed computing for Coinnect is not CPU — it's **data collection from diverse geographies**. A node in Nigeria can verify NGN rates more accurately than a server in Mexico. A node in the Philippines can access GCash pricing that may be geo-blocked elsewhere.

Future architecture: volunteer "verifier nodes" that run a lightweight Coinnect agent, collect local rate data, and submit it via the `/v1/verify` endpoint. Contributors earn quest rewards (MTP). This is conceptually similar to how Waze collects traffic data from drivers — distributed sensing, centralized routing.

### Federated directory model

Coinnect's long-term architecture follows a **federated directory model** — similar to DNS, not blockchain. Every node maintains a replica of the provider directory (edges, rates, fees) and can resolve routing queries independently.

When 100 agents query routes, one server suffices. When 10,000 agents query simultaneously, anyone can run a Coinnect node that syncs the same directory and serves queries locally. No central bottleneck. No single point of failure.

This is fundamentally different from blockchain:
- **Blockchain** requires global consensus on every state change — it scales poorly with more participants.
- **Federated directory** replicates read-only data across nodes — it scales linearly. More nodes = more capacity, not more overhead.

The directory is the protocol. Any node that speaks MRP (Money Routing Protocol) can join the network, replicate the edge data, and serve queries. The source of truth for rate data comes from the provider APIs themselves — not from a central server or a consensus mechanism.

Think of it as: providers publish their rates → nodes replicate the directory → agents query any node → the network grows organically. Like DNS resolvers, not like miners.

---

## 13. Vision

Before GPS, every driver carried a road atlas. It didn't drive. It didn't own the roads. It had no preference for which highway you took. You trusted it precisely because it had no stake in your route — it just knew every path and showed you all of them.

Then came Waze: the same neutrality, but live, collaborative, self-updating — and eventually, consulted by autonomous vehicles without any human in the loop.

That is the arc of Coinnect.

Today: we show you the map.
Tomorrow: the map updates itself with community data.
Eventually: machines consult it automatically, and money moves at its natural cost — without anyone extracting a tax from ignorance.

**The money already knows how to move. Coinnect shows it the cheapest way.**

---

*Version 0.6 (March 2026) · feedback: miguel@coinnect.bot*
