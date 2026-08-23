# 📈 CHE直早报（Daily Finance Report）

> 🌐 公网网页版（每天约 8:30 自动更新）：https://jadegovernor.github.io/daily-finance-report-site/
> 🔒 网页版访问密码：`CHEZHI`（密码以哈希形式内嵌，仅供轻量防浏览，非强安全）

每天北京时间 9:00 自动采集全网财经信息 → 用真实行情数据计算市场位置 → AI 按你的四大交易系统筛选机会 → 生成简报 → 邮件推送（可选叠加微信 Server酱）。

## 功能
- **真实行情打底**：`market_stats.py` 调腾讯/新浪 K 线接口，自动计算沪深300、上证50、中证500、恒指、标普、纳指、道指、黄金ETF(518880) 的近1年/3年价格分位与位置判断（<30% 低位区 / >70% 高位区 / 黄金「震荡结构底部」双条件）。**位置判断由代码按真实数据生成，AI 不编造点位。**
- **数据源**：新浪财经、东方财富全球快讯、CNBC、Google News、Yahoo Finance（单源失败自动跳过）
- **AI 筛选**：DeepSeek 按四大交易系统分类整理机会与线索，并校验「机会链接标题必须含标的关键词」，不匹配自动降级为相关线索；未配置 key 时自动降级为规则版
- **四大系统分类报告**：
  - 🔴 系统1 · 周期循环（A股大型指数 · 月线级牛熊，数据门控：高位区不报机会）
  - 🔵 系统2 · 大结构震荡底部反转（关键指数/黄金）
  - 🟢 系统3 · 前沿新技术早期侦察（固定五市场跟踪池：加密货币/区块链、人工智能、芯片算力、具身智能/人形机器人、航天航空，每个市场给出具体可交易标的与代码）
  - 🟣 系统4 · 上游垄断 · 紫苏叶理论（五条硬条件：新技术产业/必需/垄断/原材料低价/市场未热；已成熟被炒作的产业链如光伏多晶硅、AI覆铜板CCL 明确剔除）
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
| `MAIL_TO` | 收件邮箱（多个用逗号分隔，如 `a@x.com,b@x.com`） |
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

# 只生成报告不发送（输出到 output/，需联网拉取实时行情）
DEEPSEEK_API_KEY=sk-xxx python main.py --no-push

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
main.py               编排入口（行情统计→采集→AI筛选→组装→推送）
collectors/           5 个数据源 + 实时行情
market_stats.py       历史K线分位计算（位置判断的数据来源）
trading_systems.py    四大交易系统的说明与默认跟踪池
ai_filter.py          DeepSeek 筛选（含规则降级 + 来源匹配校验）
report.py             HTML/Markdown 简报组装（四大系统分类 UI）
push.py               SMTP 邮件 + Server酱
.github/workflows/    每日定时任务
tests/                单元测试（离线 fixture）
```

## 免责声明
本工具自动采集公开网络信息并经 AI 按个人交易系统整理，仅供信息参考，**不构成任何投资建议**。投资有风险，决策需谨慎。
