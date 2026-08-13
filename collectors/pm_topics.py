"""产品经理热门话题聚合：人人都是产品经理（论坛RSS）+ 牛客网热门讨论 + Google News（兜底）。
聚焦腾讯/美团/字节/阿里等大厂产品经理的行业动态与热门讨论，而非招聘岗位。单源失败自动跳过。"""
import re

import feedparser
import requests

from .google_news import search as _search_news

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}

WOSHIPM_URL = "https://www.woshipm.com/feed"
NOWCODER_URL = "https://www.nowcoder.com/discuss?type=2&order=3"
COMPANIES = ("腾讯", "美团", "字节", "阿里", "阿里巴巴", "京东", "百度")
TOPIC_KEYWORDS = ("产品经理", "产品运营", "产品设计", "产品", "需求", "用户增长", "商业化",
                  "AIGC", "大模型", "AI", "校招", "社招", "offer", "简历", "面试", "大厂",
                  "腾讯", "美团", "字节", "阿里")
NEWS_QUERIES = (
    "腾讯 产品经理 业务 动态",
    "美团 产品经理 业务 动态",
    "字节跳动 产品经理 业务 动态",
    "阿里巴巴 产品经理 业务 动态",
    "AI 产品经理 趋势 热门",
)

_DISCUSS_LINK_RE = re.compile(r'href="(/discuss/\d+)[^"]*"[^>]*>(.*?)</a>', re.S)


def _title_contains_keywords(title: str) -> bool:
    return any(k in title for k in TOPIC_KEYWORDS)


def parse_woshipm(entries: list, limit: int = 30) -> list:
    items = []
    for entry in entries[: max(limit * 3, 60)]:
        title = (entry.get("title") or "").strip()
        if not title or not _title_contains_keywords(title):
            continue
        items.append({
            "title": f"[人人都是产品经理] {title}",
            "summary": (entry.get("summary") or "").strip(),
            "url": entry.get("link", ""),
            "source": "人人都是产品经理",
            "company": next((c for c in COMPANIES if c in title), ""),
            "published": entry.get("published", ""),
        })
        if len(items) >= limit:
            break
    return items


def fetch_woshipm(session=None, limit: int = 30) -> list:
    session = session or requests.Session()
    resp = session.get(WOSHIPM_URL, headers=UA, timeout=12)
    resp.raise_for_status()
    return parse_woshipm(feedparser.parse(resp.content).entries, limit)


def parse_nowcoder(html: str, limit: int = 20) -> list:
    items, seen = [], set()
    for m in _DISCUSS_LINK_RE.finditer(html):
        post_id = m.group(1)
        title = re.sub(r"<[^>]+>", " ", m.group(2))
        title = re.sub(r"\s+", " ", title).strip()
        if not title or post_id in seen or not _title_contains_keywords(title):
            continue
        seen.add(post_id)
        items.append({
            "title": f"[牛客网] {title}",
            "summary": "牛客网热门讨论（社区热度高，具体讨论量见原文）",
            "url": f"https://www.nowcoder.com/discuss/{post_id}",
            "source": "牛客网",
            "company": next((c for c in COMPANIES if c in title), ""),
            "published": "",
        })
        if len(items) >= limit:
            break
    return items


def fetch_nowcoder(session=None, limit: int = 20) -> list:
    session = session or requests.Session()
    resp = session.get(NOWCODER_URL, headers=UA, timeout=12)
    resp.raise_for_status()
    return parse_nowcoder(resp.text, limit)


def fetch_news(session=None, limit: int = 20) -> list:
    session = session or requests.Session()
    items, seen = [], set()
    for q in NEWS_QUERIES:
        for it in _search_news(q, limit=5, hl="zh-CN", gl="CN", ceid="CN:zh-Hans"):
            title = it.get("title", "")
            if not title or title in seen or not _title_contains_keywords(title):
                continue
            seen.add(title)
            items.append({
                "title": f"[新闻] {title}",
                "summary": it.get("summary", ""),
                "url": it.get("url", ""),
                "source": "Google News",
                "company": next((c for c in COMPANIES if c in title), ""),
                "published": it.get("published", ""),
            })
        if len(items) >= limit:
            break
    return items


def fetch(session=None, limit: int = 40) -> list:
    """组合三个源，单源失败自动跳过。"""
    all_items, failed = [], []
    for name, fn in (("人人都是产品经理", fetch_woshipm), ("牛客网", fetch_nowcoder), ("Google News", fetch_news)):
        try:
            got = fn(session, limit)
            all_items.extend(got)
        except Exception as exc:
            failed.append(f"{name}({exc.__class__.__name__})")
    if failed:
        import logging
        logging.getLogger("daily-report").warning("pm_topics 部分源失败: %s", ", ".join(failed))
    return all_items
