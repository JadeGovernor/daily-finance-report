"""组装 HTML / Markdown 简报（四大框架分类版）。"""
import html as html_mod

TYPE_META = {
    1: {"title": "周期循环（A股年级别）", "color": "#e53935", "icon": "🔴"},
    2: {"title": "大结构震荡底部反转（指数/黄金）", "color": "#1e88e5", "icon": "🔵"},
    3: {"title": "新兴产业（AI/太空/生物医药/比特币）", "color": "#43a047", "icon": "🟢"},
    4: {"title": "上游垄断 · 紫苏叶理论", "color": "#8e24aa", "icon": "🟣"},
}

POSITION_COLOR = {
    "周期低位区": "#2e7d32", "震荡结构底部": "#2e7d32",
    "周期高位区": "#c62828", "震荡结构顶部": "#c62828",
    "趋势中": "#1565c0", "暂无明确判断": "#757575",
}


def _fmt_quote(q: dict) -> str:
    pct = q.get("pct", "")
    try:
        pct_f = float(pct)
    except (TypeError, ValueError):
        pct_f = None
    color = "#c62828" if pct_f is not None and pct_f > 0 else "#1565c0" if pct_f is not None and pct_f < 0 else "#333"
    sign = "+" if pct_f is not None and pct_f > 0 else ""
    return f"<td style='padding:6px 10px;border-bottom:1px solid #eee'>{html_mod.escape(q.get('name',''))}</td>" \
           f"<td style='padding:6px 10px;border-bottom:1px solid #eee;text-align:right'>{html_mod.escape(str(q.get('price','')))}</td>" \
           f"<td style='padding:6px 10px;border-bottom:1px solid #eee;text-align:right;color:{color}'>" \
           f"{html_mod.escape(str(q.get('change','')))} ({sign}{html_mod.escape(str(pct))}%)</td>"


def _quotes_html(quotes: list) -> str:
    if not quotes:
        return "<p>行情数据暂不可用。</p>"
    rows = "".join(_fmt_quote(q) for q in quotes)
    return f"""<table style="width:100%;border-collapse:collapse;font-size:14px">
<tr style="background:#f5f7fa"><th style="padding:6px 10px;text-align:left">指数</th>
<th style="padding:6px 10px;text-align:right">最新</th>
<th style="padding:6px 10px;text-align:right">涨跌</th></tr>{rows}</table>"""


def _market_position_html(market_position: list) -> str:
    if not market_position:
        return ""
    items = "".join(
        f"<li style='margin:4px 0;font-size:14px;color:#333'><b>{html_mod.escape(m.get('asset',''))}：</b>"
        f"<span style='color:{POSITION_COLOR.get(m.get('position',''), '#333')}'>{html_mod.escape(m.get('position',''))}</span>"
        f" — {html_mod.escape(m.get('note',''))}</li>"
        for m in market_position
    )
    return f"<h3 style='font-size:14px;color:#1a237e;margin:12px 0 6px'>📍 AI 市场位置判断</h3><ul style='padding-left:20px;margin:0'>{items}</ul>"


def _overview_html(overview: list) -> str:
    if not overview:
        return ""
    items = "".join(
        f"<li style='margin:4px 0;font-size:14px;color:#333'><b>{html_mod.escape(o.get('market',''))}：</b>{html_mod.escape(o.get('summary',''))}</li>"
        for o in overview
    )
    return f"<ul style='padding-left:20px;margin:8px 0 0'>{items}</ul>"


