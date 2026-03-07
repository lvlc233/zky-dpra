# 2026年03月06日 12:42 [INFO] 项目审查与论文素材整理
- **操作者**: Administrator Agent
- **任务**: 阅读项目，整理论文素材
- **目标**:
    1.  全面理解项目架构、功能模块、技术选型。
    2.  分析后端 Agent 设计、PDF 处理、知识图谱构建等核心技术。
    3.  整理系统设计、实现细节、测试验证等内容，输出 `PROJECT/PAPER_PREPARATION.md`。
- **状态**: 已完成
- **产出**:
    - [PROJECT/PAPER_PREPARATION.md](PROJECT/PAPER_PREPARATION.md): 包含论文标题、摘要、引言、系统架构、关键技术、实现验证等完整素材。
- **关键发现**:
    - 项目采用 FastAPI + Next.js + LangGraph 架构。
    - 核心功能包括 PDF 解析 (Marker/PyMuPDF)、混合检索 (pgvector + Keyword)、多 Agent 协作 (Summary, MindMap, Chat)。
    - 知识图谱目前主要基于 LLM 生成结构化数据 (JSON) 渲染，Neo4j 尚未深度集成。
    - 异步任务链 (Arq) 处理耗时操作，通过 Redis 队列管理。

# 2026年03月07日 06:48 [FIX] 修复论文解析NULL字节错误
- **操作人**: {masterAgent}
- **变更内容**: 
  - 修改 `main/backend/src/service/papers/paper_service.py` 中的 `parse_text` 方法。
  - 增加 `_sanitize_text` 逻辑，去除 `text_content`、`title` 和 `abstract` 中的 NULL 字节 (`\x00`)。
- **原因**: 
  - 某些 PDF 解析出的文本包含 NULL 字节，导致 PostgreSQL 在执行 `UPDATE` 操作时抛出 `CharacterNotInRepertoireError`，进而导致目录和元数据无法保存。
- **结果**: 
  - 修复了因 NULL 字节导致的数据库写入失败问题，确保论文解析和目录提取流程正常执行。