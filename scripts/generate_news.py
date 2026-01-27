import json
import os
import random
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover - zoneinfo may be unavailable
    ZoneInfo = None


BRAVE_API_URL = "https://api.search.brave.com/res/v1/web/search"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def sanitize_domain(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc or ""
    host = host.lower().lstrip("www.")
    return host or "Unknown"


def brave_search(query: str, api_key: str, count: int = 3) -> list[dict]:
    params = urllib.parse.urlencode({"q": query, "count": str(count)})
    url = f"{BRAVE_API_URL}?{params}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "X-Subscription-Token": api_key,
        },
    )
    attempts = 0
    while True:
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            if exc.code != 429:
                body = exc.read().decode("utf-8", errors="ignore")
                raise RuntimeError(
                    f"Brave API error {exc.code} for {url}: {body or exc.reason}"
                )
            attempts += 1
            if attempts >= 3:
                raise RuntimeError(
                    f"Brave API rate limited after {attempts} attempts for {url}"
                )
            wait_seconds = 2 * attempts
            time.sleep(wait_seconds)
        except (urllib.error.URLError, socket.timeout) as exc:
            attempts += 1
            if attempts >= 3:
                raise RuntimeError(
                    f"Brave API network error after {attempts} attempts for {url}: {exc}"
                )
            time.sleep(2 * attempts)

    results = payload.get("web", {}).get("results", [])
    items = []
    for item in results:
        title = item.get("title") or ""
        url = item.get("url") or ""
        description = item.get("description") or ""
        if not title or not url:
            continue
        items.append(
            {
                "title": title,
                "url": url,
                "description": description,
                "source": sanitize_domain(url),
            }
        )
    return items


def openai_summarize(prompt: str, api_key: str, model: str) -> str:
    body = json.dumps(
        {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a news briefing assistant. Output Markdown in Chinese. "
                        "Follow the exact section order and template provided. "
                        "Do not add extra sections or Slack notes."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        OPENAI_API_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    attempts = 0
    while True:
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(
                f"OpenAI API error {exc.code} for model {model}: {body or exc.reason}"
            )
        except (urllib.error.URLError, socket.timeout) as exc:
            attempts += 1
            if attempts >= 2:
                raise RuntimeError(
                    f"OpenAI API network error after {attempts} attempts: {exc}"
                )
            time.sleep(3)

    choices = payload.get("choices", [])
    if not choices:
        raise RuntimeError("OpenAI response missing choices")
    content = choices[0].get("message", {}).get("content", "")
    if not content:
        raise RuntimeError("OpenAI response missing content")
    return content.strip()


def ensure_timezone(tz_name: str) -> datetime:
    if ZoneInfo is None:
        return datetime.now()
    try:
        return datetime.now(ZoneInfo(tz_name))
    except Exception:
        return datetime.now()


def build_prompt(date_str: str, sources: list[dict]) -> str:
    data = json.dumps(sources, ensure_ascii=False, indent=2)
    return (
        f"Date: {date_str}\n\n"
        "Please produce a Chinese news briefing in GitHub-flavored Markdown.\n"
        "Rules:\n"
        "- Use sections in this exact order: Tech & AI, Finance, Startups, Life Science, Macro Trends.\n"
        "- Use '---' horizontal rules between sections.\n"
        "- Each item uses the template:\n"
        "  ### Headline\n"
        "  **Source:** <domain>\n"
        "  **Summary:** 1-2 sentences.\n"
        "  **Why it matters:** 1 sentence.\n"
        "- If a category has insufficient items, write '暂无重点更新'.\n"
        "- End with a 'Key Takeaways' section with 3 numbered items.\n"
        "- Do not add any Slack notes.\n\n"
        "Sources (JSON):\n"
        f"{data}"
    )


def main() -> int:
    brave_key = require_env("BRAVE_API_KEY")
    openai_key = require_env("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    tz_name = os.getenv("NEWS_TIMEZONE", "Asia/Shanghai")

    now = ensure_timezone(tz_name)
    date_dir = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%Y%m%d_%H%M")

    categories = [
        {
            "name": "Tech & AI",
            "query": "AI breakthroughs semiconductors software cloud chips",
        },
        {
            "name": "Finance",
            "query": "markets macroeconomics central bank rates bonds inflation",
        },
        {
            "name": "Startups",
            "query": "startup funding venture capital seed round",
        },
        {
            "name": "Life Science",
            "query": "biotech healthcare clinical trial FDA gene therapy",
        },
        {
            "name": "Macro Trends",
            "query": "geopolitics energy climate policy",
        },
    ]

    sources = []
    for index, category in enumerate(categories):
        items = brave_search(category["query"], brave_key, count=3)
        sources.append({"category": category["name"], "items": items})
        if index < len(categories) - 1:
            time.sleep(1 + random.random())

    prompt = build_prompt(date_dir, sources)
    briefing = openai_summarize(prompt, openai_key, model)

    header = f"# 今日新闻 | {date_dir}\n\n> 早上好！以下是为你整理的今日重点资讯。\n\n---\n\n"
    content = header + briefing.strip() + "\n"

    output_dir = Path("news") / date_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"今日新闻_{timestamp}.md"
    output_path = output_dir / filename
    counter = 1
    while output_path.exists():
        filename = f"今日新闻_{timestamp}_{counter}.md"
        output_path = output_dir / filename
        counter += 1

    output_path.write_text(content, encoding="utf-8")
    print(str(output_path))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)
