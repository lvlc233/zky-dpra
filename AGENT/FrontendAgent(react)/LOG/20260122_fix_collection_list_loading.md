# 前端列表加载修复日志

## 变更时间
2026-01-22

## 变更目标
修复上传论文后，收藏夹列表不显示论文数据的问题。

## 问题分析
*   **现象**: 用户上传论文成功，且后端日志显示获取收藏夹详情接口返回 200，但前端列表为空。
*   **原因**: 前后端数据结构不匹配。
    *   **后端**: `GET /api/v1/collections/{id}` 返回的数据结构为 `{ items: [...] }` (由 `CollectionDetailDTO` 定义)。
    *   **前端**: `dashboard/page.tsx` 中的 `loadCollectionPapers` 函数错误地尝试访问 `detail.papers` 属性，导致获取到 `undefined` 并回退为空数组。

## 变更内容

### 前端 (Frontend)
1.  **types/api.d.ts**:
    *   新增接口 `CollectionDetailResponse`，定义为 `{ items: Paper[] }`，以匹配后端返回结构。

2.  **services/collection.service.ts**:
    *   更新 `getById` 方法的返回类型为 `Promise<CollectionDetailResponse>`。

3.  **app/dashboard/page.tsx**:
    *   修改 `loadCollectionPapers` 函数，将取值逻辑从 `(detail as any)?.papers` 修正为 `detail.items`。
    *   移除了不安全的 `any` 类型断言，利用更新后的 TypeScript 类型定义提供更好的类型安全。

## 验证结果
*   **代码审查**: 确认前端取值逻辑与后端返回结构一致。
*   **预期效果**: 刷新页面或切换收藏夹时，前端能正确读取 `items` 数组并渲染论文列表。
