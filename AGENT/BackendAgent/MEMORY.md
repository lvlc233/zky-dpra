# BackendAgent 记忆文档

## 项目核心概念理解

### 项目整体目标
- DeepResearcher：基于 LangGraph 的 AI 辅助论文研究与管理平台
- 采用"3+1"层后端架构（Controller + Service + Infrastructure + Data）
- 通过严格的工作流（AGENT开发 → SUBMISSION提交 → 主项目合并）进行迭代

### BackendAgent 职责
- 负责后端业务逻辑的实现
- 专注于 Controller、Service、Infrastructure、Data 层的开发
- 严格遵守资源约束（仅在 AGENT/BackendAgent/ 目录下操作）
- 所有代码需经管理员审核后方可合并至主项目

## 当前任务理解

### 任务 v0.1 - 基础论文辅助功能模块
**目标**：实现基础论文集获取功能，支持通过输入 URL（如 arXiv）获取论文集用于搜索

**技术范围**：
- Controller: REST API 接口定义（接收 URL）
- Service: 论文获取业务逻辑（调用 arXiv API）
- Business Model: 论文数据模型定义（Pydantic）
- Infrastructure: 数据库 ORM 准备（如有需要）
- Testing: 单元测试编写

**关键约束**：
- 不使用模拟数据，未实现部分使用 TODO 标注
- 所有功能必须经过测试验证
- 时间戳使用中国上海时区（年月日 时分）
- 代码注释使用中文
- 严格遵循版本头格式

## 技术栈认知

### 后端核心依赖
- FastAPI: Web 框架（自动生成 Swagger）
- SQLModel: ORM（基于 Pydantic）
- PostgreSQL: 主数据库
- Redis: 缓存与会话管理
- PyJWT: 身份验证
- uv: 依赖管理 + 虚拟环境

### 开发工具链
- Ruff: 代码检查与格式化
- pytest: 单元测试框架
- Git: 版本控制（工作流支持）

## 开发模式记忆

### 代码文件模板
```python
'''
开发者: BackendAgent
当前版本: {unique_version}
创建时间: YYYY年MM月DD日 HH:MM
更新时间: YYYY年MM月DD日 HH:MM
更新记录:
    [YYYY年MM月DD日 HH:MM:version:brief_description]
'''
```

### 分层架构规则
- **Controller**: 仅 HTTP 路由 + 请求/响应模型 + 认证鉴权
- **Service**: 仅业务逻辑 + 调用 Infrastructure
- **Infrastructure**: 仅数据库操作封装
- **Data**: 仅 Pydantic 模型定义，无业务逻辑

### 工作流记忆
1. 从主项目按需拉取代码至 SANDBOX
2. 在 SANDBOX 中独立开发
3. 完成后提交至 SUBMISSION/BackendAgent/
4. 等待管理员审核与合并
5. 绝不直接修改主项目代码

## 关键经验与教训

### 需要重点关注
- 严格遵守资源约束（PROJECT 目录只读）
- 每次操作后立即更新 OPERATION_LOG
- 使用 get_current_time 工具获取准确时间
- 禁止提交任何假数据

### 常见陷阱避免
- 不要直接访问数据库（Controller 层）
- 不要在 Data 层添加业务逻辑
- 不要忽略异常处理
- 不要跳过测试验证

---

## v0.1任务的经验总结（2026年01月02日 10:45）

### 代码审核结果回顾

**初次审核评分**: 58/100（建议驳回）
**修复后评分**: 85/100（通过）

**主要问题清单**:
1. 架构违规 - Service层直接调用HTTP API，跳过了Infrastructure层
2. 模型位置错误 - 请求模型错误地放在了business_model中
3. 安全漏洞 - 异常信息直接返回给客户端
4. 依赖注入缺失 - 全局实例化服务
5. 版本号混乱 - 不同文件使用不同版本
6. 测试代码问题 - 使用sys.path硬编码路径

### 关键修复措施

**架构重构**:
- 创建Infrastructure层：`base/arxiv/client.py`和`parser.py`
- 重构Service层：仅调用Infrastructure层，不直接接触外部服务
- 修复Controller层：添加依赖注入，修复安全问题

**模型迁移**:
- 将请求模型从`business_model`移动到`controller/api/papers/requests.py`
- 明确分层：Request模型属于Controller层，Response/Business模型属于Data层

**安全加固**:
- 异常处理统一返回通用消息："服务器内部错误，请联系管理员"
- 详细错误信息记录到日志，不暴露给客户端
- 防止系统路径、数据库信息等敏感数据泄露

### 核心教训总结

**关于架构设计**:
1. 必须严格遵守"3+1"层架构（Controller→Service→Infrastructure→Data）
2. Service层不能直接调用HTTP或访问外部服务，必须通过Infrastructure层
3. Infrastructure层职责：处理所有外部通信和数据格式转换
4. 依赖注入是必须的，不能全局实例化服务类

**关于安全规范**:
1. 绝不能将异常详情返回给客户端（500错误）
2. 应该返回通用错误消息，详细错误应记录在日志中
3. 防止信息泄露：系统路径、数据库连接信息、API密钥等
4. 所有外部输入必须验证和清理

**关于模型分层**:
1. 请求模型（Request）属于Controller层
2. 响应模型（Response）和业务模型（Business）属于Data层
3. 不能混淆两层职责，每层有明确的边界

**关于测试规范**:
1. 不要使用sys.path.append()，应该使用pytest标准导入
2. 导入路径必须完整（如from src.controller...）
3. 注意语法细节：所有字符串必须有闭合引号
4. 测试覆盖率要达到关键路径

**关于版本管理**:
1. 同一功能模块的所有文件应使用统一版本号
2. 版本格式：v{version}_{feature}（如v0.1_papers）
3. 便于跨模块追踪和管理变更

### 合并结果

代码已通过审核并合并到main/backend/，包含：
- Infrastructure层：arXiv客户端和解析器
- Service层：论文获取业务逻辑
- Controller层：REST API接口
- Data层：数据模型定义
- 测试层：单元测试用例

### 后续改进建议

1. **测试增强**: 添加边界测试用例和异常场景测试
2. **功能完善**: 实现TODO功能（缓存、速率限制等）
3. **集成测试**: 添加真实API调用的集成测试
4. **性能优化**: 添加性能测试和监控
5. **文档完善**: 编写架构决策记录（ADR）

---
**最后更新**: 2026年01月02日 10:45
**记忆版本**: v1.1
