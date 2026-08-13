"""市场分位统计测试（纯函数，不访问网络）。"""
import market_stats


def test_percentile_bounds_and_mid():
    closes = [10.0, 20.0, 30.0]
    lo, hi, p = market_stats._percentile(closes, 20.0)
    assert (lo, hi) == (10.0, 30.0) and abs(p - 50.0) < 1e-6


def test_position_label_thresholds():
    assert market_stats.position_label("hs300", 20, 25) == "周期低位区"
    assert market_stats.position_label("hs300", 80, 90) == "周期高位区"
    assert market_stats.position_label("hs300", 55, 60) == "区间中位"


def test_gold_dual_condition():
    assert market_stats.position_label("gold_etf", 36, 62) == "震荡结构底部"
    assert market_stats.position_label("gold_etf", 20, 25) == "周期低位区"
    assert market_stats.position_label("gold_etf", 90, 95) == "周期高位区"
    assert market_stats.position_label("gold_etf", 60, 80) == "趋势中"


def test_build_market_position_groups_four_markets():
    stats = [
        {"key": "hs300", "name": "沪深300", "price": 4685, "position": "周期高位区", "judgment": "A股研判", "pct_3y": 81},
        {"key": "hsi", "name": "恒生指数", "price": 25363, "position": "周期高位区", "judgment": "港股研判", "pct_3y": 80},
        {"key": "spx", "name": "标普500", "price": 7748, "position": "周期高位区", "judgment": "美股研判", "pct_3y": 100},
        {"key": "gold_etf", "name": "黄金ETF", "price": 9.02, "position": "震荡结构底部", "judgment": "黄金研判", "pct_3y": 62},
    ]
    mp = market_stats.build_market_position(stats)
    assert [m["asset"] for m in mp] == ["A股", "港股", "美股", "黄金"]
    assert mp[3]["position"] == "震荡结构底部"
    assert mp[3]["judgment"] == "黄金研判"


def test_facts_text_contains_position():
    stats = [{"key": "hs300", "name": "沪深300", "price": 4685.0, "pct_1y": 68, "pct_3y": 81,
              "range_1y": (4071, 5060), "range_3y": (3159, 5060), "position": "周期高位区"}]
    text = market_stats.facts_text(stats)
    assert "4685" in text and "周期高位区" in text
