# 修复运行时错误与功能完善

**时间**: 2026年01月22日 21:20
**目标**: 解决用户反馈的 `handlePaperUpdate is not defined` 和 `Popover is not defined` 错误，确保论文列表操作功能正常。

**变更范围**:
1. `src/app/dashboard/page.tsx`:
   - 补充 `handlePaperUpdate` 函数定义，用于操作后刷新列表。
   - 修正 `handleToggleBookmark` 中错误的 ID 引用 (`p.id` -> `p.paper_id`)。
   - 统一 `Collection` 数据结构，映射 backend `collection_id` 到 frontend `id`。
2. `src/components/search/SearchResults.tsx`:
   - 引入 `@radix-ui/react-popover` 解决未定义错误。
   - 实现 `handleMove` 和 `handleDelete` 操作逻辑。
   - 补充缺失的 Service 引用 (`collectionService`, `paperService`)。
3. `src/types/models.d.ts`:
   - 为 `Paper` 接口添加 `is_bookmarked` 可选属性。

**验证方式**:
- 代码静态检查：确认引用和类型定义匹配。
- 逻辑检查：确认 `onPaperUpdate` 回调链条完整，从 `SearchResults` -> `Dashboard` -> `Service Call`。

**结果**:
- 错误已修复，相关功能逻辑已补全。
