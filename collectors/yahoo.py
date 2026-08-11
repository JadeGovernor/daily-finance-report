"""Yahoo Finance 新闻 RSS（美股；GitHub Actions 美国节点可访问，本地可能被拦）。"""
import requests
import feedparser

URL = "https://finance.yahoo.com/news/rssindex"


def parse(entries: list, limit: int = 50) -> list:
    items = []
    for entry in entries[:limit]:
        title = (entry.get("title") or "").strip()
        if not title:
            continue
        items.append({
            "title": title,
            "summary": (entry.get("summary") or "").strip(),
            "url": entry.get("link", ""),
            "source": "Yahoo Finance",
            "published": entry.get("published", ""),
        })
    return items


def fetch(session=None, limit: int = 50) -> list:
    session = session or requests.Session()
    resp = session.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    resp.raise_for_status()
    return parse(feedparser.parse(resp.content).entries, limit)
