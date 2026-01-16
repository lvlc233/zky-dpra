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
    user_id UUID REFERENCES users(id),
    config_id UUID REFERENCES config_definitions(id),
    value JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, config_id)
);
```

### 3. API接口定义

#### 3.1 获取配置
- `GET /api/v1/users/settings`: 获取当前用户所有配置（合并后）
- `GET /api/v1/users/settings/{key}`: 获取单个配置

#### 3.2 更新配置
- `PUT /api/v1/users/settings/{key}`: 更新单个配置
- `PUT /api/v1/users/settings/batch`: 批量更新配置

#### 3.3 管理员接口
- `POST /api/v1/users/settings/init-defaults`: 初始化系统默认配置
- `GET /api/v1/admin/configs`: 管理所有配置定义
