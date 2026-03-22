"""
Alternative remittance providers — static fee estimates.

These providers don't offer public rate APIs, so fees are researched from their
published pricing pages and updated manually. Exchange rates use open.er-api.com.

All edges produced here are labeled with "~est." in instructions to signal that
the fee is an approximation, not a live quote. Users should verify on provider's
site before transacting.

Sources: each provider's published pricing page, verified 2025-Q4 / 2026-Q1.
"""

import asyncio
import logging
import httpx
from coinnect.routing.engine import Edge

logger = logging.getLogger(__name__)

RATES_URL = "https://open.er-api.com/v6/latest/{base}"

# ── Provider corridor definitions ──────────────────────────────────────────
# Format: (from_currency, to_currency, fee_pct, estimated_minutes, note)
# fee_pct = total cost including exchange rate spread, not just the transfer fee

REMITLY_CORRIDORS: list[tuple] = [
    # Remitly — one of the largest remittance networks, 170+ countries
    # Fees: Economy tier (1–3 days). Express adds ~$3.99 fixed.
    ("USD", "MXN",  2.20, 1440,  "Remitly Economy — bank deposit in 1–3 days"),
    ("USD", "BRL",  2.80, 1440,  "Remitly Economy — bank/PIX deposit"),
    ("USD", "ARS",  3.80, 1440,  "Remitly Economy — bank deposit"),
    ("USD", "COP",  2.60, 1440,  "Remitly Economy — bank deposit"),
    ("USD", "PEN",  2.80, 1440,  "Remitly Economy — bank deposit"),
    ("USD", "NGN",  3.50, 2880,  "Remitly Economy — bank deposit"),
    ("USD", "KES",  2.80, 1440,  "Remitly Economy — M-Pesa or bank"),
    ("USD", "GHS",  3.20, 2880,  "Remitly Economy — mobile money or bank"),
    ("USD", "PHP",  2.00, 1440,  "Remitly Economy — bank or cash pickup"),
    ("USD", "INR",  1.20, 1440,  "Remitly Economy — bank transfer"),
    ("USD", "BDT",  2.40, 1440,  "Remitly Economy — bank deposit"),
    ("USD", "PKR",  2.60, 2880,  "Remitly Economy — bank deposit"),
    ("USD", "IDR",  2.30, 1440,  "Remitly Economy — bank deposit"),
    ("USD", "VND",  2.50, 1440,  "Remitly Economy — bank deposit"),
    ("USD", "LKR",  2.50, 1440,  "Remitly Economy — bank deposit"),
    ("USD", "THB",  2.00, 1440,  "Remitly Economy — bank deposit"),
    ("CAD", "PHP",  2.30, 1440,  "Remitly Economy — bank or cash pickup"),
    ("CAD", "INR",  1.50, 1440,  "Remitly Economy — bank deposit"),
    ("GBP", "PHP",  2.10, 1440,  "Remitly Economy — bank or cash pickup"),
    ("GBP", "INR",  1.30, 1440,  "Remitly Economy — bank deposit"),
    ("EUR", "PHP",  2.20, 1440,  "Remitly Economy — bank deposit"),
    ("EUR", "NGN",  3.80, 2880,  "Remitly Economy — bank deposit"),
    ("EUR", "INR",  1.60, 1440,  "Remitly Economy — bank deposit"),
]

WORLDREMIT_CORRIDORS: list[tuple] = [
    # WorldRemit — 130+ countries, strong in Africa/Asia
    ("USD", "NGN",  3.80, 2880,  "WorldRemit — bank deposit or mobile money"),
    ("USD", "KES",  3.20, 1440,  "WorldRemit — M-Pesa or bank"),
    ("USD", "GHS",  3.60, 2880,  "WorldRemit — mobile money or bank"),
    ("USD", "TZS",  3.50, 1440,  "WorldRemit — mobile money"),
    ("USD", "UGX",  3.60, 1440,  "WorldRemit — mobile money"),
    ("USD", "ZAR",  3.20, 1440,  "WorldRemit — bank deposit"),
    ("USD", "PHP",  2.80, 1440,  "WorldRemit — bank or cash pickup"),
    ("USD", "INR",  2.20, 1440,  "WorldRemit — bank transfer"),
    ("USD", "BDT",  2.80, 1440,  "WorldRemit — bank deposit"),
    ("USD", "PKR",  3.00, 2880,  "WorldRemit — bank deposit"),
    ("USD", "VND",  3.00, 1440,  "WorldRemit — bank deposit"),
    ("GBP", "NGN",  4.00, 2880,  "WorldRemit — bank deposit"),
    ("GBP", "KES",  3.40, 1440,  "WorldRemit — M-Pesa or bank"),
    ("GBP", "PHP",  2.90, 1440,  "WorldRemit — bank deposit"),
    ("EUR", "NGN",  4.20, 2880,  "WorldRemit — bank deposit"),
]