def _opportunity_html(color: str, o: dict) -> str:
    url = o.get("source_url", "")
    link = f"<a href='{html_mod.escape(url)}' style='color:#1565c0'>原文链接</a>" if url else ""
    return f"""<div style="border:1px solid {color};border-left:4px solid {color};border-radius:6px;padding:10px 14px;margin:8px 0;background:#fff">
<div style="font-weight:600;font-size:14px;color:#222">🎯 {html_mod.escape(o.get('target',''))}</div>
<p style="margin:4px 0;font-size:13px;color:#444"><b>逻辑：</b>{html_mod.escape(o.get('logic',''))}</p>
<p style="margin:4px 0;font-size:13px;color:#444"><b>进出场思路：</b>{html_mod.escape(o.get('entry_exit',''))}</p>
<p style="margin:4px 0;font-size:13px;color:#444"><b>仓位提示：</b>{html_mod.escape(o.get('position_hint',''))}</p>
<p style="margin:4px 0;font-size:13px;color:#b71c1c"><b>风险：</b>{html_mod.escape(o.get('risk',''))}</p>
<p style="margin:6px 0 0;font-size:12px;color:#888">{link}</p></div>"""


def _related_html(r: dict) -> str:
    url = r.get("source_url", "")
    link = f"<a href='{html_mod.escape(url)}' style='color:#1565c0'>原文链接</a>" if url else ""
    return f"""<div style="border:1px dashed #bdbdbd;border-radius:6px;padding:8px 12px;margin:8px 0;background:#fafafa">
<div style="font-weight:600;font-size:13px;color:#444">ℹ️ {html_mod.escape(r.get('title',''))}</div>
<p style="margin:4px 0;font-size:13px;color:#555">{html_mod.escape(r.get('summary',''))}</p>
<p style="margin:4px 0;font-size:12px;color:#8e8e8e"><b>为什么可能相关：</b>{html_mod.escape(r.get('why_possible',''))}</p>
<p style="margin:6px 0 0;font-size:12px;color:#888">{link}</p></div>"""


def _section_html(t: int, section: dict) -> str:
    meta = TYPE_META[t]
    head = f"<h2 style='font-size:16px;color:{meta['color']};margin:0'>{meta['icon']} 类型{t} · {meta['title']}</h2>"
    if not (section["opportunities"] or section["related"]):
        return (f"<div style='margin:18px 0 4px'>{head}"
                f"<p style='color:#999;font-size:13px;margin:6px 0 0'>今日暂无相关内容，不硬凑。</p></div>")
    parts = [f"<div style='margin:18px 0 4px'>{head}</div>"]
    if section["opportunities"]:
        parts.append("<h3 style='font-size:14px;color:#2e7d32;margin:10px 0 4px'>✅ 明确的投资机会</h3>")
        parts.append("".join(_opportunity_html(meta["color"], o) for o in section["opportunities"]))
    if section["related"]:
        parts.append("<h3 style='font-size:14px;color:#757575;margin:10px 0 4px'>ℹ️ 相关信息（可能性线索）</h3>")
        parts.append("".join(_related_html(r) for r in section["related"]))
    return "".join(parts)


def build_report(report_date, quotes, market_position=None, market_overview=None, sections=None):
    date_str = report_date.strftime("%Y-%m-%d")
    market_position = market_position or []
    market_overview = market_overview or []
    sections = sections or []

    sections_html = "".join(_section_html(t, s) for t, s in ((x["type"], x) for x in sections))
    if not sections_html:
        sections_html = "<p>今日暂无可整理内容。</p>"

    html_body = f"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><title>每日财经简报 {date_str}</title></head>
