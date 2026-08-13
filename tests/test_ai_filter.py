"""AI 筛选与规则降级测试（四大交易系统·校正版）。"""
from ai_filter import (
    ALLOWED_PLATFORMS, fallback_sections, score_type, validate_result, run,
    TYPE_KEYWORDS, TYPES,
)


def _item(title, summary="", url="http://x"):
    return {"title": title, "summary": summary, "url": url, "source": "测试"}


def test_score_type_matches_keywords():
    assert score_type(_item("黄金价格突破关键阻力位 底部反转"), 2) >= 2
    assert score_type(_item("比特币区块链技术初现"), 3) >= 2
    assert score_type(_item("普通天气新闻", "今天下雨"), 1) == 0


def test_fallback_sections_assign_types_and_limits():
    items = []
    for t, kw in TYPE_KEYWORDS.items():
        for i in range(8):
            items.append(_item(f"类型{t}标题{i}", " ".join(kw[:4]), f"http://x/{t}/{i}"))
    sections = fallback_sections(items)
    assert [s["type"] for s in sections] == TYPES
    for s in sections:
        assert 0 < len(s["opportunities"]) <= 2
        assert 0 <= len(s["related"]) <= 3
        for o in s["opportunities"]:
            assert o["target"] and o["entry_exit"] and o["position_hint"]
            assert o["target_return"] and o["stop_loss"] and o["platform"]
            assert "industry" in o and "material_role" in o and "monopoly" in o and "moat" in o
        for r in s["related"]:
            assert r["title"] and r["why_possible"]


def test_validate_result_fills_all_types_dedupes_market_position():
    data = {
        "market_position": [
            {"asset": "A股", "position": "周期低位区", "judgment": "多年难遇的便宜区间"},
            {"asset": "A股", "position": "周期高位区", "judgment": "重复应被剔除"},
            {"asset": "黄金", "position": "震荡结构底部", "judgment": "回调到结构下沿"},
        ],
        "sections": [
            {"type": 1, "opportunities": [
                {"target": f"标的{i}", "code": "510300", "platform": "A股", "industry": "i", "material_role": "m",
                 "monopoly": "mo", "moat": "mt", "logic": "l", "entry_exit": "e",
                 "position_hint": "p", "target_return": "t", "stop_loss": "s", "risk": "r", "source_url": "u"}
                for i in range(5)],
             "related": [{"title": f"线索{i}", "summary": "s", "why_possible": "w", "source_url": "u"} for i in range(5)]},
            {"type": 2, "opportunities": [], "related": []},
        ],
    }
    sections, mp = validate_result(data)
    assert [s["type"] for s in sections] == TYPES
    assert len(sections[0]["opportunities"]) == 3  # 上限 3
    assert len(sections[0]["related"]) == 3
    assert [m["asset"] for m in mp] == ["A股", "黄金"]  # 去重
    assert mp[0]["judgment"] == "多年难遇的便宜区间"


def test_allowed_platforms_constraint():
    assert set(ALLOWED_PLATFORMS) == {"A股", "港股", "美股", "中国期货", "加密货币"}


def test_run_without_key_falls_back():
    items = [_item("沪深300 估值 周期 底部", "市盈率处于历史低位", "http://x/1")] * 3
    sections, mp = run(items, api_key="")
    assert any(s["opportunities"] or s["related"] for s in sections)
    assert mp == []


def test_validate_result_downgrades_unmatched_source():
    items = [
        {"title": "港股午评：恒指涨0.07%", "summary": "s", "url": "http://hk/1", "source": "t"},
        {"title": "韩国央行买入黄金ETF", "summary": "s", "url": "http://gold/1", "source": "t"},
    ]
    data = {
        "market_position": [],
        "sections": [
            {"type": 1, "opportunities": [
                {"target": "沪深300ETF", "code": "510300", "platform": "A股", "industry": "", "material_role": "",
                 "monopoly": "", "moat": "", "logic": "月线底部", "entry_exit": "e", "position_hint": "p",
                 "target_return": "+30%", "stop_loss": "-10%", "risk": "r", "source_url": "http://hk/1"}],
             "related": []},
            {"type": 2, "opportunities": [
                {"target": "黄金ETF", "code": "518880", "platform": "A股", "industry": "", "material_role": "",
                 "monopoly": "", "moat": "", "logic": "底部反转", "entry_exit": "e", "position_hint": "p",
                 "target_return": "+15%", "stop_loss": "-5%", "risk": "r", "source_url": "http://gold/1"}],
             "related": []},
            {"type": 3, "opportunities": [], "related": []},
            {"type": 4, "opportunities": [], "related": []},
        ],
    }
    sections, _ = validate_result(data, items=items, code_positions=None)
    assert sections[0]["opportunities"] == []  # 来源未提及标的 → 降级
    assert sections[0]["related"][0]["title"].startswith("【来源待核实】")
    assert sections[1]["opportunities"][0]["target"] == "黄金ETF"  # 来源匹配 → 保留


def test_validate_result_merges_code_positions_with_ai_judgment():
    data = {
        "market_position": [{"asset": "A股", "judgment": "AI补充解读"}],
        "sections": [
            {"type": 1, "opportunities": [], "related": [{"title": "x", "summary": "s", "why_possible": "w", "source_url": "u"}]},
            {"type": 2, "opportunities": [], "related": []},
            {"type": 3, "opportunities": [], "related": []},
            {"type": 4, "opportunities": [], "related": []},
        ],
    }
    code_positions = [{"asset": "A股", "position": "周期高位区", "judgment": "代码默认研判"}]
    sections, mp = validate_result(data, code_positions=code_positions)
    assert mp == [{"asset": "A股", "position": "周期高位区", "judgment": "AI补充解读"}]
    assert sections[0]["related"][0]["title"] == "x"


def test_fallback_suppresses_system1_when_a_share_high():
    items = ([_item("沪深300 估值 周期 底部", "市盈率处于历史低位", "http://x/1")] * 3
             + [_item("黄金 金价 底部 反转 震荡 支撑", "顺大趋势回踩下沿", "http://x/2")] * 3)
    mp = [
        {"asset": "A股", "position": "周期高位区", "judgment": "高位"},
        {"asset": "黄金", "position": "震荡结构底部", "judgment": "底部"},
    ]
    sections = fallback_sections(items, mp)
    s1 = next(s for s in sections if s["type"] == 1)
    assert s1["opportunities"] == []  # A股高位 → 不给系统1机会
    s2 = next(s for s in sections if s["type"] == 2)
    assert s2["opportunities"]  # 黄金底部 → 保留系统2机会
