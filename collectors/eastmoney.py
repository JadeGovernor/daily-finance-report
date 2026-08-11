"""东方财富全球快讯（含港美股/宏观）。"""
import uuid

import requests

URL = "https://np-listapi.eastmoney.com/comm/web/getNewsByColumns"


def parse(payload: dict, limit: int = 50) -> list:
    rows = ((payload.get("data") or {}).get("list") or []) if payload.get("data") else []
    items = []
    for row in rows[:limit]:
        title = (row.get("title") or "").strip()
        if not title:
            continue
        items.append({
            "title": title,
            "summary": (row.get("summary") or "").strip(),
            "url": row.get("url") or row.get("uniqueUrl", ""),
            "source": row.get("mediaName") or "东方财富",
            "published": row.get("showTime", ""),
        })
    return items


def fetch(session=None, limit: int = 50) -> list:
    session = session or requests.Session()
    params = {
        "client": "web", "biz": "web_news_col", "column": 350,
        "order": 1, "needInteractData": 0,
        "page_index": 1, "page_size": min(limit, 100),
        "req_trace": uuid.uuid4().hex[:12],
    }
    resp = session.get(URL, params=params, timeout=10)
    resp.raise_for_status()
    return parse(resp.json(), limit)
