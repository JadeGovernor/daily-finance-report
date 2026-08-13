"""简报组装测试（四大交易系统·校正版·数据真实化）。"""
from datetime import date

import report
from trading_systems import TRADING_SYSTEMS

QUOTES = [
    {"key": "hs300", "name": "沪深300", "price": "4684.99", "change": "-5.92", "pct": "-0.13"},
    {"key": "hsi", "name": "恒生指数", "price": "25288.07", "change": "-24.42", "pct": "-0.10"},
    {"key": "gold_etf", "name": "黄金ETF华安", "price": "9.023", "change": "-0.080", "pct": "-0.88"},
]
MARKET_STATS = [
    {"key": "hs300", "name": "沪深300", "price": 4684.99, "pct_1y": 68, "pct_3y": 81, "pct_5y": 73,
     "range_1y": (4071, 5060), "range_3y": (3159, 5060), "position": "周期高位区",
     "judgment": "A股处于高位区，不是系统1的建仓位置。"},
    {"key": "hsi", "name": "恒生指数", "price": 25363, "pct_1y": 51, "pct_3y": 80, "pct_5y": 80,
     "range_1y": (22672, 27968), "range_3y": (14961, 27968), "position": "周期高位区",
     "judgment": "港股暂无系统1/2信号。"},
    {"key": "gold_etf", "name": "黄金ETF", "price": 9.023, "pct_1y": 36, "pct_3y": 62, "pct_5y": 66,
     "range_1y": (7.374, 11.904), "range_3y": (4.348, 11.904), "position": "震荡结构底部",
     "judgment": "黄金符合系统2顺大趋势回踩。"},
]
MARKET_POSITION = [
    {"asset": "A股", "position": "周期高位区", "judgment": "A股处于高位区，等回落到低位区再分批布局。"},
    {"asset": "黄金", "position": "震荡结构底部", "judgment": "黄金符合系统2顺大趋势回踩。"},
]
SECTIONS = [
    {"type": 1, "opportunities": [], "related": []},
    {"type": 2, "opportunities": [
        {"target": "黄金ETF", "code": "518880", "platform": "A股", "industry": "", "material_role": "",
         "monopoly": "", "moat": "", "logic": "顺大趋势回踩下沿",
         "entry_exit": "9.0-9.2试探仓，10.0-10.5止盈，破8.6止损", "position_hint": "试探仓10-15%",
         "target_return": "+12%~18%", "stop_loss": "-5%", "risk": "金价波动加大", "source_url": "http://gold/1"}],
     "related": [{"title": "央行购金线索", "summary": "韩国央行买入黄金ETF", "why_possible": "支撑黄金需求", "source_url": "http://gold/2"}]},
    {"type": 3, "opportunities": [], "related": [
        {"title": "人形机器人运动会线索", "summary": "具身智能热度升温", "why_possible": "行业早期热度信号", "source_url": "http://x/2"}]},
    {"type": 4, "opportunities": [
        {"target": "贝斯特", "code": "300580", "platform": "A股", "industry": "人形机器人（行星滚柱丝杠）",
         "material_role": "丝杠是人形机器人线性关节的必需传动部件", "monopoly": "国内少数具备量产能力的厂商",
         "moat": "精密加工工艺壁垒高，短期难替代", "logic": "人形机器人量产前的必需零部件，价格处于低位",
         "entry_exit": "回踩分批建仓，下游订单落地验证", "position_hint": "进攻仓10-15%",
         "target_return": "+30%", "stop_loss": "-7%", "risk": "量产进度不及预期", "source_url": "http://x/3"}],
     "related": []},
]


def test_build_report_html():
    html_body, md_body = report.build_report(date(2026, 8, 13), QUOTES, MARKET_POSITION, SECTIONS, MARKET_STATS)
    assert "📈 每日财经简报" in html_body
    assert "数据来源：新浪实时行情 + 东方财富历史K线" in html_body
    assert "板块一 · 财经市场概览" in html_body
    assert "位置（近3年分位）" in html_body
    assert "周期高位区" in html_body and "震荡结构底部" in html_body
    assert "整体研判（逐市场" in html_body
    assert "板块二 · 今日机会与线索" in html_body
    assert "系统1 · 周期循环（A股大型指数 · 月线级牛熊）" in html_body
    assert "今日暂无：沪深300 最新 4685" in html_body  # 系统1 空 + 数据说明
    assert "前沿新技术早期侦察（市场形成前）" in html_body
    assert "五市场固定跟踪池" in html_body  # 系统3 跟踪池表格
    assert "✅ 明确的投资机会（含交易方案）" in html_body
    assert "预期离场收益率" in html_body and "止损收益率" in html_body
    # 系统4 硬条件 + 四要素
    assert "紫苏叶硬条件（五条缺一不可）" in html_body
    assert "新技术产业：" in html_body and "人形机器人（行星滚柱丝杠）" in html_body
    assert "原材料参与环节/是否必需" in html_body
    assert "垄断度" in html_body and "护城河/可替换性" in html_body
    assert "四大交易系统说明（校正版）" in html_body
    assert "### 🔴 系统1 · 周期循环（A股大型指数 · 月线级牛熊）" in md_body
    assert "## 📖 附 · 四大交易系统说明（校正版）" in md_body


def test_build_report_empty():
    html_body, md_body = report.build_report(date(2026, 8, 13), [], [], [])
    assert "今日暂无可整理内容" in html_body
    assert "不构成任何投资建议" in md_body


def test_trading_systems_cover_four_corrected():
    for key in ("系统一", "系统二", "系统三", "系统四", "月线级别", "市场尚未形成", "紫苏叶理论", "垄断度", "止损", "低价", "未热"):
        assert key in TRADING_SYSTEMS


def test_build_error_report():
    html_body, md_body = report.build_error_report(date(2026, 8, 13), ["sina", "yahoo"])
    assert "⚠️" in html_body
    assert "sina、yahoo" in md_body
