"""组装 HTML / Markdown 简报（四大交易系统·校正版·数据真实化）。"""
import html as html_mod

from trading_systems import SYSTEM3_WATCHLIST, SYSTEM4_RULES, TRADING_SYSTEMS

TYPE_META = {
    1: {"title": "周期循环（A股大型指数 · 月线级牛熊）", "color": "#e53935", "icon": "🔴"},
    2: {"title": "大结构震荡底部反转（指数/黄金）", "color": "#1e88e5", "icon": "🔵"},
    3: {"title": "前沿新技术早期侦察（市场形成前）", "color": "#43a047", "icon": "🟢"},
    4: {"title": "上游垄断 · 紫苏叶理论", "color": "#8e24aa", "icon": "🟣"},
}

POSITION_COLOR = {
    "周期低位区": "#2e7d32", "震荡结构底部": "#2e7d32",
    "周期高位区": "#c62828", "震荡结构顶部": "#c62828",
    "趋势中": "#1565c0", "区间中位": "#f9a825", "暂无明确判断": "#757575",
}

EMPTY_NOTES = {
    1: "今日暂无：沪深300 不满足「月线级相对底部（分位<30%）」进场条件，不硬凑。",
    2: "今日暂无：未出现「大结构震荡底部反转」的明确信号（需下沿企稳确认），不硬凑。",
    3: "今日暂无：未出现「市场未形成期重大技术突破」级别的新信号，跟踪池见上表，持续跟踪。",
    4: "今日暂无：候选标的需同时通过「新技术产业+必需+垄断+低价+未热」五项验证，今日无通过者，宁缺毋滥。",
}


def _pct_color(pct) -> str:
    try:
        pct_f = float(pct)
    except (TypeError, ValueError):
        return "#333"
    return "#c62828" if pct_f > 0 else "#1565c0" if pct_f < 0 else "#333"


def _fmt_quote(q: dict, stat: dict = None) -> str:
    pct = q.get("pct", "")
    color = _pct_color(pct)
    sign = "+" if pct and float(pct) > 0 else ""
    pos_cell = ""
    if stat:
        pos_cell = (f"<td style='padding:6px 10px;border-bottom:1px solid #eee;text-align:left;"
                    f"color:{POSITION_COLOR.get(stat['position'], '#333')}'>"
                    f"{html_mod.escape(stat['position'])} <span style='color:#999;font-size:12px'>3年{stat['pct_3y']:.0f}%</span></td>")
    else:
        pos_cell = "<td style='padding:6px 10px;border-bottom:1px solid #eee'>—</td>"
    return (f"<td style='padding:6px 10px;border-bottom:1px solid #eee'>{html_mod.escape(q.get('name',''))}</td>"
            f"<td style='padding:6px 10px;border-bottom:1px solid #eee;text-align:right'>{html_mod.escape(str(q.get('price','')))}</td>"
            f"<td style='padding:6px 10px;border-bottom:1px solid #eee;text-align:right;color:{color}'>"
            f"{html_mod.escape(str(q.get('change','')))} ({sign}{html_mod.escape(str(pct))}%)</td>"
            f"{pos_cell}")


def _quotes_html(quotes: list, stats_by_key: dict = None) -> str:
    stats_by_key = stats_by_key or {}
    if not quotes:
        return "<p>行情数据暂不可用。</p>"
    rows = "".join(_fmt_quote(q, stats_by_key.get(q.get("key"))) for q in quotes)
    return f"""<table style="width:100%;border-collapse:collapse;font-size:14px">
<tr style="background:#f5f7fa"><th style="padding:6px 10px;text-align:left">指数</th>
<th style="padding:6px 10px;text-align:right">最新</th>
<th style="padding:6px 10px;text-align:right">涨跌</th>
<th style="padding:6px 10px;text-align:left">位置（近3年分位）</th></tr>{rows}</table>"""


def _market_position_html(market_position: list) -> str:
    if not market_position:
        return ""
    items = "".join(
        f"<li style='margin:6px 0;font-size:14px;color:#333'><b>{html_mod.escape(m.get('asset',''))}：</b>"
        f"<span style='color:{POSITION_COLOR.get(m.get('position',''), '#333')}'>{html_mod.escape(m.get('position',''))}</span>"
        f"<br><span style='font-size:13px;color:#555'>💬 {html_mod.escape(m.get('judgment',''))}</span></li>"
        for m in market_position
    )
    return (f"<h3 style='font-size:14px;color:#1a237e;margin:12px 0 6px'>📍 整体研判（逐市场 · 位置由真实行情分位计算）</h3>"
            f"<ul style='padding-left:20px;margin:0'>{items}</ul>")


