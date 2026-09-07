# AI 日报部署说明

当前使用 GitHub Actions 在每天北京时间 08:50 左右启动，汇总 AI 新闻、调用大模型筛选和分析，并在生成完成后约 09:00 推送到飞书群。

数据源配置位于 `config/config.yaml`，当前仅启用 36氪、虎嗅、IT之家、InfoQ AI、GitHub Repository Search 和 ArXiv，不再采集默认的 11 个综合热榜。

## 首次配置

1. 在飞书群的“设置 → 群机器人 → 添加机器人 → 自定义机器人”中创建机器人并获取 Webhook。
2. 将 `.env.example` 复制为 `.env`。
3. 在 `.env` 中填写 `FEISHU_WEBHOOK_URL` 和 `AI_API_KEY`。
4. 将代码推送到自己的 GitHub 仓库。
5. 在仓库 `Settings → Secrets and variables → Actions` 中配置 `FEISHU_WEBHOOK_URL`、`AI_API_KEY`、`AI_MODEL` 和 `AI_API_BASE`。
6. 在 `Actions → AI Daily Report to Feishu → Run workflow` 中运行一次，并勾选 `test_notification` 验证飞书。

## 手动测试

```powershell
./run-ai-daily-report.ps1
```

日志位于 `logs/daily-report-YYYY-MM-DD.log`，生成的数据库和 HTML 报告位于 `output/`。

## GitHub Actions 调度

工作流位于 `.github/workflows/ai-daily-report.yml`。Cron 使用 UTC，`50 0 * * *` 对应北京时间每天 08:50。任务提前启动，为采集和 AI 生成预留时间；`config/timeline.yaml` 的推送窗口为 08:45 至 12:00，用于容忍 GitHub Actions 排队延迟。

GitHub Actions 在云端运行，电脑和手机都不需要开机。GitHub 不承诺 Cron 精确到分钟，繁忙时可能延迟，因此它适合“9 点左右”推送，而不是严格的 09:00:00。

## Actions Secrets

```text
FEISHU_WEBHOOK_URL  飞书自定义机器人 Webhook
AI_API_KEY          模型 API Key
AI_MODEL            openai/deepseek-v4-flash-0731
AI_API_BASE         OpenAI 兼容接口地址
```

`GITHUB_TOKEN` 由 Actions 自动提供，不需要手动配置。
