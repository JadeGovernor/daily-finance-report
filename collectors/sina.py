"""新浪财经滚动新闻（A股/国内财经）。"""
import time

import requests

URL = "https://feed.mix.sina.com.cn/api/roll/get"
PARAMS = {"pageid": 153, "lid": 2516, "num": 50, "page": 1}


def parse(payload: dict, limit: int = 50) -> list:
    rows = payload.get("result", {}).get("data", []) or []
    items = []
    for row in rows[:limit]:
        title = (row.get("title") or "").strip()
        if not title:
            continue
        ts = int(row.get("ctime", 0) or 0)
        items.append({
            "title": title,
            "summary": (row.get("intro") or row.get("summary") or "").strip(),
            "url": row.get("url", ""),
            "source": "新浪财经",
            "published": time.strftime("%Y-%m-%d %H:%M", time.localtime(ts)) if ts else "",
        })
    return items


def fetch(session=None, limit: int = 50) -> list:
    session = session or requests.Session()
    resp = session.get(URL, params=PARAMS, timeout=10)
    resp.raise_for_status()
    return parse(resp.json(), limit)
