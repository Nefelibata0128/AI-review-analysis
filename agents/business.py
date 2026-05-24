"""Agent 5: BusinessAnalyzer — 业务分析与优先级"""
from agents import Agent
from agents.prompts import BUSINESS_PROMPT


class BusinessAnalyzer(Agent):
    def __init__(self):
        super().__init__(
            name="BusinessAnalyzer",
            label="业务分析与优先级",
            system_prompt=BUSINESS_PROMPT,
            temperature=0.5,
            mcp_tools=["rank_priority", "format_markdown"],
        )
