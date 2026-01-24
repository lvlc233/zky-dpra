# 2026-01-25 Fix Annotation Delete Bug

## 目标
修复用户反馈的无法单独删除标注的问题。
现象：删除时请求 `/annotations/undefined` 报错 422。
原因：前端从后端加载标注数据时，未将后端的 `id` 字段映射为前端使用的 `annotation_id`，导致 `annotation_id` 为 `undefined`。

## 变更范围
1. `src/app/reader/[id]/page.tsx`: 在初始化加载图层数据时，添加字段映射 `annotation_id: a.annotation_id || a.id`。
2. `src/services/reader.service.ts`: 在 `getLayers` 聚合方法中，同样添加字段映射。

## 验证方式
1. 刷新阅读器页面，加载已有标注。
2. 点击任意标注，确认弹出框正常显示（虽然之前可能也显示，但现在 ID 应该正确）。
3. 点击弹出框中的删除按钮。
4. 观察网络请求，确认 DELETE 请求 URL 中的 ID 为有效的 UUID，而非 `undefined`。
5. 确认标注从界面上消失。

## 结果
- 已修复 ID 映射逻辑。
- 解决了因 ID 缺失导致的删除失败问题。
