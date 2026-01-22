# 前端变更日志 - 修复收藏夹更新接口调用

**时间**: 2026年01月22日 17:26
**变更目标**: 
1. 修复收藏夹重命名功能报错 "Field required" (loc: query, new_name)。
2. 确保前端 `collectionService` 与后端接口规范一致。

**变更范围**:
- **Services (`src/services/`)**:
    - `collection.service.ts`: 修改 `update` 方法，将 `new_name` 从 Request Body 移至 Query Params。

**变更详情**:
- **Before**: `request.patch('/collections/${id}', { new_name: name })`
- **After**: `request.patch('/collections/${id}', null, { params: { new_name: name } })`
- **原因**: 后端 `update_collection` 接口定义中 `new_name` 为独立字符串参数，FastAPI 默认将其解析为 Query 参数，而非 Body 字段。

**验证方式与结果**:
1. **代码审计**: 确认后端 `controller/api/collections/router.py` 中 `update_collection` 签名为 `async def update_collection(..., new_name: str, ...)`，且无 `Body` 装饰器，证实其为 Query 参数。
2. **逻辑检查**: 前端请求现已通过 `axios` 的 `params` 选项传递 `new_name`，符合 Query String 格式。

**提交人**: FrontendAgent(react)
