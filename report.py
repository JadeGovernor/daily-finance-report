"""组装 HTML / Markdown 简报。"""
import html as html_mod


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


def _cards_html(cards: list) -> str:
    blocks = []
    for i, c in enumerate(cards, 1):
        url = c.get("source_url", "")
        link = f"<a href='{html_mod.escape(url)}' style='color:#1565c0'>原文链接</a>" if url else ""
        blocks.append(f"""<div style="border:1px solid #e0e0e0;border-left:4px solid #f9a825;border-radius:6px;padding:12px 16px;margin-bottom:12px;background:#fff">
<h3 style="margin:0 0 6px;font-size:15px;color:#222">#{i} {html_mod.escape(c.get('title',''))} <span style="color:#888;font-size:12px;font-weight:normal">[{html_mod.escape(c.get('market',''))}]</span></h3>
<p style="margin:4px 0;font-size:13px;color:#444"><b>事件：</b>{html_mod.escape(c.get('event',''))}</p>
<p style="margin:4px 0;font-size:13px;color:#444"><b>影响：</b>{html_mod.escape(c.get('impact',''))}</p>
<p style="margin:4px 0;font-size:13px;color:#444"><b>关注点：</b>{html_mod.escape(c.get('watch_points',''))}</p>
<p style="margin:4px 0;font-size:13px;color:#b71c1c"><b>风险：</b>{html_mod.escape(c.get('risk',''))}</p>
<p style="margin:6px 0 0;font-size:12px;color:#888">{link}</p></div>""")
    return "".join(blocks) if blocks else "<p>今日暂未发现值得关注的机会型信息。</p>"


def _overview_html(overview: list) -> str:
    if not overview:
        return ""
    items = "".join(
        f"<li style='margin:4px 0;font-size:14px;color:#333'><b>{html_mod.escape(o.get('market',''))}：</b>{html_mod.escape(o.get('summary',''))}</li>"
        for o in overview
    )
    return f"<ul style='padding-left:20px;margin:0 0 16px'>{items}</ul>"


def build_report(report_date, quotes, cards, overview=None):
    date_str = report_date.strftime("%Y-%m-%d")
    overview = overview or []
    html_body = f"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><title>每日财经简报 {date_str}</title></head>
<body style="margin:0;background:#fafafa;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif">
<div style="max-width:720px;margin:0 auto;padding:24px 16px">
<div style="background:linear-gradient(135deg,#1a237e,#283593);color:#fff;border-radius:8px;padding:20px 24px;margin-bottom:16px">
<h1 style="margin:0;font-size:20px">📈 每日财经简报</h1>
<p style="margin:6px 0 0;font-size:13px;opacity:.85">{date_str} · A股 / 港股 / 美股 · 自动生成</p>
</div>
<h2 style="font-size:16px;color:#1a237e;margin:16px 0 8px">📊 市场概览</h2>
{_quotes_html(quotes)}
{_overview_html(overview)}
<h2 style="font-size:16px;color:#1a237e;margin:16px 0 8px">🎯 今日值得关注的机会</h2>
{_cards_html(cards)}
<div style="margin-top:20px;padding:12px 16px;background:#fff8e1;border-radius:6px;font-size:12px;color:#6d4c41">
⚠️ 免责声明：本简报由程序自动采集公开网络信息并经 AI 整理，仅供信息参考，不构成任何投资建议。投资有风险，决策需谨慎。
</div>
</div></body></html>"""

    md_lines = [
        f"# 📈 每日财经简报 {date_str}",
        "",
        f"> {date_str} · A股 / 港股 / 美股 · 自动生成",
        "",
        "## 📊 市场概览",
    ]
    for q in quotes:
        md_lines.append(f"- {q.get('name','')}：{q.get('price','')}（{q.get('change','')} / {q.get('pct','')}%）")
    if not quotes:
        md_lines.append("- 行情数据暂不可用")
    for o in overview:
        md_lines.append(f"- **{o.get('market','')}**：{o.get('summary','')}")
    md_lines += ["", "## 🎯 今日值得关注的机会", ""]
    if not cards:
        md_lines.append("今日暂未发现值得关注的机会型信息。")
    for i, c in enumerate(cards, 1):
        md_lines += [
            f"### {i}. {c.get('title','')} [{c.get('market','')}]",
            "",
            f"- **事件**：{c.get('event','')}",
            f"- **影响**：{c.get('impact','')}",
            f"- **关注点**：{c.get('watch_points','')}",
            f"- **风险**：{c.get('risk','')}",
            f"- **来源**：{c.get('source_url','')}",
            "",
        ]
    md_lines.append("---")
    md_lines.append("⚠️ 免责声明：本简报由程序自动采集公开网络信息并经 AI 整理，仅供信息参考，不构成任何投资建议。投资有风险，决策需谨慎。")
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
