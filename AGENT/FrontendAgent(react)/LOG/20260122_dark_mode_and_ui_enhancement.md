# 前端变更日志 - 深色模式与UI优化

**时间**: 2026年01月22日 14:33
**变更目标**: 
1. 增强设置弹窗中 Switch 组件（切换按钮）的视觉对比度。
2. 实现完整的深色模式切换与持久化功能。

**变更范围**:
- `main/frontend/src/components/ui/switch.tsx`: 修改 Switch 组件样式，使用更高对比度的颜色。
- `main/frontend/src/components/providers/ThemeProvider.tsx`: 新增 ThemeProvider 组件，管理主题状态。
- `main/frontend/src/app/layout.tsx`: 引入 ThemeProvider。
- `main/frontend/src/components/settings/SettingsModal.tsx`: 集成 useTheme Hook，在保存设置时同步主题状态。

**验证方式与结果**:
1. **视觉验证**: Switch 组件在选中状态下现在显示为深靛蓝色 (`bg-indigo-600`)，未选中状态为灰色 (`bg-gray-300`)，在深色模式下也有相应适配，对比度显著提升。
2. **功能验证**: 
   - 在设置中切换“深色模式”并保存，页面立即切换为深色主题。
   - 刷新页面后，深色模式依然保持（通过 localStorage 持久化）。
   - “启动向量搜索”的开关也因为复用了 Switch 组件而自动获得了更明显的样式。

**提交人**: FrontendAgent(react)
