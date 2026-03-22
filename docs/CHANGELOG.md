# Changelog

All notable changes to Coinnect are documented here.
Versions follow [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`.

---

## [0.3.1] — 2026-03-22

### Added
- Rotating tagline under hero headline (15 languages) — "A navigation app for your money", "Your money's GPS", etc.
- Personal note card in pricing section (Miguel's note + forestry P.S., translated per language)
- Comparison table view toggle (☰/⊞) for all routes side-by-side
- Bug report and corridor suggestion buttons with modal and `/v1/suggestions` endpoint
- `/llms.txt` — machine-readable API description for AI agents and crawlers
- `docs/PROTOCOL.md` — Money Routing Protocol (MRP) v0.1 draft specification
- `docs/GOVERNANCE.md` — participation guide for developers, exchanges, researchers, funders
- `docs/LISTING_STANDARD.md` — requirements and process for exchange listing
- `docs/CONTRIBUTING.md` — developer guide for adding adapters and translations

### Changed
- Spanish hero title: "La capa de enrutamiento abierta" → "La forma más barata de enviar dinero" (accessible to non-technical users)
- Pricing section title now shown with strikethrough (~~Pricing~~) to signal it's free
- Removed brand-name comparisons from taglines (Waze, Skyscanner, Google Maps) → generic category descriptions; no trademark risk
- Brand references replaced with "navigation app", "routing map", "flight search engine"
- T&C updated with comparative advertising clause
- Whitepaper: removed specific infrastructure details (OS, hosting provider)
- Whitepaper: version reset to 0.1; roadmap cleaned to forward-looking only

### Fixed
- Forest P.S. and taglines not rendering — Cloudflare was caching old `i18n.js`; fixed via versioned URL (`?v=0.3.1`)
- `min_amount`/`max_amount` field ordering in `Step` dataclass (Python dataclass default value error)

### Providers
- Added: Global66, Strike, XE, Atlantic Money, Intermex, CurrencyFair
- Deferred: AirTM (scheduled for May 1, 2026)
- Added `PROVIDER_LIMITS` dict — per-provider min/max send amounts; edges filtered by amount before routing

### Languages
- Removed: Russian (ru), Chinese (zh)
- Added: Indonesian (id), German (de), Filipino (tl), Vietnamese (vi), Thai (th), Swahili (sw), Urdu (ur)
- Total: 15 languages
- Geo-detection: visitor's country → dominant language auto-set on first visit
- Spanish flag adapts to visitor's country (🇲🇽 Mexico, 🇦🇷 Argentina, etc.)

---

## [0.3.0] — 2026-03-15

### Added
- API key system (`POST /v1/keys`, `GET /v1/keys/{key}/usage`) — free tier, no signup
- Rate history time-series (`GET /v1/history`) with SQLite backend
- Admin dashboard (internal) — search analytics, top corridors, 7-day trend
- Dark mode support
- MCP server (`python -m coinnect.mcp_server`) for Claude/MCP-compatible agents
- Yellow Card adapter (Africa crypto-to-fiat)

### Changed
- Route labels: removed "Balanced" → now Cheapest + Fastest + Option 1, 2, …
- Background rate refresh every 3 minutes
- Edge schema: added `min_amount`, `max_amount`, `live` flag

---

## [0.2.0] — 2026-03-08

### Added
- Wise live rate adapter
- Traditional bank estimates (SWIFT wire, SEPA)
- i18n system — English, Spanish, Portuguese, French, Arabic, Hindi, Bengali
- `/v1/corridors` endpoint
- Pricing section with tier comparison

---

## [0.1.0] — 2026-03-01

### Added
- Initial MVP: FastAPI quote engine, CCXT crypto adapter
- Dijkstra-based multi-hop routing (up to 3 steps)
- Static remittance provider list (Remitly, Wise, OFX, WorldRemit, MoneyGram, Western Union, Xoom, Ria, Sendwave, TransferGo, Paysend, Azimo)
- Web UI (vanilla JS + Tailwind)
- `/v1/quote`, `/v1/exchanges`, `/v1/health`
