"""AI 筛选与规则降级测试。"""
from ai_filter import fallback_cards, score_item, validate_cards, run


def _item(title, summary="", url="http://x"):
    return {"title": title, "summary": summary, "url": url, "source": "测试"}


def test_score_priority():
    hot = _item("某公司财报预增", "业绩大幅增长，回购股份")
    plain = _item("普通天气新闻", "今天下雨")
    assert score_item(hot) > score_item(plain)


def test_fallback_cards_dedupe_and_limit():
    items = [_item(f"标题{i}", "财报 政策 并购 降息 中标 涨价 扩产 大单 回购 增持") for i in range(20)]
    items.append(items[0])  # 重复
    cards = fallback_cards(items, limit=8)
    assert 1 <= len(cards) <= 8
    titles = [c["title"] for c in cards]
    assert len(titles) == len(set(titles))
    for c in cards:
        assert c["title"] and c["event"] and c["risk"] and c["source_url"]


def test_validate_cards_clamps_and_filters():
    data = {"cards": [
        {"title": "有效卡片1", "event": "e", "impact": "i", "watch_points": "w", "risk": "r", "source_url": "u", "market": "A股"},
        {"title": "", "event": "空标题应被剔除"},
    ] + [{"title": f"卡片{n}", "event": "e", "impact": "i", "watch_points": "w", "risk": "r", "source_url": "u", "market": "A股"} for n in range(20)]}
    cards = validate_cards(data)
    assert len(cards) <= 10
    assert all(c["title"] for c in cards)
    assert all(c["risk"] for c in cards)


def test_run_without_key_falls_back():
    items = [_item("公司中标大单 财报预增", "订单饱满 扩产", "http://x/1")] * 3
    cards, overview = run(items, api_key="")
    assert len(cards) >= 1
    assert overview == []
