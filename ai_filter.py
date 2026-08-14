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

# 系统3护栏：已运行多年、市场已形成的成熟资产，仅凭价格/预测类新闻不得升级为机会
MATURE_TYPE3_ASSETS = ("比特币", "BTC", "以太坊", "ETH", "以太")

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
3. 系统3：固定跟踪五市场——{_WATCHLIST_PROMPT}。只识别「市场尚未形成、技术刚出现」的重大突破（如比特币初现、ChatGPT发布、首个具身智能人形机器人、早期SpaceX），这是1年以上的长期布局；严禁把成熟产业的日线事件当机会（只能放 related）；给出具体可交易载体与代码，尚无载体则 code 填「先跟踪」；只有来源原文明确报道了「新技术/新产品首次出现或重大原型/商用突破」时才可列为机会，价格走势、预测、行情类新闻一律只放 related；比特币/以太坊等已运行多年、市场已形成的资产，仅凭价格或预测类新闻不得升级为机会；
4. 系统4（紫苏叶理论）硬条件五条缺一不可：{SYSTEM4_RULES}。逐项标注 industry/material_role/monopoly/moat，并说明原材料价格处于低位、市场未被炒作；违反任一条的（如光伏多晶硅、AI服务器覆铜板CCL）一律不得作为机会；
5. 标的市场只允许五类：A股、港股、美股、中国期货、加密货币；海外期货（CME商品）、外汇、CFD 等剔除；
6. 每条机会必须给出具体进出场方案、仓位、预期离场收益率、止损收益率；target_return/stop_loss 只填数值或百分比（如"+30%"、"-10%"）；
7. source_url 必须使用提供的原文链接且与标的高度相关（标题需提及该标的或其所属领域）；禁止引用无关宏观文章；
8. market_position 只输出 A股/港股/美股/黄金 四条的 judgment，位置由代码给出、不要重复输出 position 字段；
9. related 每类最多3条，opportunities 每类最多3条，宁缺毋滥；四类 sections 必须全部出现，无内容留空数组。
10. 事实纪律（防幻觉，最高优先级）：任何事实性表述（上市状态、市场阶段、成立时间、估值、市占率、涨跌幅等）必须能在所引用来源原文中找到依据；来源未提及的写「来源未提及」，严禁自行断言、猜测或编造；logic/why_possible 必须是对来源内容的转述，AI 记忆中的知识（公司上市状态、项目成立年限等）不得写入，除非来源原文支持。"""

TYPES = [1, 2, 3, 4]

# 上市状态断言（AI 常凭过时记忆编造，与新闻原文冲突）。来源未明确支持时一律从 AI 输出中剔除。
_STATUS_PAT = re.compile(
    r"[（(][^）)]*(?:未上市|已上市|尚未上市)[^）)]*[）)]"
    r"|未上市|已上市|尚未上市|已上市公司|已挂牌上市"
)


def _strip_status(text: str) -> str:
    """剔除 AI 文本中的上市状态断言，并清理残留的转折词。"""
    if not text:
        return ""
    text = _STATUS_PAT.sub("", str(text))
    text = re.sub(r"[，,]\s*但\s*[，,]", "，", text)
    return text.strip("，,；;。 ")

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
        "logic": _strip_status(o.get("logic", ""))[:120],
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
        "summary": _strip_status(r.get("summary", ""))[:120],
        "why_possible": _strip_status(r.get("why_possible", ""))[:120],
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
        "summary": _strip_status(o.get("logic", ""))[:100],
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
        downgraded = []
        if items:
            kept = []
            for o in opps:
                keep, reason = _source_check(o, url_to_title)
                if keep:
                    kept.append(o)
                elif "不在当日采集列表中" in reason or "缺少来源链接" in reason:
                    log.info("丢弃无法核实的条目：%s（%s）", o.get("target"), reason)
                else:
                    downgraded.append(_downgrade_to_related(o, reason))
            opps = kept
            # 相关线索同样校验来源：URL 缺失或不在当日采集列表的一律丢弃（疑似编造）
            rels = [r for r in rels if r.get("source_url") and r.get("source_url") in url_to_title]
        if t == 3:
            # 系统3护栏：成熟资产仅凭价格/预测类新闻不得列为「市场形成前」机会
            kept = []
            for o in opps:
                base = _target_base(o.get("target", ""))
                if any(m.lower() in base.lower() for m in MATURE_TYPE3_ASSETS):
                    downgraded.append(_downgrade_to_related(
                        o, f"『{base}』为已运行多年的成熟资产，价格/预测类新闻不符合系统3「市场形成前」条件，降级为线索"))
                else:
                    kept.append(o)
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


# ============================================================
# 板块二：产品经理热门话题（论坛/社区动态）
# ============================================================
PM_TOPICS_SYSTEM_PROMPT = """你是互联网产品经理行业的趋势观察员。给定最近从社区论坛（人人都是产品经理、牛客网等）与新闻采集到的产品经理相关热门讨论，分析行业趋势与大厂动态。

