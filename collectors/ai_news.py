"""AI 最新技术突破信息聚合：量子位（中文）+ OpenAI/Anthropic/Google AI 官方（英文）+ Hacker News（英文）。
中英文都收，由 AI 筛选时统一整理成中文；覆盖 OpenAI/Anthropic/Kimi/DeepSeek/豆包/Gemini 六家。单源失败自动跳过。"""
import re
import time

import feedparser
import requests

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}

QBITAI_URL = "https://www.qbitai.com/feed"
OPENAI_URL = "https://openai.com/news/rss.xml"
ANTHROPIC_URL = "https://www.anthropic.com/news"
GOOGLE_AI_URL = "https://blog.google/technology/ai/rss/"
HN_API = "https://hn.algolia.com/api/v1/search"
HN_KEYWORDS = ("GPT", "artificial intelligence", "AGI", "LLM", "humanoid robot", "OpenAI", "Anthropic", "Gemini")
HN_LOOKBACK_SECONDS = 48 * 3600  # 近48小时


def parse_rss(entries: list, source: str, limit: int = 20) -> list:
    items = []
    for entry in entries[: max(limit * 3, 40)]:
        title = (entry.get("title") or "").strip()
        if not title:
            continue
        items.append({
            "title": title,
            "summary": (entry.get("summary") or entry.get("description") or "").strip(),
            "url": entry.get("link", ""),
            "source": source,
            "lang": "zh" if source in ("量子位",) else "en",
            "published": entry.get("published", entry.get("updated", "")),
        })
        if len(items) >= limit:
            break
    return items


def fetch_qbitai(session=None, limit: int = 20) -> list:
    session = session or requests.Session()
    resp = session.get(QBITAI_URL, headers=UA, timeout=12)
    resp.raise_for_status()
    return parse_rss(feedparser.parse(resp.content).entries, "量子位", limit)


def fetch_openai(session=None, limit: int = 10) -> list:
    session = session or requests.Session()
    resp = session.get(OPENAI_URL, headers=UA, timeout=12)
    resp.raise_for_status()
    return parse_rss(feedparser.parse(resp.content).entries, "OpenAI 官方博客", limit)


def fetch_hn(session=None, limit: int = 20) -> list:
    session = session or requests.Session()
    since = int(time.time()) - HN_LOOKBACK_SECONDS
    items, seen = [], set()
    for kw in HN_KEYWORDS:
        params = {
            "query": kw,
            "tags": "story",
            "hitsPerPage": 5,
            "numericFilters": f"created_at_i>{since}",
        }
        try:
            resp = session.get(HN_API, params=params, headers=UA, timeout=12)
            resp.raise_for_status()
            hits = resp.json().get("hits") or []
        except Exception:
            continue
        for h in hits:
            title = (h.get("title") or "").strip()
            url = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID','')}"
            if not title or title in seen:
                continue
            seen.add(title)
            created = h.get("created_at", "")
            items.append({
                "title": title,
                "summary": (h.get("story_text") or h.get("comment_text") or "")[:200],
                "url": url,
                "source": "Hacker News",
                "lang": "en",
                "published": created,
            })
        if len(items) >= limit:
            break
    return items



_ANTHROPIC_LINK_RE = re.compile(r'href="(/news/[a-z0-9-]+)"[^>]*>\s*([^<]+)')


def parse_anthropic(html: str, limit: int = 10) -> list:
    items, seen = [], set()
    for m in _ANTHROPIC_LINK_RE.finditer(html):
        slug = m.group(1)
        title = m.group(2).strip()
        if not title or len(title) < 8 or slug in seen:
            continue
        seen.add(slug)
        items.append({
            "title": title,
            "summary": "Anthropic 官方新闻",
            "url": f"https://www.anthropic.com{slug}",
            "source": "Anthropic 官方",
            "lang": "en",
            "published": "",
        })
        if len(items) >= limit:
            break
    return items


def fetch_anthropic(session=None, limit: int = 10) -> list:
    session = session or requests.Session()
    resp = session.get(ANTHROPIC_URL, headers=UA, timeout=12)
    resp.raise_for_status()
    return parse_anthropic(resp.text, limit)


def fetch_google_ai(session=None, limit: int = 10) -> list:
    session = session or requests.Session()
    resp = session.get(GOOGLE_AI_URL, headers=UA, timeout=12)
    resp.raise_for_status()
    return parse_rss(feedparser.parse(resp.content).entries, "Google AI Blog", limit)


def fetch(session=None, limit: int = 40) -> list:
    """组合三个源，单源失败自动跳过。"""
    all_items, failed = [], []
    for name, fn in (("量子位", fetch_qbitai), ("OpenAI 官方博客", fetch_openai),
                         ("Anthropic 官方", fetch_anthropic), ("Google AI Blog", fetch_google_ai), ("Hacker News", fetch_hn)):
        try:
            got = fn(session, limit)
            all_items.extend(got)
        except Exception as exc:
            failed.append(f"{name}({exc.__class__.__name__})")
    if failed:
        import logging
        logging.getLogger("daily-report").warning("ai_news 部分源失败: %s", ", ".join(failed))
    return all_items
