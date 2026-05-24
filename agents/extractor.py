"""Agent 3: FiveDimExtractor — 五维特征抽取"""
from agents import Agent
from agents.prompts import FIVEDIM_PROMPT


class FiveDimExtractor(Agent):
    def __init__(self):
        super().__init__(
            name="FiveDimExtractor",
            label="五维特征抽取",
            system_prompt=FIVEDIM_PROMPT,
            temperature=0.5,
            mcp_tools=["extract_keywords", "classify_emotion"],
        )