RIA_CORRIDORS: list[tuple] = [
    # Ria Money Transfer — Top 3 global network, 165+ countries, 490k+ locations
    ("USD", "MXN",  3.20, 30,   "Ria — cash pickup or bank deposit"),
    ("USD", "BRL",  4.00, 1440, "Ria — bank deposit"),
    ("USD", "COP",  3.50, 1440, "Ria — bank deposit or cash"),
    ("USD", "PHP",  3.50, 30,   "Ria — cash pickup or bank deposit"),
    ("USD", "INR",  2.80, 1440, "Ria — bank deposit"),
    ("USD", "NGN",  4.50, 2880, "Ria — bank deposit"),
    ("USD", "KES",  4.00, 1440, "Ria — bank or mobile money"),
    ("USD", "IDR",  3.80, 1440, "Ria — bank deposit"),
    ("USD", "GHS",  4.20, 2880, "Ria — cash or bank"),
    ("EUR", "MXN",  3.50, 30,   "Ria — cash pickup or bank deposit"),
    ("EUR", "PHP",  3.60, 30,   "Ria — cash pickup or bank deposit"),
    ("GBP", "PHP",  3.40, 30,   "Ria — cash pickup or bank deposit"),
]

SENDWAVE_CORRIDORS: list[tuple] = [
    # SendWave — Africa specialist, fee=0% but ~1.5% FX spread built in
    # One of the best rates for African corridors; owned by WorldRemit group
    ("USD", "KES",  1.50, 10,   "Sendwave — instant M-Pesa, no transfer fee"),
    ("USD", "UGX",  1.60, 10,   "Sendwave — MTN Mobile Money, no transfer fee"),
    ("USD", "TZS",  1.60, 10,   "Sendwave — mobile money, no transfer fee"),
    ("USD", "GHS",  1.80, 10,   "Sendwave — mobile money, no transfer fee"),
    ("USD", "NGN",  2.00, 30,   "Sendwave — bank or mobile money, no transfer fee"),
    ("USD", "SEN",  1.90, 30,   "Sendwave — mobile money, no transfer fee"),
    ("USD", "XAF",  2.00, 30,   "Sendwave — mobile money, no transfer fee"),
    ("EUR", "KES",  1.80, 10,   "Sendwave — instant M-Pesa, no transfer fee"),
    ("GBP", "KES",  1.70, 10,   "Sendwave — instant M-Pesa, no transfer fee"),
]

XOOM_CORRIDORS: list[tuple] = [
    # Xoom (PayPal) — 160+ countries, widely used in US diaspora
    ("USD", "MXN",  4.20, 60,   "Xoom (PayPal) — bank deposit or cash pickup"),
    ("USD", "BRL",  4.50, 1440, "Xoom (PayPal) — bank deposit"),
    ("USD", "COP",  4.00, 1440, "Xoom (PayPal) — bank deposit"),
    ("USD", "PHP",  3.80, 60,   "Xoom (PayPal) — bank or cash pickup"),
    ("USD", "INR",  2.80, 1440, "Xoom (PayPal) — bank deposit"),
    ("USD", "NGN",  5.00, 2880, "Xoom (PayPal) — bank deposit"),
    ("USD", "KES",  4.50, 1440, "Xoom (PayPal) — bank deposit"),
    ("USD", "VND",  4.20, 1440, "Xoom (PayPal) — bank deposit"),
    ("USD", "IDR",  4.50, 1440, "Xoom (PayPal) — bank deposit"),
    ("USD", "BDT",  4.00, 2880, "Xoom (PayPal) — bank deposit"),
    ("USD", "PKR",  4.50, 2880, "Xoom (PayPal) — bank deposit"),
]

PAYSEND_CORRIDORS: list[tuple] = [
    # Paysend — 160+ countries, card-to-card and bank, growing in LATAM/Africa
    ("USD", "MXN",  2.50, 30,   "Paysend — bank or card delivery"),
    ("USD", "COP",  2.80, 30,   "Paysend — bank delivery"),
    ("EUR", "MXN",  2.70, 30,   "Paysend — bank or card delivery"),
    ("EUR", "PHP",  2.50, 30,   "Paysend — card-to-card or bank"),
    ("EUR", "INR",  2.30, 30,   "Paysend — bank delivery"),
    ("GBP", "INR",  2.20, 30,   "Paysend — bank delivery"),
    ("GBP", "PHP",  2.40, 30,   "Paysend — card-to-card or bank"),
    ("USD", "NGN",  3.50, 1440, "Paysend — bank delivery"),
    ("USD", "KES",  3.20, 1440, "Paysend — bank or mobile money"),
    ("USD", "GHS",  3.50, 1440, "Paysend — bank delivery"),
    ("USD", "UGX",  3.60, 1440, "Paysend — mobile money"),
]

