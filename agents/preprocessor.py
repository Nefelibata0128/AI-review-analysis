"""Agent 1: Preprocessor — 数据预处理与基线建立"""
from agents import Agent
from agents.prompts import PREPROCESSOR_PROMPT


class Preprocessor(Agent):
    def __init__(self):
        super().__init__(
            name="Preprocessor",
            label="数据预处理",
            system_prompt=PREPROCESSOR_PROMPT,
            temperature=0.3,
            mcp_tools=["count_ratings", "calc_baseline"],
        )
