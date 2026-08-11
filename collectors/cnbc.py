"""CNBC 头条新闻 RSS（美股/全球，本地可访问的兜底源）。"""
import requests
import feedparser

URL = "https://www.cnbc.com/id/100003114/device/rss/rss.html"


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
            "source": "CNBC",
            "published": entry.get("published", ""),
        })
    return items


def fetch(session=None, limit: int = 50) -> list:
    session = session or requests.Session()
    resp = session.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    resp.raise_for_status()
    return parse(feedparser.parse(resp.content).entries, limit)
