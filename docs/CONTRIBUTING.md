# Contributing to Coinnect

Coinnect is the reference implementation of the [Money Routing Protocol (MRP)](PROTOCOL.md). It is open-source, non-profit, and maintained by one person. Contributions are welcome.

---

## Ways to contribute

### Report a bug or inaccurate rate

Open a GitHub issue with:
- The corridor (`USD → MXN`, etc.)
- The amount you tested
- What Coinnect showed vs. what the provider actually charges
- A link to the provider's pricing page

This is the most valuable contribution you can make. Accurate data is the whole point.

You can also use the **"Report bug"** button in the Coinnect UI — it posts directly to the issue tracker.

### Suggest a new corridor or provider

Open a GitHub issue with the provider name, website, and the corridor you'd like covered. If you have access to their API documentation, include it.

To apply for official listing as a provider, see [LISTING_STANDARD.md](LISTING_STANDARD.md).

### Submit a pull request

1. Fork the repository
2. Create a branch: `git checkout -b feature/your-change`
3. Make your changes
4. Run tests: `pytest tests/`
5. Lint: `ruff check src/`
6. Submit a PR against `main`

No CLA required. MIT license — your contribution is yours and everyone else's.

---

## Project structure

```
src/coinnect/
├── api/
│   └── routes.py          # FastAPI endpoints (/v1/quote, /v1/corridors, etc.)
├── exchanges/
│   ├── ccxt_adapter.py    # Crypto exchange rates via CCXT
│   ├── wise_adapter.py    # Wise fiat rates + traditional bank estimates
│   ├── yellowcard_adapter.py  # Yellow Card (Africa crypto-to-fiat)
│   └── remittance_adapter.py  # Static remittance providers (Remitly, OFX, etc.)
├── routing/
│   └── engine.py          # Graph construction, Dijkstra, route ranking
├── db/
│   ├── analytics.py       # Search logging
│   ├── history.py         # Time-series rate snapshots
│   └── keys.py            # API key management
├── static/
│   ├── index.html         # Frontend (vanilla JS, Tailwind CDN)
│   └── i18n.js            # Translations (15 languages)
└── main.py                # App entry point
```

---

## Adding a new exchange adapter

Each adapter is an async function returning `list[Edge]`.

```python
# src/coinnect/exchanges/myprovider_adapter.py
from coinnect.routing.engine import Edge

async def get_myprovider_edges() -> list[Edge]:
    # Fetch rates from provider API or use static estimates
    return [
        Edge(
            from_currency="USD",
            to_currency="MXN",
            via="MyProvider",
            fee_pct=1.5,           # all-in: fee + spread
            exchange_rate=17.42,
            estimated_minutes=60,
            instructions="Bank transfer via MyProvider",
            min_amount=1.0,
            max_amount=10_000.0,
        )
    ]
```

Then register it in `api/routes.py`:

```python
from coinnect.exchanges.myprovider_adapter import get_myprovider_edges

# In the quote() endpoint:
crypto_edges, wise_edges, ..., myprovider_edges = await asyncio.gather(
    get_all_edges(),
    get_wise_edges(),
    ...,
    get_myprovider_edges(),
)
all_edges = crypto_edges + wise_edges + ... + myprovider_edges
```

### Key rules for adapters

- `fee_pct` is the **all-in cost as a percentage of sent amount** — exchange rate margin plus any transfer fee. Do not separate them.
- `exchange_rate` is units of `to_currency` per 1 `from_currency`, **after fees are applied**.
- `min_amount` and `max_amount` are in `from_currency`.
- If using static/estimated rates, use `~est.` in `instructions` and do not set `live=True`.
- Do not hardcode rates that change frequently without a mechanism to update them.

---

## Adding a translation

Translations live in `static/i18n.js` in the `I18N` object.

1. Add your language code to `LANGS`:
```javascript
const LANGS = {
  // ...
  xx: { flag: '🏳️', name: 'Your Language', dir: 'ltr' },
};
```

2. Add a full translation block to `I18N`:
```javascript
const I18N = {
  // ...
  xx: {
    hero_title: '...',
    hero_subtitle: '...',
    // ... all keys (copy from en: block and translate)
  },
};
```

3. Add 5 tagline phrases to `TAGLINES`:
```javascript
const TAGLINES = {
  // ...
  xx: ['Phrase 1', 'Phrase 2', 'Phrase 3', 'Phrase 4', 'Phrase 5'],
};
```

4. Add a button to the language picker in `index.html`:
```html
<button onclick="setLang('xx')" data-lang="xx" class="lang-btn ...">🏳️ Your Language</button>
```

5. Add country → language mappings to `COUNTRY_LANG` if applicable:
```javascript
const COUNTRY_LANG = {
  // ...
  XX: 'xx',
};
```

---

## Running locally

```bash
cd /path/to/coinnect
pip install -e .
uvicorn coinnect.main:app --reload --port 8100
```

Open `http://localhost:8100` — the frontend is served as a static file.

**Environment variables:**

| Variable | Purpose | Default |
|----------|---------|---------|
| `WISE_API_KEY` | Wise live rates | Optional — falls back to estimates |
| `YELLOWCARD_API_KEY` | Yellow Card live rates | Optional |
| `CCXT_EXCHANGE_IDS` | Override supported exchanges | Uses defaults |

---

## Protocol contributions

The Money Routing Protocol (MRP) is a separate, implementation-agnostic standard. If you want to propose changes to the protocol itself (Edge schema, API contract, routing algorithm), open a GitHub issue with:

1. The change you're proposing
2. The rationale (what problem it solves)
3. Backward compatibility implications

Protocol changes follow an IETF-style rough consensus process — see [GOVERNANCE.md](GOVERNANCE.md) for the decision-making model.

**Breaking changes** (changes to the Edge schema, API contract, or response format) require:
- A GitHub issue open for at least 30 days
- No blocking objections from active contributors
- A new major version number

---

## Code style

- Python: [Ruff](https://github.com/astral-sh/ruff) for linting, [Black](https://github.com/psf/black) for formatting
- JavaScript: vanilla ES6+, no build step, no frameworks — keep it loadable without npm
- HTML: Tailwind via CDN — no PostCSS build required
- Tests: pytest

No style bikeshedding in PR reviews. If the code works, is readable, and passes lint, it will be merged.

---

## Contact

- GitHub issues: preferred for bugs and feature requests
- Email: hello@coinnect.bot — for sensitive disclosures, listing requests, or institutional collaboration

*MIT License · March 2026 · Maintained by Miguel Valencia*
