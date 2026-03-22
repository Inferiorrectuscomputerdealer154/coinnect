# Money Routing Protocol (MRP) — Draft Specification v0.1

> **Status:** Draft · Maintained by the Coinnect project · Open for comment
>
> Coinnect is the reference implementation of MRP. The protocol is implementation-agnostic — anyone may build a compatible router, aggregator, or client.

---

## 1. What is MRP?

The **Money Routing Protocol** is an open specification for describing, querying, and ranking multi-step money transfer paths between any two currencies.

It is to money transfers what BGP is to internet routing: a shared language for finding optimal paths across a fragmented, multi-provider network — without any single entity controlling the path or taking custody of funds.

MRP defines:
- A standard **Edge** data model (one conversion step)
- A standard **Route** response format (ranked multi-step paths)
- A standard **Quote API** contract (`GET /v1/quote`)
- A standard **Corridor listing** format (`GET /v1/corridors`)
- A provider **listing standard** (how exchanges declare their edges)

---

## 2. Core data model

### 2.1 Edge

An Edge represents one conversion step between two currencies via one provider.

```json
{
  "from_currency": "USD",
  "to_currency": "MXN",
  "via": "Wise",
  "fee_pct": 2.1,
  "exchange_rate": 17.42,
  "estimated_minutes": 60,
  "min_amount": 1.0,
  "max_amount": 100000.0,
  "instructions": "Bank transfer via Wise — direct deposit",
  "live": true
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `from_currency` | string (ISO 4217) | ✓ | Source currency |
| `to_currency` | string (ISO 4217) | ✓ | Destination currency |
| `via` | string | ✓ | Provider name |
| `fee_pct` | float | ✓ | Total cost as % of sent amount (fee + spread combined) |
| `exchange_rate` | float | ✓ | Units of `to_currency` per 1 `from_currency`, after fees |
| `estimated_minutes` | int | ✓ | Median transfer time in minutes |
| `min_amount` | float | ✓ | Minimum send amount in `from_currency` |
| `max_amount` | float | ✓ | Maximum send amount in `from_currency` |
| `instructions` | string | ✓ | Human-readable step description |
| `live` | bool | | `true` if rate is from live API, `false`/absent if estimated |

**Note on `fee_pct`:** This is the all-in cost — exchange rate margin plus any fixed or percentage transfer fees, normalized to a percentage of the sent amount. For a $500 transfer with a 1% fee + 0.5% spread, `fee_pct = 1.5`.

### 2.2 Route

A Route is an ordered sequence of Edges forming a complete transfer path.

```json
{
  "rank": 1,
  "label": "Cheapest",
  "total_cost_pct": 1.2,
  "total_time_minutes": 75,
  "you_send": 500.0,
  "they_receive": 8692.00,
  "they_receive_currency": "MXN",
  "steps": [ /* array of Steps, one per Edge */ ]
}
```

### 2.3 Quote response

```json
{
  "from_currency": "USD",
  "to_currency": "MXN",
  "amount": 500.0,
  "generated_at": "2026-03-22T00:00:00Z",
  "routes": [ /* ordered by total_cost_pct ascending */ ]
}
```

---

## 3. API contract

### 3.1 Quote endpoint

```
GET /v1/quote?from={ISO}&to={ISO}&amount={float}
```

Returns routes ranked by `total_cost_pct` ascending. The response MUST include at minimum the cheapest and fastest routes when they differ.

**Headers:**
- `X-Api-Key` (optional): API key for higher rate limits

**Errors:**
- `404`: No routes found for this corridor
- `503`: Exchange data temporarily unavailable

### 3.2 Corridors endpoint

```
GET /v1/corridors
```

Returns a list of supported currency pairs with example providers.

### 3.3 Health endpoint

```
GET /v1/health
```

Returns service status, version, and data freshness.

---

## 4. Provider listing standard

Any exchange or remittance provider that wishes to be indexed by an MRP-compatible router MUST provide at minimum:

1. **Published pricing page** — fee structure and rate margins publicly accessible
2. **Corridor list** — supported currency pairs with min/max send amounts
3. **Payment methods** — what the sender and recipient need (bank account, mobile money, cash, crypto wallet)
4. **Rate freshness** — how often rates are updated; if no API, a commitment to notify on pricing changes

Providers with public rate APIs receive a `"live": true` flag in Edge responses. Providers without APIs are included with `~est.` in instructions and a `"live": false` flag.

**To request listing:** Open an issue at the Coinnect GitHub repository or email hello@coinnect.bot with your corridor list and pricing documentation.

---

## 5. Routing algorithm

MRP routers MUST implement at minimum:

1. **Graph construction:** Build a directed graph where nodes are currencies and edges are provider steps
2. **Multi-hop traversal:** Support paths up to 3 hops (e.g. USD → USDC → MXN)
3. **Cost calculation:** `total_cost_pct` is the compound cost of all steps:
   - `total_cost = 1 - product((1 - fee_i/100) for each step i)`
4. **Amount filtering:** Exclude edges where `amount < min_amount` or `amount > max_amount`
5. **De-duplication:** Return at most one route per unique provider combination

Routers SHOULD rank by `total_cost_pct` ascending as the primary sort, with a "Fastest" label for the minimum-time route.

---

## 6. Governance (proposed)

MRP is designed as a community standard. The reference implementation (Coinnect) is maintained by its founder under MIT license.

**Proposed governance model:**
- **Working Group:** Open to financial inclusion researchers, fintech developers, remittance operators, and NGOs
- **Decisions:** Rough consensus (IETF model) for protocol changes
- **Versioning:** Semantic versioning; breaking changes require a new major version
- **Chair:** Founder maintains chair role while project is pre-foundation; role is transferable

**How to participate:**
- GitHub discussions at the Coinnect repository
- Email hello@coinnect.bot to join the working group mailing list

---

## 7. Vision

Global remittances move ~$800B/year. Most people sending money across borders pay 5–10% in fees because they have no easy way to compare all options. Banks, crypto rails, mobile money, and P2P platforms all offer different rates for different corridors — but there is no common language for routing across them.

MRP is an attempt to create that common language: a neutral, open, non-profit standard that benefits senders, recipients, and the broader financial inclusion mission — the same way HTTP benefited the open web.

We are not building a payment network. We are building the map.

---

*Draft v0.1 · March 2026 · Coinnect project · MIT License*
*Feedback welcome: hello@coinnect.bot*
