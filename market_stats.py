"""基于真实K线接口计算关键指数/黄金ETF的历史分位与位置判断。

数据打底：市场位置（低位/高位）由真实历史分位计算得出，杜绝 AI 编造点位。
通道：A股/港股/黄金ETF 用腾讯日K；美股指数用新浪美股日K；东财作为兜底。
"""
import json
import logging
import re
import subprocess
import time

import requests

log = logging.getLogger("daily-report")

# (key, eastmoney_secid, 显示名, 主通道, 通道代码)
ASSETS = [
    ("hs300", "1.000300", "沪深300", "tencent", "sh000300"),
    ("sz50", "1.000016", "上证50", "tencent", "sh000016"),
    ("zz500", "1.000905", "中证500", "tencent", "sh000905"),
    ("hsi", "100.HSI", "恒生指数", "tencent", "hkHSI"),
    ("spx", "100.SPX", "标普500", "sina_us", ".INX"),
    ("ndx", "100.IXIC", "纳斯达克", "sina_us", ".IXIC"),
    ("dji", "100.DJIA", "道琼斯", "sina_us", ".DJI"),
    ("gold_etf", "1.518880", "黄金ETF", "tencent", "sh518880"),
]


def _percentile(closes, cur):
    """当前价在窗口内的分位（0-100）。"""
    lo, hi = min(closes), max(closes)
    pct = (cur - lo) / (hi - lo) * 100 if hi > lo else 100.0
    return lo, hi, pct


def position_label(key: str, p1: float, p3: float) -> str:
    """按近1年/近3年分位生成位置标签；黄金用『1年分位+3年趋势』双条件。"""
    if key == "gold_etf":
        if p1 <= 45 and p3 >= 50:
            return "震荡结构底部"
        if p1 <= 30 or p3 <= 30:
            return "周期低位区"
        if p1 >= 70 and p3 >= 70:
            return "周期高位区"
        return "趋势中"
    if p1 <= 30 or p3 <= 30:
        return "周期低位区"
    if p1 >= 70 or p3 >= 70:
        return "周期高位区"
    return "区间中位"


def _judgment(key, name, price, p1, lo1, hi1, p3, lo3, hi3, pos):
    if key == "gold_etf":
        return (f"{name}最新 {price:.3f}，近1年区间 {lo1:.2f}-{hi1:.2f} 处于 {p1:.0f}% 分位，"
                f"近3年仍在 {p3:.0f}% 分位（长期上升结构未破）——符合系统2『顺大趋势回踩下沿』，可跟踪底部反转信号。")
    if key == "hsi":
        return f"恒指最新 {price:.0f}，近3年区间 {lo3:.0f}-{hi3:.0f} 处于 {p3:.0f}% 分位（{pos}），暂无系统1/2进场信号。"
    if key == "spx":
        return (f"标普500 最新 {price:.0f}，近3年区间 {lo3:.0f}-{hi3:.0f} 处于 {p3:.0f}% 分位（{pos}），"
                f"美股接近历史高位，不追高。")
    if key in ("hs300", "sz50", "zz500"):
        return (f"A股大型指数最新 {price:.0f}，近3年区间 {lo3:.0f}-{hi3:.0f} 处于 {p3:.0f}% 分位（{pos}）。"
                f"不是系统1的建仓位置，等回落到低位区（分位<30%）再分批布局。")
    return f"{name}最新 {price:.0f}，近3年区间 {lo3:.0f}-{hi3:.0f} 处于 {p3:.0f}% 分位（{pos}）。"


def _tencent_closes(sym: str) -> list:
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={sym},day,,,1500,qfq"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    resp.raise_for_status()
    data = (resp.json().get("data") or {}).get(sym) or {}
    bars = data.get("qfqday") or data.get("day") or []
    closes = [float(b[2]) for b in bars]
    if len(closes) < 60:
        raise ValueError(f"{sym} K线不足({len(closes)}条)")
    return closes


def _sina_us_closes(sym: str) -> list:
    url = f"https://stock.finance.sina.com.cn/usstock/api/jsonp_v2.php/var%20_=/US_MinKService.getDailyK?symbol={sym}"
    resp = requests.get(
        url,
        headers={"Referer": "https://finance.sina.com.cn", "User-Agent": "Mozilla/5.0"},
        timeout=20,
    )
    resp.raise_for_status()
    m = re.search(r"var\s*_=\s*\((.*)\)\s*;", resp.text, re.S)
    if not m:
        raise ValueError(f"{sym} 新浪美股响应解析失败")
    bars = json.loads(m.group(1))
    closes = [float(b["c"]) for b in bars]
    if len(closes) < 60:
        raise ValueError(f"{sym} K线不足({len(closes)}条)")
    return closes


