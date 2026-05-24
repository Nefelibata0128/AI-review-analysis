"""
MCP Server — AI评论分析平台 分析工具
FastMCP 框架，streamable-http 传输，端口 8081

两个使用场景：
1. 内部：Agent 编排过程中调用 MCP 工具进行精确计算
2. 外部：可被 Claude Desktop 等 MCP 客户端发现和调用
"""
import json
import re
from collections import Counter
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("AI评论分析平台 分析工具")


# ============================================================
# 小工具（可被 Agent 分步调用）
# ============================================================

@mcp.tool()
def count_ratings(reviews_text: str) -> dict:
    """精确统计用户评论中1-5星的评分分布。

    Args:
        reviews_text: Markdown表格格式的用户评论数据，每行含评分列
    """
    stats = {"1星": 0, "2星": 0, "3星": 0, "4星": 0, "5星": 0}
    lines = reviews_text.strip().split("\n")
    for line in lines:
        for star in range(1, 6):
            if str(star) in line and ("星" in line or "★" in line):
                stats[f"{star}星"] += 1
                break
    return stats


@mcp.tool()
def analyze_subjectivity(review_text: str) -> dict:
    """判定单条评论的主观性分数(0-1)和标签。

    Args:
        review_text: 单条用户评论文本
    """
    # 情绪宣泄信号：连续感叹号/问号、全部大写词组、极端措辞
    high_signals = 0
    total_signals = 0

    # 感叹号/问号连续
    if re.search(r'[!！]{2,}|[?？]{2,}', review_text):
        high_signals += 1
    total_signals += 1

    # 全部大写的词组（2字以上）
    if re.search(r'[A-Z一-鿿]{2,}', review_text):
        high_signals += 0.5
    total_signals += 1

    # 极端措辞关键词
    extreme_words = ["垃圾", "烂", "骗", "坑", "滚", "傻", "死", "垃圾软件", "气死", "废物"]
    for word in extreme_words:
        if word in review_text:
            high_signals += 0.5
            break
    total_signals += 1

    # 理性反馈信号：具体描述、建议句式
    if re.search(r'(建议|希望|如果|能否|请|麻烦)', review_text):
        high_signals -= 0.5
    total_signals += 1

    # 字数越多越可能是理性反馈
    if len(review_text) > 50:
        high_signals -= 0.3
    total_signals += 1

    score = max(0.0, min(1.0, high_signals / max(total_signals, 1)))

    return {
        "score": round(score, 2),
        "label": "情绪宣泄" if score >= 0.8 else "理性反馈",
    }


@mcp.tool()
def extract_keywords(text: str, top_n: int = 10) -> list[dict]:
    """提取评论文本中的关键词及权重。

    Args:
        text: 要提取关键词的文本
        top_n: 返回前N个关键词，默认10
    """
    # 分词：按标点和空格分割，保留2字以上的中文词
    words = re.findall(r'[一-鿿]{2,}', text)
    counter = Counter(words)
    total = sum(counter.values()) or 1
    results = [
        {"word": w, "weight": round(c / total, 2)}
        for w, c in counter.most_common(top_n)
    ]
    return results


@mcp.tool()
def classify_emotion(text: str) -> dict:
    """识别文本中的情绪标签。

    Args:
        text: 要分析的文本
    """
    emotion_keywords = {
        "愤怒": ["气死", "火大", "辣鸡", "垃圾", "滚", "傻逼", "他妈的", "操"],
        "失望": ["失望", "寒心", "没想到", "可惜", "遗憾", "算了"],
        "惊喜": ["惊喜", "没想到", "太棒了", "超预期", "牛", "绝了"],
        "困惑": ["搞不懂", "不明白", "为什么", "怎么", "迷惑", "迷"],
        "焦虑": ["急", "担心", "害怕", "不安", "焦虑", "紧张"],
        "满意": ["满意", "不错", "还行", "挺好", "喜欢", "赞", "好用"],
        "期待": ["期待", "希望", "要是", "如果能", "加个", "什么时候"],
        "无奈": ["无奈", "无语", "服了", "算了", "随便", "放弃"],
    }

    scores = {}
    for emotion, keywords in emotion_keywords.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[emotion] = score

    if not scores:
        return {"emotion": "中性", "confidence": 0.5}

    best = max(scores, key=scores.get)
    max_score = max(scores.values())
    confidence = min(0.95, 0.5 + max_score * 0.15)

    return {"emotion": best, "confidence": round(confidence, 2)}


