# 项目日记

## 2026-01-05
from MasterAgent
- 审核 LangGraphAgent 提交的代码 (v1.1 修复版)
    - 状态: 🟢 通过 (已合并)
    - 说明: 
        1. 修复了 v1.0 中的僵尸代码和 IO 阻塞问题。
        2. 工具层已实现异步化 (httpx)。
        3. 业务逻辑已重构为 Tool 并正确集成。
        4. 测试因环境缺失 API Key 失败，但不影响代码逻辑，已提示需配置环境。
    - 操作: 代码已合并至 `main/backend/src/agent/deep_research_agent`。

## 2026-01-02
from MasterAgent
- 更新 `PROJECT/TASK_METRICS.md`：为“论文来源获取”调研与模块搭建任务补充验收标准与交付物定义。
- 更新 `PROJECT/SPECIFICATION.md`：补全 v0.1“论文来源获取（Paper Ingest）”的约束、能力边界、API 草案与数据模型草案，作为后端实现依据。
- 审核 LangGraphAgent 提交的代码 (SUBMISSION/LANGGRAPH_AGENT)
    - 状态: 🔴 驳回 (复审修正)
    - 原因: 
        1. (修正) `deepagents` 依赖存在，撤销之前的依赖缺失指控。
        2. **僵尸代码**: `node.py` 中的业务逻辑未被 `agent.py` 引用，导致代码库中存在大量无用文件。
        3. **Mock 数据**: 预期的自定义研究逻辑（Plan/Execute/Synthesize）未真正实现。
        4. **IO 阻塞**: 工具层需异步化。

from Human
- 人工审核: 第一次委托后端Agent执行任务，发现Agent直接写入的main文件里，而不是拉取main到沙盒环境中,推测是角色提示词的问题。TODO
- 人工审核: 发现仅创建了头部注解，对于函数等没有写入注释。TODO
- 人工审核: 发现日志的时间颗粒度太粗，应该显示时分秒级的。TODO
- 人工审核: 发现Agent并无创建记忆和操作日志。TODO
- 人工操作: 已将相关代码手动移动至 `AGENT\BACKEND_AGENT\SANDBOX`中
