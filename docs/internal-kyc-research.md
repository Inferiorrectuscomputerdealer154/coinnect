# KYC/Identity Requirements Research — Provider-by-Provider

**Last updated:** 2026-03-24
**Purpose:** Factual reference for Coinnect's routing logic — what real people need to access each service.

---

## Summary Table: Crypto Exchanges

| Provider | Min ID Required | SSN Required | Bank Acct Required | No-KYC Tier | No-KYC Withdrawal Limit | Proof of Address | Notes |
|----------|----------------|--------------|-------------------|-------------|------------------------|-----------------|-------|
| **Binance** | Gov ID + selfie | No (not US) | No | Effectively none | ~0 (KYC mandatory for trading/withdrawals since 2023) | For advanced tier | KYC mandatory for all trading. Intermediate = gov ID + face scan. Advanced = +proof of address for higher limits. |
| **OKX** | Gov ID + selfie | No | No | Level 1 (basic info only) | 5,000 USDT/day (L1) | Level 3 only | L1: email + basic details = 5K USDT/day. L2: gov ID + face = 500K/day. L3: +proof of address = unlimited. |
| **MEXC** | Email + phone | No | No | Yes (email only) | 10 BTC/day (varies by region, some report 1,000 USDT/day) | No (even with KYC) | Most permissive major exchange. No KYC needed for spot trading. 2026: TIN required for airdrops/Kickstarter due to CARF. Primary KYC = 80 BTC/day. Advanced = 200 BTC/day. |
| **KuCoin** | Gov ID + face verification | No | No | Effectively none | ~1 BTC/day (legacy, restricted) | No | KYC mandatory since Aug 2023. Unverified legacy accounts limited to sell/redeem only. Verified = 999,999 USDT/day. |
| **Kraken** | Name + DOB + phone (Starter) | No (unless US) | No | Starter tier (minimal) | Limited crypto only (no fiat) | Intermediate+ | Starter = name, DOB, country, phone. Intermediate = gov ID, enables fiat. Pro = financial docs for highest limits. |
| **Coinbase** | Gov ID + selfie | Last 4 of SSN (US) | No (but needed for fiat) | None | N/A — full KYC mandatory | Yes (sometimes) | Fully regulated US exchange. SSN (last 4) required for US residents. Gov ID + selfie mandatory. No anonymous trading. |
| **Bybit** | Gov ID + selfie | No | No | Effectively none | 20,000 USDT/day (non-KYC legacy) | Advanced tier | Standard KYC mandatory since May 2023. L1 (gov ID + selfie) = 1M USDT/day. L2 (+address) = 2M/day. |
| **Gate.io** | Gov ID + selfie | No | No | Deposit only | 0 withdrawals without KYC | KYC2 | Cannot withdraw without KYC. Can deposit up to 4 BTC/day without KYC. KYC1 = 2M/day withdrawal. KYC2 = 5M/day. |
| **Bitget** | Gov ID + selfie | No | No | None | N/A — KYC mandatory since Jan 2024 | Advanced tier | KYC mandatory for all trading, deposits, P2P. Primary verified = 3M USDT/day. |
| **Bitso (Mexico)** | INE/passport + CURP | No (RFC for tax) | No (but SPEI for MXN) | Limited (unverified) | Restricted deposits/withdrawals | Likely for higher tiers | Accepts INE (voter ID), passport, national biometric ID. CURP required. Verified = $6,000/month withdrawal. Mexico-focused. |
| **Buda (LatAm)** | Gov ID + selfie holding ID | No | Yes (local bank) | None | N/A — full KYC mandatory | Yes | Requires gov ID, selfie with ID, proof of address. Must have local bank account (Chile/Colombia/Peru/Argentina). Up to $10K/month once verified. 24-72h verification. |

---

## Summary Table: Remittance / Money Transfer