只输出合法 JSON，不要输出任何其他文字。JSON 结构：
{"trend_summary": "一句话总结今日产品经理行业趋势/热门方向", "items": [{"topic": "热门话题标题", "heat": "为什么火/热度体现在哪（1-2句）", "trend": "反映的行业趋势或方向（1-2句）", "company": "关联大厂（腾讯/美团/字节/阿里/其他，无则空）", "business": "关联业务或岗位方向（如：AI应用、商业化、本地生活）", "url": "来源链接"}]}

硬性要求：
1. 主题是「热门讨论与行业趋势」，不是招聘岗位；纯招聘JD类内容剔除；
2. 优先覆盖腾讯/美团/字节/阿里四家产品经理的最新动态：哪个方向火、哪个业务最近做得好；
3. items 最多 10 条，按热度排序；宁缺毋滥，无内容可少于 10 条甚至为空；items 中每个 url 只能出现一次（同一篇聚合日报拆出的多条新闻只保留最火的一条，其余丢弃），禁止多条话题共用同一个 url；
4. url 必须来自给定列表中，禁止编造链接；
5. 全部用中文输出。"""

_PM_TOPIC_KEYWORDS = ("产品经理", "产品运营", "产品设计", "产品", "需求", "用户增长", "商业化",
                      "AIGC", "大模型", "AI", "校招", "社招", "offer", "简历", "面试", "大厂",
                      "腾讯", "美团", "字节", "阿里")


def _clean_pm_topic_item(it: dict) -> dict:
    return {
        "topic": str(it.get("topic") or "")[:80],
        "heat": str(it.get("heat") or "")[:150],
        "trend": str(it.get("trend") or "")[:150],
        "company": str(it.get("company") or "")[:20],
        "business": str(it.get("business") or "")[:60],
        "url": str(it.get("url") or ""),
    }


_SRC_PREFIXES = ("[腾讯] ", "[人人都是产品经理] ", "[牛客网] ", "[新闻] ")


def fallback_pm_topics(items: list) -> dict:
    def score(it):
        text = str(it.get("title", "")) + " " + str(it.get("summary", ""))
        for prefix in _SRC_PREFIXES:
            text = text.replace(prefix, "")
        return sum(1 for k in _PM_TOPIC_KEYWORDS if k in text)
    out, seen = [], set()
    for it in sorted(items, key=score, reverse=True):
        title = (it.get("title") or "").strip()
        if not title or title in seen or score(it) < 2:
            continue
        seen.add(title)
        company = str(it.get("company") or "")
        if not company:
            for c in ("腾讯", "美团", "字节", "阿里", "京东", "百度"):
                if c in title:
                    company = c
                    break
        topic_text = title
        for prefix in _SRC_PREFIXES:
            topic_text = topic_text.replace(prefix, "")
        out.append(_clean_pm_topic_item({
            "topic": topic_text,
            "heat": "来自社区/新闻的高热度讨论，具体热度与讨论量见原文。",
            "trend": "规则版暂未深度分析，建议点开原文查看讨论方向。",
            "company": company,
            "business": "",
            "url": it.get("url", ""),
        }))
        if len(out) >= 10:
            break
    summary = "今日产品经理相关热门讨论见下（规则版未做深度趋势总结，配置 DeepSeek key 后自动升级）。" if out else ""
    return {"trend_summary": summary, "items": out}


def filter_pm_topics(items: list, api_key: str) -> dict:
    """返回 {'trend_summary', 'items'}；无 key/失败时降级为规则版。"""
    if api_key:
        try:
            data = _call_json(PM_TOPICS_SYSTEM_PROMPT, items, api_key)
            url_ok = {str(it.get("url", "")) for it in items}
            out, seen_urls = [], set()
            for it in (data.get("items") or []):
                if not isinstance(it, dict) or not it.get("topic"):
                    continue
                if it.get("url") and str(it.get("url")) not in url_ok:
                    it = dict(it, url="", trend=str(it.get("trend", "")) + "（来源链接未核实）")
                url = str(it.get("url") or "")
                if url and url in seen_urls:
                    continue
                seen_urls.add(url)
                out.append(_clean_pm_topic_item(it))
            if out:
                log.info("DeepSeek 产品经理话题整理成功：%d 条", len(out))
                return {"trend_summary": str(data.get("trend_summary") or ""), "items": out[:10]}
            log.warning("DeepSeek 产品经理话题输出为空，降级为规则")
        except Exception as exc:
            log.warning("DeepSeek 产品经理话题调用失败，降级为规则: %s", exc)
    return fallback_pm_topics(items)


# ============================================================
# 板块三：AI 最新技术突破（大模型优先 · 六家公司必覆盖）
# ============================================================
AI_NEWS_SYSTEM_PROMPT = """你是前沿 AI 技术分析师。给定最近采集的 AI 相关新闻（中英文混合），筛选出「最新的大模型/AI 技术突破」，其余科技新闻只有在 AI 突破没有缺位时才能补位展示。

