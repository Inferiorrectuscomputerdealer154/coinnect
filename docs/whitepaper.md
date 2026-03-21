# Coinnect: The Open Route Guide for Global Money

**Version:** 0.3 (Draft — March 2026)
**Author:** [Miguel V.](https://www.linkedin.com/in/miguelvalenciav/)
**Domain:** coinnect.bot
**Status:** Pre-launch white paper

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
- **Alipay / WeChat Pay** (China) — over a billion users combined, accessible only with a Chinese bank account
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
        {"from": "USDC", "to": "NGN",  "via": "YellowCard", "fee_pct": 0.9}
      ],
      "you_send": 500.00,
      "they_receive_NGN": 762450,
      "vs_direct_saving_usd": 21.50
    },
    {
      "rank": 2,
      "label": "Fastest (15 min)",
      "total_cost_pct": 2.1,
      ...
    }
  ]
}
```

Coinnect does not execute the transfer. It does not hold funds. It does not require KYC. It shows the map. You drive.

### 2.2 The routing layer

The internet moves data through routers. Routers don't read your emails. They don't care what you're sending. They just find the fastest path from A to B and hand it off to the next node.

Coinnect is the router for money. It doesn't touch the transfer. It finds the path.

Think of it as a universal adapter: when you travel, you don't rebuild the electrical grid of each country — you carry a small device that translates between them. Coinnect is that adapter for the fragmented global payment landscape. Every closed ecosystem stays exactly as it is. Coinnect just knows how to move value between all of them.

**The value is in the information, not the transaction.** And because Coinnect never touches transactions, it needs no money transmitter license, holds no regulatory risk, and has no reason — structural or financial — to favor any ecosystem over another.

### 2.3 For humans and machines

Coinnect has two interfaces built from day one:

**For humans:** A simple web interface at coinnect.bot. Enter amount, origin currency, destination currency. Get a ranked table of routes. Click any route for step-by-step instructions. No account required.

**For machines:** A public REST API returning the same data as JSON. Any AI agent, chatbot, or automated system can query Coinnect as a tool and route payments optimally without human intervention.

```
GET https://api.coinnect.bot/v1/quote?from=USD&to=NGN&amount=500
```

This is the infrastructure layer that today doesn't exist: an open, neutral, machine-readable exchange router.

---

## 3. Why Non-Profit

### 3.1 The alignment problem

Every for-profit comparison platform faces the same structural problem: the business model eventually compromises the product. Affiliate commissions, promoted listings, premium placements — these are not malicious choices, they are business necessities. But they introduce bias into what should be a purely informational service.

A non-profit doesn't have this problem. The only metric that matters is accuracy.

### 3.2 Sustainability through donations

Coinnect is funded entirely by voluntary donations from users who save money using the platform. The logic is simple: if we save you $20 on a transfer, a $1 donation is a 2000% return for you and keeps the service running for everyone.

No advertising. No affiliate fees. No investor expectations. No exit.

### 3.3 Infrastructure cost

Coinnect is designed to run at minimal cost:

| Layer | Service | Cost/month |
|-------|---------|-----------|
| API + cron jobs | Cloudflare Workers | $5 |
| Quote engine (2 regions) | Fly.io shared instances | ~$14 |
| Rate cache | Upstash Redis (serverless) | $0–10 |
| Analytics | Turso (SQLite edge) | $0–8 |
| Frontend | Cloudflare Pages | $0 |
| **Total** | | **$28–37/mo** |

At $28/month of infrastructure, Coinnect can serve hundreds of thousands of users per month. A single $25 monthly donor covers the entire server cost. This is not a sustainability risk — it is a structural advantage over any VC-backed competitor that needs to monetize at scale.

### 3.4 Transparent compensation

The founder's compensation and all operational expenses are published publicly. The founding statutes establish a hard cap on founder compensation tied to the organization's annual budget. Financial reports are published quarterly.

---

## 4. Exchanges — Inclusion Criteria

Coinnect includes any exchange that meets three criteria:

1. **Has a public, documented API** — we can query rates programmatically
2. **Is regulated in at least one jurisdiction** — reduces counterparty risk for users
3. **Has no credible fraud or insolvency history** — basic user protection

We do not charge exchanges to be listed. We do not accept payment for rankings. Any exchange that meets the criteria is included. Any exchange that fails the criteria is excluded — regardless of who they are.

### 4.1 Launch exchange set (MVP)

| Exchange | Type | Corridors | Notes |
|----------|------|-----------|-------|
| Western Union | Traditional remittance | 200+ countries | The expensive baseline — showing the comparison |
| MoneyGram | Traditional remittance | 200+ countries | Same — their pricing validates the problem |
| Wise | Fiat transfer | 80+ currencies | Best mid-tier fiat option |
| Coinbase | Crypto exchange | USD, EUR, major crypto | Regulated, excellent API, US anchor |
| Kraken | Crypto exchange | USD, EUR, major crypto | Regulated, reliable |
| Binance | Crypto exchange | Global | Largest liquidity, USDC routing |
| Bitso | LatAm crypto | MXN, ARS, BRL, USD | Leading LatAm exchange |
| Yellow Card | Africa crypto | NGN, GHS, KES, ZAR | Africa's leading regulated exchange |
| Lemon Cash | LatAm crypto | ARS | Argentina-native |

**Why include Western Union and MoneyGram?** Because the comparison only makes sense when you can see the full spectrum. When Coinnect shows that a USDC route saves you $22 versus Western Union on the same corridor, the value proposition is immediate and concrete. We include them not to attack them — but because completeness is honesty.

More exchanges added as APIs are verified and criteria confirmed.

---

## 5. Technical Architecture

### 5.1 The quote engine

At its core, Coinnect runs a shortest-path algorithm across a live graph where:
- **Nodes** = currencies (USD, MXN, USDC, NGN, PHP, etc.)
- **Edges** = exchange pairs with real-time fee and rate data
- **Weight** = total cost (fees + spread) or total time, depending on user preference

The engine refreshes rates every few minutes via exchange APIs and caches results for performance.

### 5.2 API design

The API is designed to be consumed by both developers and AI agents:

```
GET  /v1/quote         — Get ranked routes for a transfer
GET  /v1/exchanges     — List all integrated exchanges
GET  /v1/corridors     — Most active currency pairs
GET  /v1/health        — API status
```

Full OpenAPI specification published at launch. Any AI agent (Claude, GPT, Gemini, or local models) can call these endpoints as tools.

### 5.3 Machine-readable by design

Coinnect is built for the emerging world of autonomous agents making financial decisions. This requires speaking the languages that machines already use.

**The standards Coinnect supports:**

| Standard | What it is | Who uses it |
|----------|-----------|-------------|
| **OpenAPI 3.0** | Machine-readable API specification | All HTTP clients, any language |
| **JSON Schema** | Data structure validation | Universal |
| **OpenAI Tool format** | Function definition for AI agents | GPT-4, GPT-4o and compatible |
| **Anthropic Tool Use** | Same concept, Claude's format | Claude 3+ |
| **MCP (Model Context Protocol)** | Anthropic's emerging standard for AI↔tool connections | Claude Code, early adopters |

Any AI agent that can make an HTTP request can use Coinnect today. Any agent built on major AI frameworks (LangChain, LlamaIndex, AutoGen) can use it as a tool with a single function definition.

**Example tool definition (OpenAI/Claude format):**
```json
{
  "name": "coinnect_quote",
  "description": "Find the cheapest routes to send money between currencies. Returns ranked routes with fees, exchange rates, and step-by-step instructions.",
  "parameters": {
    "from_currency": "string — ISO 4217 code (USD, MXN, NGN...)",
    "to_currency": "string — ISO 4217 code",
    "amount": "number — amount in from_currency"
  }
}
```

A user tells an AI agent: _"I need to send $500 to my sister in Kenya."_ The agent calls `coinnect_quote`, receives the ranked routes as JSON, and responds in natural language with the best option. No human needs to open a browser.

This is the machine gap Coinnect fills: not payment execution, but **payment intelligence** — freely available, openly documented, permanently neutral.

### 5.4 No custody, no KYC

Coinnect never holds funds, never processes payments, and never collects user identity information. Each exchange handles its own KYC requirements. Coinnect is purely informational — legally and technically.

---

## 6. Legal & Regulatory

### 6.1 What Coinnect is not

Coinnect is a **price comparison and routing information service**. It is not:

- A money transfer operator (MTO)
- A payment processor
- A cryptocurrency exchange
- A financial advisor
- A custodian of any kind

Coinnect never holds user funds, never processes transactions, and never has access to user wallets or accounts. Every transfer is executed entirely by the third-party exchange the user chooses to use, under that exchange's own regulatory framework.

### 6.2 Regulatory classification

In most jurisdictions, a service that provides publicly available pricing information and routing recommendations — without executing, facilitating, or touching transactions — does not require a money services business (MSB) license or equivalent.

This mirrors the legal position of price comparison services like Google Flights (which shows flight prices without being an airline) or Monito (which compares transfer fees without being a remittance service).

Users are responsible for complying with the regulations of their own jurisdiction and the KYC/AML requirements of each exchange they choose to use. Coinnect does not provide legal or financial advice.

### 6.3 Data privacy

Coinnect does not collect personal information. Quote requests include only currency types and amounts — no user identity, no wallet addresses, no IP logging. Optional analytics (GA4, opt-out available via `/?notrack`) collect only aggregate usage patterns.

---

## 7. Roadmap

| Phase | Timeline | Milestone |
|-------|----------|-----------|
| 0 — Foundation | March 2026 | White paper, GitHub repo, coinnect.bot live |
| 1 — MVP | April 2026 | Quote API live, 8 exchanges, USD/MXN/BRL/ARS/NGN/PHP/KES |
| 2 — Public launch | May 1, 2026 | Web UI, public API, MCP server, donation wallet |
| 3 — Community | Q3 2026 | User-contributed exchange reviews, rate accuracy feedback |
| 4 — Ecosystem | Q4 2026 | Stellar anchors (M-Pesa, Wave, GCash), `pip install coinnect-tool` |
| 5 — Global | 2027 | 30+ exchanges, 50+ currencies, Africa + Asia full coverage |

---

## 8. The Founder

[Miguel V.](https://www.linkedin.com/in/miguelvalenciav/) built Coinnect because the problem is real, the solution is simple, and nobody was building it without a business model attached.

His public donation wallet is listed on coinnect.bot. His compensation is capped by the founding statutes and published quarterly. He has no equity to sell, no investors to answer to, and no exit to plan.

He intends to do this for as long as it is useful.

---

## 9. Vision

Before GPS, every driver carried a road atlas. It didn't drive. It didn't own the roads. It had no preference for which highway you took. You trusted it precisely because it had no stake in your route — it just knew every path and showed you all of them.

Then came Waze: the same neutrality, but live, collaborative, self-updating — and eventually, consulted by autonomous vehicles without any human in the loop.

That is the arc of Coinnect.

Today: we show you the map.
Tomorrow: the map updates itself with community data.
Eventually: machines consult it automatically, and money moves at its natural cost — without anyone being able to extract a tax from ignorance.

**The money already knows how to move. Coinnect shows it the cheapest way.**

---

*This document is version 0.3. It will be updated publicly as the project develops.*
*All feedback welcome at miguel@coinnect.bot*
