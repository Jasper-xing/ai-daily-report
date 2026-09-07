# coding=utf-8
"""閫氱煡娴嬭瘯鍛戒护"""

import copy
from pathlib import Path
from typing import Dict, Optional

from trendradar.context import AppContext


def _build_test_report_data(ctx: AppContext) -> Dict:
    now = ctx.get_time()
    time_display = now.strftime("%H:%M")
    title = f"AI 绉戞妧鏃ユ姤閫氱煡娴嬭瘯娑堟伅锛坽now.strftime('%Y-%m-%d %H:%M:%S')}锛?

    return {
        "stats": [
            {
                "word": "AI 绉戞妧鏃ユ姤杩為€氭€ф祴璇?,
                "count": 1,
                "titles": [
                    {
                        "title": title,
                        "source_name": "TrendRadar",
                        "url": "https://github.com/sansan0/TrendRadar",
                        "mobile_url": "",
                        "ranks": [1],
                        "rank_threshold": ctx.rank_threshold,
                        "count": 1,
                        "is_new": True,
                        "time_display": time_display,
                        "matched_keyword": "AI 绉戞妧鏃ユ姤杩為€氭€ф祴璇?,
                    }
                ],
            }
        ],
        "failed_ids": [],
        "new_titles": [],
        "id_to_name": {},
    }


def _create_test_html_file(ctx: AppContext) -> Optional[str]:
    try:
        now = ctx.get_time()
        output_dir = Path("output") / "html" / ctx.format_date()
        output_dir.mkdir(parents=True, exist_ok=True)
        html_path = output_dir / f"notification_test_{ctx.format_time()}.html"
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>TrendRadar 閫氱煡娴嬭瘯</title></head>
<body>
<h2>TrendRadar 閫氱煡杩為€氭€ф祴璇?/h2>
<p>娴嬭瘯鏃堕棿锛歿now.strftime('%Y-%m-%d %H:%M:%S')} ({ctx.timezone})</p>
<p>杩欐槸涓€鏉℃祴璇曟秷鎭紝鐢ㄤ簬楠岃瘉閭欢娓犻亾鏄惁鍙揪銆?/p>
</body>
</html>"""
        html_path.write_text(html_content, encoding="utf-8")
        return str(html_path)
    except Exception as e:
        print(f"[娴嬭瘯閫氱煡] 鍒涘缓娴嬭瘯 HTML 澶辫触: {e}")
        return None


def run_test_notification(config: Dict) -> bool:
    """鍙戦€佹祴璇曢€氱煡鍒板凡閰嶇疆娓犻亾"""
    from trendradar.notification import NotificationDispatcher

    ctx = AppContext(config)

    try:
        has_notification = any(
            [
                config.get("FEISHU_WEBHOOK_URL"),
                config.get("DINGTALK_WEBHOOK_URL"),
                config.get("WEWORK_WEBHOOK_URL"),
                (config.get("TELEGRAM_BOT_TOKEN") and config.get("TELEGRAM_CHAT_ID")),
                (config.get("EMAIL_FROM") and config.get("EMAIL_PASSWORD") and config.get("EMAIL_TO")),
                (config.get("NTFY_SERVER_URL") and config.get("NTFY_TOPIC")),
                config.get("BARK_URL"),
                config.get("SLACK_WEBHOOK_URL"),
                config.get("GENERIC_WEBHOOK_URL"),
            ]
        )
        if not has_notification:
            print("鏈娴嬪埌鍙敤閫氱煡娓犻亾锛岃鍏堝湪 config.yaml 鎴栫幆澧冨彉閲忎腑閰嶇疆銆?)
            return False

        test_config = copy.deepcopy(config)
        test_display = test_config.setdefault("DISPLAY", {})
        test_regions = test_display.setdefault("REGIONS", {})
        test_regions.update(
            {
                "HOTLIST": True,
                "NEW_ITEMS": False,
                "RSS": False,
                "STANDALONE": False,
                "AI_ANALYSIS": False,
            }
        )

        if "AI_TRANSLATION" in test_config:
            test_config["AI_TRANSLATION"]["ENABLED"] = False

        proxy_url = test_config.get("DEFAULT_PROXY", "") if test_config.get("USE_PROXY") else None
        if proxy_url:
            print("[娴嬭瘯閫氱煡] 妫€娴嬪埌浠ｇ悊閰嶇疆锛屽皢浣跨敤浠ｇ悊鍙戦€?)

        dispatcher = NotificationDispatcher(
            config=test_config,
            get_time_func=ctx.get_time,
            split_content_func=ctx.split_content,
            translator=None,
        )

        report_data = _build_test_report_data(ctx)
        html_file_path = _create_test_html_file(ctx)

        print("=" * 60)
        print("閫氱煡杩為€氭€ф祴璇?)
        print("=" * 60)

        results = dispatcher.dispatch_all(
            report_data=report_data,
            report_type="AI 绉戞妧鏃ユ姤閫氱煡杩為€氭€ф祴璇?,
            proxy_url=proxy_url,
            mode="daily",
            html_file_path=html_file_path,
        )

        if not results:
            print("娌℃湁鍙祴璇曠殑鏈夋晥閫氱煡娓犻亾锛堝彲鑳介厤缃笉瀹屾暣锛夈€?)
            return False

        print("-" * 60)
        success_count = 0
        for channel, ok in results.items():
            if ok:
                success_count += 1
                print(f"鉁?{channel}: 娴嬭瘯鎴愬姛")
            else:
                print(f"鉂?{channel}: 娴嬭瘯澶辫触")

        print("-" * 60)
        print(f"娴嬭瘯缁撴灉: {success_count}/{len(results)} 涓笭閬撴垚鍔?)
        return success_count > 0
    finally:
        ctx.cleanup()
