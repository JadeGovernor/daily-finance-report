"""被动收入方法信息聚合：Hacker News（主源）+ Google News（兜底）+ Reddit（可选，反爬失败即跳过）。
关键词聚焦：AI 自动化、被动收入、副业、side project。"""
import time

import requests

from .google_news import search as _search_news

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}

HN_API = "https://hn.algolia.com/api/v1/search"
HN_KEYWORDS = ("passive income", "side project", "indie hacker", "AI agent money", "automated income")
HN_LOOKBACK_SECONDS = 30 * 24 * 3600  # 近30天
REDDIT_URLS = (
    ("https://www.reddit.com/r/passive_income/top.json?t=week&limit=20", "Reddit r/passive_income"),
    ("https://www.reddit.com/r/beermoney/top.json?t=week&limit=20", "Reddit r/beermoney"),
)
NEWS_QUERIES = ("passive income AI automation", "副业 AI 自动化 被动收入", "side project profitable AI")


def fetch_hn(session=None, limit: int = 20) -> list:
    session = session or requests.Session()
    since = int(time.time()) - HN_LOOKBACK_SECONDS
    items, seen = [], set()
    for kw in HN_KEYWORDS:
        params = {
            "query": kw,
            "tags": "story",
            "hitsPerPage": 6,
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
            items.append({
                "title": title,
                "summary": (h.get("story_text") or h.get("comment_text") or "")[:200],
                "url": url,
                "source": "Hacker News",
                "lang": "en",
                "published": h.get("created_at", ""),
            })
        if len(items) >= limit:
            break
    return items


def fetch_reddit(session=None, limit: int = 10) -> list:
    session = session or requests.Session()
    items, seen = [], set()
    for url, src in REDDIT_URLS:
        try:
            resp = session.get(url, headers=UA, timeout=12)
            resp.raise_for_status()
            children = (resp.json().get("data") or {}).get("children") or []
        except Exception:
            continue
        for c in children:
            d = (c.get("data") or {})
            title = (d.get("title") or "").strip()
            if not title or title in seen:
                continue
            seen.add(title)
            items.append({
                "title": title,
                "summary": (d.get("selftext") or "")[:200],
                "url": f"https://www.reddit.com{d.get('permalink','')}",
                "source": src,
                "lang": "en",
                "published": time.strftime("%Y-%m-%d", time.localtime(d.get("created_utc", 0))) if d.get("created_utc") else "",
            })
        if len(items) >= limit:
            break
    return items


def fetch_news(session=None, limit: int = 10) -> list:
    session = session or requests.Session()
    items, seen = [], set()
    for q in NEWS_QUERIES:
        for it in _search_news(q, limit=5, hl="zh-CN", gl="CN", ceid="CN:zh-Hans"):
            title = it.get("title", "")
            if not title or title in seen:
                continue
            seen.add(title)
            items.append({
                "title": title,
                "summary": it.get("summary", ""),
                "url": it.get("url", ""),
                "source": "Google News",
                "lang": "zh" if any(ord(ch) > 0x4E00 for ch in title) else "en",
                "published": it.get("published", ""),
            })
        if len(items) >= limit:
            break
    return items


def fetch(session=None, limit: int = 30) -> list:
    """组合三个源，单源失败自动跳过（Reddit 反爬失败属预期）。"""
    all_items, failed = [], []
    for name, fn in (("Hacker News", fetch_hn), ("Reddit", fetch_reddit), ("Google News", fetch_news)):
        try:
            got = fn(session, limit)
            all_items.extend(got)
        except Exception as exc:
            failed.append(f"{name}({exc.__class__.__name__})")
    if failed:
        import logging
        logging.getLogger("daily-report").warning("passive_income 部分源失败: %s", ", ".join(failed))
    return all_items
