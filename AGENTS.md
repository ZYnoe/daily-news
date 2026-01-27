# AGENTS.md - AI Agent Guidelines for AI_demo

This document provides instructions for AI coding agents working in this repository.

---

## Project Overview

A **personalized AI-powered news briefing system** that delivers curated news every morning.
Uses MCP servers for web search (Brave) and Slack integration.

- **Primary Language**: English (Chinese output for briefings)
- **Package Manager**: Pixi (conda-based)
- **Platform**: macOS (osx-arm64)

---

## Project Structure

```
AI_demo/
├── news/YYYY-MM-DD/今日新闻.md  # Daily briefings
├── config/
│   ├── news_sources.json       # Source configuration
│   └── MCP_SETUP_GUIDE.md      # MCP setup instructions
├── ideas.md                    # Project documentation
├── pixi.toml                   # Pixi configuration
└── AGENTS.md                   # This file
```

---

## Build / Environment Commands

```bash
pixi install              # Install dependencies
pixi run <task-name>      # Run a task
pixi add <package>        # Add a dependency
pixi shell                # Activate environment
```

**Testing**: No test framework configured. Use `pytest` if adding Python tests.

---

## MCP Server Configuration

| MCP Server | Purpose | Required |
|------------|---------|----------|
| `@anthropic/mcp-server-brave-search` | Search news sources | Yes |
| `@anthropic/mcp-server-slack` | Send briefings | Yes |
| `@anthropic/mcp-server-fetch` | Scrape websites/RSS | Optional |

See `config/MCP_SETUP_GUIDE.md` for setup details.

---

## News Briefing Workflow

**Triggers**: "你好" or "Good morning"

**Steps**:
1. Search for today's top news across all categories
2. Create folder: `news/YYYY-MM-DD/`
3. Generate `今日新闻.md` with the briefing
4. Send briefing to Slack channel `#daily-news`

### News Categories (by priority)

| Priority | Category | Focus Areas |
|----------|----------|-------------|
| High | Tech & AI | AI breakthroughs, semiconductors, software |
| High | Finance | Markets, investments, macroeconomics |
| Medium | Startups | Funding news, VC insights |
| Medium | Life Science | Healthcare, biotech, longevity |
| Low | Macro Trends | Geopolitics, energy, climate |

---

## Code Style Guidelines

### Naming Conventions

- **Config files**: lowercase with underscores (`news_sources.json`)
- **Documentation**: PascalCase (`MCP_SETUP_GUIDE.md`)
- **News folders**: ISO date format (`YYYY-MM-DD`)
- **News files**: Chinese names (`今日新闻.md`)

### JSON Format

```json
{
  "category_name": {
    "priority": "high",
    "sources": [
      { "name": "Source", "url": "https://...", "type": "web" }
    ]
  }
}
```
- 2-space indentation, trailing newline, snake_case keys

### Markdown Format

- GitHub-flavored Markdown
- Horizontal rules (`---`) between sections
- Tables for structured data
- Hierarchical headers (H1 > H2 > H3)

### News Item Template

```markdown
### Headline Here
**Source:** TechCrunch (or Hacker News with point count)
**Summary:** Brief 1-2 sentence description.
**Why it matters:** Context about significance.
```

---

## Error Handling

- If Brave Search unavailable: note it in the briefing
- If Slack fails: save locally first, then inform user
- Always create local markdown before Slack delivery

---

## Language Preferences

| Context | Language |
|---------|----------|
| Search queries | English |
| News briefing output | Chinese |
| Documentation | English |

---

## Quick Reference

| Task | Command/Action |
|------|----------------|
| Generate briefing | Say "你好" or "Good morning" |
| Check sources | Read `config/news_sources.json` |
| View past briefings | Check `news/YYYY-MM-DD/` |
| MCP setup | Read `config/MCP_SETUP_GUIDE.md` |

---

## Notes for AI Agents

1. **Always check the date** when creating news folders
2. **Prioritize high-priority categories** in the briefing
3. **Use Brave Search MCP** for real-time news search
4. **Format news items consistently** using the template above
5. **Include Key Takeaways section** at the end
6. **Save locally first**, then send to Slack
7. **Cite sources** - include HN point counts when applicable
8. **Never overwrite an existing briefing** - always create a new file in the same date folder using a timestamped name like `今日新闻_YYYYMMDD_HHMM.md`

---

*Last updated: 2026-01-27*
