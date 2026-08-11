"""推送通道：SMTP 邮件（必选）+ Server酱 微信（可选）。"""
import logging
import os
import smtplib
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr

log = logging.getLogger("daily-report")


def _config():
    host = os.environ.get("SMTP_HOST")
    port = int(os.environ.get("SMTP_PORT") or 465)
    user = os.environ.get("SMTP_USER")
    pwd = os.environ.get("SMTP_PASS")
    to = os.environ.get("MAIL_TO")
    tls = os.environ.get("SMTP_TLS", "auto")  # ssl | starttls | none | auto
    if not all([host, user, pwd, to]):
        raise ValueError("缺少 SMTP 配置（SMTP_HOST/SMTP_USER/SMTP_PASS/MAIL_TO）")
    if tls not in ("ssl", "starttls", "none", "auto"):
        raise ValueError(f"SMTP_TLS 取值无效: {tls}（可选 ssl/starttls/none/auto）")
    return host, port, user, pwd, to, tls


def send_email(subject: str, html_body: str) -> None:
    host, port, user, pwd, to, tls = _config()

    msg = MIMEText(html_body, "html", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = formataddr((str(Header("每日财经简报", "utf-8")), user))
    msg["To"] = to

    if tls == "ssl":
        server = smtplib.SMTP_SSL(host, port, timeout=30)
    elif tls == "starttls":
        server = smtplib.SMTP(host, port, timeout=30)
        server.starttls()
    elif tls == "none":
        server = smtplib.SMTP(host, port, timeout=30)
    else:  # auto：优先 SSL，失败回退 STARTTLS
        try:
            server = smtplib.SMTP_SSL(host, port, timeout=30)
        except (OSError, smtplib.SMTPException):
            server = smtplib.SMTP(host, port, timeout=30)
            server.starttls()

    with server:
        server.login(user, pwd)
        server.sendmail(user, [to], msg.as_string())
    log.info("邮件已通过 %s:%s 发送至 %s（TLS=%s）", host, port, to, tls)


def send_serverchan(title: str, desp: str) -> None:
    key = os.environ.get("SENDKEY")
    if not key:
        log.info("未配置 SENDKEY，跳过 Server酱 推送")
        return
    import requests

    resp = requests.post(
        f"https://sctapi.ftqq.com/{key}.send",
        data={"title": title, "desp": desp},
        timeout=30,
    )
    resp.raise_for_status()
    log.info("Server酱 推送完成")