@mcp.tool()
def detect_conflict(rating: int, text: str) -> dict:
    """检测用户评分与评论文本之间的冲突。

    Args:
        rating: 用户评分(1-5)
        text: 评论文本
    """
    negative_words = ["差", "烂", "垃圾", "闪退", "卡顿", "不好", "难用", "问题", "bug", "Bug"]
    positive_words = ["好", "赞", "棒", "不错", "满意", "喜欢", "好用", "优秀"]

    has_negative = any(w in text for w in negative_words)
    has_positive = any(w in text for w in positive_words)

    if rating >= 4 and has_negative:
        return {"conflict": True, "type": "高分负评", "detail": "评分高但文本包含负面内容"}
    elif rating <= 2 and has_positive and not has_negative:
        return {"conflict": True, "type": "低分正评", "detail": "评分低但文本肯定功能质量，可能缺少核心功能"}
    else:
        return {"conflict": False, "type": "无冲突", "detail": "评分与文本一致"}


@mcp.tool()
def assess_churn_risk(user_comments: list[str], user_baseline: float = 3.0) -> dict:
    """评估单个用户的流失风险。

    Args:
        user_comments: 该用户的所有评论文本列表
        user_baseline: 该用户的历史平均评分
    """
    risk_score = 0
    signals = []

    for text in user_comments:
        if any(w in text for w in ["卸载", "删了", "不用了", "放弃"]):
            risk_score += 3
            signals.append("卸载/弃用意图")
        if any(w in text for w in ["竞品", "用回", "转到", "换"]):
            risk_score += 3
            signals.append("转投竞品信号")
        if any(w in text for w in ["气死", "火大", "失望", "无奈", "无语"]):
            risk_score += 2
            signals.append("强烈负面情绪")

        # 评分趋势：如果提到的问题属于基础功能
        basic_features = ["闪退", "打不开", "崩溃", "登录", "注册", "支付"]
        if any(f in text for f in basic_features):
            risk_score += 2
            signals.append("基础功能异常")

    if risk_score >= 7:
        level = "最高级"
    elif risk_score >= 4:
        level = "高级"
    elif risk_score >= 2:
        level = "中级"
    else:
        level = "低级"

    return {"risk": level, "signals": signals, "score": risk_score}


# ============================================================
# 大工具（一键全流程，对外展示用）
# ============================================================

@mcp.tool()
def run_feedback_analysis(reviews_text: str, product_bg: str = "") -> dict:
    """一键运行完整的用户反馈分析流水线，返回完整的仪表盘数据。

    Args:
        reviews_text: Markdown表格格式的用户评论数据
        product_bg: 产品背景文档文本（可选）
    """
    from orchestrator import Orchestrator
    orch = Orchestrator()
    return orch.run_analysis(reviews_text, product_bg, mode="feedback")


@mcp.tool()
def run_competitor_analysis(competitor_info: str, product_bg: str = "") -> dict:
    """一键运行竞品分析，返回完整的竞品对比报告。

    Args:
        competitor_info: 竞品信息文本（功能列表、定价、用户评价等）
        product_bg: 自身产品背景文档文本（可选）
    """
    from orchestrator import Orchestrator
    orch = Orchestrator()
    return orch.run_analysis(competitor_info, product_bg, mode="competitor")


# ============================================================
# 启动入口
# ============================================================

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8081)
