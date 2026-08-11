"""推送模块测试（不访问网络）。"""
import os
import smtplib

import push


def test_send_serverchan_skips_without_key(monkeypatch):
    monkeypatch.delenv("SENDKEY", raising=False)
    push.send_serverchan("标题", "内容")


def test_send_email_requires_config(monkeypatch):
    for key in ("SMTP_HOST", "SMTP_USER", "SMTP_PASS", "MAIL_TO"):
        monkeypatch.delenv(key, raising=False)
    try:
        push.send_email("subject", "<p>body</p>")
    except ValueError as exc:
        assert "SMTP" in str(exc)
    else:
        raise AssertionError("缺少配置时应抛出 ValueError")


def test_send_email_builds_and_sends(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USER", "sender@example.com")
    monkeypatch.setenv("SMTP_PASS", "secret")
    monkeypatch.setenv("MAIL_TO", "me@example.com")
    monkeypatch.delenv("SMTP_TLS", raising=False)

    sent = {}
    class FakeSSL:
        def __init__(self, *a, **k):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def login(self, user, pwd):
            sent["login"] = (user, pwd)
        def sendmail(self, frm, to, message):
            sent["mail"] = (frm, to, message)

    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSSL)
    push.send_email("测试主题", "<p>测试正文</p>")

    import email as email_mod
    from email import policy

    assert sent["login"] == ("sender@example.com", "secret")
    frm, to, message = sent["mail"]
    assert frm == "sender@example.com" and to == ["me@example.com"]
    parsed = email_mod.message_from_bytes(message.encode("utf-8"), policy=policy.default)
    assert parsed["Subject"] == "测试主题"
    assert parsed.get_body(preferencelist=("html",)).get_content() == "<p>测试正文</p>"


def test_send_email_invalid_tls_mode(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USER", "u")
    monkeypatch.setenv("SMTP_PASS", "p")
    monkeypatch.setenv("MAIL_TO", "t")
    monkeypatch.setenv("SMTP_TLS", "bogus")
    try:
        push.send_email("s", "<p>b</p>")
    except ValueError as exc:
        assert "SMTP_TLS" in str(exc)
    else:
        raise AssertionError("SMTP_TLS 无效时应抛出 ValueError")
