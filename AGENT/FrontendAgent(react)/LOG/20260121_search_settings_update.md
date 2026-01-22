# 2026-01-21 搜索设置与主题适配更新

## 目标
完成搜索设置的前后端对齐，支持作者匹配、分页配置及明亮/暗黑模式切换。

## 变更范围
1.  **后端 (Backend)**:
    *   `src/controller/api/search/schema.py`: 在 `SearchRequest` 中添加 `match_author` 字段。
    *   确认 `settings_router.py` 提供 `/settings/search` 和 `/settings/system` 接口。

2.  **前端 (Frontend)**:
    *   `src/components/search/SearchFilters.tsx`: 添加"作者" (Author) 匹配开关，适配暗黑模式样式。
    *   `src/components/search/SearchSettings.tsx`: 实现分页 (`limit`)、日期范围 (`min_date`, `max_date`) 和分析状态 (`match_analysis_status`) 的配置 UI。
    *   `src/components/settings/SettingsModal.tsx`: 增加 `onSettingsChanged` 回调，适配暗黑模式。
    *   `src/services/settings.service.ts`: 修正搜索设置的 API 路径 (`GET/PUT /settings/search`) 并正确解包响应数据。
    *   `src/services/search.service.ts`: 更新 `SearchParams` 接口以支持 `match_author`。
    *   `src/app/dashboard/page.tsx`: 
        *   集成系统设置加载逻辑，应用暗黑模式。
        *   集成搜索设置加载逻辑。
        *   处理 `SettingsModal` 的变更回调以实时刷新设置。
        *   初始化搜索过滤器状态包含 `match_author`。
    *   `tailwind.config.ts`: 启用 `darkMode: 'class'`。

## 验证方式
1.  **搜索过滤器**: 在前端点击"作者"开关，确认发起搜索请求时 payload 包含 `match_author: true/false`。
2.  **搜索设置**: 在设置弹窗中修改每页数量或日期范围，保存后重新打开，确认数值已持久化（需后端支持）。
3.  **暗黑模式**: 在系统设置中切换"深色模式"，确认页面背景和组件颜色即时反转。
4.  **分页**: 修改设置中的 limit，确认搜索请求的 `page_size` (limit) 参数随之改变。

## 结果
所有功能均已按照文档要求实现并对齐。
