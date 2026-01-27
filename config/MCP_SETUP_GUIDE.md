# MCP Setup Guide for News AI

This guide will help you configure the MCP servers needed for your News AI system.

---

## Required MCPs

| MCP | Purpose | Required |
|-----|---------|----------|
| Brave Search | Search news from multiple sources | Yes |
| Fetch | Scrape specific websites/RSS | Optional |
| Slack | Send daily briefing to Slack | Yes |

---

## 1. Brave Search MCP

### Step 1: Get API Key
1. Go to [Brave Search API](https://brave.com/search/api/)
2. Sign up for a free account
3. Get your API key (free tier: 2,000 queries/month)

### Step 2: Configure in OpenCode
Add to your `~/.config/opencode/config.json`:

```json
{
  "mcp": {
    "servers": {
      "brave-search": {
        "command": "npx",
        "args": ["-y", "@anthropic/mcp-server-brave-search"],
        "env": {
          "BRAVE_API_KEY": "YOUR_API_KEY_HERE"
        }
      }
    }
  }
}
```

---

## 2. Slack MCP

### Step 1: Create Slack App
1. Go to [Slack API](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name: `News AI Bot`
4. Select your workspace

### Step 2: Configure Bot Permissions
Under "OAuth & Permissions", add these scopes:
- `chat:write` - Send messages
- `channels:read` - View channels
- `files:write` - Upload files (optional)

### Step 3: Install to Workspace
1. Click "Install to Workspace"
2. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

### Step 4: Configure in OpenCode
Add to your config:

```json
{
  "mcp": {
    "servers": {
      "slack": {
        "command": "npx",
        "args": ["-y", "@anthropic/mcp-server-slack"],
        "env": {
          "SLACK_BOT_TOKEN": "xoxb-YOUR-TOKEN-HERE"
        }
      }
    }
  }
}
```

### Step 5: Invite Bot to Channel
In Slack, go to your target channel and type:
```
/invite @News AI Bot
```

---

## 3. Fetch MCP (Optional)

For scraping specific websites or RSS feeds:

```json
{
  "mcp": {
    "servers": {
      "fetch": {
        "command": "npx",
        "args": ["-y", "@anthropic/mcp-server-fetch"]
      }
    }
  }
}
```

---

## Complete Configuration Example

Here's the full `~/.config/opencode/config.json`:

```json
{
  "mcp": {
    "servers": {
      "brave-search": {
        "command": "npx",
        "args": ["-y", "@anthropic/mcp-server-brave-search"],
        "env": {
          "BRAVE_API_KEY": "YOUR_BRAVE_API_KEY"
        }
      },
      "slack": {
        "command": "npx",
        "args": ["-y", "@anthropic/mcp-server-slack"],
        "env": {
          "SLACK_BOT_TOKEN": "xoxb-YOUR-SLACK-TOKEN"
        }
      },
      "fetch": {
        "command": "npx",
        "args": ["-y", "@anthropic/mcp-server-fetch"]
      }
    }
  }
}
```

---

## Testing

After configuration, restart OpenCode and test:

1. **Test Brave Search:** Ask me to search for today's tech news
2. **Test Slack:** Ask me to send a test message to your channel

---

## Usage

Once configured, just say:

> "你好" or "Good morning"

And I will:
1. Search for today's top news across all categories
2. Create a new folder with today's date
3. Generate 今日新闻.md with the briefing
4. Send the briefing to your Slack channel

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Brave Search not working | Check API key is valid |
| Slack message fails | Ensure bot is invited to channel |
| MCP not loading | Run `npx @anthropic/mcp-server-xxx` manually to test |

---

*Last updated: 2026-01-27*