OFX_CORRIDORS: list[tuple] = [
    # OFX — best for large transfers (min ~$250), no transfer fee, tight FX spread
    # Targets freelancers, SMBs, property buyers
    ("USD", "AUD",  0.60, 1440, "OFX — bank wire, best for large amounts"),
    ("USD", "EUR",  0.50, 1440, "OFX — bank wire, no transfer fee"),
    ("USD", "GBP",  0.50, 1440, "OFX — bank wire, no transfer fee"),
    ("USD", "CAD",  0.55, 1440, "OFX — bank wire, no transfer fee"),
    ("USD", "SGD",  0.65, 1440, "OFX — bank wire"),
    ("USD", "NZD",  0.65, 1440, "OFX — bank wire"),
    ("USD", "JPY",  0.60, 1440, "OFX — bank wire"),
    ("USD", "CHF",  0.55, 1440, "OFX — bank wire"),
    ("USD", "HKD",  0.60, 1440, "OFX — bank wire"),
    ("EUR", "USD",  0.55, 1440, "OFX — bank wire, no transfer fee"),
    ("GBP", "USD",  0.55, 1440, "OFX — bank wire, no transfer fee"),
    ("AUD", "USD",  0.65, 1440, "OFX — bank wire"),
    ("EUR", "GBP",  0.50, 1440, "OFX — bank wire, no transfer fee"),
    ("GBP", "EUR",  0.50, 1440, "OFX — bank wire"),
]

TRANSFERGO_CORRIDORS: list[tuple] = [
    # TransferGo — Europe-focused, strong in Ukraine/Poland/Romania corridors
    # Popular with Eastern European migrant workers
    ("GBP", "PLN",  1.20, 60,   "TransferGo — bank deposit"),
    ("GBP", "UAH",  1.50, 60,   "TransferGo — bank deposit"),
    ("GBP", "RON",  1.30, 60,   "TransferGo — bank deposit"),
    ("EUR", "PLN",  1.10, 60,   "TransferGo — bank deposit"),
    ("EUR", "UAH",  1.50, 60,   "TransferGo — bank deposit"),
    ("EUR", "RON",  1.20, 60,   "TransferGo — bank deposit"),
    ("EUR", "HUF",  1.20, 60,   "TransferGo — bank deposit"),
    ("EUR", "CZK",  1.10, 60,   "TransferGo — bank deposit"),
    ("EUR", "INR",  2.00, 1440, "TransferGo — bank deposit"),
    ("EUR", "PHP",  2.20, 1440, "TransferGo — bank deposit"),
    ("GBP", "INR",  1.80, 1440, "TransferGo — bank deposit"),
    ("USD", "MXN",  2.50, 1440, "TransferGo — bank deposit"),
]

SKRILL_CORRIDORS: list[tuple] = [
    # Skrill — e-wallet popular in gaming/freelancer communities, 120+ countries
    # Fee: 1.45% transfer + ~1.5% FX spread = ~3% total typical
    ("USD", "EUR",  2.80, 30,   "Skrill — wallet or bank delivery"),
    ("USD", "GBP",  2.90, 30,   "Skrill — wallet or bank delivery"),
    ("EUR", "GBP",  2.70, 30,   "Skrill — wallet or bank delivery"),
    ("EUR", "USD",  2.80, 30,   "Skrill — wallet or bank delivery"),
    ("GBP", "EUR",  2.70, 30,   "Skrill — wallet or bank delivery"),
    ("USD", "MXN",  3.50, 1440, "Skrill — bank delivery"),
    ("EUR", "MXN",  3.60, 1440, "Skrill — bank delivery"),
    ("USD", "BRL",  4.00, 1440, "Skrill — bank delivery"),
    ("USD", "ARS",  4.50, 1440, "Skrill — bank delivery"),
    ("USD", "INR",  3.20, 1440, "Skrill — bank delivery"),
    ("EUR", "PLN",  2.00, 30,   "Skrill — wallet or bank delivery"),
]

REVOLUT_CORRIDORS: list[tuple] = [
    # Revolut Standard (free plan) — 0.5% weekday, 1% weekend, +markup over limits
    # We use 1.2% as a conservative typical estimate including FX spread
    # Best for EUR/GBP/USD <£1,000/month. Premium plans are cheaper.
    ("USD", "EUR",  1.20, 5,    "Revolut Standard — instant to Revolut, then bank"),
    ("USD", "GBP",  1.20, 5,    "Revolut Standard — instant to Revolut, then bank"),
    ("USD", "MXN",  1.80, 30,   "Revolut Standard — bank delivery"),
    ("USD", "BRL",  2.00, 30,   "Revolut Standard — bank delivery"),
    ("USD", "INR",  1.50, 60,   "Revolut Standard — bank delivery"),
    ("EUR", "USD",  1.20, 5,    "Revolut Standard — instant to Revolut, then bank"),
    ("EUR", "GBP",  1.10, 5,    "Revolut Standard — instant to Revolut"),
    ("EUR", "PLN",  1.30, 5,    "Revolut Standard — instant to Revolut, then bank"),
    ("EUR", "RON",  1.30, 5,    "Revolut Standard — bank delivery"),
    ("EUR", "MXN",  2.00, 30,   "Revolut Standard — bank delivery"),
    ("GBP", "EUR",  1.10, 5,    "Revolut Standard — instant"),
    ("GBP", "USD",  1.20, 5,    "Revolut Standard — instant"),
    ("GBP", "INR",  1.60, 60,   "Revolut Standard — bank delivery"),
    ("GBP", "PHP",  1.90, 60,   "Revolut Standard — bank delivery"),
]

