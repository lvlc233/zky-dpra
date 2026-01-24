# 增强删除功能与UX

## 背景
用户反馈高光标记和备注的删除功能缺失或不可见。实际代码中存在删除按钮，但可能因为UI不够明显或操作路径（如键盘快捷键）不支持而导致用户困惑。

## 变更内容
1.  **PDFPageOverlay.tsx**:
    - 添加键盘快捷键支持：当选中标注（Popup打开）时，按下 `Delete` 或 `Backspace` 键可直接删除。
    - 针对 `Backspace` 做了防误触处理（在输入框内时不触发删除）。
    - 增强删除按钮样式：使用更深的红色背景和边框，增加阴影，使其在视觉上更显眼。
    - 使用 `useCallback` 优化 `handleDelete`，确保依赖链正确。

## 验证
-   **代码逻辑验证**: 
    -   `useEffect` 监听 `keydown`，依赖 `activeAnnotationId`，只有在选中状态下生效。
    -   `handleDelete` 调用 `onDeleteAnnotation`，与 `ReaderPage` 传递的函数一致。
    -   按钮样式更新为 `bg-red-100` 等更强的视觉提示。

## 提交人
FrontendAgent(react)
2026-01-25 10:45:00
