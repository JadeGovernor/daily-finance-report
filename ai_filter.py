"""用 DeepSeek 按四大交易系统（校正版）整理机会与线索；无 key 或失败时降级为关键词规则。

市场位置判断由 market_stats 的真实分位数据生成，AI 只补解读、禁止编造点位。
"""
import json
import logging
import re

import requests

import market_stats
from trading_systems import PROMPT_FRAMEWORK, SYSTEM3_WATCHLIST, SYSTEM4_RULES

log = logging.getLogger("daily-report")

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"

ALLOWED_PLATFORMS = ("A股", "港股", "美股", "中国期货", "加密货币")

_WATCHLIST_PROMPT = "\n".join(
    f"  {i}. {w['market']}：{w['targets']}" for i, w in enumerate(SYSTEM3_WATCHLIST, 1)
)

SYSTEM_PROMPT = f"""你是专业的财经信息分析师。给定今日财经新闻 + 实时数据事实，按用户的四大交易系统整理投资机会与线索。

用户的四大交易系统（校正版）：
{PROMPT_FRAMEWORK}

只输出合法 JSON，不要输出任何其他文字。JSON 结构：
{{"market_position": [{{"asset": "A股/港股/美股/黄金", "judgment": "通俗易懂的一句话研判（必须引用数据事实中的真实点位/分位）"}}],
"sections": [
  {{"type": 1, "opportunities": [{{"target": "具体资产名称", "code": "代码", "platform": "A股/港股/美股/中国期货/加密货币", "industry": "所属新技术产业（系统4必填，其余可空）", "material_role": "原材料如何参与产业链、是否必需（系统4必填）", "monopoly": "垄断度（系统4必填，如：全球市占率约X%的寡头）", "moat": "护城河与可替换性（系统4必填）", "logic": "为什么符合该系统", "entry_exit": "具体进出场方案（价位/信号）", "position_hint": "仓位使用建议", "target_return": "预期离场收益率", "stop_loss": "止损收益率", "risk": "风险提示", "source_url": "来源链接"}}], "related": [{{"title": "标题", "summary": "一句话", "why_possible": "为什么可能相关", "source_url": "来源链接"}}]}},
  {{"type": 2, "opportunities": [], "related": []}},
  {{"type": 3, "opportunities": [], "related": []}},
  {{"type": 4, "opportunities": [], "related": []}}
]}}

硬性要求：
0. 数据约束（最高优先级）：位置判断（周期低位区/高位区/震荡结构底部等）已由真实行情分位在代码中计算并随输入给出，你不得修改位置结论，不得编造任何点位、估值、涨跌幅；研判/进出场数字只能引用数据事实中的真实价格推算。
1. 系统1：只给A股大型指数（沪深300/上证50，含其ETF/期货），必须是「月线级牛熊周期」的相对底部机会，严禁日线级别或个股。若数据事实显示A股处于「周期高位区」或「区间中位」，系统1的 opportunities 必须为空数组，可放政策/情绪类 related；
2. 系统2：关键指数/黄金的大结构震荡底部反转，顺大趋势，给出明确价位与止损；优先检查黄金ETF（518880，数据事实中位置为「震荡结构底部」才给机会；高位/趋势不明则 opportunities 为空）；
3. 系统3：固定跟踪五市场——{_WATCHLIST_PROMPT}。只识别「市场尚未形成、技术刚出现」的重大突破（如比特币初现、ChatGPT发布、首个具身智能人形机器人、早期SpaceX），这是1年以上的长期布局；严禁把成熟产业的日线事件当机会（只能放 related）；给出具体可交易载体与代码，尚无载体则 code 填「先跟踪」；
4. 系统4（紫苏叶理论）硬条件五条缺一不可：{SYSTEM4_RULES}。逐项标注 industry/material_role/monopoly/moat，并说明原材料价格处于低位、市场未被炒作；违反任一条的（如光伏多晶硅、AI服务器覆铜板CCL）一律不得作为机会；
5. 标的市场只允许五类：A股、港股、美股、中国期货、加密货币；海外期货（CME商品）、外汇、CFD 等剔除；
6. 每条机会必须给出具体进出场方案、仓位、预期离场收益率、止损收益率；target_return/stop_loss 只填数值或百分比（如"+30%"、"-10%"）；
7. source_url 必须使用提供的原文链接且与标的高度相关（标题需提及该标的或其所属领域）；禁止引用无关宏观文章；
8. market_position 只输出 A股/港股/美股/黄金 四条的 judgment，位置由代码给出、不要重复输出 position 字段；
9. related 每类最多3条，opportunities 每类最多3条，宁缺毋滥；四类 sections 必须全部出现，无内容留空数组。"""

TYPES = [1, 2, 3, 4]

