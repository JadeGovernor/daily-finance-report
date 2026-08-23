#!/usr/bin/env bash
# CHE直早报 一键运行并发送邮件（自动读取 .env 配置）
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
cd "$ROOT"
if [[ ! -f .env ]]; then
  echo "缺少 .env，请先运行 scripts/setup.sh"
  exit 1
fi
set -a; source .env; set +a
python main.py
