"""
端到端测试：用 5 条示例评论跑通完整 5 Agent 流水线。
用法: py -3.12 test_e2e.py
"""
import os
import sys

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.dirname(__file__))

# 加载 .env
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

# 测试数据：5 条模拟评论（Markdown 表格）
TEST_REVIEWS = """| 序号 | 用户名 | 评分 | 评论文本 |
|:---|:---|:---|:---|
| 1 | 张三 | 4 | UI设计很好看，手势操作也很流畅，推荐给朋友！ |
| 2 | 李四 | 1 | 垃圾软件!!! 打开就闪退，已经卸载了，气死我了 |
| 3 | 王五 | 3 | 功能还行，但视频加载太慢了，希望能优化一下速度 |
| 4 | 赵六 | 5 | 非常好用，客服回复也快，深色模式很护眼 |
| 5 | 孙七 | 2 | 安卓版经常卡顿，准备用回XX了，失望 |"""

TEST_BG = """产品名称：XX App
产品定位：一款面向年轻用户的短视频社交平台
核心功能：视频浏览、创作工具、社交互动、直播
当前版本：3.2.1"""

if __name__ == "__main__":
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        print("错误：未设置 DEEPSEEK_API_KEY，请检查 .env 文件")
        sys.exit(1)
    print(f"API Key: {api_key[:8]}...{api_key[-4:]}")
    print(f"测试数据: 5 条评论 + 产品背景\n")

    from orchestrator import Orchestrator
    orch = Orchestrator()

    print("启动 5 Agent 流水线...\n")
    try:
        result = orch.run_analysis(TEST_REVIEWS, TEST_BG, mode="feedback")
        print("=" * 50)
        print("分析完成！结果概要：")
        print("=" * 50)
        meta = result.get("meta", {})
        print(f"总评论数: {meta.get('total_reviews')}")
        print(f"平均评分: {meta.get('avg_rating')}")
        print(f"口碑概况: {meta.get('sentiment_label')}")
        print(f"告警数量: {meta.get('alert_count')}")
        print(f"评分分布: {result.get('rating_distribution')}")
        print(f"主观性: 高={result.get('subjectivity',{}).get('high_count')} 低={result.get('subjectivity',{}).get('low_count')}")
        defects = result.get("defects", [])
        if defects:
            print(f"缺陷 Top1: {defects[0].get('issue')}")
        priority = result.get("priority_board", [])
        if priority:
            print(f"P0 项数: {sum(1 for p in priority if p.get('priority')=='P0')}")
        print(f"\n总结结论:\n{result.get('conclusion_markdown','')[:300]}...")
    except Exception as e:
        print(f"分析失败: {e}")
        sys.exit(1)