FALLBACK_ENTRY_EXIT = {
    1: "月线级周期相对底部：估值分位<30%时分4-6批建仓，估值分位>80%/情绪过热时离场",
    2: "震荡下沿企稳轻仓进场，上沿分批止盈，有效跌破下沿3-5%止损",
    3: "市场未形成先跟踪，出现可交易载体后首仓≤5%试错，验证后加至10-15%，持有1年以上",
    4: "随下游订单落地分3-4批建仓，下游资本开支见顶/供需反转时离场",
}
FALLBACK_POSITION = {
    1: "组合底仓，单一标的≤20-30%总资产，不用杠杆",
    2: "试探仓，单笔≤10-15%总资产，单笔亏损控制在2-3%",
    3: "单一赛道≤15%，首仓5%试错，长期持有",
    4: "进攻仓，单一标的10-15%",
}
FALLBACK_PLATFORM = {1: "A股", 2: "黄金/中国期货", 3: "加密货币", 4: "A股"}
TYPE_KEYWORDS = {
    1: ["沪深300", "上证50", "中证", "ETF", "牛市", "熊市", "估值", "市盈率", "A股", "上证", "大盘", "政策底", "市场底", "降息", "周期"],
    2: ["黄金", "金价", "反转", "底部", "震荡", "支撑", "压力", "贵金属", "关键指数"],
    3: ["比特币", "区块链", "人工智能", "大模型", "ChatGPT", "人形机器人", "具身智能", "量子计算", "生物科技", "脑机接口", "太空", "航天", "SpaceX", "新技术", "突破"],
    4: ["上游", "零部件", "垄断", "供应链", "订单", "晶圆", "设备", "材料", "涨价", "扩产", "中标", "供不应求", "国产替代", "光模块", "PCB", "铜缆"],
}


def score_type(item: dict, type_id: int) -> int:
    text = (item.get("title", "") + " " + item.get("summary", "")).lower()
    return sum(1 for k in TYPE_KEYWORDS.get(type_id, []) if k.lower() in text)


def format_items(items: list) -> str:
    lines = []
    for i, it in enumerate(items[:400], 1):
        lines.append(f"{i}. [{it.get('source', '')}] {it.get('title', '')} | {it.get('summary', '')} | {it.get('url', '')}")
    return "\n".join(lines)