def _eastmoney_closes(secid: str) -> list:
    """东财日K：requests 优先，curl 兜底（部分网络拒绝 python TLS 指纹）。"""
    params = {
        "secid": secid, "fields1": "f1,f2,f3",
        "fields2": "f51,f52,f53,f54,f55,f56",
        "klt": 101, "fqt": 1, "end": "20500101", "lmt": 1500,
    }
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"}
    last_exc = None
    for _ in range(2):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            resp.raise_for_status()
            closes = [float(line.split(",")[2]) for line in (resp.json().get("data") or {}).get("klines") or []]
            if len(closes) < 60:
                raise ValueError(f"{secid} K线不足({len(closes)}条)")
            return closes
        except Exception as exc:
            last_exc = exc
            time.sleep(0.5)
    try:
        from urllib.parse import urlencode
        full = url + "?" + urlencode(params)
        proc = subprocess.run(
            ["curl", "-sS", "--max-time", "25", full, "-H", "User-Agent: Mozilla/5.0"],
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr[:200] or f"curl exit {proc.returncode}")
        closes = [float(line.split(",")[2]) for line in (json.loads(proc.stdout).get("data") or {}).get("klines") or []]
        if len(closes) < 60:
            raise ValueError(f"{secid} K线不足({len(closes)}条)")
        return closes
    except Exception as exc:
        raise RuntimeError(f"{secid} 东财K线失败: {exc}") from last_exc


def _fetch_closes(key: str, secid: str, provider: str, code: str) -> list:
    if provider == "tencent":
        primary = _tencent_closes(code)
    elif provider == "sina_us":
        primary = _sina_us_closes(code)
    else:
        primary = _eastmoney_closes(secid)
    try:
        return primary
    finally:
        pass


def fetch(session=None) -> list:
    del session  # 每标的独立请求，避免连接被复用污染
    stats = []
    for key, secid, name, provider, code in ASSETS:
        closes = None
        try:
            if provider == "tencent":
                closes = _tencent_closes(code)
            elif provider == "sina_us":
                closes = _sina_us_closes(code)
            else:
                closes = _eastmoney_closes(secid)
        except Exception as exc:
            log.warning("market_stats %s 主通道失败，尝试东财兜底: %s", name, exc)
            try:
                closes = _eastmoney_closes(secid)
            except Exception as exc2:
                log.warning("market_stats %s 全部通道失败: %s", name, exc2)
                closes = None
        if not closes:
            continue
        cur = closes[-1]
        lo1, hi1, p1 = _percentile(closes[-250:], cur)
        lo3, hi3, p3 = _percentile(closes[-750:], cur)
        lo5, hi5, p5 = _percentile(closes[-1250:], cur)
        pos = position_label(key, p1, p3)
        stats.append({
            "key": key, "name": name, "price": cur,
            "pct_1y": round(p1, 1), "pct_3y": round(p3, 1), "pct_5y": round(p5, 1),
            "range_1y": (round(lo1, 3), round(hi1, 3)),
            "range_3y": (round(lo3, 3), round(hi3, 3)),
            "range_5y": (round(lo5, 3), round(hi5, 3)),
            "position": pos,
        })
        stats[-1]["judgment"] = _judgment(key, name, cur, p1, lo1, hi1, p3, lo3, hi3, pos)
        time.sleep(0.3)
    return stats


def facts_text(stats: list) -> str:
    """生成给 AI 的数据事实文本：真实点位与分位，AI 必须引用、禁止编造。"""
    lines = ["【实时数据事实 · 必须引用，禁止编造任何点位/估值】"]
    for s in stats:
        lo1, hi1 = s["range_1y"]
        lo3, hi3 = s["range_3y"]
        lines.append(
            f"- {s['name']}：最新 {s['price']:.2f}；近1年区间[{lo1:.2f},{hi1:.2f}]处于{s['pct_1y']:.0f}%分位；"
            f"近3年区间[{lo3:.2f},{hi3:.2f}]处于{s['pct_3y']:.0f}%分位 → 位置判断：{s['position']}"
        )
    return "\n".join(lines)


def build_market_position(stats: list) -> list:
    """按 4 个市场组（A股/港股/美股/黄金）输出位置研判；位置标签来自真实分位。"""
    by = {s["key"]: s for s in stats}
    out = []
    for key, asset in (("hs300", "A股"), ("hsi", "港股"), ("spx", "美股"), ("gold_etf", "黄金")):
        s = by.get(key)
        if not s:
            continue
        out.append({"asset": asset, "position": s["position"], "judgment": s["judgment"]})
    return out
