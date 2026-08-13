"""AI 筛选与规则降级测试（四大框架分类版）。"""
from ai_filter import (
    fallback_sections, score_type, validate_result, run,
    TYPE_KEYWORDS, TYPES,
)


def _item(title, summary="", url="http://x"):
    return {"title": title, "summary": summary, "url": url, "source": "测试"}


def test_score_type_matches_keywords():
    assert score_type(_item("黄金价格突破关键阻力位 底部反转"), 2) >= 2
    assert score_type(_item("AI 大模型 机器人新赛道"), 3) >= 2
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
            assert o["target"] and o["entry_exit"] and o["position_hint"] and o["risk"]
        for r in s["related"]:
            assert r["title"] and r["why_possible"]


def test_validate_result_fills_all_types_and_clamps():
    data = {
        "market_position": [{"asset": "A股", "position": "周期低位区", "note": "估值分位偏低"}],
        "market_overview": [{"market": "A股", "summary": "缩量整理"}],
        "sections": [
            {"type": 1, "opportunities": [{"target": f"标的{i}", "logic": "l", "entry_exit": "e",
                                           "position_hint": "p", "risk": "r", "source_url": "u"} for i in range(6)],
             "related": [{"title": f"线索{i}", "summary": "s", "why_possible": "w", "source_url": "u"} for i in range(6)]},
            {"type": 2, "opportunities": [], "related": []},
            {"type": 3, "opportunities": [], "related": []},
        ],
    }
    sections, mp, ov = validate_result(data)
    assert [s["type"] for s in sections] == TYPES
    assert len(sections[0]["opportunities"]) == 4  # 上限 4
    assert len(sections[0]["related"]) == 4
    assert sections[1]["opportunities"] == [] and sections[3]["related"] == []
    assert mp[0]["asset"] == "A股" and ov[0]["market"] == "A股"


def test_run_without_key_falls_back():
    items = [_item("A股 估值 周期 ETF", "市盈率处于历史低位", "http://x/1")] * 3
    sections, mp, ov = run(items, api_key="")
    assert any(s["opportunities"] or s["related"] for s in sections)
    assert mp == [] and ov == []
