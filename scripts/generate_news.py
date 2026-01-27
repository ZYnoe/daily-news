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
from typing import Optional

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover - zoneinfo may be unavailable
    ZoneInfo = None


BRAVE_API_URL = "https://api.search.brave.com/res/v1/web/search"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
SEEN_URLS_PATH = Path("news") / ".cache" / "seen_urls.json"


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


def load_sources_config(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def load_seen_urls(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return set()
    if not isinstance(payload, list):
        return set()
    return {str(item) for item in payload if item}


def save_seen_urls(path: Path, seen: set[str], limit: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = list(seen)
    if len(ordered) > limit:
        ordered = ordered[-limit:]
    path.write_text(
        json.dumps(ordered, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def brave_search(
    query: str,
    api_key: str,
    count: int = 3,
    freshness: Optional[str] = None,
    search_lang: Optional[str] = None,
) -> list[dict]:
    params_dict = {"q": query, "count": str(count)}
    if freshness:
        params_dict["freshness"] = freshness
    if search_lang:
        params_dict["search_lang"] = search_lang
    params = urllib.parse.urlencode(params_dict)
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


def build_site_filter(sources: list[dict]) -> str:
    domains = []
    for source in sources:
        url = source.get("url") or ""
        domain = sanitize_domain(url)
        if domain != "Unknown" and domain not in domains:
            domains.append(domain)
    if not domains:
        return ""
    return " OR ".join(f"site:{domain}" for domain in domains)


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


def build_query(base: str, date_hint: Optional[str]) -> str:
    if not date_hint:
        return base
    return f"{base} {date_hint}"


def dedupe_items(items: list[dict], seen: set[str]) -> list[dict]:
    filtered = []
    for item in items:
        url = item.get("url") or ""
        if not url or url in seen:
            continue
        filtered.append(item)
    return filtered


def main() -> int:
    brave_key = require_env("BRAVE_API_KEY")
    openai_key = require_env("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    tz_name = os.getenv("NEWS_TIMEZONE", "Asia/Shanghai")
    freshness = os.getenv("NEWS_FRESHNESS", "pd")
    search_lang = os.getenv("NEWS_SEARCH_LANG", "en")
    result_count = int(os.getenv("NEWS_RESULT_COUNT", "6"))
    max_items = int(os.getenv("NEWS_MAX_ITEMS", "5"))
    dedupe_limit = int(os.getenv("NEWS_DEDUP_LIMIT", "2000"))
    use_date_hint = os.getenv("NEWS_QUERY_DATE_HINT", "1") == "1"
    shuffle_results = os.getenv("NEWS_SHUFFLE_RESULTS", "1") == "1"

    config = load_sources_config(Path("config") / "news_sources.json")
    configured_categories = (
        config.get("categories", {}) if isinstance(config, dict) else {}
    )

    now = ensure_timezone(tz_name)
    date_dir = now.strftime("%Y-%m-%d")
    date_hint = date_dir if use_date_hint else None
    timestamp = now.strftime("%Y%m%d_%H%M")

    categories = [
        {
            "key": "tech",
            "name": "Tech & AI",
            "query": "AI breakthroughs semiconductors software cloud chips",
        },
        {
            "key": "finance",
            "name": "Finance",
            "query": "markets macroeconomics central bank rates bonds inflation",
        },
        {
            "key": "startups",
            "name": "Startups",
            "query": "startup funding venture capital seed round",
        },
        {
            "key": "life_science",
            "name": "Life Science",
            "query": "biotech healthcare clinical trial FDA gene therapy",
        },
        {
            "key": "macro",
            "name": "Macro Trends",
            "query": "geopolitics energy climate policy",
        },
    ]

    sources = []
    seen_urls = load_seen_urls(SEEN_URLS_PATH)
    for index, category in enumerate(categories):
        configured = configured_categories.get(category["key"], {})
        sources_config = (
            configured.get("sources", []) if isinstance(configured, dict) else []
        )
        site_filter = build_site_filter(sources_config)
        query = category["query"]
        if site_filter:
            query = f"{query} ({site_filter})"
        queries = [build_query(query, date_hint), query]
        merged: list[dict] = []
        for candidate in queries:
            items = brave_search(
                candidate,
                brave_key,
                count=result_count,
                freshness=freshness,
                search_lang=search_lang,
            )
            filtered = dedupe_items(items, seen_urls)
            merged.extend(filtered)
            if len(merged) >= max_items:
                break
        if shuffle_results:
            random.shuffle(merged)
        final_items = merged[:max_items]
        for item in final_items:
            url = item.get("url") or ""
            if url:
                seen_urls.add(url)
        sources.append({"category": category["name"], "items": final_items})
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
    save_seen_urls(SEEN_URLS_PATH, seen_urls, dedupe_limit)
    print(str(output_path))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)
