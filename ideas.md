# News AI System for LU Zeyu

## Overview
A personalized AI-powered news briefing system that delivers curated news every morning.

---

## 1. News AI

### Trigger
When I say "你好" or "Good morning", the AI will:
1. Search for today's top news across all categories
2. Create a folder with today's date: `news/YYYY-MM-DD/`
3. Generate `今日新闻.md` with the briefing
4. Send the briefing to Slack

### News Categories

| Category | Priority | Focus Areas |
|----------|----------|-------------|
| Tech & AI | High | AI breakthroughs, semiconductors, software, internet |
| Finance & Economy | High | Markets, investments, macroeconomics |
| Startups | Medium | Funding news, startup trends, VC insights |
| Life Science | Medium | Healthcare, biotech, longevity research |
| Macro Trends | Low | Geopolitics, energy, climate |

### Trusted Sources (English Primary)

**Tech:**
- MIT Technology Review
- Wired
- Ars Technica
- The Verge
- Hacker News

**Finance:**
- Bloomberg
- Financial Times
- The Economist
- Reuters

**Startups:**
- TechCrunch
- Crunchbase News
- Y Combinator Blog

**Life Science:**
- Nature News
- STAT News
- Science Daily

**Macro:**
- Foreign Affairs
- The Atlantic

---

## 2. Required MCP Servers

| MCP | Purpose | Setup |
|-----|---------|-------|
| `@anthropic/mcp-server-brave-search` | Search news from multiple sources | Need API key (free) |
| `@anthropic/mcp-server-slack` | Send briefing to Slack | Need Bot Token |
| `@anthropic/mcp-server-fetch` | Scrape specific sites/RSS | No setup needed |

See `config/MCP_SETUP_GUIDE.md` for detailed setup instructions.

---

## 3. File Structure

```
AI_demo/
├── news/                              # Daily news storage
│   └── YYYY-MM-DD/                    # Date-based folders
│       └── 今日新闻.md                 # Daily briefing
├── config/
│   ├── news_sources.json              # Source configuration
│   └── MCP_SETUP_GUIDE.md             # MCP setup guide
└── ideas.md                           # This file
```

---

## 4. News Briefing Format

Each daily briefing includes:
- Headline and source
- Brief summary
- "Why it matters" context
- Key takeaways at the end

---

## Setup Checklist

- [ ] Get Brave Search API key
- [ ] Create Slack App and get Bot Token
- [ ] Configure MCPs in OpenCode config
- [ ] Test by saying "你好"

---

*Last updated: 2026-01-27*
