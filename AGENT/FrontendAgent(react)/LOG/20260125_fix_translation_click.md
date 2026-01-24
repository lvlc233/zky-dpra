# 变更日志: 修复翻译功能交互

**提交人**: FrontendAgent(react)
**日期**: 2026-01-25 22:15:00

## 问题描述
用户反馈“点击无任何翻译”。经排查发现两个问题：
1. **Bug**: 点击已存在的翻译类型标注 (`type: 'translate'`) 时，点击事件处理函数未更新 `translationResult` 状态，导致弹窗内容为空。
2. **交互缺失**: 翻译弹窗 (`TranslationModal`) 中仅提供“保存为备注”选项，导致翻译结果被转换为普通备注 (`note`)，丢失了翻译标注的语义和特定样式（绿色虚线）。

## 变更内容

### 1. 修复点击事件
- **文件**: `src/components/reader/PDFPageOverlay.tsx`
- **修改**: 在标注元素的 `onClick` 处理逻辑中，补充了 `setTranslationResult` 的调用。
- **代码**:
  ```typescript
  onClick={(e) => {
    // ...
    setTranslationResult(annotation.type === 'translate' ? (annotation.content || '') : '');
    // ...
  }}
  ```

### 2. 完善保存流程
- **文件**: `src/components/reader/PDFPageOverlay.tsx`
- **修改**: 将翻译助手弹窗底部的操作从“保存为备注”改为“保存翻译”。
- **逻辑**: 保存时生成的 Annotation 类型从 `note` 改为 `translate`，颜色标记为 `bg-green-300`。
- **效果**: 用户保存翻译后，界面上会显示绿色虚线高亮。点击该高亮，会弹出只读的翻译结果窗口，而非可编辑的备注框。

## 验证
- **场景1**: 选中文字 -> 翻译 -> 点击“保存翻译” -> 界面出现绿色高亮 -> 点击高亮 -> 弹窗正确显示原文和译文。
- **场景2**: 点击旧的备注 -> 弹窗显示可编辑文本框（不受影响）。
