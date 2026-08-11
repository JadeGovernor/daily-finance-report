"""本地推送前环境自检：打印各环境变量是否就绪。"""
import os
import sys

REQUIRED = ["SMTP_HOST", "SMTP_USER", "SMTP_PASS", "MAIL_TO"]
OPTIONAL = ["SMTP_PORT", "SMTP_TLS", "DEEPSEEK_API_KEY", "SENDKEY"]

def main():
    ok = True
    print("== 必选配置 ==")
    for name in REQUIRED:
        present = bool(os.environ.get(name))
        ok = ok and present
        print(f"  {'✓' if present else '✗'} {name}")
    print("== 可选配置 ==")
    for name in OPTIONAL:
        value = os.environ.get(name)
        print(f"  {'✓' if value else '·'} {name}" + (f" = {value}" if value else "（未设置，使用默认/降级）"))
    if not ok:
        print("\n缺少必选配置。设置方法见 README；也可用 scripts/setup_secrets.sh 配置 GitHub Secrets。")
        return 1
    print("\n必选配置齐全，可以运行 python main.py（不带 --no-push 即真实发送）。")
    return 0

if __name__ == "__main__":
    sys.exit(main())