ZINLI_CORRIDORS: list[tuple] = [
    # Zinli — US-based wallet focused on Venezuela/LatAm diaspora
    # Popular for USD→VES (sovereign bolivar). Fees ~1.5–2% total.
    ("USD", "VES",  1.80, 60,   "Zinli — wallet deposit, Venezuela"),
    ("USD", "COP",  1.70, 60,   "Zinli — bank or wallet"),
    ("USD", "PEN",  2.00, 60,   "Zinli — bank deposit"),
    ("USD", "MXN",  2.00, 60,   "Zinli — bank or wallet"),
    ("USD", "BRL",  2.20, 60,   "Zinli — bank deposit"),
]

LEMON_CASH_CORRIDORS: list[tuple] = [
    # Lemon Cash — crypto wallet, one of the largest in Argentina
    # Users buy USDC/USDT on-app with ARS, then transfer. ~1% spread.
    ("ARS", "USDC", 1.20, 5,    "Lemon Cash — buy stablecoin with ARS, instant"),
    ("ARS", "USDT", 1.20, 5,    "Lemon Cash — buy stablecoin with ARS, instant"),
    ("ARS", "BTC",  1.40, 5,    "Lemon Cash — buy BTC with ARS"),
]

MUKURU_CORRIDORS: list[tuple] = [
    # Mukuru — top remittance brand in southern/eastern Africa
    # Strong in ZAR-outbound migrant corridors. Fees ~3–5%.
    ("ZAR", "ZWL",  3.50, 60,   "Mukuru — cash pickup or mobile money in Zimbabwe"),
    ("ZAR", "MWK",  4.00, 60,   "Mukuru — cash pickup in Malawi"),
    ("ZAR", "MOZ",  4.00, 60,   "Mukuru — cash pickup in Mozambique (MZN)"),
    ("ZAR", "ZMW",  3.80, 60,   "Mukuru — cash pickup in Zambia"),
    ("ZAR", "NGN",  4.50, 1440, "Mukuru — bank deposit in Nigeria"),
    ("GBP", "ZWL",  3.80, 60,   "Mukuru — cash pickup in Zimbabwe"),
    ("USD", "ZWL",  3.50, 60,   "Mukuru — cash pickup in Zimbabwe"),
    ("USD", "ZAR",  3.00, 1440, "Mukuru — bank deposit in South Africa"),
]

MAMA_MONEY_CORRIDORS: list[tuple] = [
    # Mama Money — South Africa remittance specialist, migrant worker focus
    # Serves ZAR outbound to neighboring countries. Fees ~3–5%.
    ("ZAR", "ZWL",  3.20, 30,   "Mama Money — mobile money or cash, Zimbabwe"),
    ("ZAR", "MWK",  3.80, 60,   "Mama Money — mobile money, Malawi"),
    ("ZAR", "MZN",  3.80, 60,   "Mama Money — mobile money, Mozambique"),
    ("ZAR", "ZMW",  3.60, 60,   "Mama Money — mobile money, Zambia"),
    ("ZAR", "SZL",  3.00, 30,   "Mama Money — mobile money, Eswatini"),
]

GLOBAL66_CORRIDORS: list[tuple] = [
    # Global66 — Chilean fintech, "Wise of LatAm". 0.5–1.5% FX margin, no fixed fee.
    # Dominant brand in Chile; expanding across LatAm and into Spain/USA.
    # Sources: global66.com public rate page, verified 2026-Q1.
    ("USD", "CLP",  0.90, 60,   "Global66 — bank deposit in Chile (CLP)"),
    ("USD", "COP",  1.10, 60,   "Global66 — bank deposit in Colombia"),
    ("USD", "PEN",  1.00, 60,   "Global66 — bank deposit in Peru"),
    ("USD", "BRL",  1.50, 1440, "Global66 — bank deposit in Brazil"),
    ("USD", "MXN",  1.20, 60,   "Global66 — bank deposit in Mexico"),
    ("USD", "ARS",  1.50, 60,   "Global66 — bank deposit in Argentina"),
    ("EUR", "CLP",  1.00, 60,   "Global66 — bank deposit in Chile"),
    ("EUR", "COP",  1.20, 60,   "Global66 — bank deposit in Colombia"),
    ("EUR", "PEN",  1.10, 60,   "Global66 — bank deposit in Peru"),
    ("EUR", "MXN",  1.30, 60,   "Global66 — bank deposit in Mexico"),
    ("GBP", "CLP",  1.10, 60,   "Global66 — bank deposit in Chile"),
    ("CLP", "USD",  0.90, 60,   "Global66 — send CLP, receive USD"),
    ("CLP", "EUR",  1.00, 60,   "Global66 — send CLP, receive EUR"),
    ("COP", "USD",  1.10, 60,   "Global66 — send COP, receive USD"),
]


