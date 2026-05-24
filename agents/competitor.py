"""Agent 6: CompetitorAnalyzer — 竞品分析（第二场景）"""
from agents import Agent
from agents.prompts import COMPETITOR_PROMPT


class CompetitorAnalyzer(Agent):
    def __init__(self):
        super().__init__(
            name="CompetitorAnalyzer",
            label="竞品分析",
            system_prompt=COMPETITOR_PROMPT,
            temperature=0.5,
            mcp_tools=[],
        )
