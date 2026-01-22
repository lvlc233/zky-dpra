# 前端与后端逻辑修复日志

## 变更时间
2026-01-22

## 变更目标
1. 移除前端“全部论文”视图，严格遵循“论文必归属于收藏夹”的业务逻辑。
2. 修复后端 `CollectionRepository` 中的字段引用错误。
3. 确保论文上传和删除时的收藏夹关联逻辑正确。

## 变更内容

### 前端 (Frontend)
1.  **Sidebar.tsx**:
    *   移除了之前添加的“全部论文”按钮。
2.  **dashboard/page.tsx**:
    *   修改初始化逻辑：页面加载时不再调用 `loadRecentPapers()`（该方法用于获取所有论文列表）。
    *   新增自动选择逻辑：若当前未选中任何收藏夹，自动查找并选中“默认收藏夹”。
    *   修改 `onSelectCollection` 回调：当收藏夹被取消选中或删除时，不再回退到“全部论文”，而是尝试切换回“默认收藏夹”。
    *   修改 `handleUploadSuccess`：上传成功后，刷新收藏夹列表并保持在当前收藏夹或切换至默认收藏夹。

### 后端 (Backend)
1.  **base/pg/service.py**:
    *   修复 `remove_paper_from_user_collections` 方法中的 Bug。
    *   将错误的 `Collection.id` 修改为正确的 `Collection.collection_id`。
    *   此修复解决了删除论文时可能因字段名错误导致的异常。

## 验证结果
*   **前端**：进入首页默认显示“默认收藏夹”内容；删除/移动操作后状态同步正常；无“全部论文”入口。
*   **后端**：代码审查确认 `upload_paper` 包含默认收藏夹创建逻辑；`delete_paper` 依赖的 `remove_paper_from_user_collections` 已修复字段引用。
