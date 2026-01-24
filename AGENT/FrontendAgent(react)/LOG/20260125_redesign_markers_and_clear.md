# 2026-01-25 Redesign Markers and Clear Functionality

## 目标
响应用户需求："现在这些标记没有删除,就算你看到有,也全部消失,重新设计"。
1. 实现"清空所有标注"功能，解决用户无法删除或想要一键清除的问题。
2. 实现"隐藏/显示标注"功能，提供更灵活的视图控制。
3. 重新设计标注的视觉样式，使其更美观（圆角、选中状态）。
4. 在阅读器导航栏增加设置菜单，整合上述功能。

## 变更范围
1. `src/components/reader/ReaderNavbar.tsx`: 
   - 引入 `Popover` 组件作为设置菜单。
   - 新增 `Settings` 图标按钮。
   - 新增 "显示/隐藏所有标注" 和 "清空所有标注" 选项。
   - 新增 props: `showAnnotations`, `onToggleAnnotations`, `onClearAllAnnotations`。

2. `src/app/reader/[id]/page.tsx`:
   - 实现 `handleToggleAnnotations`: 更新当前图层的可见性，并尝试同步到后端（乐观更新）。
   - 实现 `handleClearAllAnnotations`: 遍历当前图层的所有标注并逐个调用删除接口（乐观更新 + 异步删除）。
   - 将新处理函数传递给 `ReaderNavbar`。

3. `src/components/reader/PDFPageOverlay.tsx`:
   - 样式微调：添加 `rounded-[2px]` 使高亮更自然。
   - 选中状态优化：选中时添加 `ring-2` 边框，提升交互体验。
   - 兼容性调整：备注(Note)和翻译(Translate)类型保持下划线样式，不使用圆角。

## 验证方式
1. **清空测试**: 打开一篇有标注的论文，点击导航栏设置 -> 清空所有标注。预期：所有标注立即消失，并在后台被删除。
2. **隐藏测试**: 点击设置 -> 隐藏所有标注。预期：标注暂时消失，再次点击显示后出现。
3. **视觉测试**: 创建一个新的高亮，预期看到圆角矩形样式；点击高亮，预期看到选中边框。

## 结果
- 已完成代码修改。
- 提供了强力的"清空"手段，直接回应用户"make them all disappear"的诉求。
- 优化了 UI 交互，符合"redesign"的要求。
