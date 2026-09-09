const GITHUB_API =
  "https://api.github.com/repos/Jasper-xing/ai-daily-report/actions/workflows/ai-daily-report.yml/dispatches";

async function triggerReport(env) {
  const response = await fetch(GITHUB_API, {
    method: "POST",
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      "Content-Type": "application/json",
      "User-Agent": "ai-daily-report-scheduler",
      "X-GitHub-Api-Version": "2022-11-28",
    },
    body: JSON.stringify({
      ref: "main",
      inputs: {
        test_notification: "false",
        external_trigger: "true",
      },
    }),
  });

  if (!response.ok) {
    throw new Error(`GitHub dispatch failed: ${response.status} ${await response.text()}`);
  }
}

export default {
  async scheduled(_controller, env, ctx) {
    ctx.waitUntil(triggerReport(env));
  },

  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("AI Daily Report scheduler is running.", { status: 200 });
    }

    if (!env.TRIGGER_SECRET || request.headers.get("Authorization") !== `Bearer ${env.TRIGGER_SECRET}`) {
      return new Response("Unauthorized", { status: 401 });
    }

    await triggerReport(env);
    return new Response("GitHub Actions triggered.", { status: 202 });
  },
};
