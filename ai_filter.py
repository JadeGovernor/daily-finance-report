"""用 DeepSeek 按用户的四大投资框架整理机会；无 key 或失败时降级为关键词规则。"""
import json
import logging

import requests

log = logging.getLogger("daily-report")

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"

FRAMEWORK = (
    "1. 周期循环（仅A股为主）：年级别牛熊周期，低位分批建仓、高位离场，如宽基ETF；\n"
    "2. 大结构震荡底部反转：关键指数或黄金等，在震荡边界做顺大趋势的反转，长线；\n"
    "3. 新兴产业：AI、太空、生物医药、比特币等新赛道，有商业想象力且位置不高时及时入场；\n"
    "4. 上游垄断（紫苏叶理论）：新兴产业崛起中寻找上游必须零部件的垄断厂商。"
)

SYSTEM_PROMPT = f"""你是专业的财经信息分析师。给定今日财经新闻，按用户的投资框架整理投资机会。

用户的四大投资框架：
{FRAMEWORK}

只输出合法 JSON，不要输出任何其他文字。JSON 结构：
{{"market_position": [{{"asset": "A股/美股/港股/黄金", "position": "周期低位区/周期高位区/震荡结构底部/震荡结构顶部/趋势中/暂无明确判断", "note": "一句话说明"}}],
"market_overview": [{{"market": "A股/港股/美股", "summary": "一句话行情解读"}}],
"sections": [
  {{"type": 1, "opportunities": [{{"target": "具体标的或方向", "logic": "为什么符合该框架", "entry_exit": "进出场思路", "position_hint": "仓位管理建议", "risk": "风险提示", "source_url": "来源链接"}}], "related": [{{"title": "标题", "summary": "一句话", "why_possible": "为什么可能相关（可能性而非明确机会）", "source_url": "来源链接"}}]}},
  {{"type": 2, "opportunities": [], "related": []}},
  {{"type": 3, "opportunities": [], "related": []}},
  {{"type": 4, "opportunities": [], "related": []}}
]}}

要求：
1. opportunities 只放明确、可操作的机会，宁缺毋滥，每条都要给出进出场与仓位思路；
2. related 放相关但非明确机会的信息或线索（政策动向、行业数据、公司动态、潜在可能）；
3. 四个大类都必须出现，没有内容就留空数组，不要硬凑；
4. source_url 必须使用提供的原文链接；
5. 长线视角，避开短线量化噪音，不构成投资建议。"""

TYPES = [1, 2, 3, 4]

FALLBACK_ENTRY_EXIT = {
    1: "分批定投/等待周期底部信号（估值分位、政策底）建仓，牛市中后期情绪过热时分批离场",
    2: "在震荡边界确认企稳后轻仓试反转，严格跟随大趋势，破位即止损",
    3: "早期小额试探建仓，跟踪商业化进展与资金流入，趋势确认后再加仓",
    4: "关注上游垄断厂商的订单与产能释放节奏，逢调整分批布局",
}
FALLBACK_POSITION = {
    1: "作为组合底仓配置，单标的建议不超过总仓位 20%，长线持有",
    2: "试探性仓位，建议不超过 10%，严格止损",
    3: "单一新赛道建议不超过 10%，分批参与，控制回撤",
    4: "作为组合的进攻仓，建议 15% 以内",
}
TYPE_KEYWORDS = {
    1: ["ETF", "指数", "牛市", "熊市", "估值", "市盈率", "A股", "上证", "沪深", "大盘", "政策底", "市场底", "降息", "放水", "周期"],
    2: ["黄金", "金价", "反转", "底部", "震荡", "支撑", "压力", "贵金属", "关键指数"],
    3: ["AI", "人工智能", "大模型", "机器人", "比特币", "加密", "太空", "航天", "生物医药", "创新药", "新赛道", "云计算"],
    4: ["上游", "零部件", "垄断", "供应链", "订单", "晶圆", "设备", "材料", "涨价", "扩产", "中标", "供不应求", "国产替代"],
}


