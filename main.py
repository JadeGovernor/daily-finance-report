"""每日财经简报：采集 -> AI筛选 -> 组装 -> 推送。"""
import argparse
import logging
import os
import sys
from datetime import date
from pathlib import Path

from collectors import SOURCES, fetch_market
import ai_filter
import market_stats
import push
import report

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("daily-report")


def collect(limit_per_source: int):
    items, failed = [], []
    for fetch in SOURCES:
        name = fetch.__module__.rsplit(".", 1)[-1]
        try:
            got = fetch(limit=limit_per_source)
            log.info("采集 %s: %d 条", name, len(got))
            items.extend(got)
        except Exception as exc:  # 单源失败不中断整体
            log.warning("采集 %s 失败: %s", name, exc)
            failed.append(name)
    seen, uniq = set(), []
    for it in items:
        key = it.get("url") or it.get("title")
        if not key or key in seen:
            continue
        seen.add(key)
        uniq.append(it)
    log.info("去重后共 %d 条，失败源: %s", len(uniq), ", ".join(failed) or "无")
    return uniq


def build_error_report(today, failed_sources, output_dir: Path):
    lines = "、".join(failed_sources) if failed_sources else "未知"
    html_body, md_body = report.build_error_report(today, lines)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "report.html").write_text(html_body, encoding="utf-8")
    (output_dir / "report.md").write_text(md_body, encoding="utf-8")
    log.warning("所有数据源均失败，已生成异常报告: %s", output_dir)
    return html_body


def main():
    parser = argparse.ArgumentParser(description="每日财经简报工具")
    parser.add_argument("--date", help="报告日期 YYYY-MM-DD（默认今天）")
    parser.add_argument("--limit", type=int, default=50, help="每个数据源最多采集条数")
    parser.add_argument("--no-push", action="store_true", help="只生成报告，不发送")
    parser.add_argument("--dry-run", action="store_true", help="同 --no-push，仅本地生成报告")
    parser.add_argument("--output", default="output", help="报告输出目录")
    args = parser.parse_args()

    report_date = date.today() if not args.date else date.fromisoformat(args.date)
    no_push = args.no_push or args.dry_run
    output_dir = Path(args.output)

    items = collect(args.limit)
    if not items:
        html = build_error_report(report_date, [], output_dir)
        if not no_push:
            try:
                push.send_email(f"⚠️ 每日财经简报 {report_date:%Y-%m-%d}（数据源异常）", html)
                log.info("已发送异常通知邮件")
            except Exception as exc:
                log.error("异常通知邮件发送失败: %s", exc)
        return 1

    quotes = []
    try:
        quotes = fetch_market()
        log.info("行情获取: %d 条指数", len(quotes))
    except Exception as exc:
        log.warning("行情获取失败: %s", exc)

    stats = []
    try:
        stats = market_stats.fetch()
        log.info("历史分位统计: %d 个标的", len(stats))
    except Exception as exc:
        log.warning("历史分位统计失败: %s", exc)

    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    sections, market_position = ai_filter.run(items, api_key, stats)
    log.info("四大类整理完成：机会 %d 条 / 线索 %d 条",
             sum(len(s["opportunities"]) for s in sections),
             sum(len(s["related"]) for s in sections))

    html_body, md_body = report.build_report(report_date, quotes, market_position, sections, stats)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "report.html").write_text(html_body, encoding="utf-8")
    (output_dir / "report.md").write_text(md_body, encoding="utf-8")
    log.info("报告已生成: %s", output_dir)

    if no_push:
        log.info("--no-push：跳过推送（可用浏览器打开 output/report.html 预览）")
        return 0

    subject = f"📈 每日财经简报 {report_date:%Y-%m-%d}"
    try:
        push.send_email(subject, html_body)
        log.info("邮件已发送")
    except Exception as exc:
        log.error("邮件发送失败: %s", exc)
        return 1
    try:
        push.send_serverchan(subject, md_body)
        log.info("Server酱推送完成")
    except Exception as exc:
        log.warning("Server酱推送失败: %s", exc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
