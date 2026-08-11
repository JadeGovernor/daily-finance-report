"""简报组装测试。"""
from datetime import date

import report

CARDS = [
    {"title": "半导体龙头业绩预增", "event": "Q2 净利大增", "impact": "利好板块",
     "watch_points": "关注下游需求", "risk": "行业周期波动", "source_url": "http://x/1", "market": "A股"},
]
QUOTES = [
    {"name": "上证指数", "price": "3933.62", "change": "-32.97", "pct": "-0.83"},
    {"name": "恒生指数", "price": "25998.59", "change": "-258.04", "pct": "-0.99"},
]


def test_build_report_html():
    html_body, md_body = report.build_report(date(2026, 8, 12), QUOTES, CARDS,
                                             [{"market": "A股", "summary": "缩量整理"}])
    assert "📈 每日财经简报" in html_body
    assert "2026-08-12" in html_body
    assert "半导体龙头业绩预增" in html_body
    assert "不构成任何投资建议" in html_body
    assert "上证指数" in html_body
    assert "缩量整理" in html_body
    assert "不构成任何投资建议" in md_body
    assert "### 1. 半导体龙头业绩预增" in md_body


def test_build_report_empty_cards():
    html_body, _ = report.build_report(date(2026, 8, 12), [], [])
    assert "今日暂未发现值得关注的机会型信息" in html_body


def test_build_error_report():
    html_body, md_body = report.build_error_report(date(2026, 8, 12), ["sina", "yahoo"])
    assert "⚠️" in html_body
    assert "sina、yahoo" in md_body
