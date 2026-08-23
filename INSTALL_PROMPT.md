# 🤖 AI 安装提示词（一键安装 CHE直早报）

> 用法：把下面「复制我」到「复制结束」之间的内容，整段发给你的 AI 编程助手（Codex / OpenClaw / Cursor / Claude Code 等），它会自动帮你下载、安装、配置并试运行。

## 复制我

请帮我在当前电脑上安装并配置 GitHub 上的开源项目「CHE直早报」（每日财经信息聚合工具），仓库地址：https://github.com/JadeGovernor/daily-finance-report

请按以下步骤执行，每完成一步就告诉我结果，不要跳过任何一步：

1. 用 git 把仓库克隆到本地：`git clone https://github.com/JadeGovernor/daily-finance-report.git`，然后进入目录。
2. 阅读 README.md，了解项目用途和文件结构。
3. 检查本机 Python 版本（需要 3.10+），然后创建虚拟环境并安装依赖：
   - macOS/Linux：`python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
   - Windows：`python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt`
4. 生成配置文件：把 `.env.example` 复制为 `.env`（macOS/Linux 用 `cp`，Windows 用 `copy`）。
5. 【关键】逐个问我以下配置项，我说一个、你填一个到 .env，不要替我编造或猜测：
   - `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASS`：发件邮箱的 SMTP 服务器地址和「授权码」（不是登录密码）
   - `MAIL_TO`：收件邮箱，可多个用逗号分隔
   - `DEEPSEEK_API_KEY`：DeepSeek 开放平台（platform.deepseek.com）申请的 API key
   - `SENDKEY`（可选）：Server酱 的 SendKey
   这些是隐私凭据，只写入本地 `.env` 文件（该文件已在 .gitignore 中，不会被上传），不要提交到任何仓库，也不要外传。
6. 试运行验证：先跑 `python scripts/check_env.py` 确认配置齐全；再跑 `python main.py --dry-run --no-push` 生成一份测试报告，把 output/report.html 打开给我看效果。
7. 最后用大白话教我怎么设置每天自动运行（任选一种）：
   - 方式 A（云端，推荐）：把代码推到 GitHub 仓库并配置 Actions Secrets，让 GitHub 每天自动跑（按 README 操作）。
   - 方式 B（本机）：用系统定时任务（macOS launchd / Windows 计划任务）每天 8:30 执行 `scripts/run_daily.sh`（Windows 用 `scripts\run_daily.bat`）。

如果任何一步报错：先读 README 或错误日志自己排查，解决不了就把具体错误信息发给我，我们一起处理。整个过程不要修改项目源码文件。

## 复制结束
