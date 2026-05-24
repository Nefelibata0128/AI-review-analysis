# AI评论分析平台 v3.0 — 项目总设计文档

> **本文档用途**：新对话开始时，将本文档内容作为上下文提供给 Claude，即可让 Claude 理解整个项目并开始开发。
>
> **更新日期**：2026-05-23
>
> **状态**：阶段一+二完成，阶段三（包装交付）待开始
>
> **维护规则**：本文档是活文档，随代码同步更新。任何代码变更后发现文档描述与实现不一致，应立即修正，确保新对话可独立理解项目全貌。

---

## 目录

1. [项目身份](#1-项目身份)
2. [技术栈总览](#2-技术栈总览)
3. [文件结构](#3-文件结构)
4. [系统架构](#4-系统架构)
5. [多 Agent 编排引擎设计](#5-多-agent-编排引擎设计)
6. [MCP Server 设计](#6-mcp-server-设计)
7. [前端设计](#7-前端设计)
8. [竞品分析第二场景](#8-竞品分析第二场景)
9. [跨平台通知设计](#9-跨平台通知设计)
10. [Prompt 版本管理](#10-prompt-版本管理)
11. [Dify 工作流回退模式](#11-dify-工作流回退模式)
12. [分阶段实施计划](#12-分阶段实施计划)
13. [环境配置](#13-环境配置)
14. [决策记录](#14-决策记录)
15. [写给 Claude 的开发指引](#15-写给-claude-的开发指引)

---

## 1. 项目身份

### 1.1 基本信息

| 项 | 值 |
|:---|:---|
| **项目名称** | AI评论分析平台 |
| **版本** | v3.0 |
| **一句话描述** | AI 驱动的用户反馈分析工具——上传用户评论(.txt)+产品文档(.docx/.md) → 多 Agent 协作分析 → 自动生成深度洞察仪表盘 |
| **目标用户** | 产品经理、运营负责人、创业者、数据分析师 |
| **设计原则** | 零门槛、工业级美学、非瀑布流、证据链完整 |

### 1.2 差异化卖点（面试用）

- 不是"调一个 API"的玩具，而是**多 Agent 协作 + MCP 协议 + SSE 实时反馈**的完整系统
- 同时覆盖**低代码平台（Dify）** 和**底层代码能力（Python Agent 编排）**
- 从 PRD → 原型 → 全栈开发 → 部署的完整产品交付
- 两个分析场景：用户反馈分析 + 竞品分析

### 1.3 对标岗位

| JD | 岗位 | 匹配度 | 核心关联点 |
|:---|:---|:---|:---|
| JD 2 | 技术/运营实习生（AI Native 创业团队） | ⭐⭐⭐⭐⭐ 90% | Agent 工作流、Python 自动化、MCP、前沿探索 |
| JD 8 | AI 产品管培生 | ⭐⭐⭐⭐⭐ 88% | API 拼接、业务流程 AI 重构、Agent 平台实战 |
| JD 1 | 产品运营实习生（快决测） | ⭐⭐⭐⭐ 80% | 数据看板配置、AI 工具产出文档 |
| JD 7 | 产品助理 | ⭐⭐⭐⭐ 75% | PRD 撰写、AI 提效、原型设计 |

---

## 2. 技术栈总览

### 2.1 全景图

```
┌─────────────────────────────────────────────────────────┐
│                     前端 (单文件 SPA)                      │
│  HTML5 + CSS3 + Vanilla JavaScript (ES6+)                │
│  Chart.js 4.4  →  4 类图表（柱状图/环形图/雷达图/条形图）  │
│  marked.js 15  →  Markdown 渲染                          │
│  html2canvas   →  PNG 导出                               │
│  lz-string     →  数据压缩                                │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP + SSE (Server-Sent Events)
┌────────────────────────▼────────────────────────────────┐
│                 Python 代理服务器 (proxy-server.py)        │
│  http.server (标准库)                                     │
│  ├─ 端口 8080，单文件静态服务                              │
│  ├─ CORS 头自动注入                                       │
│  ├─ Chrome UA 伪装 (绕过 Cloudflare Bot Detection)         │
│  ├─ SSE 流式中继 (防 Cloudflare 504 超时)                  │
│  └─ 路由分发: /api/* (Dify) + /api/orch/* (多Agent)       │
└────┬──────────────────┬────────────────┬────────────────┘
     │                  │                │
┌────▼───┐  ┌───────────▼──┐  ┌─────────▼──────────┐
│  Dify  │  │ orchestrator │  │   MCP Server        │
│  API   │  │   (编排引擎)  │  │   (mcp_server.py)    │
│ (保留) │  │              │  │                      │
│        │  │ 6 Agent 协作  │  │ FastMCP 框架         │
│ 文件   │  │ DeepSeek API  │  │ streamable-http      │
│ 上传   │  │ 结果合并      │  │ 端口 8081            │
│ 单工作 │  │ SSE 事件发射  │  │ 8 个分析工具          │
│ 流回退 │  │              │  │                      │
└────────┘  └──────────────┘  └──────────────────────┘
```

### 2.2 核心 Python 依赖

| 包名 | 版本 | 用途 | 为什么用它 |
|:---|:---|:---|:---|
| `openai` | >=1.0 | 调用 DeepSeek API | DeepSeek 与 OpenAI 接口完全兼容，改 base_url 即可 |
| `mcp` | >=1.0 | MCP Server | Anthropic 官方 Python SDK，FastMCP API 简洁 |
| `httpx` | >=0.28 | HTTP 客户端 | 支持异步，用于飞书通知等场景 |
| `python-docx` | >=1.0 | 解析 .docx 文件 | 用户上传的产品文档可能是 Word 格式，需提取纯文本 |

> **不需要** LangChain / CrewAI / AutoGen。本项目的 Agent 协作是简单的串行调用链——前一个 Agent 的输出作为后一个的输入，Python 原生函数即可实现。引入框架反而增加复杂度和学习成本。

### 2.3 外部服务

| 服务 | 用途 | API 端点 |
|:---|:---|:---|
| **Dify** | 文件上传 + 单工作流回退 | `https://api.dify.ai/v1` |
| **DeepSeek** | 所有 Agent 的 LLM 推理 | `https://api.deepseek.com/v1`（OpenAI 兼容） |
| **飞书** | 分析完成通知推送 | Webhook URL |

---

## 3. 文件结构

```
D:\桌面\分析web\3.0\
│
├── PROJECT.md                       # [本文档] 项目总设计文档
├── README.md                        # [阶段三] 精品 README（给面试官看的）
├── PRD-用户反馈分析仪表盘.md         # [阶段三] PRD 文档（嵌入原型图）
├── requirements.txt                 # Python 依赖清单
├── .env.example                     # 环境变量模板（不含真实 Key）
├── .env                             # 真实环境变量（不提交到 Git）
├── .gitignore                       # Git 忽略规则
│
├── proxy-server.py                  # [主入口] HTTP 代理服务器
│
├── orchestrator.py                  # [核心] 多 Agent 编排引擎
│
├── mcp_server.py                    # [核心] MCP Server (FastMCP)
│
├── lark_notifier.py                 # 飞书通知模块
│
├── agents/                          # Agent 定义目录
│   ├── __init__.py                  # 包初始化 + Agent 基类
│   ├── prompts.py                   # 所有 Agent 的 System Prompt 文本
│   ├── preprocessor.py             # Agent 1: 数据预处理
│   ├── subjectivity.py             # Agent 2: 主观性过滤
│   ├── extractor.py                # Agent 3: 五维特征抽取
│   ├── validator.py                # Agent 4: 交叉验证与异常识别
│   ├── business.py                 # Agent 5: 业务分析与优先级
│   └── competitor.py               # Agent 6: 竞品分析（第二场景）
│
├── prompts/                         # Prompt 版本管理目录
│   ├── v1/                          # 当前版本
│   │   ├── preprocessor.md
│   │   ├── subjectivity.md
│   │   ├── extractor.md
│   │   ├── validator.md
│   │   ├── business.md
│   │   └── competitor.md
│   └── CHANGELOG.md                 # Prompt 修改记录
│
├── report-dashboard.html            # [前端] 单文件 SPA
│
├── docs/                            # 文档资源
│   ├── architecture.png            # 系统架构图
│   ├── demo.gif                    # 操作演示 GIF
│   ├── benchmarks.md               # 性能对比数据
│   └── prototypes/                 # 原型图
│       ├── 01-upload.html          # 上传页原型
│       ├── 02-dashboard.html       # 仪表盘原型
│       └── 03-agent-timeline.html  # Agent 时间线原型
│
├── deploy/                          # 部署配置
│   ├── Dockerfile                   # 容器化配置
│   ├── railway.json                 # Railway 部署配置
│   └── nginx.conf                   # Nginx 配置（可选）
│
└── tests/                           # 测试文件
    └── test_orchestrator.py         # 编排引擎单元测试
```

---

## 4. 系统架构

### 4.1 请求流转路径

```
用户浏览器 (localhost:8080)
    │
    │ POST /api/orch/run   (多 Agent 模式)
    │   ├─ 用户评论 .txt 文件
    │   └─ 产品介绍 .docx / .md 文件 (可选)
    │ GET  /api/orch/events (SSE 进度流)
    │
    ▼
proxy-server.py  ──────────────────────────────────────────
    │                   │                   │
    │ 文件上传          │ Agent 调用         │ SSE 事件
    ▼                   ▼                   ▼
Dify API          orchestrator.py      前端时间线
(单工作流回退)       │                  实时更新
                    │
                    ├─ Agent1 (预处理)
                    ├─ Agent2 (主观性)
                    ├─ Agent3 (五维抽取)
                    ├─ Agent4 (交叉验证)
                    ├─ Agent5 (业务分析)
                    └─ Agent6 (竞品分析, 第二场景)
                    │
                    ▼
              DeepSeek API
           (每个 Agent 独立调用)
                    │
                    ▼
              MCP Server (工具调用)
```

### 4.2 两种分析模式

| 模式 | 前端标签 | 后端路径 | LLM 调用次数 | 进度可见 | 适用场景 |
|:---|:---|:---|:---|:---|:---|
| **快速模式** | "单工作流" | Dify Workflow API | 1 次 | 仅完成/失败 | 小文件、快速预览 |
| **深度模式** | "多 Agent" | orchestrator.py | 5 次 | 5 步逐个可见 | 完整分析、面试演示 |

用户在前端通过单选按钮切换，默认为深度模式。

### 4.3 SSE 事件协议

多 Agent 模式下，orchestrator 通过 SSE 向浏览器推送以下事件：

```
event: agent_started
data: {"agent": "Preprocessor", "agent_label": "数据预处理", "message": "正在统计数据分布...", "ts": 1700000000}

event: agent_completed
data: {"agent": "Preprocessor", "agent_label": "数据预处理", "duration_ms": 5200, "ts": 1700000005}

event: agent_started
data: {"agent": "SubjectivityFilter", "agent_label": "主观性过滤", "message": "正在逐条判定主观性...", "ts": 1700000006}

... (每个 Agent 一对 started/completed 事件) ...

event: workflow_completed
data: {"status": "succeeded", "outputs": {"final_report": "---JSON---\n{...}\n---MARKDOWN---\n..."}, "total_duration_ms": 52000}

event: error
data: {"agent": "BusinessAnalyzer", "message": "API 调用超时", "ts": 1700000050}
```

心跳：每 15 秒发送 `: heartbeat\n\n`（SSE 注释行，浏览器忽略），防止连接超时断开。

---

## 5. 多 Agent 编排引擎设计

### 5.1 设计理念

**不做复杂的 Agent 框架，只做清晰的函数调用链。**

每个 Agent 本质上是：
```
Agent = 专属 System Prompt + DeepSeek API 调用 + 可选的 MCP 工具
```

编排引擎的本质是：
```
Orchestrator = 按依赖顺序串行调用 Agent + 传递中间结果 + 合并最终输出
```

### 5.2 六个 Agent 详表

#### Agent 1: Preprocessor（数据预处理）

| 项 | 值 |
|:---|:---|
| **中文名** | 数据预处理 |
| **职责** | 逐条统计 1-5 星评分分布、计算平均分、建立用户评分基线 |
| **输入** | 用户评论原始文本（Markdown 表格格式） |
| **输出** | `{total_reviews, avg_rating, rating_distribution, user_baselines}` |
| **Temperature** | 0.3（计数任务要求精确，低温度减少随机性） |
| **可用 MCP 工具** | `count_ratings`, `calc_baseline` |
| **预估耗时** | 5-10 秒 |

#### Agent 2: SubjectivityFilter（主观性过滤）

| 项 | 值 |
|:---|:---|
| **中文名** | 主观性过滤 |
| **职责** | 逐条判定评论主观性分数(0-1)，分流为"情绪宣泄"或"理性反馈" |
| **输入** | 原始评论文本 + Agent 1 输出 |
| **输出** | `{high_count, low_count, high_avg_rating, low_avg_rating, classifications[]}` |
| **Temperature** | 0.5 |
| **可用 MCP 工具** | `analyze_subjectivity` |
| **预估耗时** | 8-12 秒 |

#### Agent 3: FiveDimExtractor（五维特征抽取）

| 项 | 值 |
|:---|:---|
| **中文名** | 五维特征抽取 |
| **职责** | ABSA 态度-目标矩阵、8 种情绪分布、5 类行为意图、信息源归因、缺陷 Top10、亮点 Top5、功能诉求 |
| **输入** | 原始评论 + Agent 1 输出 + Agent 2 输出 |
| **输出** | `{attitude_goal_matrix, emotion_distribution, behavioral_intentions, info_sources, defects, highlights, feature_requests}` |
| **Temperature** | 0.5 |
| **可用 MCP 工具** | `extract_keywords`, `classify_emotion` |
| **预估耗时** | 15-20 秒（最大 Agent） |

#### Agent 4: CrossValidator（交叉验证）

| 项 | 值 |
|:---|:---|
| **中文名** | 交叉验证与异常识别 |
| **职责** | 检测评分-文本冲突（高分负评/低分正评）、识别流失预警用户 |
| **输入** | 原始评论 + Agent 1+2+3 输出 |
| **输出** | `{conflicts[], churn_risks[], alert_count}` |
| **Temperature** | 0.3（检测任务要求精确） |
| **可用 MCP 工具** | `detect_conflict`, `assess_churn_risk` |
| **预估耗时** | 8-12 秒 |

#### Agent 5: BusinessAnalyzer（业务分析）

| 项 | 值 |
|:---|:---|
| **中文名** | 业务分析与优先级 |
| **职责** | 生成 P0-P3 产品迭代优先级看板 + Markdown 总结结论 + 口碑概况 |
| **输入** | 原始评论 + Agent 1+2+3+4 全部输出 |
| **输出** | `{priority_board[], conclusion_markdown, sentiment_label}` |
| **Temperature** | 0.5 |
| **可用 MCP 工具** | `rank_priority`, `format_markdown` |
| **预估耗时** | 10-15 秒 |

#### Agent 6: CompetitorAnalyzer（竞品分析 — 第二场景）

| 项 | 值 |
|:---|:---|
| **中文名** | 竞品分析 |
| **职责** | 基于竞品信息 + 产品背景文档，分析竞争优势劣势、功能差异、市场定位 |
| **输入** | 竞品信息文本 + 产品背景文档 + Agent 1 输出（复用预处理统计） |
| **输出** | `{competitor_overview, feature_comparison, swot, recommendations}` |
| **Temperature** | 0.5 |
| **预估耗时** | 12-18 秒 |
| **注意** | Agent 6 是第二场景入口。竞品分析场景中，Agent 1 预处理后 → Agent 6 → Agent 4 → Agent 5（复用交叉验证和业务分析） |

### 5.3 Agent 基类设计

```python
# agents/__init__.py 中的核心接口

class Agent:
    """所有 Agent 的基类"""
    name: str           # 英文标识，如 "Preprocessor"
    label: str          # 中文显示名，如 "数据预处理"
    system_prompt: str  # System Prompt 文本
    temperature: float  # 0.3-0.5
    model: str          # "deepseek-chat"
    mcp_tools: list     # 该 Agent 可调用的 MCP 工具名列表

    def run(self, context: dict) -> dict:
        """调用 DeepSeek API，传入上下文，返回解析后的 JSON 结果"""
        # 1. 组装 messages: [system_prompt, user_message(context)]
        # 2. 调用 DeepSeek API (OpenAI 兼容)
        # 3. 从响应中提取 JSON（3 级降级解析）
        # 4. 如果 Agent 有 MCP 工具，在 tool_choice 中声明
        # 5. 返回 dict
```

### 5.4 编排器设计

```python
# orchestrator.py 中的核心逻辑

class Orchestrator:
    """多 Agent 编排引擎"""

    agents: dict[str, Agent]  # 6 个 Agent 实例
    sse_emitter: SSEEmitter   # SSE 事件发射器

    def run_analysis(self, review_text: str, bg_text: str, mode: str = "feedback") -> dict:
        """运行分析流水线"""
        # mode = "feedback" → Agent1→2→3→4→5
        # mode = "competitor" → Agent1→6→4→5

        context = {"review_text": review_text, "bg_text": bg_text}

        # 逐步执行，每步前发 started 事件，后发 completed 事件
        for agent_id in self._get_pipeline(mode):
            self.sse_emitter.agent_started(agent_id)
            result = self.agents[agent_id].run(context)
            context[agent_id] = result  # 存入上下文供后续 Agent 使用
            self.sse_emitter.agent_completed(agent_id, duration_ms)

        # 合并所有 Agent 结果
        final = self._merge_results(context, mode)
        self.sse_emitter.workflow_completed(final)
        return final
```

### 5.5 结果合并逻辑

编排器将 5 个 Agent 的碎片化输出合并为前端期望的 14 字段 JSON：

```python
def _merge_results(self, context: dict) -> dict:
    a1 = context["Preprocessor"]
    a2 = context["SubjectivityFilter"]
    a3 = context["FiveDimExtractor"]
    a4 = context["CrossValidator"]
    a5 = context["BusinessAnalyzer"]

    return {
        "meta": {
            "total_reviews": a1["total_reviews"],
            "avg_rating": a1["avg_rating"],
            "sentiment_label": a5["sentiment_label"],
            "alert_count": a4["alert_count"]
        },
        "rating_distribution": a1["rating_distribution"],
        "subjectivity": {
            "high_count": a2["high_count"],
            "low_count": a2["low_count"],
            "high_avg_rating": a2["high_avg_rating"],
            "low_avg_rating": a2["low_avg_rating"],
            "high_label": "情绪宣泄",
            "low_label": "理性反馈"
        },
        "attitude_goal_matrix": a3["attitude_goal_matrix"],
        "emotion_distribution": a3["emotion_distribution"],
        "behavioral_intentions": a3["behavioral_intentions"],
        "info_sources": a3["info_sources"],
        "defects": a3["defects"],
        "highlights": a3["highlights"],
        "feature_requests": a3["feature_requests"],
        "conflicts": a4["conflicts"],
        "churn_risks": a4["churn_risks"],
        "priority_board": a5["priority_board"],
        "conclusion_markdown": a5["conclusion_markdown"]
    }
```

### 5.6 SSE 事件发射器

```python
class SSEEmitter:
    """线程安全的 SSE 事件发射器"""
    event_queue: queue.Queue  # 事件队列

    def agent_started(self, agent_id, message): ...
    def agent_completed(self, agent_id, duration_ms): ...
    def workflow_completed(self, outputs): ...
    def agent_error(self, agent_id, error_message): ...
```

Proxy 从 event_queue 中读取事件，格式化为 `event: xxx\ndata: {...}\n\n` 写入 HTTP 响应。

---

## 6. MCP Server 设计

### 6.1 概述

MCP Server 是一个独立的工具服务器，遵循 [Model Context Protocol](https://spec.modelcontextprotocol.io) 2025-11-25 规范。

**两个使用场景**：
1. **内部**：Agent 编排过程中调用 MCP 工具进行精确计算
2. **外部**：可以被 Claude Desktop 等 MCP 客户端发现和调用

### 6.2 技术选型

| 项 | 选择 | 原因 |
|:---|:---|:---|
| **框架** | FastMCP（`mcp` 包内置） | 官方推荐的高级 API，减少约 68% 样板代码 |
| **传输** | streamable-http | 可被多个客户端同时访问，不需要进程管理 |
| **端口** | 8081 | 与 proxy 8080 分离，互不干扰 |

### 6.3 工具清单

#### 小工具（可被 Agent 分步调用）

| # | 工具名 | 功能 | 输入参数 | 返回值 |
|:---|:---|:---|:---|:---|
| 1 | `count_ratings` | 从表格文本中精确统计 1-5 星评分数 | `reviews_text: str` | `{"5星": N, "4星": N, ...}` |
| 2 | `analyze_subjectivity` | 判定单条评论的主观性分数 | `review_text: str` | `{"score": 0.85, "label": "情绪宣泄"}` |
| 3 | `extract_keywords` | 提取评论文本关键词及权重 | `text: str, top_n: int=10` | `[{"word": "闪退", "weight": 0.9}, ...]` |
| 4 | `classify_emotion` | 识别文本中的情绪标签 | `text: str` | `{"emotion": "愤怒", "confidence": 0.9}` |
| 5 | `detect_conflict` | 检测评分与文本的冲突 | `rating: int, text: str` | `{"conflict": true, "type": "高分负评"}` |
| 6 | `assess_churn_risk` | 评估单用户的流失风险 | `user_comments: list, user_baseline: float` | `{"risk": "高级", "signals": [...]}` |

#### 大工具（一键全流程，对外展示用）

| # | 工具名 | 功能 | 输入参数 | 返回值 |
|:---|:---|:---|:---|:---|
| 7 | `run_feedback_analysis` | 一键运行用户反馈完整分析 | `reviews_text: str, product_bg: str=""` | 完整 JSON 报告（14 字段） |
| 8 | `run_competitor_analysis` | 一键运行竞品分析 | `competitor_info: str, product_bg: str=""` | 竞品对比报告 |

### 6.4 FastMCP 代码骨架

```python
# mcp_server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("AI评论分析平台 分析工具")

@mcp.tool()
def count_ratings(reviews_text: str) -> dict:
    """精确统计用户评论中1-5星的评分分布。
    
    Args:
        reviews_text: Markdown表格格式的用户评论数据
    """
    # 实现...

@mcp.tool()
def run_feedback_analysis(reviews_text: str, product_bg: str = "") -> dict:
    """一键运行完整的用户反馈分析流水线。
    
    Args:
        reviews_text: 用户评论数据
        product_bg: 产品背景文档（可选）
    """
    from orchestrator import Orchestrator
    orch = Orchestrator()
    return orch.run_analysis(reviews_text, product_bg, mode="feedback")

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8081)
```

---

## 7. 前端设计

### 7.1 概述

- **文件**：`report-dashboard.html`（单文件，HTML + CSS + JS 全部内联）
- **设计系统**：Google Material 风格（蓝色主色调 `#0050cb`），21 个 CSS 变量
- **依赖**：Chart.js 4.4、marked.js 15、html2canvas 1.4、lz-string 1.5（均通过 CDN 加载）
- **输入文件**：支持双文件上传——用户评论(.txt) + 产品介绍(.docx/.md)，产品文档为可选

### 7.2 上传区域设计

上传区支持两个独立的文件选择器，布局如下：

```
┌──────────────────────────────────────────────────┐
│  📎 用户评论文件 (必填)                            │
│  ┌──────────────────────────────────────────────┐│
│  │  📄 拖拽或点击上传 .txt 文件                   ││
│  │  支持 Markdown 表格格式的评论数据               ││
│  └──────────────────────────────────────────────┘│
│                                                  │
│  📎 产品介绍文档 (可选)                            │
│  ┌──────────────────────────────────────────────┐│
│  │  📄 拖拽或点击上传 .docx / .md 文件             ││
│  │  PRD、产品背景说明、功能列表等                   ││
│  └──────────────────────────────────────────────┘│
└──────────────────────────────────────────────────┘
```

**文件格式支持**：

| 输入 | 格式 | 必填 | 内容 | 后端处理 |
|:---|:---|:---|:---|:---|
| 用户评论 | `.txt` | 是 | Markdown 表格格式的评论数据（含评分+文本） | 直接读取文本内容 → `review_text` |
| 产品文档 | `.docx` / `.md` | 否 | PRD、产品背景、功能说明 | proxy 端解析 .docx → `bg_text` |

> **注意**：`.docx` 文件在 `proxy-server.py` 端用 `python-docx` 库解析为纯文本后再传入编排器。如果只上传评论文件不传产品文档，分析仍可进行，但业务分析 Agent 缺少产品背景上下文。

### 7.3 页面布局

```
┌──────────────────────────────────────────────────────────────┐
│ ┌──────────┐ ┌──────────────────────────────────────────────┐│
│ │          │ │  Top Bar (文件摘要 + 重新上传按钮)             ││
│ │          │ ├──────────────────────────────────────────────┤│
│ │ Sidebar  │ │  Status Bar / Agent Timeline                 ││
│ │ 256px    │ ├──────────────────────────────────────────────┤│
│ │ 深色     │ │                                              ││
│ │ 固定     │ │  Dashboard Area (局部滚动)                    ││
│ │          │ │  ├─ KPI Cards (4 列网格)                      ││
│ │ 导航链接 │ │  ├─ Charts Row1 (评分柱状图 + 主观性环形图)    ││
│ │ + 导出   │ │  ├─ Charts Row2 (态度矩阵 + 情绪雷达图)       ││
│ │          │ │  ├─ Behavior & Info Sources                  ││
│ │          │ │  ├─ Tabbed Tables (6 个标签面板)              ││
│ │          │ │  └─ Conclusion (Markdown 渲染)               ││
│ └──────────┘ └──────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

### 7.3 v3.0 新增 UI 组件

#### 组件 1：模式选择器

位置：上传区域底部，CTA 按钮上方

```html
<div class="mode-selector">
  <label class="mode-option">
    <input type="radio" name="analysisMode" value="multi-agent" checked>
    <span class="mode-label">🔍 深度分析（多 Agent）</span>
    <span class="mode-desc">5 步推进，进度可见，结果更精准</span>
  </label>
  <label class="mode-option">
    <input type="radio" name="analysisMode" value="single">
    <span class="mode-label">⚡ 快速分析（单工作流）</span>
    <span class="mode-desc">一次完成，速度更快</span>
  </label>
</div>
```

#### 组件 2：Agent 进度时间线

位置：状态栏和 Dashboard 之间，分析过程中显示

```html
<div class="agent-timeline" id="agentTimeline">
  <div class="timeline-track">
    <!-- JS 动态生成 5 个节点 -->
  </div>
</div>
```

**视觉设计**：
- 左侧竖线（2px，灰色）
- 每个节点：圆点标记 + Agent 中文名 + 状态文字 + 耗时
- 颜色语义：灰色=等待中，蓝色脉冲=进行中，绿色=完成，红色=失败

**支持的操作**：
- 点击已完成的节点 → 展开 Agent 中间输出摘要
- 全部完成后时间线保留显示（不再隐藏），方便复盘

#### 组件 3：竞品分析入口

位置：上传区域顶部，两个场景标签切换

```html
<div class="scene-tabs">
  <button class="scene-tab active" data-scene="feedback">📊 用户反馈分析</button>
  <button class="scene-tab" data-scene="competitor">🔍 竞品分析</button>
</div>
```

切换场景后，上传区文件输入标签相应变化（"上传用户评论"→"上传竞品信息"）。

### 7.4 JavaScript 核心函数（v3.0 新增/修改）

| 函数名 | 类型 | 功能 |
|:---|:---|:---|
| `runMultiAgent()` | 新增 | 多 Agent 模式的 SSE 流监听与进度更新 |
| `initTimeline()` | 新增 | 初始化 Agent 时间线节点 |
| `updateTimelineNode()` | 新增 | 更新单个 Agent 节点的状态（等待→进行中→完成→失败） |
| `toggleAgentDetail()` | 新增 | 展开/收起 Agent 中间输出 |
| `runAnalysis()` | 修改 | 根据模式选择器分发到 `runWorkflow()` 或 `runMultiAgent()` |
| `switchScene()` | 新增 | 切换"用户反馈分析"和"竞品分析"场景 |

### 7.5 现有功能保留

以下功能从 v2.0 完整保留，不做修改：
- 文件上传卡片（虚线空态/实线已选态）
- KPI 卡片渲染
- 4 类 Chart.js 图表渲染
- 6 标签数据表格
- Markdown 总结结论区
- Scroll Spy 导航
- 浏览器打印导出
- 错误 Toast
- 响应式三断点（1024/768/480px）

---

## 8. 竞品分析第二场景

### 8.1 两个场景的用户流程

#### 场景 A：用户反馈分析

```
1. 保持「用户反馈分析」场景标签
2. 上传用户评论 .txt 文件（必填，Markdown 表格格式）
3. 上传产品介绍 .docx/.md 文件（可选，提供产品背景上下文）
4. 选择分析模式（深度 / 快速）
5. 点击「开始分析」
6. Agent1 → Agent2 → Agent3 → Agent4 → Agent5
7. 输出用户反馈分析仪表盘
```

#### 场景 B：竞品分析

```
1. 用户切换到「竞品分析」场景标签
2. 上传竞品信息文件 .txt/.docx/.md（竞品名称、功能列表、定价、用户评价等）
3. 上传产品介绍 .docx/.md 文件（可选，与场景 A 共用同一输入框）
4. 点击「开始分析」
5. Agent1(预处理) → Agent6(竞品分析) → Agent4(交叉验证) → Agent5(业务分析)
6. 输出竞品对比报告仪表盘
```

### 8.2 竞品分析输出结构

```json
{
  "competitor_overview": {
    "competitor_name": "...",
    "market_position": "...",
    "target_users": "..."
  },
  "feature_comparison": [
    {"feature": "功能A", "us": "有/优", "them": "无/劣", "gap": "领先|落后|持平"}
  ],
  "swot": {
    "strengths": ["..."],
    "weaknesses": ["..."],
    "opportunities": ["..."],
    "threats": ["..."]
  },
  "recommendations": [
    {"priority": "P0", "action": "...", "reason": "...", "timeline": "..."}
  ]
}
```

### 8.3 Agent 复用关系

```
用户反馈分析场景:  Agent1 → Agent2 → Agent3 → Agent4 → Agent5
                        ↓                          ↓        ↓
竞品分析场景:      Agent1 → Agent6(竞品) ──────────┘        │
                  (复用)   (新增)    复用交叉验证逻辑    (复用)
```

Agent 1（预处理）、Agent 4（交叉验证）、Agent 5（业务分析）在两个场景间复用，大幅减少开发量。

---

## 9. 跨平台通知设计

### 9.1 飞书通知

**触发时机**：多 Agent 分析完成后，`orchestrator` 发出 `workflow_completed` 事件时。

**通知内容**：
```
🤖 AI评论分析平台 分析完成
📊 [场景名] — [文件名]
━━━━━━━━━━━━━━━━━━━━
⭐ 均分: 3.2/5  |  评论: 70 条
🔴 告警: 5 人流失风险
📎 查看报告: http://localhost:8080
```

**实现方式**：飞书自定义机器人 Webhook。

```python
# lark_notifier.py
import httpx

LARK_WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"

async def send_notification(title, summary, report_url):
    async with httpx.AsyncClient() as client:
        await client.post(LARK_WEBHOOK_URL, json={
            "msg_type": "interactive",
            "card": {
                "header": {"title": {"content": f"🤖 AI评论分析平台 — {title}"}},
                "elements": [
                    {"tag": "div", "text": {"content": summary}},
                    {"tag": "action", "actions": [{"tag": "button", "text": {"content": "查看完整报告"}, "url": report_url}]}
                ]
            }
        })
```

---

## 10. Prompt 版本管理

### 10.1 目的

- 将 Prompt 作为独立资产，用 Git 追踪每次修改
- 展示 PE（Prompt Engineer）协作流程：设计 → 实验 → 迭代 → 文档
- 面试时可以直接打开 `prompts/CHANGELOG.md` 展示迭代思路

### 10.2 目录结构

```
prompts/
├── v1/
│   ├── preprocessor.md    # Agent 1 的完整 System Prompt
│   ├── subjectivity.md    # Agent 2
│   ├── extractor.md       # Agent 3
│   ├── validator.md       # Agent 4
│   ├── business.md        # Agent 5
│   └── competitor.md      # Agent 6
└── CHANGELOG.md
```

### 10.3 CHANGELOG 格式

```markdown
# Prompt 修改记录

## 2026-05-22 — v1.0 初始版本
- **来源**: 从 Dify YML `txt用户评论文本分析 (1).yml` 中提取并拆分
- **拆分策略**: 将原 3000 字单一 Prompt 按"五阶段"边界拆分为 5 段
- **变更**: 每条 Prompt 新增输出 JSON Schema 约束
- **验证**: 用同一份测试数据（用户评价表格.xlsx），对比拆分前后 JSON 输出一致性
```

---

## 11. Dify 工作流回退模式

### 11.1 保留原因

1. **展示多平台能力**：证明既能用 Dify 等低代码平台，也能从零写 Python Agent
2. **快速模式**：小文件或快速预览时，单工作流更快（1 次 API 调用 vs 5 次）
3. **容灾**：如果 DeepSeek API 出问题，Dify 工作流可作为备用路径

### 11.2 实现方式

- `proxy-server.py` 中保留原有的 `POST /api/workflows/run` 代理逻辑
- 前端选择"快速模式"时，走 Dify 路径（现有代码，100% 不变）
- 前端选择"深度模式"时，走 `POST /api/orch/run`
- 两种模式最终输出格式一致（14 字段 JSON），`renderAll()` 无需修改

---

## 12. 分阶段实施计划

### 阶段一：技术地基（预计 4-6 小时） ✅ 已完成

| 步骤 | 产出文件 | 说明 | 状态 |
|:---|:---|:---|:---|
| 1.1 | `requirements.txt` | `openai>=1.0` `mcp>=1.0` `httpx>=0.28` `python-docx>=1.0` | ✅ |
| 1.2 | `agents/prompts.py` | 从 v2.0 Dify YML 提取 6 段 Prompt（含竞品分析），拆分为独立变量 | ✅ |
| 1.3 | `agents/__init__.py` | Agent 基类：`Agent` dataclass + `call_deepseek()` + `extract_json()` 3级降级解析 | ✅ |
| 1.4 | `agents/preprocessor.py` → `business.py` | 5 个 Agent 子类，各自持有一个 System Prompt | ✅ |
| 1.5 | `orchestrator.py` | 编排引擎：`Orchestrator` 类 + `SSEEmitter` 类 + `_merge_results()` 14字段合并 | ✅ |
| 1.6 | `mcp_server.py` | FastMCP Server：8 个 `@mcp.tool()` 函数，streamable-http 端口 8081 | ✅ |
| 1.7 | `proxy-server.py` | 新增：双文件上传解析、`POST /api/orch/run`、`GET /api/orch/events` SSE 流、`.docx` 解析 | ✅ |
| 1.8 | `report-dashboard.html` | 新增：场景标签、模式选择器、Agent 时间线、`runMultiAgent()` SSE 监听、`switchScene()` | ✅ |

### 阶段二：技术增量（预计 3-4 小时） ✅ 已完成

| 步骤 | 产出文件 | 说明 | 状态 |
|:---|:---|:---|:---|
| 2.1 | `agents/competitor.py` | Agent 6 竞品分析类，已在 orchestrator 中注册 | ✅ |
| 2.2 | `lark_notifier.py` | 飞书 Webhook 通知模块，支持异步/同步两种调用方式 | ✅ |
| 2.3 | `prompts/v1/*.md` + `prompts/CHANGELOG.md` | 6 个 Prompt 版本文件 + 修改记录 | ✅ |
| 2.4 | `deploy/Dockerfile` + `deploy/railway.json` | Docker 容器化 + Railway 一键部署配置 | ✅ |

### 阶段三：包装交付（预计 4-5 小时） 🔴 P0

| 步骤 | 产出文件 | 说明 |
|:---|:---|:---|
| 3.1 | `docs/architecture.png` | Mermaid 生成架构图 |
| 3.2 | `docs/demo.gif` | 录屏操作演示 |
| 3.3 | `docs/benchmarks.md` | 人工 vs AI 效率对比数据表 |
| 3.4 | `.gitignore` + GitHub 仓库初始化 | 公开仓库，API Key 不入库 |
| 3.5 | `README.md` | 精品 README：项目介绍 + 架构图 + 快速开始 + 技术栈 + Benchmark |
| 3.6 | `docs/prototypes/*.html` | 3 个 HTML 原型页面，截图后嵌入 PRD |
| 3.7 | `PRD-用户反馈分析仪表盘.md` | 更新 PRD，嵌入原型图 |

---

## 13. 环境配置

### 13.1 `.env` 文件

```bash
# .env — 真实 Key，不提交到 Git

# DeepSeek API（Agent LLM 调用）
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# Dify API（文件上传 + 单工作流回退）
DIFY_API_KEY=app-C1KcaMNdlCYgzG2k0ncUFBnm

# 飞书机器人 Webhook（可选）
LARK_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx
```

### 13.2 `.env.example`

```bash
# .env.example — 提交到 Git，不含真实 Key

DEEPSEEK_API_KEY=your-deepseek-api-key-here
DIFY_API_KEY=your-dify-api-key-here
LARK_WEBHOOK_URL=your-lark-webhook-url-here  # 可选
```

### 13.3 `.gitignore`

```
.env
__pycache__/
*.pyc
*.pyo
.DS_Store
Thumbs.db
```

### 13.4 安装与启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入真实 API Key

# 3. 启动主服务（proxy + orchestrator）
python proxy-server.py
# 访问 http://localhost:8080

# 4. （可选）启动 MCP Server
python mcp_server.py
# 运行在 http://localhost:8081/mcp
```

---

## 14. 决策记录

| # | 决策点 | 选择 | 原因 |
|:---|:---|:---|:---|
| 1 | 第二 Agent 场景 | **竞品分析** | 复用度最高（4/5 Agent 可复用）、产品经理面试高频需求 |
| 2 | MCP 工具粒度 | **粗细结合** | 既能被 Agent 分步调用，也能被外部 AI 一键使用 |
| 3 | 跨平台通知 | **飞书** | 国内实习主流协作工具，JD 3 提及飞书生态 |
| 4 | 线上部署 | **Railway** | 免费、稳定、关联 GitHub 自动部署 |
| 5 | 原型图方式 | **HTML 画原型** | 可以直接打开交互，截图后可嵌入 PRD |
| 6 | GitHub 仓库 | **公开但隐藏 Key** | 面试可直接发链接，Key 通过 .env 隔离 |
| 7 | Dify 回退模式 | **保留** | 证明低代码 + 自研双重能力 |
| 8 | 项目名称 | **重命名为 AI评论分析平台** | 简单直白，体现核心功能 |
| 9 | LLM 后端 | **DeepSeek API 直接调用** | Dify API Key 是 Workflow 类型无法用于 Chat |
| 10 | Agent 框架 | **不使用任何框架** | 串行调用链足够简单，无需 LangChain/CrewAI |

---

## 15. 写给 Claude 的开发指引

> **当在新对话中引用本文档时，请按以下原则进行开发：**

### 编码原则

1. **先想后写**：先理解本文档中的架构设计，再动手写代码。不确定的地方提问。
2. **简单优先**：最少的代码解决问题。不为只使用一次的代码创建抽象。
3. **精准修改**：每次只改一个文件、一个功能点。不碰无关代码。
4. **匹配现有风格**：Python 用 snake_case，JavaScript 用 camelCase，CSS 用 kebab-case。

### 技术约束

- **Python** 使用标准库 + `openai` / `mcp` / `httpx` / `python-docx`，不引入其他第三方包
- **前端** 所有 CSS/JS 内联在单个 HTML 文件中，不拆分为独立文件
- **API Key** 始终从环境变量读取，不硬编码
- **DeepSeek API** 使用 `openai` 包，设置 `base_url="https://api.deepseek.com/v1"`
- **MCP** 使用 `FastMCP` 高级 API，传输方式 `streamable-http`

### 优先级

实施顺序严格按 **阶段一 → 阶段二 → 阶段三**。不要跳步骤或提前做后续阶段的工作。

### 参考源

- 现有 v2.0 项目位于 `D:\桌面\xiugai\`，其中：
  - `report-dashboard.html` 是前端完整参考
  - `proxy-server.py` 是代理服务器完整参考
  - `txt用户评论文本分析 (1).yml` 包含 Agent Prompt 的原始文本
  - `PRD-用户反馈分析仪表盘.md` 是 PRD 文档
- DeekSeek API: `base_url` 为 `https://api.deepseek.com/v1`，模型名 `deepseek-chat`
- MCP SDK: `pip install mcp`，文档见 [github.com/modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk)

---

> **文档结束**
>
> 将此文档作为新对话的起始上下文，Claude 将可以独立完成 v3.0 的全部开发工作。

---

## 16. 后续优化项

> 在开发过程中发现的技术债、改进思路记录于此，避免遗忘。实施优先级由阶段规划决定。

| # | 优化项 | 优先级 | 关联文件 | 提出日期 |
|---|--------|--------|----------|----------|
| 1 | proxy 端 .docx 流式解析（避免大文件全量读入内存） | P2 | proxy-server.py | 2026-05-22 |
| 2 | 场景 B 竞品信息支持从 URL 抓取竞品数据 | P3 | — | 2026-05-22 |
| — | _(待补充)_ | — | — | — |

---

## 17. 维护 Checklist

每次代码变更完成后，对照以下节检查是否需要同步更新 CLAUDE.md：

| 检查节 | 触发条件 |
|--------|----------|
| §3 文件结构 | 新增/删除/重命名任何文件 |
| §4 系统架构 | 路由变更、数据流变更、端口变更 |
| §5/6 Agent/MCP | Agent 增删、参数变更、工具增删 |
| §7 前端设计 | 组件变更、API 变更、布局调整 |
| §8 场景流程 | 用户流程变更、文件输入格式变更 |
| §12 实施计划 | 阶段性完成、进度更新 |
| §14 决策记录 | 任何架构选择、技术取舍 |
| §16 后续优化项 | 发现新问题或改进思路 |
