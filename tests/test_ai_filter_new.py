"""三个新板块 AI 筛选函数的降级（规则）路径与清洗测试。"""
from ai_filter import (fallback_ai_news, fallback_passive_income, fallback_pm_topics,
                       filter_ai_news, filter_passive_income, filter_pm_topics)


PM_ITEMS = [
    {"title": "[人人都是产品经理] AI产品经理是2026最火方向吗", "summary": "大厂都在招AI产品", "url": "https://w/1",
     "source": "人人都是产品经理", "company": ""},
    {"title": "[牛客网] 腾讯产品经理业务复盘讨论", "summary": "讨论", "url": "https://n/1",
     "source": "牛客网", "company": "腾讯"},
    {"title": "[人人都是产品经理] 如何高效开会", "summary": "无关", "url": "https://w/2", "source": "人人都是产品经理"},
]


def test_fallback_pm_topics():
    out = fallback_pm_topics(PM_ITEMS)
    assert isinstance(out, dict) and "items" in out and "trend_summary" in out
    assert len(out["items"]) == 2  # 无关的“如何高效开会”被剔除
    assert out["items"][0]["topic"]
    assert all(it["topic"] for it in out["items"])


def test_filter_pm_topics_no_key():
    out = filter_pm_topics(PM_ITEMS, "")
    assert isinstance(out, dict) and len(out["items"]) >= 1


def test_fallback_ai_news():
    items = [
        {"title": "OpenAI 发布新模型突破", "summary": "多模态推理能力大幅提升", "url": "https://a/1", "published": "2026-08-13"},
        {"title": "某公司团建活动", "summary": "内部活动", "url": "https://a/2"},
        {"title": "Anthropic 开源新 Agent 框架", "summary": "开发者工具", "url": "https://a/3"},
    ]
    out = fallback_ai_news(items)
    assert len(out) <= 5
    assert all(it["title"] for it in out)
    assert out[0]["company"] == "OpenAI"  # 六家公司识别
    assert any(it["company"] == "Anthropic" for it in out)


def test_detect_ai_company():
    from ai_filter import detect_ai_company
    assert detect_ai_company("Gemini 2.5 发布") == "Google Gemini"
    assert detect_ai_company("Kimi 新模型月之暗面") == "Kimi 月之暗面"
    assert detect_ai_company("DeepSeek 推理模型") == "DeepSeek"
    assert detect_ai_company("豆包大模型升级") == "字节豆包"
    assert detect_ai_company("随便一条无关消息") == ""


def test_filter_ai_news_no_key():
    out = filter_ai_news([], "")
    assert out == []


def test_fallback_passive_income():
    items = [
        {"title": "我靠 AI 自动化跑 passive income 副业月入1000刀", "summary": "自动化流程", "url": "https://p/1"},
        {"title": "周末吃什么", "summary": "", "url": "https://p/2"},
        {"title": "Side project 如何用 AI agent 实现自动收款", "summary": "indie hacker", "url": "https://p/3"},
    ]
    out = fallback_passive_income(items)
    assert 1 <= len(out) <= 3
    assert out[0]["tech_feasibility"] in ("高", "中", "低")
    assert "demand" in out[0] and "monetizable" in out[0] and "operation" in out[0]


def test_filter_passive_income_no_key():
    out = filter_passive_income([], "")
    assert out == []


def test_filter_pm_topics_dedupe_url(monkeypatch):
    """AI 返回多条共用同一 url 时，代码层硬去重，每个 url 只保留一条。"""
    import ai_filter
    fake = {
        "trend_summary": "今日趋势",
        "items": [
            {"topic": "话题A", "heat": "热", "trend": "趋势", "company": "腾讯", "business": "AI", "url": "https://same/1"},
            {"topic": "话题B", "heat": "热", "trend": "趋势", "company": "美团", "business": "AI", "url": "https://same/1"},
            {"topic": "话题C", "heat": "热", "trend": "趋势", "company": "字节", "business": "AI", "url": "https://other/2"},
            {"topic": "话题D", "heat": "热", "trend": "趋势", "company": "阿里", "business": "AI", "url": "https://fake/notin"},
        ],
    }
    monkeypatch.setattr(ai_filter, "_call_json", lambda *a, **k: fake)
    out = filter_pm_topics([{"url": "https://same/1"}, {"url": "https://other/2"}], "sk-test")
    urls = [it["url"] for it in out["items"]]
    assert len(urls) == len(set(urls))  # url 互不相同
    assert urls.count("https://same/1") == 1  # 同 url 只留 1 条
    assert "https://other/2" in urls  # 其余正常条目保留
