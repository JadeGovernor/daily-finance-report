#!/usr/bin/env bash
# CHE直早报 一键安装（macOS / Linux）
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
cd "$ROOT"

echo "==> 1/4 检查 Python"
if ! command -v python3 >/dev/null 2>&1; then
  echo "未找到 python3，请先安装 Python 3.10+（https://python.org）"
  exit 1
fi

echo "==> 2/4 创建虚拟环境并安装依赖"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo "==> 3/4 生成配置文件"
if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "已生成 .env —— 请用文本编辑器打开并填写你的邮箱 / API Key"
else
  echo ".env 已存在，跳过"
fi

echo "==> 4/4 安装完成"
echo "接下来："
echo "  1) 编辑 .env 填入配置（SMTP 邮箱授权码、收件邮箱、DEEPSEEK_API_KEY）"
echo "  2) 检查配置：python scripts/check_env.py"
echo "  3) 试运行：python main.py --dry-run --no-push"
echo "  4) 正式发送：./scripts/run_daily.sh"
