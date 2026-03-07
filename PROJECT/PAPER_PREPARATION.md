# 深度论文研究助手 (DeepPaperResearcher) - 论文素材整理

**日期**: 2026-03-06
**整理者**: Administrator Agent

## 1. 标题与摘要 (Title & Abstract)

**建议标题**: 
- 基于多智能体协同与混合检索的深度论文研究辅助系统
- DeepPaperResearcher: An Agentic System for Deep Paper Reading and Knowledge Graph Generation

**摘要要点**:
- **背景**: 科研人员面临海量论文阅读压力，传统工具缺乏深度理解和知识关联能力。
- **方法**: 提出一种基于 LangGraph 的多智能体协作系统。
    - **混合检索 (Hybrid Retrieval)**: 结合 pgvector 语义检索与关键词检索，通过 RRF 算法优化召回。
    - **多模态解析**: 集成 Marker 和 PyMuPDF，实现高质量 PDF 文本与元数据提取。
    - **智能体编排**: 设计专门的 SummaryAgent, MindMapAgent 和 ReAct 模式的 PaperChatAgent，分别负责摘要生成、结构化脑图构建和深度问答。
- **结果**: 系统能够自动生成论文思维导图、多维度摘要，并提供基于上下文的精准问答，显著提升阅读效率。
- **关键词**: Large Language Models, Multi-Agent Systems, LangGraph, RAG, Knowledge Graph

## 2. 引言 (Introduction)

*   **痛点分析**: 
    *   论文数量爆炸，筛选困难。
    *   PDF 格式非结构化，难以机器理解。
    *   传统 RAG (Retrieval-Augmented Generation) 在长文档理解和跨段落推理上存在局限。
*   **本文贡献**:
    *   设计了基于任务链 (Job Pipeline) 的异步处理架构，解耦解析、向量化和生成任务。
    *   实现了基于 LangGraph 的可控 Agent 工作流，支持动态模型选择和工具调用。
    *   提出了一种轻量级的知识可视化方案，利用 LLM 生成结构化图数据并在前端交互式渲染。

## 3. 系统架构 (System Architecture)

### 3.1 总体架构
采用前后端分离架构，基于容器化部署。

*   **前端**: Next.js 14 (App Router), TypeScript, TailwindCSS。
    *   核心组件: PDFViewer (React PDF), GraphViz (Reagraph), ChatInterface (Vercel AI SDK)。
*   **后端**: FastAPI, Python 3.12+。
    *   **数据层**: PostgreSQL (存储元数据、全文、向量、JSON 脑图), Redis (缓存、任务队列)。
    *   **服务层**: PaperService (上传/解析), RetrievalService (检索), AgentService (状态管理)。
    *   **异步任务**: Arq + Redis，处理 PDF 解析、Embedding 生成、LLM 推理等耗时任务。

### 3.2 智能体设计 (Agent Design)
基于 LangGraph 框架，设计了三种专用 Agent：

1.  **SummaryAgent**:
    *   **输入**: 论文全文。
    *   **流程**: 单节点图，调用 LLM 生成结构化摘要（背景、方法、结果等）。
    *   **输出**: 存储于 `PaperSummary` 表。

2.  **MindMapAgent**:
    *   **输入**: 论文全文。
    *   **流程**: 单节点图，Prompt 引导 LLM 输出特定的 JSON 图结构 (Nodes, Edges)。
    *   **输出**: 存储于 `MindMap` 实体，前端通过 WebGL 渲染。

3.  **PaperChatAgent (InPaperChatAgent)**:
    *   **模式**: ReAct (Reasoning + Acting)。
    *   **状态**: `InPaperChatState` (messages, context)。
    *   **工具**: `retrieve_paper_tool`。
    *   **流程**: 
        *   Agent 节点分析用户意图。
        *   决定是否调用检索工具。
        *   Tools 节点执行检索。
        *   Agent 节点根据检索结果生成回答。
    *   **动态性**: 支持根据用户设置动态加载不同的 LLM 后端 (OpenAI, DeepSeek 等)。

## 4. 关键技术 (Key Technologies)

### 4.1 高质量 PDF 解析
*   **双引擎策略**:
    *   **PyMuPDF (fitz)**: 用于快速提取元数据 (标题、作者) 和预览。
    *   **Marker**: 用于高质量全文提取，支持公式、表格转 Markdown，解决传统 OCR 丢失结构信息的问题。
*   **异步处理**: 解析任务封装为 `parse_text` Job，通过 Redis 队列异步执行，并通过 SSE (Server-Sent Events) 实时推送进度到前端。

### 4.2 混合检索增强 (Hybrid RAG)
*   **向量检索**: 使用 `OpenAIEmbeddings` (或自定义模型) 将文本块向量化，存储于 pgvector 列。使用 Cosine Distance 进行相似度计算。
*   **关键词检索**: 补充语义检索的不足，处理专有名词。
*   **RRF 融合**: 
    $$ Score = \frac{1}{k + rank_{semantic}} + \frac{1}{k + rank_{keyword}} $$
    通过倒数排名融合算法合并两路检索结果，提高 Top-K 准确率。

### 4.3 动态配置与任务调度
*   **任务链**: `parse_text` -> `vectorize` -> `summary` & `mind_map`。支持任务依赖和断点恢复。
*   **用户级配置**: 允许用户为不同 Agent (Chat, Summary) 配置不同的模型参数 (API Key, Base URL)，实现成本与性能的平衡。

## 5. 系统实现与验证 (Implementation & Verification)

### 5.1 数据库设计
*   **Paper**: 存储核心元数据、全文、解析状态。
*   **PaperChunk**: 存储切分后的文本块和 Embedding 向量。
*   **Job**: 统一的任务状态管理 (Queued, Running, Succeeded, Failed)，支持进度追踪。
*   **MindMap**: 存储图结构的 JSON 数据。

### 5.2 交互设计
*   **分屏阅读**: 左侧 PDF 原文，右侧 Chat/Notes/Graph 多标签页切换。
*   **沉浸式翻译**: 点击段落即时翻译（计划中）。
*   **引用跳转**: 识别文中引用，点击跳转到参考文献或对应段落。

## 6. 总结与展望 (Conclusion & Future Work)
*   **当前限制**: 
    *   Neo4j 目前仅作为基础设施引入，尚未深度应用于多跳推理。
    *   长文档的上下文窗口限制仍需优化 (如使用 LongContext 模型或滑动窗口)。
*   **未来工作**:
    *   真正集成 Neo4j，构建跨论文的全局知识图谱。
    *   引入多模态模型 (VLM) 理解论文中的图表信息。
    *   支持本地 LLM (如 Ollama) 的一键接入。

