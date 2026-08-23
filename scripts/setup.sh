#!/usr/bin/env bash
# CHE直早报 一键安装（macOS / Linux）
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
cd "$ROOT"

echo "==> 1/4 检查 Python（优先 3.11/3.12）"
PY=""
for c in python3.11 python3.12 python3.13 python3.10 python3; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
if [[ -z "$PY" ]]; then
  echo "未找到 Python 3.10+，请先安装（https://python.org）"
  exit 1
fi
echo "使用 $($PY --version)（$PY）"

echo "==> 2/4 创建虚拟环境并安装依赖"
"$PY" -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
if ! command -v pip >/dev/null 2>&1; then
  echo "（venv 未自带 pip，改用官方引导脚本安装）"
  curl -sS https://bootstrap.pypa.io/get-pip.py | "$PY"
fi
python -m pip install --upgrade pip -q
python -m pip install -r requirements.txt -q

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