| Provider | Min ID Required | SSN Required | Bank Acct Required | Cash Option | Accepts Matricula Consular | Proof of Address | Notes |
|----------|----------------|--------------|-------------------|-------------|---------------------------|-----------------|-------|
| **Wise** | Gov ID (passport/DL/national ID) + selfie | SSN or ITIN (US residents) | Yes (for transfers) | No | No (standard gov IDs only) | Yes (utility bill <3 months) | Fully digital. SSN/ITIN required for US users for USD transfers and Wise card. No cash option. Bank account or card needed. |
| **Western Union** | Gov photo ID | No (for small cash sends) | No | Yes (send & receive cash) | Not confirmed (likely varies by agent) | No (for basic sends) | Can send cash in person with just a gov ID. No bank account, card, or membership needed. Receiver needs ID + MTCN tracking number. |
| **MoneyGram** | Gov photo ID | No (for cash) | No | Yes (send & receive cash) | **Yes — explicitly accepted** | Sometimes (if ID lacks address) | Specifically lists "Certificado de Matricula (Matricula Consular)" as accepted ID. Also accepts: Mexican Electoral Card, Border Crossing Card, Resident Alien Card, Seafarer ID, Welfare ID, Inmate exit ID. Most inclusive ID policy. |
| **Remitly** | Gov photo ID | Not confirmed | Yes (card or bank to send) | No (digital only) | Not confirmed | Yes (for large transfers) | App-based. Requires gov ID + selfie. Source of funds docs for large transfers. Receiver can get cash pickup, bank deposit, or mobile money. |
| **Ria** | Gov photo ID | SSN (for large in-store sends) | No | Yes (in-store cash) | Not confirmed | No (basic sends) | Can send cash in-store with gov ID. SSN may be required for larger amounts at store locations. Receiver needs gov photo ID + PIN. |
| **WorldRemit** | Gov ID (passport/national ID) | No | Yes (card or bank to send) | No (digital only) | No (passport/national ID/DL only) | Yes (utility bill <6 months) | Digital-only sender. Receiver can pick up cash. EU driving licenses not accepted. Verification usually <5 minutes. |
| **Global66** | Gov ID + selfie | No | Yes (for transfers) | No | Not confirmed | Not confirmed | LatAm-focused (Chile, Mexico, Colombia, Peru, Brazil, Argentina). Digital platform. Uses Jumio for identity verification. Gov ID + live selfie required. |
| **Strike** | Gov ID + selfie | Yes (US) | Yes (linked bank/card) | No | No | Not confirmed | Bitcoin/Lightning-focused. Full KYC required (US MSB). SSN required for US users. Enhanced KYC for transfers >$1,000. US-centric. |

---

## Key Findings

### Easiest access without full KYC (crypto):
1. **MEXC** — Still allows trading and withdrawals (up to 10 BTC/day in some regions) with just email. Most permissive major exchange as of 2026. Regional limits vary.
2. **Kraken Starter** — Name + DOB + phone number gets limited crypto access (no fiat). Least invasive "KYC" among regulated exchanges.
3. **OKX Level 1** — Basic info (no document upload) gets 5,000 USDT/day withdrawals.

### Exchanges that killed no-KYC access:
- **Binance** — Mandatory KYC for all trading since 2023
- **KuCoin** — Mandatory since Aug 2023
- **Bybit** — Mandatory since May 2023
- **Bitget** — Mandatory since Jan 2024
- **Gate.io** — Can deposit but cannot withdraw without KYC
- **Coinbase** — Always required full KYC

### Best for people without SSN (US context):
1. **MoneyGram** — Accepts matricula consular, no SSN needed for cash transfers
2. **Western Union** — Cash with gov ID, no SSN for small amounts
3. **Ria** — Cash in-store with gov ID (SSN only for large amounts)
4. **MEXC/OKX/Kraken** — No SSN needed (non-US exchanges)

### Best for people without bank accounts:
1. **Western Union** — Full cash-to-cash, no bank account needed
2. **MoneyGram** — Full cash-to-cash, most inclusive ID policy
3. **Ria** — Cash in-store option
4. **MEXC** — Crypto-only, no bank account needed for crypto deposits/withdrawals

### Accepts matricula consular (confirmed):
- **MoneyGram** — Explicitly listed
- **Many US banks/credit unions** — For account opening
- Western Union — Likely varies by agent location (not officially confirmed in current docs)

### Does NOT accept matricula consular:
- Coinbase, Wise, WorldRemit, Strike (standard gov IDs only)
- Federal agencies (USCIS, SSA, DHS)

### Proof of address requirements:
- **Required:** Wise, WorldRemit, Buda, Kraken (Intermediate+), Binance (Advanced), OKX (L3), Bybit (Advanced), Gate.io (KYC2)
- **Not required:** MEXC, MoneyGram (basic), Western Union (basic), Ria (basic)

---

## Implications for Coinnect

1. **The KYC gap is real.** Most major crypto exchanges now require full KYC. The window of no-KYC crypto access is closing fast. MEXC remains the notable exception but regional limits are tightening.

2. **Cash corridors still work.** Western Union and MoneyGram remain accessible to people with just a government ID and cash. No bank account, no SSN, no app needed. This is the baseline that crypto needs to match or beat.

3. **MoneyGram is the most inclusive.** Their explicit acceptance of matricula consular, welfare ID, inmate exit ID, and other non-standard documents makes them the most accessible for underbanked populations.

4. **The SSN barrier.** Coinbase, Wise, and Strike all require SSN/ITIN for US users. This excludes undocumented immigrants and recent arrivals who haven't obtained an ITIN yet.

5. **Proof of address is the hidden barrier.** Many services require utility bills or bank statements. People without stable housing, those in informal living situations, or newly arrived immigrants often cannot provide this.

