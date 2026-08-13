"""四板块组合报告测试：顺序、默认输出不变、新板块渲染。"""
from datetime import date

import report

PM_ITEMS = {"trend_summary": "AI产品经理成为大厂热门方向，商业化与AI应用是主线。", "items": [
    {"topic": "AI产品经理是2026最火方向吗", "heat": "社区讨论热度高，多篇高赞回复", "trend": "大厂产品岗向AI应用倾斜",
     "company": "腾讯", "business": "AI应用产品", "url": "https://w/1"},
]}
AI_ITEMS = [
    {"title": "OpenAI 发布新模型", "company": "OpenAI", "what": "多模态能力突破", "impact": "推动行业应用", "date": "2026-08-13", "url": "https://a/1"},
]
PASSIVE_ITEMS = [
    {"title": "AI 数字产品自动销售", "demand": "中小企业缺落地AI方案，供给不足", "build": "AI 生成 + 自动收款",
     "tech_feasibility": "高", "cost": "低", "operation": "低成本低运营，周末更新内容",
     "expected_income": "保守估计每月数百元", "monetizable": "变现路径清晰：按订阅收费", "risk": "竞争加剧", "url": "https://p/1"},
]


def test_default_output_unchanged():
    """不带新参数时，输出与 v2 版完全一致（默认标题/无新板块）。"""
    html_body, _ = report.build_report(date(2026, 8, 13), [], [], [])
    assert "📈 每日财经简报" in html_body
    assert "💼 产品经理" not in html_body
    assert "AI 最新技术突破" not in html_body


def test_extra_blocks_order():
    blocks = [
        {"html": report.build_extra_block_html("pm", PM_ITEMS), "md": report.build_extra_block_md("pm", PM_ITEMS)},
        {"html": report.build_extra_block_html("ai", AI_ITEMS), "md": report.build_extra_block_md("ai", AI_ITEMS)},
        {"html": report.build_extra_block_html("passive", PASSIVE_ITEMS), "md": report.build_extra_block_md("passive", PASSIVE_ITEMS)},
    ]
    html_body, md_body = report.build_report(
        date(2026, 8, 13), [], [], [], extra_blocks=blocks,
        title="📬 每日信息简报", subtitle="财经 · 产品经理话题 · AI 突破 · 被动收入（每日聚合）",
    )
    # 顺序：财经(板块一) → 产品经理 → AI → 被动收入 → 附
    idx_finance = html_body.index("板块一 · 财经市场概览")
    idx_pm = html_body.index("💼 产品经理热门话题")
    idx_ai = html_body.index("🤖 AI 最新技术突破")
    idx_passive = html_body.index("💰 被动收入方法")
    idx_appendix = html_body.index("📖 附 · 四大交易系统说明")
    assert idx_finance < idx_pm < idx_ai < idx_passive < idx_appendix
    assert "📬 每日信息简报" in html_body
    assert "📬 每日信息简报" in md_body


def test_pm_block_render():
    html = report.build_extra_block_html("pm", PM_ITEMS)
    assert "💼" in html and "AI产品经理是2026最火方向吗" in html
    assert "今日行业趋势" in html and "为什么火" in html and "行业趋势" in html
    assert "查看讨论" in html
    assert "今日暂无" in report.build_extra_block_html("pm", {"items": []})


def test_ai_block_render():
    html = report.build_extra_block_html("ai", AI_ITEMS)
    assert "突破：" in html and "为什么重要" in html
    assert "OpenAI" in html
    assert "今日暂无" in report.build_extra_block_html("ai", [])


def test_passive_block_render():
    html = report.build_extra_block_html("passive", PASSIVE_ITEMS)
    assert "AI可实现性：高" in html and "需求真实性/缺供给" in html and "可变现性" in html and "运营压力" in html
    assert "今日暂无" in report.build_extra_block_html("passive", [])


def test_extra_block_md():
    md = "\n".join(report.build_extra_block_md("pm", PM_ITEMS))
    assert "## 💼 产品经理热门话题" in md and "AI产品经理是2026最火方向吗" in md
    md_ai = "\n".join(report.build_extra_block_md("ai", AI_ITEMS))
    assert "## 🤖 AI 最新技术突破" in md_ai and "突破：" in md_ai
    md_passive = "\n".join(report.build_extra_block_md("passive", PASSIVE_ITEMS))
    assert "## 💰 被动收入方法" in md_passive and "可变现性" in md_passive
