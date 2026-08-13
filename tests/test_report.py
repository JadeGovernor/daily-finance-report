"""简报组装测试（四大框架分类版）。"""
from datetime import date

import report

QUOTES = [
    {"name": "上证指数", "price": "3933.62", "change": "-32.97", "pct": "-0.83"},
    {"name": "恒生指数", "price": "25998.59", "change": "-258.04", "pct": "-0.99"},
]
MARKET_POSITION = [{"asset": "A股", "position": "周期低位区", "note": "估值分位偏低"}, {"asset": "黄金", "position": "震荡结构底部", "note": "多头趋势中的回调边界"}]
OVERVIEW = [{"market": "A股", "summary": "缩量整理"}]
SECTIONS = [
    {"type": 1, "opportunities": [
        {"target": "沪深300 ETF", "logic": "估值处于历史低位，符合周期底部特征",
         "entry_exit": "分三批定投，情绪过热时分批离场", "position_hint": "底仓不超过20%",
         "risk": "周期可能比预期长", "source_url": "http://x/1"}],
     "related": [{"title": "央行释放流动性信号", "summary": "降准预期升温",
                  "why_possible": "政策底信号可能提前出现", "source_url": "http://x/2"}]},
    {"type": 2, "opportunities": [], "related": []},
    {"type": 3, "opportunities": [], "related": []},
    {"type": 4, "opportunities": [], "related": []},
]


def test_build_report_html():
    html_body, md_body = report.build_report(date(2026, 8, 13), QUOTES, MARKET_POSITION, OVERVIEW, SECTIONS)
    assert "📈 每日财经简报" in html_body
    assert "板块一 · 财经市场概览" in html_body
    assert "板块二 · 今日四大类机会" in html_body
    assert "周期循环（A股年级别）" in html_body
    assert "上游垄断 · 紫苏叶理论" in html_body
    assert "✅ 明确的投资机会" in html_body
    assert "ℹ️ 相关信息（可能性线索）" in html_body
    assert "沪深300 ETF" in html_body and "进出场思路" in html_body
    assert "央行释放流动性信号" in html_body
    assert "周期低位区" in html_body and "震荡结构底部" in html_body
    assert "不构成任何投资建议" in html_body
    assert "今日暂无相关内容" in html_body  # 类型2 空板块提示
    assert "### 🔴 类型1 · 周期循环（A股年级别）" in md_body
    assert "**✅ 明确的投资机会**" in md_body
    assert "**ℹ️ 相关信息（可能性线索）**" in md_body


def test_build_report_empty():
    html_body, md_body = report.build_report(date(2026, 8, 13), [], [], [], [])
    assert "今日暂无可整理内容" in html_body
    assert "不构成任何投资建议" in md_body


def test_build_error_report():
    html_body, md_body = report.build_error_report(date(2026, 8, 13), ["sina", "yahoo"])
    assert "⚠️" in html_body
    assert "sina、yahoo" in md_body
