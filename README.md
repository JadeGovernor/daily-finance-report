# 📈 每日财经简报（Daily Finance Report）

每天北京时间 9:00 自动采集全网财经信息 → AI 筛选投资机会 → 生成简报 → 邮件推送（可选叠加微信 Server酱）。

## 功能
- **数据源**：新浪财经、东方财富全球快讯、CNBC、Google News、Yahoo Finance（单源失败自动跳过）
- **AI 筛选**：DeepSeek 从 200-500 条新闻中筛出 5-10 张「机会卡片」+ 三大市场概览；未配置 key 时自动降级为关键词规则
- **推送**：SMTP 邮件（必选）+ Server酱 微信（可选双通道）
- **调度**：GitHub Actions 免费运行，`cron: "0 1 * * *"`（UTC）= 北京 9:00，支持手动触发

## 快速开始
1. 把本项目推到你的 GitHub 仓库
2. 配置 Secrets（见下）
3. 仓库 → Actions → 左侧「Daily Finance Report」→ **Run workflow** 手动跑一次验证
4. 之后每天自动运行

## 需要配置的 Secrets
| Secret | 说明 |
| --- | --- |
| `SMTP_HOST` | 邮箱 SMTP 服务器，如 QQ `smtp.qq.com`、163 `smtp.163.com` |
| `SMTP_PORT` | 465（SSL，默认）或 587（STARTTLS） |
| `SMTP_TLS`（可选） | `ssl` / `starttls` / `none` / `auto`（默认自动回退） |
| `SMTP_USER` | 邮箱地址 |
| `SMTP_PASS` | **授权码**（不是登录密码，见下） |
| `MAIL_TO` | 收件邮箱 |
| `DEEPSEEK_API_KEY` | [platform.deepseek.com](https://platform.deepseek.com) 申请的 API key |
| `SENDKEY`（可选） | [sct.ftqq.com](https://sct.ftqq.com) 的 Server酱 SendKey，配置后微信同步推送 |

### 一键配置 Secrets
```bash
gh auth login
REPO=你的用户名/daily-finance-report ./scripts/setup_secrets.sh
```
脚本会逐个提示输入（也可提前用同名环境变量预填）。

### 获取邮箱授权码
- **QQ 邮箱**：设置 → 账户 → 开启「POP3/SMTP 服务」→ 生成授权码
- **163 邮箱**：设置 → POP3/SMTP/IMAP → 开启 SMTP → 新增授权码
- 授权码填入 `SMTP_PASS`，不是邮箱登录密码

## 本地验证邮件（无需真实邮箱）
```bash
# 终端 1：启动假 SMTP 服务器
python scripts/fake_smtp_server.py 1025

# 终端 2：跑通完整推送链路（邮件被捕获到 captured_email.eml）
SMTP_HOST=127.0.0.1 SMTP_PORT=1025 SMTP_TLS=none \
SMTP_USER=test@test.com SMTP_PASS=x MAIL_TO=me@test.com python main.py
```

## 本地环境自检
```bash
python scripts/check_env.py
```

## 本地运行
```bash
pip install -r requirements-dev.txt

# 只生成报告不发送（输出到 output/）
python main.py --dry-run

# 真实发送（需先配置环境变量）
SMTP_HOST=smtp.qq.com SMTP_USER=xx@qq.com SMTP_PASS=授权码 MAIL_TO=xx@qq.com \
DEEPSEEK_API_KEY=sk-xxx python main.py
```

## 测试
```bash
pytest -q
```

## 目录结构
```
main.py               编排入口（采集→筛选→组装→推送）
collectors/           5 个数据源 + 行情
ai_filter.py          DeepSeek 筛选（含规则降级）
report.py             HTML/Markdown 简报组装
push.py               SMTP 邮件 + Server酱
.github/workflows/    每日定时任务
tests/                单元测试（离线 fixture）
```

## 免责声明
本工具自动采集公开网络信息并经 AI 整理，仅供信息参考，**不构成任何投资建议**。投资有风险，决策需谨慎。
