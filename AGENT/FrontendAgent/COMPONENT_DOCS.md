# 前端组件文档 (Component Documentation)

**负责人**: FrontendAgent  
**最后更新**: 2026-01-11  
**描述**: 本文档记录项目中核心组件的 API、使用方法及设计细节。

---

## 1. 布局组件 (Layout)

### 1.1 Navbar
**路径**: `src/components/layout/Navbar.tsx`

**描述**: 
应用的顶部导航栏。采用现代化 Glassmorphism（毛玻璃）设计风格。包含 Logo、居中的导航菜单以及右侧的登录/用户信息区域。

**Props**:
| 属性名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `className` | `string` | `undefined` | 可选的额外 CSS 类名，用于合并样式 |

**依赖**:
- `lucide-react`: 用于图标 (BookOpen, Search, Upload, etc.)
- `AuthModalContext`: 用于触发全局登录弹窗

**代码示例**:
```tsx
import { Navbar } from '@/components/layout/Navbar';

export default function Layout({ children }) {
  return (
    <div className="min-h-screen">
      <Navbar className="fixed top-0" />
      <main>{children}</main>
    </div>
  );
}
```

### 1.2 Sidebar
**路径**: `src/components/layout/Sidebar.tsx`

**描述**:
应用的侧边导航栏。支持折叠/展开，管理收藏夹列表。

**功能**:
- **折叠/展开**: 点击分隔线上的箭头按钮切换状态。
- **全局搜索**: 点击顶部的 "搜索论文" 按钮，重置当前视图为全局搜索模式（取消选中任何收藏夹）。
- **收藏夹管理**:
    - **新建**: 点击 "+" 号，出现带文件夹图标的输入框，输入名称回车即可创建。
    - **切换**: 点击列表项高亮选中，并触发 `onSelectCollection` 回调。
    - **重命名**: 悬浮列表项显示菜单，点击 "重命名" 进入编辑模式，失焦或回车保存。
    - **删除**: 悬浮列表项显示菜单，点击删除确认移除。
- **设置入口**: 底部固定设置按钮，触发用户级全局配置。

**Props**:
| 属性名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `className` | `string` | `undefined` | 样式类名 |
| `onSettingsClick` | `() => void` | `undefined` | 点击设置按钮的回调 |
| `onSelectCollection` | `(col: Collection \| null) => void` | `undefined` | 选中收藏夹的回调，传入 null 表示重置/全局搜索 |

---

## 2. 认证模块 (Authentication)

认证模块采用 **全局弹窗 (Modal)** 模式，由 Context 控制状态，组件负责展示。

### 2.1 AuthModalContext
**路径**: `src/components/auth/AuthModalContext.tsx`

**描述**: 
管理全局认证弹窗的状态（开启/关闭）以及当前视图（登录/注册/找回密码）。

**API (useAuthModal)**:
| 方法/属性 | 类型 | 说明 |
| :--- | :--- | :--- |
| `isOpen` | `boolean` | 弹窗是否打开 |
| `view` | `'login' \| 'register' \| 'forgot-password'` | 当前展示的表单视图 |
| `openAuthModal` | `(view?: AuthView) => void` | 打开弹窗，可指定初始视图（默认 login） |
| `closeAuthModal` | `() => void` | 关闭弹窗 |
| `setAuthView` | `(view: AuthView) => void` | 切换当前视图 |

**使用示例**:
```tsx
'use client';
import { useAuthModal } from '@/components/auth/AuthModalContext';

export function LoginButton() {
  const { openAuthModal } = useAuthModal();
  return <button onClick={() => openAuthModal('login')}>登录</button>;
}
```

### 2.2 AuthModal
**路径**: `src/components/auth/AuthModal.tsx`

**描述**: 
认证弹窗的容器组件。监听 Context 状态，使用 `Dialog` 组件包裹具体的表单（Login/Register/Forgot）。

**特点**:
- 背景透明，去除了默认的 Dialog 样式，以适应内部组件的圆角设计。
- 自动处理关闭事件。

### 2.3 认证表单组件 (Forms)

