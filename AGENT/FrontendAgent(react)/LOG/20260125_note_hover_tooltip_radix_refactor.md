# 2026-01-25 笔记(Note)悬停显示重构 (Radix UI)

## 基本信息
- **时间**: 2026年01月25日 02:38
- **责任人**: FrontendAgent(react)
- **目标**: 废弃之前的手动 Hover 状态管理方案，改用 Radix UI 的 Tooltip 组件来实现笔记(Note)的悬停显示，以提供更稳定、标准化的交互体验，并解决闪烁和层级问题。

## 变更范围

### 1. 新增 UI 组件 (Tooltip)
- **路径**: `src/components/ui/tooltip.tsx`
- **变更**: 
    - 封装 `@radix-ui/react-tooltip`。
    - 导出 `Tooltip`, `TooltipTrigger`, `TooltipContent`, `TooltipProvider`。
    - 配置默认动画和样式（基于 Tailwind CSS）。

### 2. 阅读器覆盖层 (PDFPageOverlay)
- **路径**: `src/components/reader/PDFPageOverlay.tsx`
- **变更**:
    - **移除旧逻辑**: 删除了 `hoveredAnnotationId`, `hoverPosition`, `hoverTimeoutRef` 等手动状态管理代码，以及 `handleAnnotationMouseEnter/Leave` 处理函数。
    - **组件重构**: 使用 `<Tooltip>` 组件包裹 `annotation.type === 'note'` 的渲染元素。
    - **逻辑优化**: 
        - 仅在非编辑状态 (`!activeAnnotationId`) 且有内容时启用 Tooltip。
        - 为每个 `rect` 单独包裹 Tooltip，确保多行标注在任意位置都能触发。
    - **修复**: 
        - 修正了重构过程中意外引入的重复删除按钮问题。
        - 修正了 JSX 结构错误（Popup Header 部分标签闭合错乱）。
        - 补充了缺失的 `</TooltipProvider>` 闭合标签。

## 验证方式与结果
- **代码结构验证**:
    - 确认 `PDFPageOverlay.tsx` 已正确引入并使用 `@/components/ui/tooltip`。
    - 确认 Tooltip 包裹逻辑正确，且 Trigger 为 `asChild` 模式。
    - 确认删除了所有不再使用的手动 Hover 状态代码。
    - 确认 Popup Header 结构清晰，无多余闭合标签。
- **预期效果**:
    - 鼠标悬停在笔记区域时，由 Radix UI 接管显示逻辑，提供平滑的动画和自动定位。
    - 交互更加稳定，符合 Shadcn/UI 设计规范。
