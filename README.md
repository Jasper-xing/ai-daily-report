# AI 科技日报

基于 [TrendRadar](https://github.com/sansan0/TrendRadar) 定制的 AI 科技资讯日报。项目每天自动采集科技新闻，通过大模型生成分析，并将日报推送到飞书群。

当前方案不依赖本地电脑常驻运行：Cloudflare Workers 负责准时触发，GitHub Actions 负责运行 Python 程序，飞书机器人负责接收日报。

## 系统架构

```text
Cloudflare Workers Cron Trigger
        |
        | GitHub workflow_dispatch API
        v
GitHub Actions (Ubuntu + Python 3.12)
        |
        |-- 采集科技资讯
        |-- 关键词筛选
        |-- 调用大模型分析
        |-- 生成 HTML 报告
        v
飞书自定义机器人
```

Cloudflare 只负责发送触发请求，实际的数据采集、AI 分析和飞书推送都在 GitHub Actions 的临时 Ubuntu Runner 中完成。

## 当前功能

- 每天自动生成一份 AI 科技日报。
- 使用 Cloudflare Workers 免费 Cron 触发 GitHub Actions。
- 设置三个触发时间并自动防止重复推送。
- 使用关键词规则稳定筛选科技内容。
- 调用 OpenAI 兼容的大模型接口生成 AI 分析。
- 通过飞书自定义机器人推送日报。
- 将 HTML 报告作为 GitHub Actions Artifact 保存 14 天。
- 支持在 GitHub Actions 页面手动补发完整日报。
- 支持单独测试飞书机器人连通性。

## 数据来源

| 来源 | 类型 | 数量或范围 |
|---|---|---|
| 36氪 | RSS | Feed 最新内容 |
| 虎嗅 | RSS | Feed 最新内容 |
| IT之家 | RSS | Feed 最新内容 |
| InfoQ AI/ML/Data | RSS | Feed 最新内容 |
| GitHub AI 最近更新 | GitHub Repository Search | 每次最多 10 条 |
| ArXiv AI 最新论文 | ArXiv API | 每次最多 5 条 |

TrendRadar 默认的综合热榜已关闭，只采集科技和 AI 相关来源。数据源配置位于 `config/config.yaml`。

## 定时策略

Cloudflare Cron 使用 UTC，当前配置如下：

| UTC | 北京时间 | 用途 |
|---|---|---|
| `00:50` | `08:50` | 主触发 |
| `01:20` | `09:20` | 第一次补偿触发 |
| `01:50` | `09:50` | 第二次补偿触发 |

GitHub 工作流也保留相同的 Cron 作为额外兜底。防重复守卫会查询当天成功生成的日报 Artifact：当天已有完整日报时，后续触发只执行检查，不再次生成和推送。

日报允许在北京时间 `08:45-12:00` 内推送，以容忍云端任务排队和网络波动。该窗口配置位于 `config/timeline.yaml`。

## GitHub Actions

工作流文件：

```text
.github/workflows/ai-daily-report.yml
```

查看运行记录：

https://github.com/Jasper-xing/ai-daily-report/actions

完整运行包含以下步骤：

```text
Check for an earlier successful report
Checkout repository
Set up Python
Install uv
Install dependencies
Validate configuration
Generate and push AI daily report
Upload report for troubleshooting
```

Actions 页面显示绿色只代表命令正常退出。确认飞书真正收到请求时，应在 `Generate and push AI daily report` 日志中看到：

```text
[推送] 准备发送
飞书第 1/1 批次发送成功
飞书所有批次发送完成
```

如果日志显示 `跳过通知`，说明程序没有调用飞书，常见原因是没有匹配内容或当前时间不在推送窗口。

## 手动运行

在 GitHub 仓库中打开：

```text
Actions -> AI Daily Report to Feishu -> Run workflow
```

| 输入项 | 用途 |
|---|---|
| `test_notification=false` | 生成并推送完整日报 |
| `test_notification=true` | 只发送飞书连通性测试 |
| `external_trigger=true` | 外部定时器触发，当天已有日报时自动跳过 |

普通网页手动运行默认不会被防重复守卫阻止，适合当天漏报时强制补发。

## HTML 报告

每次完整运行会上传名称类似下面的 Artifact：

```text
ai-daily-report-<GitHub Run ID>
```

在对应 Actions 运行页面底部下载并解压，打开 `html/日期/时间.html` 或 `html/latest/daily.html` 即可查看浏览器版日报。Artifact 当前保留 14 天。

GitHub Actions 是临时执行环境，不提供长期在线的热点网页。如果需要固定网址和长期历史数据，需要迁移到云服务器或增加对象存储与静态网站部署。

## 敏感配置

GitHub Actions Secrets：

| Secret | 用途 |
|---|---|
| `FEISHU_WEBHOOK_URL` | 飞书自定义机器人 Webhook |
| `AI_API_KEY` | 大模型 API Key |
| `AI_MODEL` | LiteLLM/OpenAI 兼容模型名称 |
| `AI_API_BASE` | OpenAI 兼容 API 地址 |

Cloudflare Worker Secrets：

| Secret | 用途 |
|---|---|
| `GITHUB_TOKEN` | 调用 GitHub `workflow_dispatch` API |
| `TRIGGER_SECRET` | 保护 Worker 的 HTTP 手动触发入口 |

Cloudflare 使用的 GitHub Fine-grained Token 只需访问 `ai-daily-report` 仓库，并授予：

```text
Actions: Read and write
Metadata: Read-only
```

不要将真实 Secret 写入仓库、Issue、Actions 配置文件或日志。

## Cloudflare Worker

Worker 代码位于 `cloudflare-worker/`。首次部署：

```bash
cd cloudflare-worker
npm install
npx wrangler login
npx wrangler secret put GITHUB_TOKEN
npx wrangler secret put TRIGGER_SECRET
npm run deploy
```

检查构建但不部署：

```bash
cd cloudflare-worker
npm run check
```

修改 `cloudflare-worker/wrangler.toml` 中的 `crons` 后，需要再次运行 `npm run deploy` 才会更新线上定时器。

## 本地运行

本地调试时复制环境变量示例并填写自己的配置：

```powershell
Copy-Item .env.example .env
./run-ai-daily-report.ps1
```

本地日志位于 `logs/`，数据库和 HTML 报告位于 `output/`。`.env`、日志、输出目录和虚拟环境均已被 `.gitignore` 排除。

## 常见问题

### 到时间没有日报

1. 打开 GitHub Actions 页面，检查当天是否存在运行记录。
2. 没有运行记录时，检查 Cloudflare Worker 的 Cron Triggers 和日志。
3. 有运行记录时，展开 `Generate and push AI daily report`。
4. 搜索 `飞书`、`跳过通知`、`AI`、`请求超时` 等关键词。
5. 必要时从 Actions 页面手动运行完整日报。

### Actions 成功但飞书没有消息

必须检查生成步骤日志。只有出现 `飞书批次发送成功` 才代表飞书服务器接受了请求。若飞书返回成功但群里不可见，应确认 Webhook 是否属于当前查看的群，以及机器人是否仍在群中。

### 飞书返回 Key Words Not Found

机器人启用了关键词安全策略。请确保允许关键词包含 `AI`，或者调整飞书机器人的安全设置。项目的测试消息已包含 `AI`。

### Cloudflare Token 到期

重新创建 GitHub Fine-grained Token，然后更新 Worker Secret：

```bash
cd cloudflare-worker
npx wrangler secret put GITHUB_TOKEN
```

更新 Secret 后不需要修改或提交代码。

## 关键文件

| 文件 | 作用 |
|---|---|
| `.github/workflows/ai-daily-report.yml` | GitHub Actions 工作流和防重复守卫 |
| `cloudflare-worker/src/index.js` | Cloudflare 调用 GitHub API 的代码 |
| `cloudflare-worker/wrangler.toml` | Worker 名称和 Cron 时间 |
| `config/config.yaml` | 数据源、筛选、通知和 AI 配置 |
| `config/timeline.yaml` | 日报执行与推送时间窗口 |
| `config/frequency_words.txt` | 关键词筛选规则 |
| `config/ai_interests.txt` | AI 分析兴趣主题 |
| `.env.example` | 本地环境变量示例 |
| `DEPLOYMENT.md` | 详细部署说明 |

## 成本说明

当前架构主要使用 GitHub 公共仓库的 Actions 托管 Runner、Cloudflare Workers 免费套餐的 Cron Trigger、用户自行提供的大模型 API 和飞书自定义机器人。

GitHub 和 Cloudflare 的免费额度及政策可能调整。大模型 API 是否收费取决于实际服务商和账户额度。

## 上游项目

本项目基于 TrendRadar v6.10.0 定制：

https://github.com/sansan0/TrendRadar