6. **Coinnect's routing advantage.** By knowing these requirements per provider, Coinnect can route users to the path of least friction based on what documents they actually have. Someone with only a matricula consular gets routed to MoneyGram. Someone with email-only gets routed to MEXC. Someone with full docs gets the best rate across all providers.

---

## Sources

### Crypto Exchanges
- [Binance KYC Requirements 2026](https://scribehow.com/page/Binance_KYC_Requirements_2026_Documents_Steps_and_FAQs___HWqhBelzQIisDiQdlC0uIA)
- [Binance Lowers Daily Withdrawal Limit for Non-KYC Accounts](https://gordonlaw.com/learn/binance-daily-withdrawal-limit-kyc/)
- [Does Binance Require KYC in 2025?](https://cashandcoffeeclub.com/does-binance-require/)
- [OKX KYC Requirements Guide](https://www.okx.com/en-us/learn/okx-kyc-requirements-guide)
- [OKX Withdrawal Limits and KYC Guide](https://www.ukcamo.com/6769.html)
- [MEXC KYC Complete Guide](https://www.mexc.com/learn/article/does-mexc-require-kyc-complete-guide-to-mexc-kyc-verification/1)
- [MEXC Deposit & Withdrawal Guide](https://www.mexc.com/learn/article/mexc-deposit-withdrawal-guide-fees-limits-kyc-requirements-faq/1)
- [MEXC KYC Explained — BitDegree](https://www.bitdegree.org/crypto/tutorials/mexc-kyc)
- [KuCoin KYC Requirements 2026 — BitDegree](https://www.bitdegree.org/crypto/tutorials/kucoin-kyc-requirements)
- [KuCoin Identity Verification Guide](https://www.kucoin.com/support/360015102254)
- [Kraken Verification Levels and Limits](https://support.kraken.com/articles/verification-levels-and-limits)
- [Kraken Verification Level Requirements](https://support.kraken.com/articles/201352206-verification-level-requirements)
- [Coinbase KYC Verification](https://www.coinbase.com/en-gb/blog/know-your-customer-kyc-verification)
- [Bybit KYC Levels](https://www.bybit.com/en/help-center/article/Benefits-of-Different-KYC-Levels)
- [Bybit KYC Requirements — Bitget](https://www.bitget.com/academy/bybit-kyc-limits)
- [Gate.io KYC Procedures](https://www.gate.com/help/guide/account/17399/About-Identity-Verification-KYC-Procedures)
- [Bitget KYC Guide](https://www.bitget.com/academy/bitget-kyc-guide)
- [Bitso Review 2026 — FXEmpire](https://www.fxempire.com/crypto/exchange/bitso/review)
- [How to Use Bitso in Mexico](https://blog.bitso.com/blog/how-to-use-bitso-in-mexico)
- [Buda Crypto Exchange Review](https://arristor.com/buda-crypto-exchange-review-best-for-latin-american-traders-in)
- [Buda AML/KYC Policies](https://www.buda.com/politicas-kyc-aml)

### Remittance / Money Transfer
- [Wise Getting Verified in the US](https://wise.com/help/articles/2747380/getting-verified-in-the-us)
- [Wise Identity Verification](https://wise.com/help/articles/2949801/how-does-wise-verify-my-identity)
- [Western Union Acceptable Documents for Pickup](https://wucare.westernunion.com/s/article/What-are-the-acceptable-documents-to-pick-up-a-money-transfer?language=en_US)
- [Western Union FAQ](https://www.westernunion.com/cf/en/frequently-asked-questions.html)
- [MoneyGram ID Requirements](https://www.moneygram.com/us/en/help-center/faq/send-receive/general-questions/why-does-moneygram-require-me-to-provide-identification)
- [MoneyGram ID for Cash Pickup (Colombia)](https://www.moneygram.com/r/co/en/help-center/faq/app-info/profile-help-troubleshooting/what-kind-of-id-do-i-need-to-withdraw-cash)
- [Remitly Verification Process](https://help.remitly.com/s/article/verification-process?language=en_US)
- [Ria — What Details to Send Money](https://help.riamoneytransfer.com/hc/en-us/articles/4406286465297-What-details-do-I-need-to-send-money)
- [Ria — Cash Pickup Requirements](https://help.riamoneytransfer.com/hc/en-us/articles/4406058323601-What-does-my-recipient-need-to-pickup-a-cash-money-transfer)
- [WorldRemit Identity Verification FAQ](https://www.worldremit.com/en-us/faq/verification)
- [Global66 + Jumio Case Study](https://www.jumio.com/case-study-global66/)
- [Strike FAQ](https://strike.me/faq/)
- [Strike Compliance — InnReg](https://www.innreg.com/resources/case-studies/strike)
- [Matricula Consular Explained — CitizenPath](https://citizenpath.com/mexican-matricula-consular-card/)
