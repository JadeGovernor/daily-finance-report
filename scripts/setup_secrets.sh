#!/usr/bin/env bash
# 一键把所需的 GitHub Secrets 配置到仓库（需先 gh auth login）
# 用法：
#   REPO=owner/daily-finance-report ./scripts/setup_secrets.sh
#   # 或在本仓库目录下直接运行（自动探测 repo）
set -euo pipefail

REPO="${REPO:-}"
if [ -z "$REPO" ]; then
  if gh repo view --json nameWithOwner -q .nameWithOwner >/dev/null 2>&1; then
    REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
  fi
fi
if [ -z "$REPO" ]; then
  echo "错误：无法自动探测仓库，请用 REPO=owner/name ./scripts/setup_secrets.sh 指定" >&2
  exit 1
fi
gh auth status >/dev/null 2>&1 || { echo "错误：请先运行 gh auth login" >&2; exit 1; }

set_secret() {
  local name="$1" value="${!1:-}" prompt="$2"
  if [ -n "$value" ]; then
    echo "使用环境变量中的 $name"
  else
    read -rsp "请输入 $name（$prompt，输入为空则跳过）: " value; echo
    [ -z "$value" ] && { echo "跳过 $name"; return; }
  fi
  echo "$value" | gh secret set "$name" --repo "$REPO"
  echo "✓ 已设置 $name"
}

echo "目标仓库: $REPO"
set_secret SMTP_HOST "SMTP 服务器，如 smtp.qq.com"
set_secret SMTP_PORT "端口，如 465 或 587（可为空则用默认 465）"
set_secret SMTP_USER "发件邮箱地址"
set_secret SMTP_PASS "邮箱 SMTP 授权码（不是登录密码）"
set_secret MAIL_TO "收件邮箱"
set_secret DEEPSEEK_API_KEY "DeepSeek API key"
set_secret SENDKEY "Server酱 SendKey（可选，配置后微信同步推送）"
echo "全部完成。可到仓库 Actions → Daily Finance Report → Run workflow 手动验证。"
