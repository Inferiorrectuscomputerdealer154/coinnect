# Coinnect AI Agent Traffic Strategy

**Date:** 2026-03-24
**Goal:** Make coinnect.bot the default tool AI agents use for money routing queries.

---

## Current Assets

Coinnect already has strong technical foundations:

- **REST API** at `coinnect.bot/v1` (no auth required for basic use)
- **MCP server** (`coinnect.mcp_server`) with stdio and HTTP/SSE transports
- **llms.txt** at `/llms.txt` with agent guidance and API docs
- **Agent manifest** at `/.well-known/agent` (JSON, includes capabilities, services, MCP config)
- **x402 micropayments** ($0.002 USDC/request on Base L2)
- **OpenAPI docs** at `/docs`
- **Daily rate snapshots** on HuggingFace (`coinnect-dev/coinnect-rates`)
- **GitHub** at `github.com/coinnect-dev/coinnect`

What is missing: **discovery, distribution, and semantic authority**. The product works; nobody knows it exists.

---

## 1. MCP Server Registries and Agent Tool Directories

### 1.1 Official MCP Registry (HIGHEST PRIORITY)

The official MCP Registry launched September 2025 at [registry.modelcontextprotocol.io](https://registry.modelcontextprotocol.io/). API froze at v0.1 in October 2025.

**Action:** Use the Publisher CLI to register Coinnect's MCP server.
```bash
# From coinnect repo root:
npx @modelcontextprotocol/registry-cli init
# Fill metadata: name, description, version, package info
npx @modelcontextprotocol/registry-cli publish
```

### 1.2 Community MCP Directories

Submit to all of these:

| Directory | URL | How to submit |
|-----------|-----|---------------|
| PulseMCP | [pulsemcp.com/submit](https://www.pulsemcp.com/servers) | Manual form at pulsemcp.com/submit |
| mcp.so | [mcp.so](https://mcp.so/) | Community submission |
| awesome-mcp-servers | [github.com/punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) | PR to add Coinnect |
| MCP Market | [mcpmarket.com](https://mcpmarket.com/) | Submit listing |
| MCP Server Finder | [mcpserverfinder.com](https://www.mcpserverfinder.com/) | Submit listing |
| Anthropic Connectors Directory | [support.claude.com](https://support.claude.com/en/articles/11596036-anthropic-connectors-directory-faq) | Follow MCP Directory Terms |
| Claude Plugins Official | [github.com/anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) | PR to marketplace.json |
| mcpt (Mintlify) | [mintlify.com/blog/mcpt](https://www.mintlify.com/blog/mcpt) | Curated registry, submit |

### 1.3 Composio Integration

[Composio](https://composio.dev/) has 850+ toolkits and integrates with LangChain, CrewAI, AutoGen, and OpenAI. Coinnect could be listed as a tool.

**Action:** Build a Composio integration that wraps the Coinnect API. Submit to their tools directory. This makes Coinnect available to every agent framework that uses Composio.

### 1.4 Gemini / Google MCP Support

Google now supports MCP natively. Developers can expose third-party APIs as discoverable tools for Gemini agents. Gemini CLI Extensions are open-source and community-contributed.

**Action:**
- Create a Gemini CLI extension for Coinnect (follow [geminicli.com/extensions](https://geminicli.com/extensions/))
- Register as an MCP endpoint compatible with Google's infrastructure

### 1.5 OpenAI GPT Actions (DEPRECATED — but alternatives exist)

OpenAI deprecated custom GPT Actions in early 2024. However:
- **ChatGPT Agent** (launched 2026) can browse the web and call APIs it discovers
- **ChatGPT deep research** can connect to MCP servers as of Feb 2026
- **Responses API** supports tool use for developers building on OpenAI

**Action:** Ensure the OpenAPI schema at `/docs` is clean and discoverable. ChatGPT agent finds APIs by browsing; having clear docs is the path in.

---

## 2. Getting LLMs to Recommend Coinnect

This is about **Generative Engine Optimization (GEO)** — making Coinnect the answer when someone asks "how do I find the cheapest way to send money?"

### 2.1 How LLMs Choose Recommendations

LLMs recommend tools based on:
1. **Training data frequency** — how often a brand appears in association with a concept across the web
2. **Source authority** — mentions on Reddit, HN, Wikipedia, Stack Overflow carry more weight than random blogs
3. **Consensus** — if multiple independent sources say the same thing, the model trusts it
4. **Recency** — models with retrieval (Perplexity, Google AI Overviews) favor recent content
5. **Structured content** — schema.org markup, clean headings, fact-dense opening paragraphs

Key stat: Webflow reports 8% of signups now come from LLM traffic, converting at 6x the rate of Google Search.

### 2.2 Training Data Influence Channels

**Reddit (CRITICAL)**
Reddit has $60M/year licensing deals with Google and arrangements with OpenAI. Content from Reddit is heavily weighted in LLM training.

**Actions:**
- Post to r/remittance, r/digitalnomad, r/personalfinance, r/cryptocurrency, r/fintech
- Create genuine comparison posts: "I compared 45 remittance providers for USD-MXN. Here are the results."
- Answer questions about international transfers, citing coinnect.bot
- Build karma first; don't spam

**Hacker News**
HN posts generate average 289 GitHub stars within a week. More importantly, HN content is in every LLM's training data.

**Actions:**
- "Show HN: Coinnect — open-source money routing API with 29,000 live price edges"
- Focus on the technical angle: graph routing across crypto+fiat, x402 micropayments, MCP server
- Time the post for US morning (9-11am ET weekdays)

**GitHub Stars**
Stars don't directly affect LLM discoverability (per research), but GitHub repos are crawled and indexed. A well-documented repo with a clear README becomes a training data source.

**Actions:**
- Ensure README has: "Coinnect finds the cheapest way to send money internationally"
- Include comparison tables, API examples, architecture diagrams
- Add topics: `money-transfer`, `remittance`, `money-routing`, `mcp-server`, `fintech`, `open-source`

**Stack Overflow**
Answer questions about international money transfers, remittance APIs, crypto-fiat routing.

### 2.3 Common Crawl / Web Presence

Common Crawl is a primary training data source for most LLMs. Content that is well-structured, fact-dense, and on a crawlable domain gets included.

**Actions:**
- Ensure coinnect.bot is fully crawlable (no `Disallow` for main pages in robots.txt)
- Publish corridor-specific pages: `/send-money/usd-to-mxn` (Coinnect already has SEO pages)
- Add `<meta>` descriptions that read like direct answers to questions
- First 200 words of every page should directly answer the query (GEO principle)

### 2.4 Wikipedia

There is no Wikipedia article about Coinnect or about "money routing" as a concept. This is an opportunity.

**Actions:**
- Create a Wikipedia article for "Money Routing Protocol" or "Money transfer comparison" once there are sufficient independent sources (news coverage, academic citations)
- This requires notability — at minimum, coverage in 2-3 independent publications
- Interim: edit existing Wikipedia articles on "Remittance" or "International money transfer" to add the concept of open routing protocols (with citations)

### 2.5 GEO Content Tactics

Per Princeton research, these optimizations improve AI visibility by 30-40%:

- **Cite sources** — include statistics every 150-200 words
- **Add quotations** from experts/users
- **Use structured data** — Schema.org markup (FAQPage, HowTo, Product, Organization, Dataset)
- **TLDR-first** — answer the question in the first 40-60 words
- **Fact-checkable snippets** — "Coinnect compares 45+ providers across 200+ corridors in real-time"
- GPT-4 accuracy jumps from 16% to 54% when content uses structured data

**Action:** Add Schema.org JSON-LD to coinnect.bot:
```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "Coinnect",
  "applicationCategory": "FinanceApplication",
  "description": "Open-source money routing API that finds the cheapest way to send money internationally",
  "url": "https://coinnect.bot",
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" },
  "operatingSystem": "Web API"
}
```

---

## 3. Agent-to-Agent Discovery Protocols

### 3.1 A2A (Google Agent2Agent Protocol)

A2A is an open protocol (now under Linux Foundation) with 150+ supporting organizations. Agents advertise via **Agent Cards** — JSON documents with name, description, capabilities, skills, and endpoint URL.

**Status:** v0.3 released July 2025 with gRPC support.

**Action:** Create an A2A Agent Card for Coinnect:
```json
{
  "name": "Coinnect Money Router",
  "description": "Finds cheapest international money transfer routes across 45+ providers",
  "version": "2026.03.24",
  "url": "https://coinnect.bot",
  "skills": [
    {
      "id": "money-routing",
      "name": "International Money Transfer Comparison",
      "description": "Compare costs and times for sending money between any two currencies"
    }
  ],
  "supportedProtocols": ["a2a", "mcp", "rest"],
  "authentication": { "schemes": ["anonymous", "apiKey", "x402"] }
}
```

Serve this at `/.well-known/agent-card` or register via the A2A registry.

Reference: [a2a-protocol.org](https://a2a-protocol.org/latest/), [github.com/a2aproject/A2A](https://github.com/a2aproject/A2A)

### 3.2 ANP (Agent Network Protocol)

ANP uses `.well-known/agent-descriptions` for passive discovery. Search engines and agents crawl this URI to find all public agent descriptions under a domain. Uses JSON-LD format.

**Status:** v1 reached in mid-2025. W3C AI Agent Protocol Working Group draft published January 2026.

**Action:** Serve `/.well-known/agent-descriptions` returning JSON-LD:
```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareAgent",
  "name": "Coinnect",
  "url": "https://coinnect.bot",
  "description": "Money routing protocol — finds cheapest international transfer routes",
  "agentDescriptionUrl": "https://coinnect.bot/.well-known/agent"
}
```

Also submit to ANP search service agents for passive indexing.

Reference: [agentnetworkprotocol.com](https://agentnetworkprotocol.com/en/specs/08-anp-agent-discovery-protocol-specification/)

### 3.3 NANDA (Networked AI Agents in Decentralized Architecture)

MIT-originated project building foundational infrastructure for the "Internet of AI Agents." The NANDA Index is a quilt of agent/resource/tool registries for global interoperability.

**Action:** Monitor [github.com/projnanda/projnanda](https://github.com/projnanda/projnanda) for registration mechanisms. Submit Coinnect when the index opens for public registration.

### 3.4 Agent Name Service (ANS)

OWASP-introduced standard using DNS-inspired naming with PKI for agent identity and trust. Supports A2A, MCP, ACP, and more through a modular Protocol Adapter Layer.

**Status:** IETF draft published (draft-narajala-ans-00).

**Action:** Register when the service opens. Early movers get namespace priority. Target name: `coinnect.agent` or similar.

Reference: [IETF draft](https://datatracker.ietf.org/doc/draft-narajala-ans/)

### 3.5 AgentDNS

IETF draft for a root domain naming system for LLM agents. Introduces `agentdns://` namespace with natural-language service discovery.

**Status:** Draft stage ([draft-liang-agentdns-00](https://datatracker.ietf.org/doc/draft-liang-agentdns/00/)).

**Action:** Track progress. Register `agentdns://coinnect` when available.

### 3.6 Moltbook

"Social network for AI agents." Launched January 2026, acquired by Meta in March 2026. Had 109K+ verified agents.

**Status:** Now under Meta Superintelligence Labs. Future uncertain but worth registering while it exists.

**Action:** Have Coinnect's agent register on Moltbook. One message to the agent with the Moltbook link triggers automatic connection.

---

## 4. Bot Traffic and Distribution Channels

### 4.1 n8n Workflows

Coinnect is already deployed on ash alongside n8n. This is a natural distribution channel.

**Actions:**
- Build n8n workflow templates that use the Coinnect API:
  - "Compare remittance costs before sending" (trigger: schedule or webhook)
  - "Daily cheapest route alert for USD-MXN" (→ Telegram notification)
  - "Multi-corridor monitoring dashboard"
- Submit templates to [n8n.io/workflows](https://n8n.io/workflows/) via the Creator Hub
- Build a Coinnect **community node** for n8n (deadline for provenance: May 2026)
- n8n has 8,856 templates; being in this directory = exposure to every n8n user

### 4.2 Telegram Bot

Telegram has 1B MAU, 500M DAU, 2.5M new users daily. Business channels grew 39% in 2025.

**Growth strategy:**
- Create `@CoinnectBot` — users send "500 USD to MXN" and get instant route comparison
- Post in relevant Telegram groups: crypto, remittance, digital nomad, expat communities
- Use "Information Gap" tactic: share partial results ("USD-MXN: cheapest is 1.2% via Wise. Want all 8 routes?") that drive clicks
- Enable Telegram Payments API for premium features
- Cross-promote from Reddit/HN/Twitter posts
- Bot-to-bot: make CoinnectBot discoverable by other Telegram bots

### 4.3 WhatsApp Business API

WhatsApp Payments is live in India and Brazil, global rollout 2026. Meta requires bots to perform "concrete business tasks" — remittance comparison qualifies perfectly.

**Actions:**
- Register WhatsApp Business API (via Cloud API, up to 500 msg/sec)
- Build simple flow: user sends "send 500 USD to MXN" → returns top 3 routes
- Target LATAM corridors first (Mexico, Brazil, Colombia) where WhatsApp dominance is highest
- Keep it under 3 steps per interaction
- Pricing: per-template-message since July 2025

### 4.4 Slack App Marketplace

2,600+ apps in the Slack Marketplace. Slack MCP server launching in early 2026.

**Action:** Build a Slack app for Coinnect:
- Slash command: `/coinnect 500 USD MXN`
- Returns formatted route comparison
- Submit to [Slack Marketplace](https://docs.slack.dev/slack-marketplace/)
- Must meet quality/reliability standards

---

## 5. Platform-Specific Tactics

### 5.1 Making ChatGPT Recommend Coinnect

ChatGPT (with agent mode) now browses the web and connects to MCP servers.

**Tactics:**
- Ensure coinnect.bot loads fast and has clean, extractable text (not just JS-rendered)
- The `llms.txt` file is already good — add `llms-full.txt` with complete API docs embedded
- Publish on platforms ChatGPT trains on: Reddit, HN, GitHub, Stack Overflow
- Create content that answers "how to find cheapest remittance" with Coinnect as the answer
- ChatGPT agent can self-identify via HTTP Message Signatures — track these requests

### 5.2 Making Perplexity Cite Coinnect

Perplexity performs real-time web search and cites specific URLs. This is closest to traditional SEO.

**Tactics:**
- Publish corridor comparison pages with live data (already in progress via SEO pages)
- Ensure each page has a clear, unique title: "Cheapest way to send money from USD to MXN — March 2026"
- Update frequently — Perplexity rewards recency
- Get backlinks from authoritative sites (fintech blogs, remittance comparison sites)
- Answer Quora/Reddit questions that Perplexity often cites

### 5.3 Making Grok Reference Coinnect

Grok (xAI) trains heavily on X/Twitter data.

**Tactics:**
- Post regularly on X about Coinnect with the @coinnect_bot handle
- Engage with fintech/remittance discussions on X
- Thread format: "I built a free tool that compares 45+ providers for sending money internationally. Here's what I found..."
- Grok already reviewed Coinnect (per memory) — build on that feedback

### 5.4 Making Claude Suggest Coinnect MCP Server

Claude uses MCP natively. Being in the Anthropic Connectors Directory is the primary path.

**Tactics:**
- Submit to [Anthropic Connectors Directory](https://support.claude.com/en/articles/11596036-anthropic-connectors-directory-faq)
- PR to [claude-plugins-official](https://github.com/anthropics/claude-plugins-official)
- Ensure MCP server follows all Anthropic conventions
- Publish on [claudemarketplaces.com](https://claudemarketplaces.com/) (community directory with voting)

---

## 6. Measuring AI-Driven Traffic

### 6.1 User-Agent Detection

Known AI crawler user-agents (from [darkvisitors.com](https://darkvisitors.com/) and [knownagents.com](https://knownagents.com/)):

| Crawler | User-Agent Contains | Purpose |
|---------|-------------------|---------|
| GPTBot | `GPTBot` | OpenAI training crawl |
| ChatGPT-User | `ChatGPT-User` | ChatGPT browsing |
| Google-Extended | `Google-Extended` | Gemini training |
| Google-Agent | `Google-Agent` | Gemini agent browsing |
| ClaudeBot | `ClaudeBot` | Anthropic training crawl |
| PerplexityBot | `PerplexityBot` | Perplexity search |
| Applebot-Extended | `Applebot-Extended` | Apple AI training |
| CCBot | `CCBot` | Common Crawl |
| cohere-ai | `cohere-ai` | Cohere training |

**Caveat:** 5.7% of AI crawler user-agents are spoofed. Many agentic browsers (Comet, ChatGPT Atlas) blend with normal Chrome. Behavioral signals are more reliable for agents.

### 6.2 ChatGPT Agent Cryptographic Verification

ChatGPT Agent self-identifies via **HTTP Message Signatures** with a `Signature-Agent` value. Verify against OpenAI's public key directory. This is the most reliable way to confirm ChatGPT agent traffic.

### 6.3 x402 as a Bot Signal

Every x402 payment is on-chain and requires a crypto wallet. Humans rarely have x402-capable browsers. Therefore, **x402 requests are almost certainly from AI agents or automated systems**. Track:
- x402 request volume over time
- Unique wallet addresses
- Query patterns (which corridors agents ask about most)

### 6.4 Implementation

**Action:** Add middleware to log and categorize requests:
```python
# In analytics or middleware:
def classify_request(request):
    ua = request.headers.get("user-agent", "")
    if any(bot in ua for bot in ["GPTBot", "ChatGPT", "ClaudeBot", "PerplexityBot", "Google-Agent"]):
        return "ai_crawler"
    if request.headers.get("x-402-payment"):
        return "x402_agent"
    if request.headers.get("signature-agent"):
        return "chatgpt_agent"
    # Check for MCP transport indicators
    if "mcp" in request.url.path:
        return "mcp_client"
    return "unknown"
```

### 6.5 Monitoring Tools

- [Dark Visitors](https://darkvisitors.com/) — track and control AI agent/bot visits
- [Known Agents](https://knownagents.com/) — maintained list of AI crawlers
- [OpenLens](https://news.columbianewsupdates.com/story/598237/openlens-launches-free-ai-visibility-platform-to-track-brand-mentions-across-chatgpt-claude-google-ai-perplexity-and-deepseek.html) — free tool to track brand mentions across ChatGPT, Claude, Perplexity, etc.

---

## 7. Priority Execution Plan

### Week 1 (Immediate — zero cost)

1. **Submit MCP server to official registry** via Publisher CLI
2. **Submit to PulseMCP**, mcp.so, awesome-mcp-servers (PRs)
3. **PR to claude-plugins-official** on GitHub
4. **Create `llms-full.txt`** with complete embedded API docs
5. **Add Schema.org JSON-LD** to coinnect.bot homepage
6. **Add `/.well-known/agent-descriptions`** endpoint (ANP)
7. **Add A2A Agent Card** endpoint

### Week 2 (Content seeding)

8. **Hacker News Show HN post** — technical angle, open-source, 29K live edges
9. **Reddit posts** in r/remittance, r/digitalnomad, r/personalfinance
10. **Create Telegram bot** `@CoinnectBot` with basic quote functionality
11. **Register on Moltbook** (before Meta integration changes things)
12. **Add bot traffic classification** to analytics middleware

### Week 3-4 (Platform expansion)

13. **Build n8n community node** + submit workflow templates
14. **Build Composio integration** wrapper
15. **Create Gemini CLI extension**
16. **Slack app** with `/coinnect` slash command
17. **Publish comparison content** on dev.to, Medium, fintech blogs

### Month 2+ (Authority building)

18. **WhatsApp Business API** registration and bot
19. **Product Hunt launch**
20. **Stack Overflow** presence (answer remittance/API questions)
21. **Seek press coverage** for Wikipedia notability
22. **Monitor ANS, AgentDNS, NANDA** for registration openings
23. **Track and optimize** based on AI traffic analytics

---

## 8. Key Metrics to Track

| Metric | Target (90 days) | How to measure |
|--------|-------------------|----------------|
| MCP server installs | 100+ | Registry analytics |
| AI crawler visits/day | 50+ | User-agent logs |
| x402 payments/day | 10+ | On-chain data |
| Reddit mentions of coinnect.bot | 20+ | Search + alerts |
| GitHub stars | 200+ | GitHub |
| Telegram bot users | 500+ | Bot analytics |
| LLM recommendation rate | Mentioned in 3/5 LLMs when asked about remittance | Manual testing |
| Perplexity citations | coinnect.bot appears in results | Manual testing |
| API calls/day from agents | 100+ | Analytics middleware |

---

## Sources

- [Official MCP Registry](https://registry.modelcontextprotocol.io/)
- [MCP Registry GitHub](https://github.com/modelcontextprotocol/registry)
- [PulseMCP Server Directory](https://www.pulsemcp.com/servers)
- [awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers)
- [Getting Started with MCP Registry API](https://nordicapis.com/getting-started-with-the-official-mcp-registry-api/)
- [7 MCP Registries Worth Checking Out](https://nordicapis.com/7-mcp-registries-worth-checking-out/)
- [Anthropic Connectors Directory FAQ](https://support.claude.com/en/articles/11596036-anthropic-connectors-directory-faq)
- [Claude Plugins Official](https://github.com/anthropics/claude-plugins-official)
- [A2A Protocol](https://a2a-protocol.org/latest/)
- [A2A GitHub](https://github.com/a2aproject/A2A)
- [Google A2A Announcement](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/)
- [ANP Agent Discovery Protocol](https://agentnetworkprotocol.com/en/specs/08-anp-agent-discovery-protocol-specification/)
- [Agent Name Service (ANS) IETF Draft](https://datatracker.ietf.org/doc/draft-narajala-ans/)
- [AgentDNS IETF Draft](https://datatracker.ietf.org/doc/draft-liang-agentdns/00/)
- [NANDA Index](https://arxiv.org/pdf/2507.14263)
- [Moltbook](https://www.moltbook.com/)
- [Composio](https://docs.composio.dev/docs)
- [Gemini CLI Extensions](https://geminicli.com/extensions/)
- [Google MCP Support](https://cloud.google.com/blog/products/ai-machine-learning/announcing-official-mcp-support-for-google-services)
- [OpenAI ChatGPT Agent](https://openai.com/index/introducing-chatgpt-agent/)
- [x402 Protocol](https://www.x402.org/)
- [x402 + MCP via Zuplo](https://zuplo.com/blog/mcp-api-payments-with-x402)
- [Cloudflare x402 Foundation](https://blog.cloudflare.com/x402/)
- [LLM SEO Strategies](https://seo.ai/blog/llm-seo)
- [AI Search Optimization Guide](https://sapt.ai/insights/ai-search-optimization-complete-guide-chatgpt-perplexity-citations)
- [GEO Complete 2026 Guide](https://searchengineland.com/mastering-generative-engine-optimization-in-2026-full-guide-469142)
- [Structured Data for GEO](https://www.digidop.com/blog/structured-data-secret-weapon-seo)
- [Reddit and LLM Training Data](https://www.perrill.com/why-is-reddit-cited-in-llms/)
- [HN Impact on GitHub Stars](https://arxiv.org/html/2511.04453v1)
- [Dark Visitors](https://darkvisitors.com/)
- [Known Agents](https://knownagents.com/)
- [AI Crawler User-Agents List](https://www.searchenginejournal.com/ai-crawler-user-agents-list/558130/)
- [Cloudflare AI Crawler Traffic Analysis](https://blog.cloudflare.com/ai-crawler-traffic-by-purpose-and-industry/)
- [n8n Workflow Templates](https://n8n.io/workflows/)
- [n8n Community Nodes](https://docs.n8n.io/integrations/creating-nodes/deploy/submit-community-nodes/)
- [Slack Marketplace](https://docs.slack.dev/slack-marketplace/)
- [Telegram Bot Growth Strategy](https://marketingagent.blog/2026/01/08/the-complete-telegram-marketing-strategy-for-2026-direct-encrypted-and-highly-profitable/)
- [WhatsApp Business API Fintech](https://www.chatarchitect.com/news/whatsapp-business-api-in-fintech-payment-services-and-remittances/)
- [llms.txt Specification](https://llmstxt.org/)
- [API Docs for AI Agents: llms.txt Guide](https://buildwithfern.com/post/optimizing-api-docs-ai-agents-llms-txt-guide)
