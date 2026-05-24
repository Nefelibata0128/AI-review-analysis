"""Agent 2: SubjectivityFilter — 主观性过滤"""
from agents import Agent
from agents.prompts import SUBJECTIVITY_PROMPT


class SubjectivityFilter(Agent):
    def __init__(self):
        super().__init__(
            name="SubjectivityFilter",
            label="主观性过滤",
            system_prompt=SUBJECTIVITY_PROMPT,
            temperature=0.5,
            mcp_tools=["analyze_subjectivity"],
        )
