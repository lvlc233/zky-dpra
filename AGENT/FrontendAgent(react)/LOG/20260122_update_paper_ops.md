# 2026-01-22 21:13 前端变更记录

## 变更目标
1. 完善论文列表的操作列功能（删除、移动）。
2. 修复并美化侧边栏收藏夹的论文数量显示。

## 变更范围
1. `src/services/paper.service.ts`: 新增 `delete` 接口。
2. `src/components/search/SearchResults.tsx`: 
    - 操作列移除“查看详情”和“收藏”按钮。
    - 新增“移动到收藏夹”下拉菜单（支持展示收藏夹列表及数量）。
    - 新增“删除论文”按钮。
    - 接入 `onPaperUpdate` 回调以刷新父组件状态。
3. `src/app/dashboard/page.tsx`:
    - 向 `SearchResults` 传递 `collections` 数据。
    - 实现 `handlePaperUpdate` 逻辑，同时刷新论文列表和收藏夹统计信息。
4. `src/components/layout/Sidebar.tsx`:
    - 优化收藏夹论文数量的显示样式（Badge风格）。

## 验证方式与结果
- 代码逻辑验证：
    - 删除/移动操作成功后调用 `loadCollections` 和列表刷新函数，确保 UI 状态（包括左侧数量）即时更新。
    - 移动操作下拉菜单过滤展示所有可用收藏夹。
    - 侧边栏数量显示增加背景色和圆角，视觉更清晰。