包括 `LoginForm`, `RegisterForm`, `ForgotPasswordForm`。

**路径**: `src/components/auth/*.tsx`

**通用 Props**:
| 属性名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `className` | `string` | `undefined` | 样式类名 |
| `isModal` | `boolean` | `false` | 是否在弹窗模式下运行。如果为 true，链接点击会切换 Context 视图而不是跳转页面。 |

**设计细节**:
- **左侧**: 品牌形象区，包含背景图、渐变遮罩和 Slogan。
- **右侧**: 交互表单区，包含输入框、操作按钮和切换链接。
- **响应式**: 在移动端 (md 以下) 自动隐藏左侧图片区，只展示表单。

**组件列表**:
- **LoginForm**: 邮箱/密码登录。

---

## 3. 搜索与检索模块 (Search & Retrieval)

### 3.1 SearchBar
**路径**: `src/components/search/SearchBar.tsx`

**描述**:
主搜索框组件。支持 AI 搜索模式切换和高级搜索配置。

**功能**:
- **搜索输入**: 实时响应用户输入。
- **AI 模式**: 左侧 Toggle 开关切换普通/AI 深度搜索。
- **配置气泡**: 右侧设置按钮点击弹出 `SearchSettings` Popover。

### 3.2 SearchSettings
**路径**: `src/components/search/SearchSettings.tsx`

**描述**:
搜索相关的局部配置面板。作为 Popover 依附于 SearchBar。

**配置项**:
- **AI 搜索配置**: 深度推理模式开关。
- **结果排序**: 相关性、时间、引用量排序。
- **过滤选项**: 年份范围、来源筛选。

### 3.3 SearchFilters
**路径**: `src/components/search/SearchFilters.tsx`

**描述**:
搜索结果页面的快捷筛选标签栏和操作区。

**功能**:
- **标签筛选**: 全部、标题、作者、摘要等快速过滤。
- **操作入口**: 
    - **AI 助手**: 触发 `onChatClick` 打开问答面板。
    - **上传论文**: 触发 `onUploadClick` 打开上传弹窗。

### 3.4 UploadModal
**路径**: `src/components/upload/UploadModal.tsx`

**描述**:
文件上传弹窗。支持 PDF 文件的拖拽上传和列表管理。

**功能**:
- **拖拽区域**: 视觉反馈明确的拖拽上传区。
- **文件验证**: 自动过滤非 PDF 文件。
- **列表管理**: 展示待上传文件，支持移除。
- **上传模拟**: 模拟上传进度条和成功/失败状态。

**Props**:
| 属性名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `isOpen` | `boolean` | `false` | 是否显示 |
| `onClose` | `() => void` | `undefined` | 关闭回调 |

### 3.5 SearchResults
**路径**: `src/components/search/SearchResults.tsx`

**描述**:
搜索结果列表展示组件。采用网格/表格布局展示论文核心信息。支持 AI 增强显示和收藏操作。

**Props**:
| 属性名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `results` | `Paper[]` | `[]` | 论文数据列表 |
| `className` | `string` | `undefined` | 样式类名 |
| `onToggleBookmark` | `(id: string) => void` | `undefined` | 点击收藏/取消收藏的回调 |
| `aiEnabled` | `boolean` | `false` | 是否开启 AI 增强显示 (评分与推荐理由) |

**展示字段**:
- **基础信息**: 标题、作者、年份、来源、引用数、摘要。
- **状态**: 收藏 (Bookmark) 按钮及状态高亮。
- **AI 增强 (当 aiEnabled=true)**:
    - **评分 (Score)**: 标题旁的动态颜色标签 (如 "AI 98")。
    - **推荐理由 (Reason)**: 摘要下方的 AI 生成推荐理由卡片。



## 4. 设置模块 (Settings)

### 4.1 SettingsModal
**路径**: `src/components/settings/SettingsModal.tsx`

**描述**:
用户级全局设置弹窗。

**功能**:
- **Tab 导航**: 通用、账号、通知、关于。
- **界面设置**: 深色模式、紧凑模式开关。
- **账号安全**: 修改密码、两步验证入口。
