# 2026-01-25 阅读模块笔记与标注功能完善

## 基本信息
- **时间**: 2026年01月25日 01:28
- **责任人**: BackendAgent(python)
- **目标**: 完成阅读模块(Reader)的笔记(Note)和标注(Annotation)功能的后端开发与修复，确保前后端接口一致且功能完整。

## 变更范围

### 1. 数据库实体 (Entity)
- **路径**: `src/base/pg/entity.py`
- **变更**:
    - `Annotation` 模型: 
        - 将主键 `annotation_id` 重命名为 `id`，保持命名规范统一。
        - 将 `rect` 字段重命名为 `rects` 并修改类型为 `List[Dict]`，适配前端多区域标注需求。
    - `Note` 模型: 
        - 确保主键为 `id`。

### 2. 数据访问层 (Repository)
- **路径**: `src/base/pg/service.py`
- **变更**:
    - `ReaderRepository`:
        - 补充 `get_notes_by_paper`, `get_note_detail`, `get_note_by_id` 等缺失方法。
        - 补充 `create_annotation`, `get_annotation_by_id`, `update_annotation`, `delete_annotation` 方法。
        - 修复 `create_annotation` 中的事务提交与刷新逻辑。

### 3. 服务层 (Service)
- **路径**: `src/service/reader/note_service.py`
- **变更**:
    - 完善 `NoteService` 的 CRUD 逻辑，确保正确调用 Repository。
    - 增加 `get_notes_meta` 方法用于列表展示。

- **路径**: `src/service/reader/reader_service.py`
- **变更**:
    - 修复 `get_annotations` 中 `rects` 字段的解析逻辑。
    - 适配 `Annotation` 实体字段变更。
    - **修复**: 适配 `AnnotationRequest` 字段变更，使用 `rects` 替代 `rect`。

### 4. 接口层 (Controller)
- **路径**: `src/controller/api/reader/router.py`
- **变更**:
    - 新增笔记相关接口:
        - `GET /{paper_id}/notes`
        - `GET /{paper_id}/notes/{note_id}`
        - `POST /{paper_id}/notes`
        - `PUT /{paper_id}/notes/{note_id}`
        - `DELETE /{paper_id}/notes/{note_id}`
    - 修复 `Annotation` 相关接口调用逻辑。
    - 补充缺失的 `HTTPException` 引用。

### 5. 数据校验 (Schema)
- **路径**: `src/service/reader/schema.py` & `src/controller/api/reader/schema.py`
- **变更**:
    - 更新 `Annotation` Schema，字段 `id` 对应后端实体 `id`。
    - 更新 `NoteResponse` Schema，字段 `id` 对应后端实体 `id`。
    - **修复**: 更新 `AnnotationRequest` Schema，将 `rect` 字段重命名为 `rects`，适配前端请求。

## 验证方式与结果

### 验证脚本
- 创建了自动化验证脚本 `tests/verify_reader_features.py`。
- 覆盖场景:
    1. 创建用户与论文。
    2. 笔记(Note)的增删改查。
    3. 标注(Annotation)的增删改查。

### 验证结果
- **状态**: 通过 (Passed)
- **日志摘要**:
    ```
    Starting verification...
    Created User: ...
    Created Paper: ...
    Created Note: ...
    Note Service Verified!
    Added Annotation
    Annotation Service Verified!
    Cleaning up...
    ```
- 所有 CRUD 操作均按预期执行，无报错。

## 后续建议
- 前端需确认调用接口时使用的主键字段名为 `id` (在 DTO 中已通过 alias 适配，前端可见为 `id` 或 `note_id`/`annotation_id` 取决于 Schema 定义，目前 Schema 中 output alias 为 `id`)。
