# Coinnect — Sustainability & Funding Policy

> This document establishes how Coinnect is funded, how funds are allocated,
> and the compensation terms for the founding maintainer. It is public, versioned,
> and binding on any entity that manages Coinnect funds.

---

## Principles

1. **Coinnect is free for end users — always.** No paywalls, no affiliate fees, no ads.
2. **Sustainability does not compromise neutrality.** Routes are ranked by cost to the sender, not by what earns Coinnect revenue.
3. **Compensation is transparent and rule-bound.** The maintainer's salary is public, capped, and tied to organizational revenue — not granted unilaterally.
4. **Funding is diversified.** No single donor or institutional relationship should have undue influence over the protocol.

---

## Revenue sources

| Source | Use |
|--------|-----|
| Individual donations (GitHub Sponsors, Buy Me a Coffee, crypto) | Maintainer salary + infrastructure |
| Foundation grants | Infrastructure, research, working group stipends |
| High-volume API (future) | Infrastructure + sustainability fund |
| Institutional partnerships | Protocol research only — no route ranking influence |

Coinnect does **not** accept:
- Revenue from providers listed in its index (no affiliate arrangements)
- VC investment or equity arrangements
- Payments in exchange for favorable route rankings

---

## Founder / maintainer compensation

### Policy

The founding maintainer (Miguel Valencia, `@miguelvalenciav`) is entitled to a salary for full-time development and stewardship of Coinnect. The salary is governed by these rules:

**Starting salary:** USD 2,500/month (USD 30,000/year)

**Cap rule:** The maintainer salary shall not exceed **10% of total annual organizational revenue** in any given year. If revenue is insufficient, the unpaid portion accrues as deferred compensation to be paid when revenue allows, with no interest.

**Growth rule:** The target salary scales with organizational size, benchmarked against the compensation of the executive director of a non-profit organization of equivalent budget and impact. At the scale of a major open internet foundation (annual budget > USD 50M), the target salary may reach USD 200,000/year. Adjustments require a public governance decision with at least 30 days of community notice.

**Inflation / cost-of-living:** Salary may be adjusted annually by CPI or equivalent cost-of-living index, with no governance vote required, up to a maximum of 8% per year.

**No other equity:** The maintainer holds no equity, tokens, or other financial instruments tied to the project. Compensation is salary only.

### Rationale

Open-source infrastructure is labor. Coinnect routes billions of dollars in potential transfers; its maintainer should be compensated accordingly — but only to the extent the organization can afford it, and only transparently. This policy follows the model of organizations like Mozilla Foundation, Wikimedia Foundation, and Signal Foundation.

---

## Budget allocation (target)

Once Coinnect has a legal entity or fiscal sponsor:

| Category | Target allocation |
|----------|------------------|
| Maintainer salary | ≤ 10% of revenue |
| Infrastructure (servers, APIs, monitoring) | ≤ 15% of revenue |
| Working group stipends / contributor grants | ≤ 25% of revenue |
| Research & protocol development | ≤ 20% of revenue |
| Reserve fund (3–6 months operating) | ≥ 30% of revenue |

---

## Accepted donations

### Crypto

| Asset | Network | Address |
|-------|---------|---------|
| ETH | Ethereum mainnet | `0xf0813041b9b017a88f28B8600E73a695E2B02e0A` |
| USDC | Polygon (recommended) | `0xf0813041b9b017a88f28B8600E73a695E2B02e0A` |
| BNB | BNB Smart Chain | `0xf0813041b9b017a88f28B8600E73a695E2B02e0A` |
| BTC | Bitcoin | `bc1q7jxdfgv6gacyx5vmmnz2nekxhptxym69ducaqz` |

USDC on Polygon is preferred for small donations — fees under $0.01. ETH mainnet for larger amounts.

> **Why USDC over USDT?** USDC is issued by Circle, subject to US regulatory oversight, with monthly audited reserves. It is more appropriate for a transparent non-profit treasury.

> **Why not privacy coins (ZCASH, Monero)?** Transparency is a core value of this organization. All treasury activity is publicly verifiable on-chain.

### Fiat

- **GitHub Sponsors:** github.com/sponsors/miguelvalenciav
- **Buy Me a Coffee:** buymeacoffee.com/miguelvalenciav

Fiat donations fund maintainer salary first, then infrastructure.

---

## Open data policy

Historical rate snapshots captured by Coinnect are published as open data under **CC-BY 4.0**:

- API: `GET /v1/snapshot/daily?date=YYYY-MM-DD`
- Available dates: `GET /v1/snapshot/meta`

This data may be freely used for research, training, or analysis. Citation requested:
> *Coinnect Open Rate Data (coinnect.bot), CC-BY 4.0*

---

## Fiscal status

Coinnect is currently an unincorporated open-source project maintained by Miguel Valencia. It is seeking a fiscal sponsor (e.g., Open Source Collective, NLnet, or a dedicated legal entity) to handle formal grant management and treasury governance.

Until a fiscal sponsor is established, all funds are managed transparently and reported publicly.

---

## Questions or proposals

Contact: **hello@coinnect.bot**

For institutional funding discussions, include "Funding proposal" in the subject line.

---

*Last updated: March 2026 · Version 1.0 · MIT License*