STRIKE_CORRIDORS: list[tuple] = [
    # Strike — Bitcoin/Lightning Network remittance app.
    # 0% platform fee on BTC sends; FX conversion ~0.5–1.5% spread.
    # Fast (Lightning: seconds) for BTC legs; final fiat delivery adds time.
    # Public API: developer.strike.me
    ("USD", "MXN",  1.00, 30,   "Strike — Lightning Network, bank deposit in Mexico"),
    ("USD", "BRL",  1.20, 60,   "Strike — Lightning Network, bank deposit in Brazil"),
    ("USD", "ARS",  1.00, 30,   "Strike — Lightning Network, bank deposit in Argentina"),
    ("USD", "PHP",  1.00, 60,   "Strike — Lightning Network, bank deposit in Philippines"),
    ("USD", "BTC",  0.50, 5,    "Strike — instant BTC via Lightning, 0% fee"),
    ("EUR", "MXN",  1.20, 30,   "Strike — Lightning Network, bank deposit in Mexico"),
]

XE_CORRIDORS: list[tuple] = [
    # xe.com (Euronet) — major global FX brand, 170+ currencies.
    # No transfer fee; FX margin ~1.0–2.5% depending on corridor.
    # Minimum transfer: $10 USD. Best for small-to-mid amounts.
    ("USD", "EUR",  1.30, 1440, "XE Money Transfer — bank wire, no transfer fee"),
    ("USD", "GBP",  1.40, 1440, "XE Money Transfer — bank wire, no transfer fee"),
    ("USD", "CAD",  1.30, 1440, "XE Money Transfer — bank wire"),
    ("USD", "AUD",  1.40, 1440, "XE Money Transfer — bank wire"),
    ("USD", "MXN",  2.00, 1440, "XE Money Transfer — bank wire to Mexico"),
    ("USD", "INR",  1.80, 1440, "XE Money Transfer — bank wire to India"),
    ("USD", "PHP",  2.00, 1440, "XE Money Transfer — bank wire to Philippines"),
    ("EUR", "USD",  1.30, 1440, "XE Money Transfer — bank wire, no transfer fee"),
    ("EUR", "GBP",  1.20, 1440, "XE Money Transfer — bank wire"),
    ("GBP", "EUR",  1.20, 1440, "XE Money Transfer — bank wire"),
    ("GBP", "USD",  1.30, 1440, "XE Money Transfer — bank wire"),
]

ATLANTIC_MONEY_CORRIDORS: list[tuple] = [
    # Atlantic Money — UK/EU flat-fee model (£3 / €3 per transfer, no FX margin).
    # Best for large transfers (£500+) where fee % drops below 0.5%.
    # We model at 0.7% all-in for £1,000 transfer as typical.
    # Only UK/EU send side; limited receive countries.
    ("GBP", "EUR",  0.70, 60,   "Atlantic Money — flat £3 fee, mid-market rate, best for large amounts"),
    ("GBP", "USD",  0.70, 60,   "Atlantic Money — flat £3 fee, mid-market rate"),
    ("GBP", "INR",  0.80, 60,   "Atlantic Money — flat £3 fee, mid-market rate"),
    ("GBP", "AUD",  0.70, 60,   "Atlantic Money — flat £3 fee, mid-market rate"),
    ("GBP", "CAD",  0.70, 60,   "Atlantic Money — flat £3 fee, mid-market rate"),
    ("EUR", "GBP",  0.70, 60,   "Atlantic Money — flat €3 fee, mid-market rate"),
    ("EUR", "USD",  0.70, 60,   "Atlantic Money — flat €3 fee, mid-market rate"),
    ("EUR", "INR",  0.80, 60,   "Atlantic Money — flat €3 fee, mid-market rate"),
]

INTERMEX_CORRIDORS: list[tuple] = [
    # Intermex — US-based, specializes in US→LatAm via agent network and bank.
    # Strong brand in US Hispanic communities; 100k+ agent locations in LatAm.
    # Fees vary; typically $4.99 fixed + ~2% FX spread for bank; less for cash.
    ("USD", "MXN",  3.00, 60,   "Intermex — cash pickup or bank deposit, Mexico"),
    ("USD", "COP",  3.50, 1440, "Intermex — bank deposit, Colombia"),
    ("USD", "GTQ",  3.50, 60,   "Intermex — cash pickup or bank deposit, Guatemala"),
    ("USD", "HNL",  3.80, 60,   "Intermex — cash pickup, Honduras"),
    ("USD", "DOP",  3.50, 60,   "Intermex — cash pickup, Dominican Republic"),
    ("USD", "BRL",  4.00, 1440, "Intermex — bank deposit, Brazil"),
    ("USD", "PEN",  3.80, 1440, "Intermex — bank deposit, Peru"),
]

