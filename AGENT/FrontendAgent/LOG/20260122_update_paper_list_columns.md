# 变更记录

**时间**: 2026-01-22 21:05
**目标**: 调整论文列表列头及展示内容，使其与 `PaperMetaDTO` 定义一一对应。
**变更范围**:
- `main/frontend/src/components/search/SearchResults.tsx`: 重构表格列布局，从 3 列调整为 7 列（标题、作者、摘要、发布时间、来源、状态、操作），并完善数据展示逻辑。
- `main/frontend/src/types/models.d.ts`: 补充 `analysis_status` 字段定义。

**验证方式**:
1. 静态代码检查：确认 `SearchResults.tsx` 的列数（grid-cols-12）分配正确（3+2+3+1+1+1+1=12）。
2. 类型检查：确认 `Paper` 接口包含所需字段。

**结果**:
- 论文列表现在展示更详细的信息，且与后端 DTO 结构对齐。
