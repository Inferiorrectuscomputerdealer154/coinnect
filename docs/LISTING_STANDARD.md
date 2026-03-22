# Coinnect Exchange Listing Standard

> **Version:** 1.0 · March 2026
> Part of the [Money Routing Protocol (MRP)](PROTOCOL.md) specification.

Coinnect lists exchanges and remittance providers so that users can find the cheapest route to send money. This document defines what information a provider must supply to be listed, and how Coinnect ranks and displays them.

---

## Principles

1. **Neutral ranking** — routes are ranked by cost to the sender, always. Coinnect does not accept affiliate fees, referral commissions, or paid placements.
2. **Transparency** — all listed providers must have publicly accessible pricing documentation. Opaque fees disqualify a provider.
3. **No exclusivity** — being listed does not grant exclusive treatment. Being unlisted does not penalize a provider.
4. **Live over estimated** — providers with live rate APIs are labeled `live: true`. Estimated rates are labeled `~est.` and ranked last when cost is equal.

---

## Minimum requirements for listing

### 1. Public pricing documentation

Your fees and exchange rate margins must be findable by any user without logging in or creating an account. A pricing page URL is required.

Acceptable: a public webpage, a PDF, or a published API spec.
Not acceptable: pricing disclosed only after signup, or "contact us for rates."

### 2. Corridor list

Provide a list of supported currency pairs (corridors) with:

| Field | Type | Required | Example |
|-------|------|----------|---------|
| `from_currency` | ISO 4217 | ✓ | `USD` |
| `to_currency` | ISO 4217 | ✓ | `MXN` |
| `min_send` | float | ✓ | `1.00` |
| `max_send` | float | ✓ | `10000.00` |
| `payment_methods_in` | string[] | ✓ | `["bank_transfer", "debit_card"]` |
| `payment_methods_out` | string[] | ✓ | `["bank_deposit", "cash_pickup"]` |
| `estimated_minutes` | int | ✓ | `60` |

Corridors not in this list will not be displayed, even if the provider technically supports them.

### 3. Fee structure

Provide your all-in cost as a percentage of the sent amount, combining:

- Transfer fee (flat or %)
- Exchange rate margin (spread over mid-market rate)

**Example:** "1% fee + 0.5% spread = 1.5% total" → `fee_pct: 1.5`

If your fees vary by payment method or corridor, provide the range and Coinnect will display the best available rate with a `~est.` label until a live API is available.

### 4. Rate freshness

Specify how often your rates are updated. Options:

| Update frequency | Label shown | `live` flag |
|-----------------|-------------|-------------|
| Real-time API | (no label) | `true` |
| Hourly or less | `~est.` | `false` |
| Daily | `~est.` | `false` |
| Less than daily | Not eligible for listing | — |

If you have a public rate API, Coinnect will integrate it directly for live rates.

### 5. Contact for updates

Provide an email or webhook for rate change notifications. When your fees change, Coinnect must be able to update within 24 hours to avoid showing stale data.

---

## How to apply

**Email:** hello@coinnect.bot
**Subject:** `Exchange listing request — [Your Provider Name]`

**Include:**
1. Provider name and website
2. Pricing page URL
3. Corridor list (CSV, JSON, or spreadsheet — any format is fine)
4. Contact email for rate updates
5. Public API documentation (if available)

No application fee. No SLA on review time — Coinnect is maintained by a small team. Expect a response within 5–10 business days.

---

## What happens after you apply

1. We review your pricing documentation for completeness and public accessibility
2. We add your corridors to the `ALL_STATIC_PROVIDERS` list with `~est.` labels
3. If you have a public API, we integrate it for live rates (labeled `live: true`)
4. We notify you when your provider goes live in the index

---

## Maintenance obligations

Once listed, you are expected to:

- Notify hello@coinnect.bot within 48 hours if your fee structure changes significantly (>0.5% change)
- Respond to accuracy complaints raised by users within 10 business days
- Maintain publicly accessible pricing documentation at all times

**Failure to maintain accurate rates** will result in your provider being marked `stale` or removed from the index. We will attempt to notify you first.

---

## Grounds for removal

A provider may be removed if:

- Pricing becomes inaccessible or undisclosed
- Fee changes are not communicated and rates are materially wrong for more than 7 days
- The provider ceases to operate in a listed corridor
- The provider requests favorable ranking in exchange for payment or other arrangement

Removal is reversible — if the issue is resolved, reapply.

---

## Data format for programmatic submission

If you'd like to submit corridor data in a structured format for direct import:

```json
{
  "provider": "YourProvider",
  "website": "https://yourprovider.com",
  "pricing_url": "https://yourprovider.com/pricing",
  "contact": "rates@yourprovider.com",
  "corridors": [
    {
      "from_currency": "USD",
      "to_currency": "MXN",
      "fee_pct": 1.5,
      "exchange_rate": 17.42,
      "estimated_minutes": 60,
      "min_send": 1.0,
      "max_send": 10000.0,
      "payment_methods_in": ["bank_transfer", "debit_card"],
      "payment_methods_out": ["bank_deposit"],
      "live": false
    }
  ]
}
```

This is the same format as the MRP [Edge schema](PROTOCOL.md#21-edge), extended with provider metadata.

---

## A note on neutrality

Coinnect was built because there is no neutral, open tool that shows you the cheapest way to send money globally. We intend to stay that way.

If you notice that your provider is ranked unfairly — either too high or too low — please reach out. Accuracy is the point.

---

*Version 1.0 · March 2026 · MIT License · hello@coinnect.bot*