只输出合法 JSON，不要输出任何其他文字。JSON 结构：
{"items": [{"title": "中文标题", "company": "发布方（OpenAI / Anthropic / Kimi月之暗面 / DeepSeek / 字节豆包 / Google Gemini / 其他）", "what": "突破/发布是什么（1-2句）", "impact": "为什么重要（1-2句）", "date": "发布日期", "url": "来源链接"}]}

硬性要求：
1. 只保留有实质技术内容的最新突破：新模型/能力提升、重要产品发布、开源、重要论文、重大技术决策；
2. 六家公司优先：OpenAI、Anthropic、Kimi（月之暗面）、DeepSeek、字节豆包、Google Gemini——当日信息里出现哪几家，就必须整理进去；其他公司/方向的内容只有在六家信息不缺位时才补充；
3. items 最多 5 条，按重要性排序；英文内容必须翻译成中文；
4. 剔除单纯股价、融资、营销软文、无实质内容的传闻；
5. url 必须来自给定列表中，禁止编造链接；
6. 宁缺毋滥，没有值得报的可以少于 5 条甚至为空。"""

_AI_FALLBACK_KEYWORDS = ("GPT", "模型", "发布", "开源", "机器人", "具身", "芯片", "Agent", "突破",
                         "OpenAI", "Anthropic", "Claude", "Gemini", "量子", "DeepMind", "大模型",
                         "推理", "多模态")

_AI_COMPANY_KEYWORDS = (
    ("OpenAI", ("openai", "gpt", "chatgpt", "sora")),
    ("Anthropic", ("anthropic", "claude")),
    ("Kimi 月之暗面", ("kimi", "月之暗面", "moonshot")),
    ("DeepSeek", ("deepseek", "深度求索")),
    ("字节豆包", ("豆包", "doubao", "字节跳动", "字节", "seed")),
    ("Google Gemini", ("gemini", "google", "deepmind")),
)


def detect_ai_company(text: str) -> str:
    text = text.lower()
    for name, kws in _AI_COMPANY_KEYWORDS:
        if any(k in text for k in kws):
            return name
    return ""


def _clean_ai_item(it: dict) -> dict:
    return {
        "title": str(it.get("title") or "")[:80],
        "company": str(it.get("company") or "")[:20],
        "what": str(it.get("what") or "")[:150],
        "impact": str(it.get("impact") or "")[:150],
        "date": str(it.get("date") or "")[:20],
        "url": str(it.get("url") or ""),
    }


def fallback_ai_news(items: list) -> list:
    def score(it):
        text = (str(it.get("title", "")) + " " + str(it.get("summary", ""))).lower()
        return sum(1 for k in _AI_FALLBACK_KEYWORDS if k.lower() in text)
    out, seen = [], set()
    for it in sorted(items, key=score, reverse=True):
        title = (it.get("title") or "").strip()
        if not title or title in seen or score(it) < 2:
            continue
        seen.add(title)
        out.append(_clean_ai_item({
            "title": title,
            "company": detect_ai_company(title + " " + str(it.get("summary", ""))),
            "what": (it.get("summary") or title)[:150],
            "impact": "来自科技社区/媒体的重要 AI 动态，建议点开原文核实细节。",
            "date": it.get("published", ""),
            "url": it.get("url", ""),
        }))
        if len(out) >= 5:
            break
    return out


def filter_ai_news(items: list, api_key: str) -> list:
    """返回 AI 突破列表；无 key/失败时降级为关键词规则。"""
    if api_key:
        try:
            data = _call_json(AI_NEWS_SYSTEM_PROMPT, items, api_key)
            url_ok = {str(it.get("url", "")) for it in items}
            out = []
            for it in (data.get("items") or []):
                if not isinstance(it, dict) or not it.get("what"):
                    continue
                if it.get("url") and str(it.get("url")) not in url_ok:
                    it = dict(it, url="", impact=str(it.get("impact", "")) + "（来源链接未核实）")
                if not it.get("company"):
                    it = dict(it, company=detect_ai_company(str(it.get("title", "")) + " " + str(it.get("what", ""))))
                out.append(_clean_ai_item(it))
            if out:
                log.info("DeepSeek AI突破整理成功：%d 条", len(out))
                return out[:5]
            log.warning("DeepSeek AI突破输出为空，降级为规则")
        except Exception as exc:
            log.warning("DeepSeek AI突破调用失败，降级为规则: %s", exc)
    return fallback_ai_news(items)


# ============================================================
# 板块四：被动收入方法卡（含市场分析）
# ============================================================
PASSIVE_INCOME_SYSTEM_PROMPT = """你是被动收入项目评估顾问。给定最近收集的信息（中英文混合），筛选「能用 AI 全栈能力（AI webcoding）在 1 个月内搭出自动化流程、成本低、运营压力小、只需周末人工维护」的被动收入方法，并重点做市场分析。

