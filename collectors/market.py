"""市场指数 / 黄金ETF 实时行情（新浪行情接口）。

行情代码顺序即报告展示顺序；key 用于与 market_stats 的历史分位数据对齐。
"""
import requests

CODES = [
    ("hs300", "s_sh000300"),   # 沪深300
    ("sz50", "s_sh000016"),    # 上证50
    ("zz500", "s_sh000905"),   # 中证500
    ("hsi", "rt_hkHSI"),       # 恒生指数
    ("spx", "gb_$inx"),        # 标普500
    ("ndx", "gb_$ixic"),       # 纳斯达克
    ("dji", "gb_$dji"),        # 道琼斯
    ("gold_etf", "sh518880"),  # 黄金ETF(518880)
]


def parse(text: str) -> list:
    overview = []
    for line in text.strip().splitlines():
        if "=" not in line:
            continue
        var, payload = line.split("=", 1)
        code = var.replace("var hq_str_", "").strip()
        fields = payload.strip('";').split(",")
        if not fields or fields == [""]:
            continue
        key = next((k for k, c in CODES if c == code), None)
        if key is None:
            continue
        if code.startswith("s_"):
            name, price, change, pct = fields[0], fields[1], fields[2], fields[3]
        elif code.startswith("rt_hk"):
            name, price, change, pct = fields[1], fields[2], fields[7], fields[8]
        elif code.startswith("gb_"):
            name, price, pct = fields[0], fields[1], fields[2]
            change = fields[4]
        elif code.startswith(("sh", "sz")):
            # A股股票/ETF：名称,今开,昨收,现价,最高,最低,...
            name = fields[0]
            price = fields[3]
            try:
                prev = float(fields[2])
                delta = float(price) - prev
                pct = delta / prev * 100 if prev else 0.0
                change = f"{delta:.3f}"
                pct = f"{pct:.2f}"
            except (TypeError, ValueError):
                change, pct = "", ""
        else:
            continue
        overview.append({"key": key, "name": name, "price": price, "change": change, "pct": pct})
    return overview


def fetch(session=None) -> list:
    session = session or requests.Session()
    resp = session.get(
        "https://hq.sinajs.cn/list=" + ",".join(c for _, c in CODES),
        headers={"Referer": "https://finance.sina.com.cn", "User-Agent": "Mozilla/5.0"},
        timeout=15,
    )
    resp.encoding = "gbk"
    resp.raise_for_status()
    return parse(resp.text)
