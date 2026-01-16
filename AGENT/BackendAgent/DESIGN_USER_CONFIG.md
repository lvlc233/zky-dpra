# 用户可配置项设计方案

## 项目信息
- **设计者**: BackendAgent
- **设计时间**: 2026-01-14 18:30:00
- **关联任务**: T-145, T-146, T-147
- **版本**: v1.0

## 设计目标
1. 提供灵活的用户配置管理系统
2. 支持多层级配置（系统/用户/会话）
3. 实现配置的热更新和版本管理
4. 与LangGraphAgent深度集成
5. 提供友好的API接口

## 核心设计原则
1. **分层配置**: 系统默认 → 用户偏好 → 会话临时
2. **类型安全**: 强类型定义，运行时验证
3. **事件驱动**: 配置变更通过事件通知
4. **版本控制**: 支持配置的版本管理和回滚
5. **缓存友好**: Redis缓存提升性能

## 详细设计

### 1. 配置项分类

#### 1.1 系统级配置
- **LLM模型配置**
  - 默认模型选择（gpt-4, gpt-3.5-turbo, claude）
  - 模型参数（temperature: 0.7, max_tokens: 4000）
  - API密钥管理
  - base_url: 供应商的API基础URL
- **搜索服务配置**
  - 搜索引擎权重（Google Scholar: 0.4, ArXiv: 0.3, PubMed: 0.3）
  - 搜索结果数量限制（默认50）
  - 搜索超时时间（默认30s）

#### 1.2 用户级配置
- **界面偏好**
  - 主题模式（light/dark/auto）
  - 语言设置（zh/en）
  - 字体大小（14px-20px）

- **阅读偏好**
  - PDF阅读器模式（single/dual/scroll）
  - 默认缩放（fit_width/fit_page/100%）

- **Agent行为配置**
  - 搜索深度（1-5级）
  - 摘要长度（short/medium/long）
  - 对话风格（formal/concise/detailed）

#### 1.3 Agent专属配置
- **SearchAgent**
  - 混合搜索权重（dense: 0.4, sparse: 0.3, bm25: 0.3）
  - 相关性阈值（0.7）
  - 最大返回结果（20）

- **SummaryAgent**
  - 摘要长度范围（100-500字）
  - 关键信息提取规则（方法/结果/结论）

- **DeepResearchAgent**
  - 最大迭代次数（5）
  - 研究深度级别（1-3）

### 2. 数据库设计

#### 2.1 表结构
```sql
-- 配置分类表
CREATE TABLE config_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 配置项定义表
CREATE TABLE config_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID REFERENCES config_categories(id),
    key VARCHAR(200) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    value_type VARCHAR(50) NOT NULL,
    default_value JSONB,
    validation_rules JSONB,
    options JSONB,
    scope VARCHAR(50) NOT NULL,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(category_id, key)
);

-- 用户配置值表
CREATE TABLE user_config_values (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    config_id UUID REFERENCES config_definitions(id),
    value JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, config_id)
);
```

#### 2.2 索引设计
- `idx_config_definitions_scope` - 按作用域查询
- `idx_config_definitions_public` - 公开配置查询
- `idx_user_config_values_user` - 用户配置查询
- `idx_user_config_values_updated` - 配置更新查询

### 3. API设计

#### 3.1 获取用户配置
```http
GET /api/v1/users/settings
```

响应示例：
```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "theme": "dark",
    "language": "zh",
    "pdf_reader": {
      "mode": "scroll",
      "zoom": "fit_width"
    },
    "search": {
      "depth": 3,
      "max_results": 50
    }
  }
}
```

#### 3.2 更新配置
```http
PUT /api/v1/users/settings/{key}
```

请求体：
```json
{
  "value": "dark"
}
```

#### 3.3 批量更新
```http
PUT /api/v1/users/settings/batch
```

请求体：
```json
{
  "theme": "dark",
  "language": "en",
  "search.depth": 5
}
```

