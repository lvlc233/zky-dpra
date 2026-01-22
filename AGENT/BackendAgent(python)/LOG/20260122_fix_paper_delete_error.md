# 修复论文删除时的外键约束错误

**时间**: 2026年01月22日 21:24
**目标**: 解决删除论文时因外键约束 (`ForeignKeyViolationError`) 导致的 `collection_papers` 等关联数据无法自动删除的问题。

**变更范围**:
1. `src/base/pg/service.py`:
   - 修改 `PaperRepository.delete_paper` 方法。
   - 在删除 Paper 实体前，手动清理以下关联表数据：
     - `CollectionPaper` (收藏夹关联)
     - `PaperChunk` (向量切片)
     - `PaperSummary` (摘要)
     - `Annotation` (标注)
     - `Note` (笔记)
     - `MindMap` (思维导图)
   - 将以下弱关联实体的 `paper_id` 置为 NULL (保留记录)：
     - `AgentSession` (对话会话)
     - `Job` (异步任务)

**验证方式**:
- 逻辑验证：代码中显式添加了对所有已知关联表的清理/更新操作，并在同一个事务中执行，确保原子性。
- 数据库一致性：确保删除操作不会留下悬挂的外键引用。

**结果**:
- 修复了 `delete_paper` 的实现，使其能够正确处理级联删除逻辑，避免数据库抛出完整性错误。
