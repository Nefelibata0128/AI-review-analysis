# 系统架构图

```mermaid
graph TD
    A[用户浏览器] -->|HTTP + SSE| B[proxy-server.py :8080]
    B -->|静态文件| C[report-dashboard.html]
    B -->|/api/*| D[Dify API<br/>单工作流回退]
    B -->|/api/orch/run| E[orchestrator.py<br/>编排引擎]
    B -->|/api/orch/events<br/>SSE 进度流| A

    E --> F[Agent 1: Preprocessor<br/>数据预处理 t=0.3]
    E --> G[Agent 2: SubjectivityFilter<br/>主观性过滤 t=0.5]
    E --> H[Agent 3: FiveDimExtractor<br/>五维特征抽取 t=0.5]
    E --> I[Agent 4: CrossValidator<br/>交叉验证 t=0.3]
    E --> J[Agent 5: BusinessAnalyzer<br/>业务分析 t=0.5]
    E --> K[Agent 6: CompetitorAnalyzer<br/>竞品分析 t=0.5]

    F --> L[DeepSeek API]
    G --> L
    H --> L
    I --> L
    J --> L
    K --> L

    E -.->|工具调用| M[MCP Server :8081<br/>8 个分析工具]
    M -.->|FastMCP| L

    J --> N[飞书通知<br/>lark_notifier.py]

    E --> O[SSEEmitter<br/>事件队列]
    O -->|agent_started / agent_completed| B

    style B fill:#0050cb,color:#fff
    style E fill:#1a73e8,color:#fff
    style M fill:#34a853,color:#fff
    style L fill:#ea4335,color:#fff
    style N fill:#4285f4,color:#fff
```

## 数据流

```
用户上传双文件 (.txt + .docx/.md)
  → proxy-server 解析 .docx
    → orchestrator 串行调用 5-6 个 Agent
      → 每个 Agent 调用 DeepSeek API + 可选 MCP 工具
        → SSE 实时推送进度到浏览器
          → 前端时间线实时更新
            → 分析完成 + 飞书通知
```

## 两种分析模式

| 模式 | 流水线 | LLM 调用 | 适用场景 |
|:---|:---|:---|:---|
| 深度（多 Agent） | Agent1→2→3→4→5 | 5 次 | 完整分析、进度可见 |
| 快速（单工作流） | Dify Workflow | 1 次 | 小文件、快速预览 |

| 场景 | 流水线 |
|:---|:---|
| 用户反馈分析 | Agent1→2→3→4→5 |
| 竞品分析 | Agent1→6→4→5 |

## 端口分配

| 端口 | 服务 | 协议 |
|:---|:---|:---|
| 8080 | HTTP 代理 + 静态文件 | HTTP/SSE |
| 8081 | MCP 工具服务 | streamable-http |