def score_type(item: dict, type_id: int) -> int:
    text = (item.get("title", "") + " " + item.get("summary", "")).lower()
    return sum(1 for k in TYPE_KEYWORDS.get(type_id, []) if k.lower() in text)


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
        timeout=120,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
    return json.loads(content)


def _clean_opp(o: dict) -> dict:
    return {
        "target": str(o.get("target", ""))[:80],
        "logic": str(o.get("logic", ""))[:120],
        "entry_exit": str(o.get("entry_exit", ""))[:160],
        "position_hint": str(o.get("position_hint", ""))[:120],
        "risk": str(o.get("risk", ""))[:120],
        "source_url": str(o.get("source_url", "")),
    }


def _clean_rel(r: dict) -> dict:
    return {
        "title": str(r.get("title", ""))[:80],
        "summary": str(r.get("summary", ""))[:120],
        "why_possible": str(r.get("why_possible", ""))[:120],
        "source_url": str(r.get("source_url", "")),
    }


def validate_result(data: dict):
    secs_raw = {s.get("type"): s for s in (data.get("sections") or []) if isinstance(s, dict)}
    sections = []
    for t in TYPES:
        s = secs_raw.get(t, {})
        opps = [_clean_opp(o) for o in (s.get("opportunities") or []) if isinstance(o, dict) and o.get("target")]
        rels = [_clean_rel(r) for r in (s.get("related") or []) if isinstance(r, dict) and r.get("title")]
        sections.append({"type": t, "opportunities": opps[:4], "related": rels[:4]})
    market_position = [
        {"asset": str(m.get("asset", ""))[:10], "position": str(m.get("position", ""))[:14], "note": str(m.get("note", ""))[:60]}
        for m in (data.get("market_position") or [])
        if isinstance(m, dict) and m.get("asset")
    ][:4]
    market_overview = [
        {"market": str(o.get("market", ""))[:10], "summary": str(o.get("summary", ""))[:80]}
        for o in (data.get("market_overview") or [])
        if isinstance(o, dict) and o.get("market")
    ][:3]
    return sections, market_position, market_overview


def fallback_sections(items: list) -> list:
    sections = []
    for t in TYPES:
        scored = sorted(items, key=lambda it: score_type(it, t), reverse=True)
        opps, rels, seen = [], [], set()
        for it in scored:
            title = (it.get("title") or "").strip()
            if not title or title in seen:
                continue
            seen.add(title)
            s = score_type(it, t)
            if len(opps) < 2 and s >= 2:
                opps.append({
                    "target": title[:60],
                    "logic": (it.get("summary") or title)[:80],
                    "entry_exit": FALLBACK_ENTRY_EXIT[t],
                    "position_hint": FALLBACK_POSITION[t],
                    "risk": "信息来自公开网络，需自行核实；市场有波动风险，不构成投资建议。",
                    "source_url": it.get("url", ""),
                })
            elif len(rels) < 3 and s >= 1:
                rels.append({
                    "title": title[:60],
                    "summary": (it.get("summary") or "")[:100],
                    "why_possible": "与对应框架相关，可能是机会的线索，建议持续跟踪确认。",
                    "source_url": it.get("url", ""),
                })
            if len(opps) >= 2 and len(rels) >= 3:
                break
        sections.append({"type": t, "opportunities": opps, "related": rels})
    return sections


def run(items: list, api_key: str):
    """返回 (sections, market_position, market_overview)。AI 不可用时降级为规则分类。"""
    if api_key:
        try:
            data = call_deepseek(items, api_key)
            sections, mp, ov = validate_result(data)
            if any(s["opportunities"] or s["related"] for s in sections):
                log.info("DeepSeek 整理成功：%s", {s["type"]: len(s["opportunities"]) + len(s["related"]) for s in sections})
                return sections, mp, ov
            log.warning("DeepSeek 返回内容为空，降级为规则分类")
        except Exception as exc:
            log.warning("DeepSeek 调用失败，降级为规则分类: %s", exc)
    else:
        log.info("未配置 DEEPSEEK_API_KEY，使用关键词规则分类")
    return fallback_sections(items), [], []