<body style="margin:0;background:#fafafa;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif">
<div style="max-width:760px;margin:0 auto;padding:24px 16px">
<div style="background:linear-gradient(135deg,#1a237e,#283593);color:#fff;border-radius:8px;padding:20px 24px;margin-bottom:16px">
<h1 style="margin:0;font-size:20px">📈 每日财经简报</h1>
<p style="margin:6px 0 0;font-size:13px;opacity:.85">{date_str} · 四大框架机会梳理 · 长线视角</p>
</div>
<h2 style="font-size:17px;color:#1a237e;margin:16px 0 8px">板块一 · 财经市场概览</h2>
{_quotes_html(quotes)}
{_market_position_html(market_position)}
{_overview_html(market_overview)}
<h2 style="font-size:17px;color:#1a237e;margin:20px 0 8px">板块二 · 今日四大类机会</h2>
{sections_html}
<div style="margin-top:20px;padding:12px 16px;background:#fff8e1;border-radius:6px;font-size:12px;color:#6d4c41">
⚠️ 免责声明：本简报由程序自动采集公开网络信息并经 AI 按个人投资框架整理，仅供信息参考，不构成任何投资建议。投资有风险，决策需谨慎。
</div>
</div></body></html>"""

    md_lines = [
        f"# 📈 每日财经简报 {date_str}",
        "",
        f"> {date_str} · 四大框架机会梳理 · 长线视角",
        "",
        "## 板块一 · 财经市场概览",
    ]
    for q in quotes:
        md_lines.append(f"- {q.get('name','')}：{q.get('price','')}（{q.get('change','')} / {q.get('pct','')}%）")
    if not quotes:
        md_lines.append("- 行情数据暂不可用")
    if market_position:
        md_lines.append("")
        md_lines.append("📍 **AI 市场位置判断**")
        for m in market_position:
            md_lines.append(f"- **{m.get('asset','')}**：{m.get('position','')} — {m.get('note','')}")
    for o in market_overview:
        md_lines.append(f"- **{o.get('market','')}**：{o.get('summary','')}")
    md_lines += ["", "## 板块二 · 今日四大类机会", ""]
    for sec in sections:
        t = sec.get("type")
        meta = TYPE_META.get(t, {"title": "", "icon": ""})
        md_lines.append(f"### {meta['icon']} 类型{t} · {meta['title']}")
        if not (sec.get("opportunities") or sec.get("related")):
            md_lines.append("今日暂无相关内容，不硬凑。")
            md_lines.append("")
            continue
        if sec.get("opportunities"):
            md_lines.append("**✅ 明确的投资机会**")
            for i, o in enumerate(sec["opportunities"], 1):
                md_lines += [
                    f"{i}. **{o.get('target','')}**",
                    f"   - 逻辑：{o.get('logic','')}",
                    f"   - 进出场思路：{o.get('entry_exit','')}",
                    f"   - 仓位提示：{o.get('position_hint','')}",
                    f"   - 风险：{o.get('risk','')}",
                    f"   - 来源：{o.get('source_url','')}",
                ]
            md_lines.append("")
        if sec.get("related"):
            md_lines.append("**ℹ️ 相关信息（可能性线索）**")
            for r in sec["related"]:
                md_lines += [
                    f"- **{r.get('title','')}**：{r.get('summary','')}（{r.get('why_possible','')}）",
                    f"  来源：{r.get('source_url','')}",
                ]
            md_lines.append("")
    md_lines.append("---")
    md_lines.append("⚠️ 免责声明：本简报由程序自动采集公开网络信息并经 AI 按个人投资框架整理，仅供信息参考，不构成任何投资建议。投资有风险，决策需谨慎。")
    return html_body, "\n".join(md_lines)


def build_error_report(report_date, failed_sources):
    date_str = report_date.strftime("%Y-%m-%d")
    detail = "、".join(failed_sources) if failed_sources else "未知原因"
    html_body = f"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><title>数据源异常 {date_str}</title></head>
<body style="font-family:-apple-system,'PingFang SC',sans-serif;background:#fafafa;padding:24px">
<div style="max-width:640px;margin:0 auto;background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:20px">
<h1 style="font-size:18px;color:#b71c1c">⚠️ 每日财经简报生成失败</h1>
<p>日期：{date_str}</p><p>原因：所有数据源采集失败（{html_mod.escape(detail)}）。</p>
<p style="color:#666;font-size:13px">请稍后手动触发工作流重试，或检查网络与数据源可用性。</p>
</div></body></html>"""
    md_body = f"# ⚠️ 每日财经简报生成失败\n\n日期：{date_str}\n\n原因：所有数据源采集失败（{detail}）。"
    return html_body, md_body
