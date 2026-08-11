"""用 DeepSeek 从新闻中筛选投资机会；无 key 或失败时降级为关键词规则。"""
import json
import logging

import requests

log = logging.getLogger("daily-report")

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"

OPPORTUNITY_KEYWORDS = [
    "财报", "业绩", "预增", "回购", "增持", "减持", "中标", "涨价", "提价",
    "政策", "降息", "加息", "并购", "重组", "上市", "IPO", "获批", "突破",
    "创新高", "合作协议", "大单", "扩产", "投产", "分红", "涨停", "大跌",
    "崩盘", "龙头", "景气", "订单",
]

SYSTEM_PROMPT = """你是专业的财经信息分析师。给定今日财经新闻列表，筛选出值得投资者关注的机会型信息（财报业绩、政策变化、并购重组、涨价、行业趋势、资金动向等）。
只输出合法 JSON，不要输出任何其他文字。JSON 格式必须为：
{"cards": [{"title": "简短标题", "event": "发生了什么", "impact": "可能的影响", "watch_points": "后续关注什么", "risk": "风险提示", "source_url": "原始链接", "market": "A股/港股/美股/宏观"}],
 "market_overview": [{"market": "A股", "summary": "一句话"}, {"market": "港股", "summary": "一句话"}, {"market": "美股", "summary": "一句话"}]}
要求：
1. cards 输出 5-10 条，按重要程度排序，各字段 40-80 字；
2. source_url 必须使用我提供的原始链接；
3. 每条机会都要有对应的 risk 提示，不构成投资建议。"""


def score_item(item: dict) -> int:
    text = (item.get("title", "") + " " + item.get("summary", "")).lower()
    return sum(1 for k in OPPORTUNITY_KEYWORDS if k in text)


def format_items(items: list) -> str:
    lines = []
    for i, it in enumerate(items[:400], 1):
        lines.append(f"{i}. [{it.get('source', '')}] {it.get('title', '')} | {it.get('summary', '')} | {it.get('url', '')}")
    return "\n".join(lines)


def call_deepseek(items: list, api_key: str) -> dict:
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": format_items(items)},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.3,
    }
    resp = requests.post(
        DEEPSEEK_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json=payload,
        timeout=90,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
    return json.loads(content)


def validate_cards(data: dict) -> list:
    cards = data.get("cards", []) or []
    clean = []
    for c in cards:
        if not isinstance(c, dict) or not c.get("title"):
            continue
        clean.append({
            "title": str(c.get("title", ""))[:80],
            "event": str(c.get("event", ""))[:120],
            "impact": str(c.get("impact", ""))[:120],
            "watch_points": str(c.get("watch_points", ""))[:120],
            "risk": str(c.get("risk", ""))[:120],
            "source_url": str(c.get("source_url", "")),
            "market": str(c.get("market", "宏观/多市场")),
        })
        if len(clean) >= 10:
            break
    return clean


def fallback_cards(items: list, limit: int = 8) -> list:
    scored = sorted(items, key=score_item, reverse=True)
    seen, cards = set(), []
    for it in scored:
        title = (it.get("title") or "").strip()
        if not title or title in seen:
            continue
        seen.add(title)
        cards.append({
            "title": title[:60],
            "event": (it.get("summary") or title)[:80],
            "impact": "可能影响相关板块与个股走势，建议结合盘面与公告进一步确认。",
            "watch_points": "关注对应公司/板块的后续公告、资金动向与成交量变化。",
            "risk": "信息来自公开网络，需自行核实；市场有波动风险，不构成投资建议。",
            "source_url": it.get("url", ""),
            "market": "宏观/多市场",
        })
        if len(cards) >= limit:
            break
    return cards


def run(items: list, api_key: str):
    """返回 (cards, market_overview)。AI 不可用时自动降级为规则筛选。"""
    if api_key:
        try:
            data = call_deepseek(items, api_key)
            cards = validate_cards(data)
            if cards:
                overview = [o for o in (data.get("market_overview") or []) if o.get("market")][:3]
                log.info("DeepSeek 筛选成功: %d 张卡片", len(cards))
                return cards, overview
            log.warning("DeepSeek 未返回有效卡片，降级为规则筛选")
        except Exception as exc:
            log.warning("DeepSeek 调用失败，降级为规则筛选: %s", exc)
    else:
        log.info("未配置 DEEPSEEK_API_KEY，使用关键词规则筛选")
    return fallback_cards(items), []