WESTERN_UNION_CORRIDORS: list[tuple] = [
    # Western Union — ~200 countries, largest cash pickup network globally
    # Fees vary by corridor and delivery method; 3–8% all-in typical
    ("USD", "MXN",  4.50,  30,   "Western Union — bank deposit or cash pickup, Mexico"),
    ("USD", "BRL",  5.00, 1440,  "Western Union — bank deposit, Brazil"),
    ("USD", "COP",  4.80, 1440,  "Western Union — bank deposit or cash, Colombia"),
    ("USD", "PEN",  5.00, 1440,  "Western Union — bank deposit or cash, Peru"),
    ("USD", "ARS",  5.50,  60,   "Western Union — bank deposit, Argentina"),
    ("USD", "NGN",  5.50, 2880,  "Western Union — bank deposit, Nigeria"),
    ("USD", "KES",  5.00, 1440,  "Western Union — bank or M-Pesa, Kenya"),
    ("USD", "GHS",  5.50, 2880,  "Western Union — bank deposit, Ghana"),
    ("USD", "PHP",  4.50,  60,   "Western Union — bank or cash pickup, Philippines"),
    ("USD", "INR",  3.80, 1440,  "Western Union — bank deposit, India"),
    ("USD", "BDT",  5.00, 2880,  "Western Union — bank deposit, Bangladesh"),
    ("USD", "PKR",  5.00, 2880,  "Western Union — bank deposit, Pakistan"),
    ("USD", "IDR",  5.00, 1440,  "Western Union — bank deposit, Indonesia"),
    ("USD", "VND",  5.00, 1440,  "Western Union — bank deposit, Vietnam"),
    ("EUR", "MXN",  5.00,  30,   "Western Union — bank deposit or cash pickup, Mexico"),
    ("EUR", "NGN",  6.00, 2880,  "Western Union — bank deposit, Nigeria"),
    ("EUR", "PHP",  5.00,  60,   "Western Union — bank or cash pickup, Philippines"),
    ("GBP", "INR",  4.00, 1440,  "Western Union — bank deposit, India"),
    # Reverse corridors — sending FROM these countries to USD/EUR
    ("MXN", "USD",  5.00,  60,   "Western Union — cash or bank, Mexico to USA"),
    ("BRL", "USD",  5.50, 1440,  "Western Union — bank, Brazil to USA"),
    ("COP", "USD",  5.20, 1440,  "Western Union — bank or cash, Colombia to USA"),
    ("PHP", "USD",  5.00,  60,   "Western Union — cash or bank, Philippines to USA"),
    ("INR", "USD",  4.50, 1440,  "Western Union — bank, India to USA"),
    ("NGN", "USD",  6.00, 2880,  "Western Union — bank, Nigeria to USA"),
    ("KES", "USD",  5.50, 1440,  "Western Union — bank or M-Pesa, Kenya to USA"),
    ("GHS", "USD",  6.00, 2880,  "Western Union — bank, Ghana to USA"),
    ("MXN", "EUR",  5.50,  60,   "Western Union — bank, Mexico to Europe"),
    ("PHP", "EUR",  5.50,  60,   "Western Union — bank, Philippines to Europe"),
]