只输出合法 JSON，不要输出任何其他文字。JSON 结构：
{"items": [{"title": "方法名", "demand": "需求是否真实存在且供给不足（1-2句，给出判断依据）", "build": "用 AI 全栈怎么搭（具体可执行步骤）", "tech_feasibility": "AI全栈可实现性评级：高/中/低", "cost": "启动成本", "operation": "运营压力（应低成本低运营，只需周末维护）", "expected_income": "预期收益（客观保守，不夸大）", "monetizable": "可获利性判断（1-2句：变现路径是否清晰）", "risk": "主要风险", "url": "来源链接"}]}

硬性要求：
1. 宁缺毋滥，最多 3 条；
2. 必须同时满足：需求真实且缺供给、AI 可全栈实现、成本低、运营压力小（周末维护即可）、变现路径清晰；
3. 剔除需大量人工时间、需大额初始资金、或明显不靠谱的；
4. 预期收益必须客观保守，禁止承诺收益；
5. url 必须来自给定列表中，禁止编造链接；
6. 英文内容翻译成中文。"""

_PASSIVE_FALLBACK_KEYWORDS = ("passive", "income", "side project", "side-project", "indie", "副业",
                              "被动收入", "automation", "agent", "subscription", "digital product",
                              "digital download", "affiliate", "saas", "newsletter")


def _clean_passive_item(it: dict) -> dict:
    return {
        "title": str(it.get("title") or "")[:60],
        "demand": str(it.get("demand") or "")[:150],
        "build": str(it.get("build") or "")[:150],
        "tech_feasibility": str(it.get("tech_feasibility") or "中")[:4],
        "cost": str(it.get("cost") or "")[:60],
        "operation": str(it.get("operation") or "")[:120],
        "expected_income": str(it.get("expected_income") or "")[:80],
        "monetizable": str(it.get("monetizable") or "")[:150],
        "risk": str(it.get("risk") or "")[:100],
        "url": str(it.get("url") or ""),
    }


def fallback_passive_income(items: list) -> list:
    def score(it):
        text = (str(it.get("title", "")) + " " + str(it.get("summary", ""))).lower()
        return sum(1 for k in _PASSIVE_FALLBACK_KEYWORDS if k.lower() in text)
    out, seen = [], set()
    for it in sorted(items, key=score, reverse=True):
        title = (it.get("title") or "").strip()
        if not title or title in seen or score(it) < 2:
            continue
        seen.add(title)
        out.append(_clean_passive_item({
            "title": title,
            "demand": "待评估：需人工核实目标人群是否真实存在该需求且供给不足。",
            "build": "需根据原文思路用 AI 全栈搭建，具体方案待评估。",
            "tech_feasibility": "中",
            "cost": "待评估",
            "operation": "待评估（目标：低成本、低运营、周末维护）",
            "expected_income": "待评估（未经过 AI 深度分析，不承诺收益）",
            "monetizable": "待评估：需判断变现路径是否清晰。",
            "risk": "待评估；任何副业都有不确定性，需自行验证。",
            "url": it.get("url", ""),
        }))
        if len(out) >= 3:
            break
    return out


def filter_passive_income(items: list, api_key: str) -> list:
    """返回被动收入方法卡；无 key/失败时降级为关键词规则。"""
    if api_key:
        try:
            data = _call_json(PASSIVE_INCOME_SYSTEM_PROMPT, items, api_key)
            url_ok = {str(it.get("url", "")) for it in items}
            out = []
            for it in (data.get("items") or []):
                if not isinstance(it, dict) or not it.get("title"):
                    continue
                if it.get("url") and str(it.get("url")) not in url_ok:
                    it = dict(it, url="", risk=str(it.get("risk", "")) + "（来源链接未核实）")
                out.append(_clean_passive_item(it))
            if out:
                log.info("DeepSeek 被动收入整理成功：%d 条", len(out))
                return out[:3]
            log.warning("DeepSeek 被动收入输出为空，降级为规则")
        except Exception as exc:
            log.warning("DeepSeek 被动收入调用失败，降级为规则: %s", exc)
    return fallback_passive_income(items)


def _call_json(system_prompt: str, items: list, api_key: str) -> dict:
    """通用 DeepSeek JSON 调用（供新板块使用）。"""
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
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
