"""
飞书通知模块
在每次多 Agent 分析完成后，通过飞书自定义机器人 Webhook 发送通知卡片。
"""
import os
import json
import logging
import httpx

logger = logging.getLogger(__name__)

LARK_WEBHOOK_URL = os.environ.get("LARK_WEBHOOK_URL", "")


async def send_analysis_notification(
    scene_name: str,
    file_name: str,
    meta: dict,
    report_url: str = "http://localhost:8080",
) -> bool:
    """分析完成后发送飞书消息卡片。

    Args:
        scene_name: 场景名（用户反馈分析 / 竞品分析）
        file_name: 分析的文件名
        meta: 分析结果的 meta 字段 {total_reviews, avg_rating, alert_count}
        report_url: 查看报告的链接
    """
    if not LARK_WEBHOOK_URL:
        logger.info("LARK_WEBHOOK_URL 未配置，跳过通知")
        return False

    avg = meta.get("avg_rating", 0)
    total = meta.get("total_reviews", 0)
    alerts = meta.get("alert_count", 0)

    summary = (
        f"均分: {avg}/5  |  评论: {total} 条\n"
        f"告警: {alerts} 人流失风险"
    )

    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"content": f"AI评论分析平台 — {scene_name}", "tag": "plain_text"},
                "template": "blue",
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {"content": f"**文件**: {file_name}", "tag": "lark_md"},
                },
                {
                    "tag": "hr",
                },
                {
                    "tag": "div",
                    "text": {"content": summary, "tag": "lark_md"},
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"content": "查看完整报告", "tag": "plain_text"},
                            "url": report_url,
                            "type": "default",
                        }
                    ],
                },
            ],
        },
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(LARK_WEBHOOK_URL, json=card)
            if resp.status_code == 200:
                logger.info(f"飞书通知发送成功: {file_name}")
                return True
            else:
                logger.warning(f"飞书通知发送失败: {resp.status_code} {resp.text}")
                return False
    except Exception as e:
        logger.error(f"飞书通知异常: {e}")
        return False


def send_notification_sync(
    scene_name: str,
    file_name: str,
    meta: dict,
    report_url: str = "http://localhost:8080",
) -> bool:
    """同步包装器，方便在同步代码中调用。"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            future = asyncio.run_coroutine_threadsafe(
                send_analysis_notification(scene_name, file_name, meta, report_url),
                loop,
            )
            return future.result(timeout=15)
        else:
            return asyncio.run(send_analysis_notification(scene_name, file_name, meta, report_url))
    except RuntimeError:
        return asyncio.run(send_analysis_notification(scene_name, file_name, meta, report_url))