MONEYGRAM_CORRIDORS: list[tuple] = [
    # MoneyGram — ~200 countries, strong cash pickup and bank network
    # Fees 3–7% all-in typical
    ("USD", "MXN",  4.20,  30,   "MoneyGram — bank deposit or cash pickup, Mexico"),
    ("USD", "BRL",  5.00, 1440,  "MoneyGram — bank deposit, Brazil"),
    ("USD", "COP",  4.50, 1440,  "MoneyGram — bank deposit or cash, Colombia"),
    ("USD", "NGN",  5.80, 2880,  "MoneyGram — bank deposit, Nigeria"),
    ("USD", "KES",  5.00, 1440,  "MoneyGram — bank or mobile money, Kenya"),
    ("USD", "GHS",  5.50, 2880,  "MoneyGram — bank deposit, Ghana"),
    ("USD", "PHP",  4.20,  60,   "MoneyGram — bank or cash pickup, Philippines"),
    ("USD", "INR",  4.00, 1440,  "MoneyGram — bank deposit, India"),
    ("USD", "PKR",  5.50, 2880,  "MoneyGram — bank deposit, Pakistan"),
    ("USD", "IDR",  5.00, 1440,  "MoneyGram — bank deposit, Indonesia"),
    ("EUR", "MXN",  4.80,  30,   "MoneyGram — cash pickup or bank, Mexico"),
    ("EUR", "PHP",  4.50,  60,   "MoneyGram — bank or cash pickup, Philippines"),
    ("GBP", "INR",  4.20, 1440,  "MoneyGram — bank deposit, India"),
    # Reverse corridors — sending FROM these countries to USD/EUR
    ("MXN", "USD",  4.80,  60,   "MoneyGram — cash or bank, Mexico to USA"),
    ("BRL", "USD",  5.50, 1440,  "MoneyGram — bank, Brazil to USA"),
    ("COP", "USD",  5.00, 1440,  "MoneyGram — bank or cash, Colombia to USA"),
    ("PHP", "USD",  4.80,  60,   "MoneyGram — cash or bank, Philippines to USA"),
    ("INR", "USD",  4.50, 1440,  "MoneyGram — bank, India to USA"),
    ("NGN", "USD",  6.20, 2880,  "MoneyGram — bank, Nigeria to USA"),
    ("KES", "USD",  5.50, 1440,  "MoneyGram — bank or mobile money, Kenya to USA"),
    ("MXN", "EUR",  5.20,  60,   "MoneyGram — bank, Mexico to Europe"),
]

CURRENCYFAIR_CORRIDORS: list[tuple] = [
    # CurrencyFair — Ireland-based P2P FX marketplace (acquired by Western Union 2021).
    # €3 flat fee + 0.3–0.5% FX margin on matched trades. Best for EUR/GBP large transfers.
    # Modeled at 0.8% all-in as conservative (some trades match at 0.4%).
    ("EUR", "GBP",  0.80, 1440, "CurrencyFair — P2P matched FX, €3 fee, competitive for large amounts"),
    ("EUR", "USD",  0.80, 1440, "CurrencyFair — P2P matched FX, €3 fee"),
    ("GBP", "EUR",  0.80, 1440, "CurrencyFair — P2P matched FX, £3 fee"),
    ("GBP", "USD",  0.85, 1440, "CurrencyFair — P2P matched FX, £3 fee"),
    ("AUD", "EUR",  0.90, 1440, "CurrencyFair — P2P matched FX, AUD→EUR"),
    ("AUD", "GBP",  0.90, 1440, "CurrencyFair — P2P matched FX, AUD→GBP"),
    ("CAD", "EUR",  0.85, 1440, "CurrencyFair — P2P matched FX, CAD→EUR"),
]

BINANCE_P2P_CORRIDORS: list[tuple] = [
    # Binance P2P — peer-to-peer marketplace, rates set by individual traders
    # Platform fee: 0%. FX spread varies 0.5–2% depending on pair and liquidity.
    # Modeled at 1.0% (mid-range typical spread) as a conservative estimate.
    ("USD", "VES",  1.00, 30,   "Binance P2P — peer-set rates, verify before transacting"),
    ("USD", "ARS",  1.00, 30,   "Binance P2P — peer-set rates, popular in Argentina"),
    ("USD", "COP",  1.00, 30,   "Binance P2P — peer-set rates"),
    ("USD", "MXN",  1.00, 30,   "Binance P2P — peer-set rates"),
    ("USD", "BRL",  1.00, 30,   "Binance P2P — peer-set rates"),
    ("USD", "NGN",  1.20, 30,   "Binance P2P — peer-set rates, Nigeria"),
    ("USD", "KES",  1.20, 30,   "Binance P2P — peer-set rates, Kenya"),
    ("USD", "GHS",  1.20, 30,   "Binance P2P — peer-set rates, Ghana"),
    ("EUR", "VES",  1.00, 30,   "Binance P2P — peer-set rates"),
    ("EUR", "ARS",  1.00, 30,   "Binance P2P — peer-set rates"),
    ("USDT","VES",  0.50, 15,   "Binance P2P — USDT to VES, lowest spread"),
    ("USDT","ARS",  0.50, 15,   "Binance P2P — USDT to ARS, lowest spread"),
    ("USDT","COP",  0.50, 15,   "Binance P2P — USDT to COP"),
    ("USDT","NGN",  0.80, 15,   "Binance P2P — USDT to NGN"),
]

