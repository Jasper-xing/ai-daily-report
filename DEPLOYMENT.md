# AI 日报部署说明

当前使用 Cloudflare Workers Cron 调用 GitHub `workflow_dispatch`，由 GitHub Actions 汇总 AI 新闻、调用大模型分析并推送到飞书群。GitHub 自带 Cron 只作为额外兜底。

数据源配置位于 `config/config.yaml`，当前仅启用 36氪、虎嗅、IT之家、InfoQ AI、GitHub Repository Search 和 ArXiv，不再采集默认的 11 个综合热榜。

## 首次配置

1. 在飞书群的“设置 → 群机器人 → 添加机器人 → 自定义机器人”中创建机器人并获取 Webhook。
2. 将 `.env.example` 复制为 `.env`。
3. 在 `.env` 中填写 `FEISHU_WEBHOOK_URL` 和 `AI_API_KEY`。
4. 将代码推送到自己的 GitHub 仓库。
5. 在仓库 `Settings → Secrets and variables → Actions` 中配置 `FEISHU_WEBHOOK_URL`、`AI_API_KEY`、`AI_MODEL` 和 `AI_API_BASE`。
6. 在 `Actions → AI Daily Report to Feishu → Run workflow` 中运行一次，并勾选 `test_notification` 验证飞书。
7. 按下方 Cloudflare Workers 章节部署外部定时器。

## 手动测试

```powershell
./run-ai-daily-report.ps1
```

日志位于 `logs/daily-report-YYYY-MM-DD.log`，生成的数据库和 HTML 报告位于 `output/`。

## 调度架构

工作流位于 `.github/workflows/ai-daily-report.yml`。Cloudflare Worker 位于 `cloudflare-worker/`，通过 GitHub API 触发工作流。

Cron 使用 UTC，三个时间分别为：

```text
50 0 * * *  北京时间 08:50
20 1 * * *  北京时间 09:20
50 1 * * *  北京时间 09:50
```

后两次为补偿触发。GitHub 工作流会检查当天是否已有成功生成的日报 Artifact，已有则跳过，避免重复推送。`config/timeline.yaml` 的推送窗口为北京时间 08:45 至 12:00。

GitHub Actions 在云端运行，电脑和手机都不需要开机。

## Actions Secrets

```text
FEISHU_WEBHOOK_URL  飞书自定义机器人 Webhook
AI_API_KEY          模型 API Key
AI_MODEL            openai/deepseek-v4-flash-0731
AI_API_BASE         OpenAI 兼容接口地址
```

`GITHUB_TOKEN` 由 Actions 自动提供，不需要手动配置。

## Cloudflare Workers

Cloudflare Worker 只负责调用 GitHub API，不运行 TrendRadar。进入 `cloudflare-worker/` 后执行：

```bash
npm install
npx wrangler login
npx wrangler secret put GITHUB_TOKEN
npx wrangler secret put TRIGGER_SECRET
npm run deploy
```

`GITHUB_TOKEN` 应使用 Fine-grained personal access token，只选择 `ai-daily-report` 仓库并配置：

```text
Actions: Read and write
Metadata: Read-only
```

`TRIGGER_SECRET` 用于保护 Worker 的 HTTP 手动触发入口，应使用随机字符串。

修改 `cloudflare-worker/wrangler.toml` 中的 Cron 后，需要重新执行 `npm run deploy`。

## 验证推送

不要只看 Actions 是否显示绿色。展开 `Generate and push AI daily report`，确认日志包含：

```text
[推送] 准备发送
飞书第 1/1 批次发送成功
飞书所有批次发送完成
```

如果日志显示 `跳过通知`，说明程序没有调用飞书。
