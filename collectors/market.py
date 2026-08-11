"""三大市场指数行情（新浪行情接口）。"""
import requests

URL = "https://hq.sinajs.cn/list={codes}"
CODES = "s_sh000001,s_sz399001,rt_hkHSI,gb_$inx,gb_$ixic,gb_$dji"


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
        if code.startswith("s_"):
            name, price, change, pct = fields[0], fields[1], fields[2], fields[3]
        elif code.startswith("rt_hk"):
            name, price, change, pct = fields[1], fields[2], fields[7], fields[8]
        elif code.startswith("gb_"):
            name, price, pct = fields[0], fields[1], fields[2]
            change = fields[4]
        else:
            continue
        overview.append({"name": name, "price": price, "change": change, "pct": pct})
    return overview


def fetch(session=None) -> list:
    session = session or requests.Session()
    resp = session.get(
        URL.format(codes=CODES),
        headers={"Referer": "https://finance.sina.com.cn", "User-Agent": "Mozilla/5.0"},
        timeout=15,
    )
    resp.encoding = "gbk"
    resp.raise_for_status()
    return parse(resp.text)