# ── Per-provider send limits (min, max) in source currency ─────────────────
# Based on published limits; ~est. for providers without public documentation.
PROVIDER_LIMITS: dict[str, tuple[float, float]] = {
    "Remitly":        (1.0,    10_000.0),
    "WorldRemit":     (1.0,     7_000.0),
    "Ria":            (1.0,     3_000.0),
    "Sendwave":       (1.0,       500.0),
    "Xoom":           (10.0,   10_000.0),
    "Paysend":        (0.5,     5_000.0),
    "OFX":            (150.0, 500_000.0),
    "TransferGo":     (1.0,     5_000.0),
    "Skrill":         (1.0,    45_000.0),
    "Revolut":        (1.0,    20_000.0),
    "Zinli":          (10.0,    5_000.0),
    "Lemon Cash":     (1.0,    10_000.0),
    "Mukuru":         (10.0,    3_000.0),
    "Mama Money":     (10.0,    3_000.0),
    "Binance P2P":    (1.0,   100_000.0),
    "Global66":       (1.0,    50_000.0),
    "Strike":         (1.0,    50_000.0),
    "XE":             (50.0,  500_000.0),
    "Atlantic Money": (50.0, 1_000_000.0),
    "Intermex":       (1.0,     5_000.0),
    "CurrencyFair":   (50.0,  500_000.0),
    "Western Union":  (1.0,  50_000.0),
    "MoneyGram":      (1.0,  10_000.0),
}

# ── All corridors grouped by provider ──────────────────────────────────────
ALL_STATIC_PROVIDERS = [
    ("Remitly",      REMITLY_CORRIDORS),
    ("WorldRemit",   WORLDREMIT_CORRIDORS),
    ("Ria",          RIA_CORRIDORS),
    ("Sendwave",     SENDWAVE_CORRIDORS),
    ("Xoom",         XOOM_CORRIDORS),
    ("Paysend",      PAYSEND_CORRIDORS),
    ("OFX",          OFX_CORRIDORS),
    ("TransferGo",   TRANSFERGO_CORRIDORS),
    ("Skrill",       SKRILL_CORRIDORS),
    ("Revolut",      REVOLUT_CORRIDORS),
    ("Zinli",           ZINLI_CORRIDORS),
    ("Lemon Cash",      LEMON_CASH_CORRIDORS),
    ("Mukuru",          MUKURU_CORRIDORS),
    ("Mama Money",      MAMA_MONEY_CORRIDORS),
    ("Binance P2P",     BINANCE_P2P_CORRIDORS),
    ("Global66",        GLOBAL66_CORRIDORS),
    ("Strike",          STRIKE_CORRIDORS),
    ("XE",              XE_CORRIDORS),
    ("Atlantic Money",  ATLANTIC_MONEY_CORRIDORS),
    ("Intermex",        INTERMEX_CORRIDORS),
    ("CurrencyFair",    CURRENCYFAIR_CORRIDORS),
    ("Western Union",   WESTERN_UNION_CORRIDORS),
    ("MoneyGram",       MONEYGRAM_CORRIDORS),
]


# ── Rate fetch (shared cache with TTL) ─────────────────────────────────────
import time

_rate_cache: dict[str, tuple[float, dict]] = {}  # base → (timestamp, rates)
_RATE_CACHE_TTL = 300  # 5 minutes


async def _fetch_rates(base: str, client: httpx.AsyncClient) -> dict[str, float]:
    now = time.monotonic()
    if base in _rate_cache:
        cached_at, rates = _rate_cache[base]
        if now - cached_at < _RATE_CACHE_TTL:
            return rates
    try:
        r = await client.get(RATES_URL.format(base=base), timeout=5)
        data = r.json()
        if data.get("result") == "success":
            rates = data.get("rates", {})
            _rate_cache[base] = (now, rates)
            return rates
    except Exception as e:
        logger.warning(f"Remittance adapter rate fetch failed for {base}: {e}")
        # Return stale cache if available
        if base in _rate_cache:
            return _rate_cache[base][1]
    return {}


async def get_remittance_edges() -> list[Edge]:
    """Return edges for all static remittance providers."""
    all_corridors = [
        (provider, from_, to_, fee, minutes, note)
        for provider, corridors in ALL_STATIC_PROVIDERS
        for from_, to_, fee, minutes, note in corridors
    ]

    bases_needed = {from_ for _, from_, _, _, _, _ in all_corridors}

    try:
        async with httpx.AsyncClient() as client:
            rate_maps = dict(zip(
                bases_needed,
                await asyncio.gather(*[_fetch_rates(b, client) for b in bases_needed])
            ))
    except Exception as e:
        logger.warning(f"Remittance adapter failed: {e}")
        return []

    edges = []
    for provider, from_, to_, fee, minutes, note in all_corridors:
        rates = rate_maps.get(from_, {})
        rate = rates.get(to_, 1.0)
        if rate == 0:
            rate = 1.0
        min_amt, max_amt = PROVIDER_LIMITS.get(provider, (0.01, 1_000_000.0))
        edges.append(Edge(
            from_currency=from_,
            to_currency=to_,
            via=provider,
            fee_pct=fee,
            estimated_minutes=minutes,
            instructions=f"{note} (~est. {fee}% total cost)",
            exchange_rate=rate,
            min_amount=min_amt,
            max_amount=max_amt,
        ))

    logger.info(f"Remittance adapter: {len(edges)} edges from {len(ALL_STATIC_PROVIDERS)} providers")
    return edges
