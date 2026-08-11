from . import cnbc, eastmoney, google_news, sina, yahoo
from .market import fetch as fetch_market

# 按可靠性排序：靠前的源优先保留去重结果
SOURCES = [sina.fetch, eastmoney.fetch, cnbc.fetch, google_news.fetch, yahoo.fetch]
