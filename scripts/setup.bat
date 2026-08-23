@echo off
chcp 65001 >nul
echo ==^> 1/3 创建虚拟环境并安装依赖
python -m venv .venv
call .venv\Scripts\activate.bat
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo ==^> 2/3 生成配置文件
if not exist .env (
  copy .env.example .env
  echo 已生成 .env —— 请编辑填入邮箱 / API Key
)
echo ==^> 3/3 安装完成
echo 接下来：1) 编辑 .env  2) python scripts\check_env.py  3) python main.py --dry-run --no-push  4) scripts\run_daily.bat
pause
