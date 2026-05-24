# Prompt 修改记录

## 2026-05-22 — v1.0 初始版本

- **来源**: 从 Dify YML `txt用户评论文本分析 (1).yml` 中提取并拆分
- **拆分策略**: 将原 3000+ 字单一 System Prompt 按"五阶段"边界拆分为 5 段独立 Prompt
- **新增**: Agent 6 竞品分析 Prompt（独立编写，非来自 Dify YML）
- **变更**: 每条 Prompt 新增独立的输出 JSON Schema 约束
- **验证**: 待用测试数据验证拆分前后 JSON 输出一致性
- **各 Agent Prompt 概览**:

| Agent | 文件名 | 原对应阶段 | 核心输出字段数 |
|:---|:---|:---|:---|
| Preprocessor | preprocessor.md | 第一阶段：数据预处理与基线建立 | 4 |
| SubjectivityFilter | subjectivity.md | 第二阶段：主观性过滤与分流 | 7 |
| FiveDimExtractor | extractor.md | 第三阶段：核心五维特征抽取 | 7 |
| CrossValidator | validator.md | 第四阶段：交叉验证与异常识别 | 3 |
| BusinessAnalyzer | business.md | 第五阶段：业务分发视角 | 3 |
| CompetitorAnalyzer | competitor.md | 第二场景（新增） | 4 |

## 待记录
- v1.0 实测效果
- 各 Agent temperature 调优过程
- 竞品分析场景实测结果