#### 3.4 获取Agent配置
```http
GET /api/v1/agents/{agent_name}/config
```

### 4. 与LangGraph集成

#### 4.1 配置提供者
```python
class ConfigProvider:
    """为Agent提供配置数据"""

    async def get_agent_config(self, user_id: str, agent_name: str) -> Dict:
        """获取Agent专属配置"""
        config = await self.fetch_user_config(user_id, f"agent.{agent_name}")
        return config or self.get_default_agent_config(agent_name)
```

#### 4.2 Agent状态集成
```python
class BaseAgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    context: Dict[str, Any]
    config: Dict[str, Any]  # 运行时配置
    config_version: str  # 配置版本
```

#### 4.3 配置热更新
```python
async def handle_config_update(event: ConfigUpdatedEvent):
    """处理配置更新事件"""
    if event.scope == "user":
        # 更新相关用户的Agent配置
        await agent_manager.reload_user_config(event.user_id)
```

### 5. 缓存策略

#### 5.1 多级缓存
1. **内存缓存**: 热点配置（LRU）
2. **Redis缓存**: 用户配置（TTL: 1小时）
3. **数据库**: 持久化存储

#### 5.2 缓存失效
- 用户更新配置时，主动失效相关缓存
- 使用发布订阅通知其他服务节点
- 支持批量失效（用户维度）

### 6. 版本管理

#### 6.1 版本号规则
- 主版本.次版本.修订版本（如：1.2.3）
- 主版本：不兼容的API变更
- 次版本：向下兼容的功能新增
- 修订版本：向下兼容的问题修正

#### 6.2 迁移机制
```python
class ConfigMigration:
    """配置迁移管理"""

    async def migrate(self, user_id: str, from_version: str, to_version: str):
        """执行配置迁移"""
        migrations = self.get_migrations(from_version, to_version)

        for migration in migrations:
            await migration.apply(user_id)
```

### 7. 安全设计

#### 7.1 权限控制
- 系统配置：仅管理员可修改
- 用户配置：用户只能修改自己的配置
- 会话配置：仅当前会话有效

#### 7.2 数据验证
- 类型验证：确保值类型匹配
- 范围验证：数值在合理范围内
- 业务验证：符合业务规则

#### 7.3 敏感信息
- API密钥等敏感信息加密存储
- 支持密钥轮换机制
- 审计日志记录访问

### 8. 性能优化

#### 8.1 批量操作
- 支持批量获取/更新配置
- 减少数据库查询次数
- 使用pipeline优化Redis操作

#### 8.2 延迟加载
- 配置按需加载
- Agent启动时获取必要配置
- 支持配置预加载

#### 8.3 压缩存储
- JSON配置压缩存储
- 减少网络传输量
- 支持大配置分页加载

## 实施计划

### 阶段1：基础框架（2天）
1. 创建数据库表和模型
2. 实现配置服务基础功能
3. 添加缓存支持

### 阶段2：API实现（2天）
1. 实现RESTful API
2. 添加权限控制
3. 集成测试

### 阶段3：Agent集成（1天）
1. 实现配置提供者
2. 修改Agent读取配置
3. 测试配置热更新

### 阶段4：高级功能（2天）
1. 版本管理实现
2. 迁移机制
3. 性能优化

## 验收标准

1. ✅ 支持所有配置项的CRUD操作
2. ✅ 配置变更实时生效
3. ✅ 与Agent无缝集成
4. ✅ 支持版本管理和回滚
5. ✅ API响应时间 < 100ms
6. ✅ 100%单元测试覆盖率

## 风险评估

1. **性能风险**：大量配置读取可能影响性能
   - 缓解：多级缓存、批量操作

2. **兼容性风险**：配置结构变更影响Agent
   - 缓解：版本管理、渐进式迁移

3. **安全风险**：敏感配置泄露
   - 缓解：加密存储、权限控制、审计日志

## 后续优化

1. 支持配置模板和快速导入
2. 实现配置推荐系统
3. 添加配置使用统计
4. 支持A/B测试配置