def call_deepseek(items: list, api_key: str, facts: str = "") -> dict:
    user_content = (facts + "\n\n" if facts else "") + format_items(items)
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
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
    def _no_prefix(v: str, prefixes: tuple) -> str:
        v = str(v or "")
        for pr in prefixes:
            v = v.replace(pr, "")
        return v.strip()

    def _clean_ret(v: str) -> str:
        return _no_prefix(v, ("预期离场收益率", "止损收益率", "预期收益", "目标收益"))

    return {
        "target": str(o.get("target", ""))[:60],
        "code": str(o.get("code", ""))[:30],
        "platform": str(o.get("platform", ""))[:20],
        "industry": str(o.get("industry", ""))[:80],
        "material_role": str(o.get("material_role", ""))[:120],
        "monopoly": str(o.get("monopoly", ""))[:80],
        "moat": str(o.get("moat", ""))[:120],
        "logic": str(o.get("logic", ""))[:120],
        "entry_exit": str(o.get("entry_exit", ""))[:180],
        "position_hint": str(o.get("position_hint", ""))[:120],
        "target_return": _clean_ret(o.get("target_return", ""))[:60],
        "stop_loss": _clean_ret(o.get("stop_loss", ""))[:60],
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


def _target_base(target: str) -> str:
    return re.split(r"[（(]", str(target or ""))[0].strip()


def _source_check(o: dict, url_to_title: dict):
    """校验机会的来源链接与标的是否匹配；返回 (保留 or None, 降级原因)。"""
    url = str(o.get("source_url", "")).strip()
    if not url:
        return None, "缺少来源链接，无法核实，降级为线索"
    title = url_to_title.get(url, "")
    if not title:
        return None, "来源链接不在当日采集列表中（疑似编造），无法核实，降级为线索"
    base = _target_base(o.get("target"))
    code = str(o.get("code", ""))
    if (base and base in title) or (len(code) >= 3 and code in title) or (len(base) >= 3 and base[:3] in title):
        return o, None
    return None, f"来源标题未提及标的『{base}』，结论与来源不匹配，降级为线索"


def _downgrade_to_related(o: dict, reason: str) -> dict:
    return {
        "title": f"【来源待核实】{o.get('target', '')}",
        "summary": str(o.get("logic", ""))[:100],
        "why_possible": reason,
        "source_url": str(o.get("source_url", "")),
    }


def validate_result(data: dict, items: list = None, code_positions: list = None):
    """返回 (sections, market_position)。code_positions 为代码按真实分位生成的研判。"""
    url_to_title = {str(it.get("url", "")): str(it.get("title", "")) for it in (items or [])}
    secs_raw = {s.get("type"): s for s in (data.get("sections") or []) if isinstance(s, dict)}
    sections = []
    for t in TYPES:
        s = secs_raw.get(t, {})
        opps = [_clean_opp(o) for o in (s.get("opportunities") or []) if isinstance(o, dict) and o.get("target")]
        rels = [_clean_rel(r) for r in (s.get("related") or []) if isinstance(r, dict) and r.get("title")]
        if items:
            kept, downgraded = [], []
            for o in opps:
                keep, reason = _source_check(o, url_to_title)
                if keep:
                    kept.append(o)
                else:
                    downgraded.append(_downgrade_to_related(o, reason))
            opps = kept
            rels = (downgraded + rels)[:3]
        sections.append({"type": t, "opportunities": opps[:3], "related": rels[:3]})

    mp = []
    if code_positions:
        ai_map = {m.get("asset"): m for m in (data.get("market_position") or []) if isinstance(m, dict)}
        for cp in code_positions:
            ai = ai_map.get(cp["asset"], {})
            mp.append({
                "asset": cp["asset"],
                "position": cp["position"],
                "judgment": str(ai.get("judgment") or cp.get("judgment", ""))[:80],
            })
    else:
        seen_assets = set()
        for m in (data.get("market_position") or []):
            if not isinstance(m, dict) or not m.get("asset"):
                continue
            asset = str(m.get("asset", ""))[:10]
            if asset in seen_assets:
                continue
            seen_assets.add(asset)
            mp.append({
                "asset": asset,
                "position": str(m.get("position", ""))[:14],
                "judgment": str(m.get("judgment", ""))[:80],
            })
            if len(mp) >= 4:
                break
    return sections, mp


def _data_gate(market_position: list) -> set:
    """依据真实分位位置，禁止在错误的位置给出对应系统的明确机会。"""
    gate = {m["asset"]: m["position"] for m in (market_position or [])}
    suppressed = set()
    if gate.get("A股") in ("周期高位区", "区间中位"):
        suppressed.add(1)
    if gate.get("黄金") in ("周期高位区", "震荡结构顶部"):
        suppressed.add(2)
    return suppressed


def fallback_sections(items: list, market_position: list = None) -> list:
    sections = []
    suppressed = _data_gate(market_position)
    for t in TYPES:
        scored = sorted(items, key=lambda it: score_type(it, t), reverse=True)
        opps, rels, seen = [], [], set()
        for it in scored:
            title = (it.get("title") or "").strip()
            if not title or title in seen:
                continue
            seen.add(title)
            s = score_type(it, t)
            if t not in suppressed and len(opps) < 2 and s >= 2:
                opps.append({
                    "target": title[:50],
                    "code": "需人工确认",
                    "platform": FALLBACK_PLATFORM[t],
                    "industry": "", "material_role": "", "monopoly": "", "moat": "",
                    "logic": (it.get("summary") or title)[:80],
                    "entry_exit": FALLBACK_ENTRY_EXIT[t],
                    "position_hint": FALLBACK_POSITION[t],
                    "target_return": "以系统规则为准",
                    "stop_loss": "以系统规则为准",
                    "risk": "信息来自公开网络，需自行核实；市场有波动风险，不构成投资建议。",
                    "source_url": it.get("url", ""),
                })
            elif len(rels) < 3 and s >= 1:
                rels.append({
                    "title": title[:60],
                    "summary": (it.get("summary") or "")[:100],
                    "why_possible": "与对应交易系统相关，可能是机会的线索，建议持续跟踪确认。",
                    "source_url": it.get("url", ""),
                })
            if len(opps) >= 2 and len(rels) >= 3:
                break
        sections.append({"type": t, "opportunities": opps, "related": rels})
    return sections


def run(items: list, api_key: str, stats: list = None):
    """返回 (sections, market_position)。位置研判由真实分位数据生成，AI 不可用时降级。"""
    code_positions = market_stats.build_market_position(stats) if stats else []
    if api_key:
        try:
            facts = market_stats.facts_text(stats) if stats else ""
            data = call_deepseek(items, api_key, facts)
            sections, mp = validate_result(data, items, code_positions)
            if any(s["opportunities"] or s["related"] for s in sections):
                log.info("DeepSeek 整理成功：机会 %s / 线索 %s",
                         {s["type"]: len(s["opportunities"]) for s in sections},
                         {s["type"]: len(s["related"]) for s in sections})
                return sections, mp
            log.warning("DeepSeek 返回内容为空，降级为规则分类")
        except Exception as exc:
            log.warning("DeepSeek 调用失败，降级为规则分类: %s", exc)
    else:
        log.info("未配置 DEEPSEEK_API_KEY，使用关键词规则分类")
    return fallback_sections(items, code_positions), code_positions
