"""
多 Agent 编排引擎 — Orchestrator + SSEEmitter + 结果合并

设计理念：不做复杂的 Agent 框架，只做清晰的函数调用链。
每个 Agent 是 System Prompt + DeepSeek API 调用的封装，
编排器按依赖顺序串行调用，前一个输出作为后一个输入。
"""
import time
import json
import queue
import threading
import logging
from typing import Generator

from agents.preprocessor import Preprocessor
from agents.subjectivity import SubjectivityFilter
from agents.extractor import FiveDimExtractor
from agents.validator import CrossValidator
from agents.business import BusinessAnalyzer
from agents.competitor import CompetitorAnalyzer

logger = logging.getLogger(__name__)


class SSEEmitter:
    """线程安全的 SSE 事件发射器"""

    def __init__(self):
        self.event_queue = queue.Queue()

    def _emit(self, event: str, data: dict) -> None:
        self.event_queue.put({
            "event": event,
            "data": json.dumps(data, ensure_ascii=False),
            "ts": int(time.time()),
        })

    def agent_started(self, agent_id: str, label: str, message: str = "") -> None:
        self._emit("agent_started", {
            "agent": agent_id,
            "agent_label": label,
            "message": message or f"正在执行{label}...",
        })

    def agent_completed(self, agent_id: str, label: str, duration_ms: int) -> None:
        self._emit("agent_completed", {
            "agent": agent_id,
            "agent_label": label,
            "duration_ms": duration_ms,
        })

    def workflow_completed(self, outputs: dict, total_duration_ms: int) -> None:
        self._emit("workflow_completed", {
            "status": "succeeded",
            "outputs": outputs,
            "total_duration_ms": total_duration_ms,
        })

    def agent_error(self, agent_id: str, message: str) -> None:
        self._emit("error", {
            "agent": agent_id,
            "message": message,
        })

    def heartbeat(self) -> None:
        self.event_queue.put(": heartbeat")

    def stream(self) -> Generator[str, None, None]:
        """生成器：从队列中取出事件，格式化为 SSE 文本行"""
        while True:
            item = self.event_queue.get()
            if item is None:
                break
            if isinstance(item, str):
                yield f"{item}\n\n"
            else:
                yield f"event: {item['event']}\ndata: {item['data']}\n\n"


class Orchestrator:
    """多 Agent 编排引擎"""

    def __init__(self):
        self.agents = {
            "Preprocessor": Preprocessor(),
            "SubjectivityFilter": SubjectivityFilter(),
            "FiveDimExtractor": FiveDimExtractor(),
            "CrossValidator": CrossValidator(),
            "BusinessAnalyzer": BusinessAnalyzer(),
            "CompetitorAnalyzer": CompetitorAnalyzer(),
        }
        self.sse = SSEEmitter()

    def _get_pipeline(self, mode: str) -> list[str]:
        """根据分析模式返回 Agent 执行顺序"""
        if mode == "feedback":
            return [
                "Preprocessor",
                "SubjectivityFilter",
                "FiveDimExtractor",
                "CrossValidator",
                "BusinessAnalyzer",
            ]
        elif mode == "competitor":
            # 竞品分析模式：Agent1→Agent6→Agent4→Agent5
            # Agent 6 (CompetitorAnalyzer) 在阶段二实现
            return [
                "Preprocessor",
                "CompetitorAnalyzer",
                "CrossValidator",
                "BusinessAnalyzer",
            ]
        else:
            raise ValueError(f"未知分析模式: {mode}")

    def run_analysis(
        self, review_text: str, bg_text: str = "", mode: str = "feedback"
    ) -> dict:
        """运行分析流水线。

        Args:
            review_text: 用户评论原始文本（.txt 文件内容）
            bg_text: 产品背景文档文本（.docx/.md 解析后的内容，可选）
            mode: "feedback" 或 "competitor"

        Returns:
            合并后的 14 字段结果 JSON
        """
        context = {
            "用户评论原始数据": review_text,
            "产品背景文档": bg_text,
        }

        pipeline = self._get_pipeline(mode)
        total_start = time.time()

        for agent_id in pipeline:
            agent = self.agents.get(agent_id)
            if agent is None:
                logger.warning(f"Agent {agent_id} 未注册，跳过")
                continue

            self.sse.agent_started(agent_id, agent.label)

            try:
                step_start = time.time()
                result = agent.run(context)
                duration_ms = int((time.time() - step_start) * 1000)

                context[agent_id] = result
                self.sse.agent_completed(agent_id, agent.label, duration_ms)
                logger.info(f"[{agent.label}] 完成，耗时 {duration_ms}ms")

            except Exception as e:
                error_msg = f"{agent.label} 执行失败: {str(e)}"
                logger.error(error_msg)
                self.sse.agent_error(agent_id, error_msg)
                raise

        total_duration_ms = int((time.time() - total_start) * 1000)
        final = self._merge_results(context, mode)
        self.sse.workflow_completed(final, total_duration_ms)

        return final

    def _merge_results(self, context: dict, mode: str) -> dict:
        """将各 Agent 的碎片化输出合并为前端期望的 14 字段 JSON"""
        a1 = context.get("Preprocessor", {})
        a2 = context.get("SubjectivityFilter", {})
        a3 = context.get("FiveDimExtractor", {})
        a4 = context.get("CrossValidator", {})
        a5 = context.get("BusinessAnalyzer", {})

        return {
            "meta": {
                "total_reviews": a1.get("total_reviews", 0),
                "avg_rating": a1.get("avg_rating", 0),
                "sentiment_label": a5.get("sentiment_label", ""),
                "alert_count": a4.get("alert_count", 0),
            },
            "rating_distribution": a1.get("rating_distribution", {}),
            "subjectivity": {
                "high_count": a2.get("high_count", 0),
                "low_count": a2.get("low_count", 0),
                "high_avg_rating": a2.get("high_avg_rating", 0),
                "low_avg_rating": a2.get("low_avg_rating", 0),
                "high_label": "情绪宣泄",
                "low_label": "理性反馈",
            },
            "attitude_goal_matrix": a3.get("attitude_goal_matrix", []),
            "emotion_distribution": a3.get("emotion_distribution", []),
            "behavioral_intentions": a3.get("behavioral_intentions", []),
            "info_sources": a3.get("info_sources", []),
            "defects": a3.get("defects", []),
            "highlights": a3.get("highlights", []),
            "feature_requests": a3.get("feature_requests", []),
            "conflicts": a4.get("conflicts", []),
            "churn_risks": a4.get("churn_risks", []),
            "priority_board": a5.get("priority_board", []),
            "conclusion_markdown": a5.get("conclusion_markdown", ""),
        }
