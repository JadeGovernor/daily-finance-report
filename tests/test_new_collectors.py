"""三个新板块采集器的解析测试（不联网，只测解析逻辑）。"""
from collectors import ai_news, pm_topics

NOWCODER_HTML = """
<a href="/discuss/915186991019352064?sourceSSR=home" target="_blank" class="x"><span><span>校招产品经理求建议：offer怎么选</span></span></a>
<a href="/discuss/917437951150161920?sourceSSR=home" target="_blank" class="x"><span><span>腾讯产品经理面试经验分享</span></span></a>
<a href="/discuss/916372934183124992?sourceSSR=home" target="_blank" class="x"><span><span>游戏服务器开发一面（无关话题）</span></span></a>
"""


def test_parse_woshipm():
    entries = [
        {"title": "大厂产品经理如何做AI需求评审", "summary": "讨论", "link": "https://w/1"},
        {"title": "前端工程化实践（无关）", "summary": "", "link": "https://w/2"},
        {"title": "用户增长：美团商家端产品复盘", "summary": "", "link": "https://w/3"},
    ]
    items = pm_topics.parse_woshipm(entries, limit=10)
    assert len(items) == 2
    assert items[0]["source"] == "人人都是产品经理"
    assert items[0]["title"].startswith("[人人都是产品经理]")
    assert items[1]["company"] == "美团"


def test_parse_nowcoder():
    items = pm_topics.parse_nowcoder(NOWCODER_HTML, limit=10)
    assert len(items) == 2  # 无关的游戏帖被剔除
    assert items[0]["source"] == "牛客网"
    assert items[0]["url"].startswith("https://www.nowcoder.com/discuss/")
    assert items[1]["company"] == "腾讯"


def test_parse_rss():
    entries = [
        {"title": "OpenAI 发布新模型", "summary": "摘要", "link": "https://a/1", "published": "2026-08-13"},
        {"title": "某公司融资新闻", "summary": "", "link": "https://a/2"},
    ]
    items = ai_news.parse_rss(entries, "量子位", limit=10)
    assert len(items) == 2
    assert items[0]["lang"] == "zh"
    assert items[1]["url"] == "https://a/2"


def test_parse_rss_limit():
    entries = [{"title": f"标题{i}", "link": f"https://a/{i}"} for i in range(10)]
    items = ai_news.parse_rss(entries, "OpenAI 官方博客", limit=3)
    assert len(items) == 3
    assert items[0]["lang"] == "en"


def test_parse_anthropic():
    html = """
<a href="/news/claude-opus-5" class="z">Introducing Claude Opus 5<span>ProductJul 24, 2026</span></a>
<a href="/news/claude-sonnet-5" class="z">Introducing Claude Sonnet 5<span>ProductJun 30, 2026</span></a>
<a href="/news/hard-questions" class="z">Inviting hard questions<span>AnnouncementsJul 9, 2026</span></a>
"""
    items = ai_news.parse_anthropic(html, limit=10)
    assert len(items) == 3
    assert items[0]["title"] == "Introducing Claude Opus 5"
    assert items[0]["url"] == "https://www.anthropic.com/news/claude-opus-5"
    assert items[0]["source"] == "Anthropic 官方"
