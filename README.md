# Daily News Briefing

A scheduled workflow that generates a daily Chinese news briefing and pushes it to this repository.

## What it does

- Runs every day at 08:00 Asia/Shanghai (00:00 UTC)
- Fetches sources from Brave Search
- Summarizes with OpenAI
- Writes to `news/YYYY-MM-DD/今日新闻_YYYYMMDD_HHMM.md`
- Commits and pushes automatically

## Requirements

Set these GitHub Actions secrets in the repository settings:

- `BRAVE_API_KEY`
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (optional, default: `gpt-4o-mini`)

## Run manually

From GitHub Actions, choose the `Daily News Briefing` workflow and click `Run workflow`.

## Run locally

```bash
export BRAVE_API_KEY=...
export OPENAI_API_KEY=...
export OPENAI_MODEL=gpt-4o-mini
python scripts/generate_news.py
```

## Notes

- The workflow is defined in `.github/workflows/daily-news.yml`.
- Briefings are written in Chinese.
