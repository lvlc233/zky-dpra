# 前端变更日志 - 登录页“记住我”功能

**时间**: 2026年01月22日 14:40
**变更目标**: 
1. 登录表单新增“记住我”复选框。
2. 调用登录 API 时传递 `remember_me` 状态。

**变更范围**:
- `main/frontend/src/components/auth/LoginForm.tsx`: 
    - 新增 Checkbox UI。
    - 更新 `formData` 状态管理。
    - 调整布局以容纳新控件。
- `main/frontend/src/services/auth.service.ts`:
    - `login` 方法签名增加 `rememberMe` 参数。

**验证方式与结果**:
1. **UI验证**: 登录表单出现“记住我 [7天有效]”复选框，样式与现有设计保持一致。
2. **功能验证**: 勾选复选框登录，Payload 中包含 `remember_me: true`。

**提交人**: FrontendAgent(react)
