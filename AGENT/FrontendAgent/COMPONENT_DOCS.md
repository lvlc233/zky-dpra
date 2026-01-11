# 前端组件文档 (Component Documentation)

**负责人**: FrontendAgent  
**最后更新**: 2026-01-10  
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
- **RegisterForm**: 用户名/邮箱/密码注册。
- **ForgotPasswordForm**: 邮箱找回密码，包含“发送成功”的状态反馈。

---

## 3. 检索模块 (Search)

首页核心检索区域，集成搜索、筛选与 AI 模式切换。

### 3.1 SearchBar
**路径**: `src/components/search/SearchBar.tsx`

**描述**:
主要的搜索输入框组件。

**功能**:
- **输入**: 支持文本输入。
- **AI 模式**: 右侧 "AI" 按钮可切换搜索模式（普通/深度AI）。
- **设置**: 提供高级搜索设置入口。
- **样式**: 悬浮发光效果 (Glow Effect) 和 focus 状态的动效。

### 3.2 SearchFilters
**路径**: `src/components/search/SearchFilters.tsx`

**描述**:
搜索框下方的辅助组件，包含快速筛选条件和上传入口。

**功能**:
- **条件筛选**: 提供年份、领域等预设 Tag 切换。
- **上传入口**: 右侧显眼的 "上传你的论文" 链接。

### 3.3 SearchSection
**路径**: `src/components/search/SearchSection.tsx`

**描述**:
首页的 Hero 区域容器，组合了 `SearchBar` 和 `SearchFilters`，并包含背景装饰和产品特性介绍。

---

## 4. 样式系统 (Design System)

本项目使用 Tailwind CSS 进行样式管理，核心设计语言如下：

- **主色调**: Indigo (`indigo-600`) 至 Violet (`violet-600`) 渐变。
- **背景**: 纯白 (`bg-white`) 或 浅灰 (`bg-gray-50`)，搭配 `backdrop-blur` 毛玻璃效果。
- **圆角**: 统一使用 `rounded-xl` (12px) 或 `rounded-2xl` (16px) 营造现代感。
- **阴影**: 多层级阴影 (`shadow-lg`, `shadow-indigo-200`) 增加深度。
- **交互**: `hover:scale` 和 `transition-all` 提供丝滑的微交互体验。
