"""采集器解析测试（离线 fixture，不访问网络）。"""
from collectors import cnbc, eastmoney, google_news, sina, yahoo, market


def test_sina_parse():
    payload = {
        "result": {"data": [
            {"title": "  A股今日大涨  ", "intro": "市场回暖", "url": "http://x/1", "ctime": "1786431075"},
            {"title": "", "intro": "空标题应被跳过", "url": "http://x/2", "ctime": "0"},
        ]}
    }
    items = sina.parse(payload, limit=10)
    assert len(items) == 1
    assert items[0]["title"] == "A股今日大涨"
    assert items[0]["source"] == "新浪财经"
    assert items[0]["published"]


def test_eastmoney_parse():
    payload = {"data": {"list": [
        {"title": "半导体公司业绩预增", "summary": "订单饱满", "url": "http://em/1", "mediaName": "证券时报", "showTime": "2026-08-11 09:00:00"},
        {"title": "", "summary": "x", "url": "http://em/2"},
    ]}}
    items = eastmoney.parse(payload, limit=10)
    assert len(items) == 1
    assert items[0]["source"] == "证券时报"
    assert items[0]["published"] == "2026-08-11 09:00:00"


def test_cnbc_parse():
    xml = """<?xml version="1.0" encoding="UTF-8"?><rss><channel>
    <item><title>Fed signals rate cut</title><description>Markets rally.</description>
    <link>https://www.cnbc.com/1</link><pubDate>Mon, 11 Aug 2026 01:00:00 GMT</pubDate></item>
    </channel></rss>"""
    import feedparser
    items = cnbc.parse(feedparser.parse(xml).entries)
    assert len(items) == 1
    assert items[0]["title"] == "Fed signals rate cut"
    assert items[0]["url"] == "https://www.cnbc.com/1"


def test_google_news_parse():
    xml = """<?xml version="1.0"?><rss version="2.0"><channel>
    <item><title>港股大涨</title><description>sum</description><link>http://g/1</link></item>
    </channel></rss>"""
    import feedparser
    items = google_news.parse(feedparser.parse(xml).entries)
    assert len(items) == 1
    assert items[0]["source"] == "Google News"


def test_yahoo_parse():
    xml = """<?xml version="1.0"?><rss><channel><item>
    <title>Apple beats estimates</title><link>http://y/1</link></item></channel></rss>"""
    import feedparser
    items = yahoo.parse(feedparser.parse(xml).entries)
    assert items[0]["title"] == "Apple beats estimates"


def test_market_parse():
    pass  # 行情解析见 test_market_parse_new.py
