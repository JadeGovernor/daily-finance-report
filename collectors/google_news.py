"""Google News RSS 关键词聚合（GitHub Actions 美国节点可访问；本地可能超时被跳过）。"""
from urllib.parse import quote

import requests
import feedparser

QUERY = "A股 OR 港股 OR 美股 OR 财报 OR 美联储 OR 降息"
BASE_URL = "https://news.google.com/rss/search"


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
            "source": "Google News",
            "published": entry.get("published", ""),
        })
    return items


def fetch(session=None, limit: int = 50) -> list:
    session = session or requests.Session()
    url = f"{BASE_URL}?q={quote(QUERY)}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
    resp = session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    resp.raise_for_status()
    return parse(feedparser.parse(resp.content).entries, limit)
