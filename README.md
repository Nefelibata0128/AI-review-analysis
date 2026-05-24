# AI评论分析平台 v3.0

AI 驱动的用户反馈分析工具——上传评论 + 产品文档 → 多 Agent 协作分析 → 自动生成深度洞察仪表盘。

![架构图](docs/architecture.md)

## 项目亮点

- **多 Agent 协作**：6 个专用 Agent 串行分析，每个负责一个分析阶段
- **MCP 协议集成**：8 个 MCP 工具可被 Agent 分步调用或外部 AI 一键使用
- **SSE 实时反馈**：分析进度 5 步可视化，每步状态、耗时清晰可见
- **双场景覆盖**：用户反馈分析 + 竞品分析，Agent 高度复用
- **双模式回退**：深度多 Agent 模式 + 快速 Dify 单工作流模式
- **零框架依赖**：Agent 编排不使用 LangChain/CrewAI，纯 Python 实现

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY 和 DIFY_API_KEY

# 3. 启动主服务
python proxy-server.py
# 访问 http://localhost:8080

# 4. （可选）启动 MCP 工具服务
python mcp_server.py
# 运行在 http://localhost:8081
```

## 技术栈

| 层级 | 技术 |
|:---|:---|
| **前端** | HTML5 + CSS3 + Vanilla JS, Chart.js, marked.js |
| **后端** | Python 3.12, http.server (标准库) |
| **LLM** | DeepSeek API (OpenAI 兼容) |
| **Agent 编排** | 自研 Orchestrator，6 Agent 串行流水线 |
| **MCP** | FastMCP, streamable-http |
| **通知** | 飞书 Webhook |
| **部署** | Railway / Docker |

## 系统架构

```
用户浏览器 (localhost:8080)
    │
    │ POST /api/orch/run (双文件上传)
    │ GET  /api/orch/events (SSE 进度流)
    ▼
proxy-server.py :8080 ─────────────────────────
    │                   │                   │
    │ 文件上传          │ Agent 调用         │ SSE 事件
    ▼                   ▼                   ▼
Dify API          orchestrator.py      前端时间线
(快速模式回退)       │                  实时更新
                    │
                    ├─ Agent1 数据预处理 (t=0.3)
                    ├─ Agent2 主观性过滤 (t=0.5)
                    ├─ Agent3 五维特征抽取 (t=0.5)
                    ├─ Agent4 交叉验证 (t=0.3)
                    ├─ Agent5 业务分析 (t=0.5)
                    └─ Agent6 竞品分析 (t=0.5)
                    │
                    ▼
              DeepSeek API
```

## 项目结构

```
├── proxy-server.py          # HTTP 代理 + SSE 中继
├── orchestrator.py          # 多 Agent 编排引擎
├── mcp_server.py            # MCP 工具服务 (8 tools)
├── lark_notifier.py         # 飞书通知
├── report-dashboard.html    # 前端单文件 SPA
├── agents/
│   ├── __init__.py          # Agent 基类
│   ├── prompts.py           # 6 段 System Prompt
│   ├── preprocessor.py      # Agent 1
│   ├── subjectivity.py      # Agent 2
│   ├── extractor.py         # Agent 3
│   ├── validator.py         # Agent 4
│   ├── business.py          # Agent 5
│   └── competitor.py        # Agent 6
├── prompts/v1/              # Prompt 版本管理
├── deploy/                  # Docker + Railway
├── docs/                    # 文档 + 原型
└── tests/                   # 测试
```

## Benchmark

| 任务 | 人工 | AI | 提升 |
|:---|:---|:---|:---|
| 70 条评论完整分析 | ~125 分钟 | ~58 秒 | **130x** |
| 分析成本 | ~200 元 | ~0.03 元 | **6700x** |

详见 [完整 Benchmark](docs/benchmarks.md)

## License

MIT
