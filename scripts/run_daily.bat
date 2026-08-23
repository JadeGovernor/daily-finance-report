@echo off
chcp 65001 >nul
cd /d "%~dp0.."
if not exist .env (
  echo 缺少 .env，请先运行 scripts\setup.bat
  pause
  exit /b 1
)
for /f "usebackq delims=" %%i in (.env) do set "%%i"
python main.py
pause
