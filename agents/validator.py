"""Agent 4: CrossValidator — 交叉验证与异常识别"""
from agents import Agent
from agents.prompts import CROSSVALIDATOR_PROMPT


class CrossValidator(Agent):
    def __init__(self):
        super().__init__(
            name="CrossValidator",
            label="交叉验证与异常识别",
            system_prompt=CROSSVALIDATOR_PROMPT,
            temperature=0.3,
            mcp_tools=["detect_conflict", "assess_churn_risk"],
        )
