"""
Agent 基类与通用 DeepSeek 调用函数
"""
from dataclasses import dataclass, field
from openai import OpenAI
import json
import re
import os
import logging

logger = logging.getLogger(__name__)

DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-chat"


@dataclass
class Agent:
    """所有 Agent 的基类"""
    name: str                    # 英文标识，如 "Preprocessor"
    label: str                   # 中文显示名，如 "数据预处理"
    system_prompt: str           # System Prompt 文本
    temperature: float = 0.5     # 0.3-0.5
    model: str = DEEPSEEK_MODEL
    mcp_tools: list = field(default_factory=list)  # 该 Agent 可调用的 MCP 工具名列表

    def run(self, context: dict) -> dict:
        """调用 DeepSeek API，传入上下文，返回解析后的 JSON 结果"""
        return call_deepseek(
            system_prompt=self.system_prompt,
            user_message=format_context(context),
            temperature=self.temperature,
            model=self.model,
            mcp_tools=self.mcp_tools,
        )


def call_deepseek(
    system_prompt: str,
    user_message: str,
    temperature: float = 0.5,
    model: str = DEEPSEEK_MODEL,
    mcp_tools: list | None = None,
) -> dict:
    """通用 DeepSeek API 调用函数。

    Args:
        system_prompt: System Prompt 文本
        user_message: 用户消息（上下文的文本表示）
        temperature: 0.3-0.5
        model: 模型名
        mcp_tools: 可选的 MCP 工具名列表（暂未实现自动调用，保留接口）

    Returns:
        解析后的 JSON dict
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY 环境变量未设置")

    client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    kwargs = {"model": model, "messages": messages, "temperature": temperature}

    if mcp_tools:
        kwargs["tools"] = [{"type": "function", "function": {"name": t, "description": f"调用 {t} 工具"}} for t in mcp_tools]

    try:
        response = client.chat.completions.create(**kwargs)
        raw_text = response.choices[0].message.content
        return extract_json(raw_text)
    except Exception as e:
        logger.error(f"DeepSeek API 调用失败: {e}")
        raise


def extract_json(raw_text: str) -> dict:
    """3级降级解析：从 LLM 响应中提取 JSON 对象。

    Level 1: 直接整个文本解析
    Level 2: 提取第一个 { 到最后一个 } 之间的内容
    Level 3: 正则提取 JSON 对象
    """
    text = raw_text.strip()

    # Level 1: 直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Level 2: 提取 { ... } 块
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and start < end:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    # Level 3: 正则匹配第一个完整 JSON 对象
    match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"无法从响应中提取 JSON:\n{raw_text[:500]}")


def format_context(context: dict) -> str:
    """将上下文字典格式化为 LLM 可读的文本。"""
    parts = []
    for key, value in context.items():
        if isinstance(value, str):
            parts.append(f"## {key}\n{value}")
        elif isinstance(value, dict):
            parts.append(f"## {key}\n{json.dumps(value, ensure_ascii=False, indent=2)}")
        elif isinstance(value, list):
            parts.append(f"## {key}\n{json.dumps(value, ensure_ascii=False, indent=2)}")
    return "\n\n".join(parts)