def _opportunity_html(color: str, o: dict) -> str:
    url = o.get("source_url", "")
    link = f"<a href='{html_mod.escape(url)}' style='color:#1565c0'>原文链接</a>" if url else ""
    code_line = f"{html_mod.escape(o.get('code',''))} · {html_mod.escape(o.get('platform',''))}" if o.get("code") else html_mod.escape(o.get("platform",""))
    extra = ""
    if o.get("industry"):
        extra += f"<p style='margin:4px 0;font-size:13px;color:#444'><b>新技术产业：</b>{html_mod.escape(o.get('industry',''))}</p>"
    if o.get("material_role"):
        extra += f"<p style='margin:4px 0;font-size:13px;color:#444'><b>原材料参与环节/是否必需：</b>{html_mod.escape(o.get('material_role',''))}</p>"
    if o.get("monopoly"):
        extra += f"<p style='margin:4px 0;font-size:13px;color:#444'><b>垄断度：</b>{html_mod.escape(o.get('monopoly',''))}</p>"
    if o.get("moat"):
        extra += f"<p style='margin:4px 0;font-size:13px;color:#444'><b>护城河/可替换性：</b>{html_mod.escape(o.get('moat',''))}</p>"
    return f"""<div style="border:1px solid {color};border-left:4px solid {color};border-radius:6px;padding:10px 14px;margin:8px 0;background:#fff">
<div style="font-weight:600;font-size:14px;color:#222">🎯 {html_mod.escape(o.get('target',''))} <span style="color:#666;font-size:12px;font-weight:normal">（{code_line}）</span></div>
{extra}
<p style="margin:4px 0;font-size:13px;color:#444"><b>逻辑：</b>{html_mod.escape(o.get('logic',''))}</p>
<p style="margin:4px 0;font-size:13px;color:#444"><b>进出场方案：</b>{html_mod.escape(o.get('entry_exit',''))}</p>
<p style="margin:4px 0;font-size:13px;color:#444"><b>仓位使用：</b>{html_mod.escape(o.get('position_hint',''))}</p>
<p style="margin:4px 0;font-size:13px;color:#2e7d32"><b>预期离场收益率：</b>{html_mod.escape(o.get('target_return',''))}　<b style="color:#c62828">止损收益率：</b>{html_mod.escape(o.get('stop_loss',''))}</p>
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


def _watchlist_html() -> str:
    rows = "".join(
        f"<tr style='border-bottom:1px solid #eee'><td style='padding:6px 10px;font-weight:600;color:#333;white-space:nowrap'>{html_mod.escape(w['market'])}</td>"
        f"<td style='padding:6px 10px;font-size:13px;color:#444'>{html_mod.escape(w['targets'])}</td>"
        f"<td style='padding:6px 10px;font-size:12px;color:#888'>{html_mod.escape(w['note'])}</td></tr>"
        for w in SYSTEM3_WATCHLIST
    )
    return (f"<h3 style='font-size:14px;color:#2e7d32;margin:10px 0 4px'>🌐 五市场固定跟踪池（持续跟踪，出现市场未形成期的重大突破才升级为机会）</h3>"
            f"<table style='width:100%;border-collapse:collapse;font-size:13px;background:#fafafa;border:1px solid #e0e0e0;border-radius:6px'>"
            f"<tr style='background:#f0f4ec'><th style='padding:6px 10px;text-align:left'>领域</th><th style='padding:6px 10px;text-align:left'>具体可交易标的</th><th style='padding:6px 10px;text-align:left'>关注点</th></tr>{rows}</table>")


def _system4_rules_html() -> str:
    return (f"<h3 style='font-size:14px;color:#8e24aa;margin:10px 0 4px'>🧪 紫苏叶硬条件（五条缺一不可）</h3>"
            f"<div style='border:1px dashed #8e24aa;border-radius:6px;padding:8px 12px;margin:8px 0;background:#faf5fc;font-size:13px;color:#4a2c63'>"
            f"{html_mod.escape(SYSTEM4_RULES)}</div>")


def _empty_note_html(t: int, stats_by_key: dict) -> str:
    if t == 1 and stats_by_key.get("hs300"):
        s = stats_by_key["hs300"]
        lo3, hi3 = s["range_3y"]
        return (f"今日暂无：沪深300 最新 {s['price']:.0f}，近3年区间[{lo3:.0f},{hi3:.0f}]处于 {s['pct_3y']:.0f}% 分位"
                f"（{s['position']}），不满足「月线级相对底部（分位&lt;30%）」进场条件，不硬凑。")
    return EMPTY_NOTES.get(t, "今日暂无，不硬凑。")


def _section_html(t: int, section: dict, stats_by_key: dict = None) -> str:
    meta = TYPE_META[t]
    head = f"<h2 style='font-size:16px;color:{meta['color']};margin:0'>{meta['icon']} 系统{t} · {meta['title']}</h2>"
    parts = [f"<div style='margin:18px 0 4px'>{head}</div>"]
    if t == 3:
        parts.append(_watchlist_html())
    if t == 4:
        parts.append(_system4_rules_html())
    if not (section["opportunities"] or section["related"]):
        parts.append(f"<p style='color:#999;font-size:13px;margin:6px 0 0'>{_empty_note_html(t, stats_by_key or {})}</p>")
        return "".join(parts)
    if section["opportunities"]:
        parts.append("<h3 style='font-size:14px;color:#2e7d32;margin:10px 0 4px'>✅ 明确的投资机会（含交易方案）</h3>")
        parts.append("".join(_opportunity_html(meta["color"], o) for o in section["opportunities"]))
    if section["related"]:
        parts.append("<h3 style='font-size:14px;color:#757575;margin:10px 0 4px'>ℹ️ 相关信息（可能性线索）</h3>")
        parts.append("".join(_related_html(r) for r in section["related"]))
    return "".join(parts)


def _systems_html() -> str:
    blocks = []
    for para in TRADING_SYSTEMS.strip().split("\n\n"):
        lines = para.strip().split("\n")
        title = lines[0]
        body = "<br>".join(html_mod.escape(line) for line in lines[1:])
        blocks.append(f"<div style='margin:8px 0;padding:10px 14px;background:#f5f7fa;border-radius:6px'>"
                      f"<div style='font-weight:600;font-size:13px;color:#333'>{html_mod.escape(title)}</div>"
                      f"<div style='font-size:12px;color:#555;margin-top:4px'>{body}</div></div>")
    return "".join(blocks)


def _quote_md(q: dict, stat: dict = None) -> str:
    pos = ""
    if stat:
        pos = f"　位置：{stat['position']}（3年{stat['pct_3y']:.0f}%）"
    return f"- {q.get('name','')}：{q.get('price','')}（{q.get('change','')} / {q.get('pct','')}%）{pos}"


def _empty_note_md(t: int, stats_by_key: dict) -> str:
    if t == 1 and stats_by_key.get("hs300"):
        s = stats_by_key["hs300"]
        lo3, hi3 = s["range_3y"]
        return (f"今日暂无：沪深300 最新 {s['price']:.0f}，近3年区间[{lo3:.0f},{hi3:.0f}]处于 {s['pct_3y']:.0f}% 分位"
                f"（{s['position']}），不满足「月线级相对底部（分位<30%）」进场条件，不硬凑。")
    return EMPTY_NOTES.get(t, "今日暂无，不硬凑。")


def build_report(report_date, quotes, market_position=None, sections=None, stats=None):
    date_str = report_date.strftime("%Y-%m-%d")
    market_position = market_position or []
    sections = sections or []
    stats_by_key = {s.get("key"): s for s in (stats or [])}

    sections_html = "".join(_section_html(s["type"], s, stats_by_key) for s in sections)
    if not sections_html:
        sections_html = "<p>今日暂无可整理内容。</p>"

    html_body = f"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><title>每日财经简报 {date_str}</title></head>
<body style="margin:0;background:#fafafa;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif">
<div style="max-width:780px;margin:0 auto;padding:24px 16px">
<div style="background:linear-gradient(135deg,#1a237e,#283593);color:#fff;border-radius:8px;padding:20px 24px;margin-bottom:16px">
<h1 style="margin:0;font-size:20px">📈 每日财经简报</h1>
<p style="margin:6px 0 0;font-size:13px;opacity:.85">{date_str} · 四大交易系统（校正版） · 长线视角</p>
<p style="margin:4px 0 0;font-size:12px;opacity:.7">数据来源：新浪实时行情 + 东方财富历史K线 · 位置由真实分位自动计算</p>
</div>
<h2 style="font-size:17px;color:#1a237e;margin:16px 0 8px">板块一 · 财经市场概览</h2>
{_quotes_html(quotes, stats_by_key)}
{_market_position_html(market_position)}
<h2 style="font-size:17px;color:#1a237e;margin:20px 0 8px">板块二 · 今日机会与线索</h2>
{sections_html}
<h2 style="font-size:17px;color:#1a237e;margin:24px 0 8px">📖 附 · 四大交易系统说明（校正版）</h2>
{_systems_html()}
<div style="margin-top:20px;padding:12px 16px;background:#fff8e1;border-radius:6px;font-size:12px;color:#6d4c41">
⚠️ 免责声明：本简报由程序自动采集公开网络信息并经 AI 按个人交易系统整理，仅供信息参考，不构成任何投资建议。投资有风险，决策需谨慎。
</div>
</div></body></html>"""

    md_lines = [
        f"# 📈 每日财经简报 {date_str}",
        "",
        f"> {date_str} · 四大交易系统（校正版） · 长线视角",
        "> 数据来源：新浪实时行情 + 东方财富历史K线 · 位置由真实分位自动计算",
        "",
        "## 板块一 · 财经市场概览",
    ]
    for q in quotes:
        md_lines.append(_quote_md(q, stats_by_key.get(q.get("key"))))
    if not quotes:
        md_lines.append("- 行情数据暂不可用")
    if market_position:
        md_lines.append("")
        md_lines.append("📍 **整体研判（逐市场 · 位置由真实行情分位计算）**")
        for m in market_position:
            md_lines.append(f"- **{m.get('asset','')}**：{m.get('position','')}")
            if m.get("judgment"):
                md_lines.append(f"  💬 {m.get('judgment','')}")
    md_lines += ["", "## 板块二 · 今日机会与线索", ""]
    for sec in sections:
        t = sec.get("type")
        meta = TYPE_META.get(t, {"title": "", "icon": ""})
        md_lines.append(f"### {meta['icon']} 系统{t} · {meta['title']}")
        if t == 3:
            md_lines.append("")
            md_lines.append("**🌐 五市场固定跟踪池（持续跟踪，出现市场未形成期的重大突破才升级为机会）**")
            for i, w in enumerate(SYSTEM3_WATCHLIST, 1):
                md_lines.append(f"- {i}. **{w['market']}**：{w['targets']}（{w['note']}）")
        if t == 4:
            md_lines.append("")
            md_lines.append(f"**🧪 紫苏叶硬条件（五条缺一不可）**：{SYSTEM4_RULES}")
        if not (sec.get("opportunities") or sec.get("related")):
            md_lines.append(_empty_note_md(t, stats_by_key))
            md_lines.append("")
            continue
        if sec.get("opportunities"):
            md_lines.append("**✅ 明确的投资机会（含交易方案）**")
            for i, o in enumerate(sec["opportunities"], 1):
                md_lines += [
                    f"{i}. **{o.get('target','')}**（{o.get('code','')} · {o.get('platform','')}）",
                ]
                if o.get("industry"):
                    md_lines.append(f"   - 新技术产业：{o.get('industry','')}")
                if o.get("material_role"):
                    md_lines.append(f"   - 原材料参与环节/是否必需：{o.get('material_role','')}")
                if o.get("monopoly"):
                    md_lines.append(f"   - 垄断度：{o.get('monopoly','')}")
                if o.get("moat"):
                    md_lines.append(f"   - 护城河/可替换性：{o.get('moat','')}")
                md_lines += [
                    f"   - 逻辑：{o.get('logic','')}",
                    f"   - 进出场方案：{o.get('entry_exit','')}",
                    f"   - 仓位使用：{o.get('position_hint','')}",
                    f"   - 预期离场收益率：{o.get('target_return','')}　止损收益率：{o.get('stop_loss','')}",
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
    md_lines += ["## 📖 附 · 四大交易系统说明（校正版）", ""]
    for para in TRADING_SYSTEMS.strip().split("\n\n"):
        for line in para.strip().split("\n"):
            md_lines.append(line)
        md_lines.append("")
    md_lines.append("---")
    md_lines.append("⚠️ 免责声明：本简报由程序自动采集公开网络信息并经 AI 按个人交易系统整理，仅供信息参考，不构成任何投资建议。投资有风险，决策需谨慎。")
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
