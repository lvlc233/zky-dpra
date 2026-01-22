# 前端变更日志 - 注册页集成自动登录与记住我

**时间**: 2026年01月22日 14:50
**变更目标**: 
1. 注册流程优化：注册成功后自动触发登录。
2. 注册页新增“记住我”选项，与登录页保持体验一致。

**变更范围**:
- `main/frontend/src/components/auth/RegisterForm.tsx`: 
    - 新增 `rememberMe` 状态与复选框 UI。
    - 在 `handleSubmit` 中调用 `register` 成功后，立即调用 `login` 并传递 `rememberMe` 参数。
    - 更新 Toast 提示为“注册成功并已自动登录”。

**验证方式与结果**:
1. **功能验证**: 
   - 填写注册表单并勾选“记住我”。
   - 点击注册，观察到 Toast 提示“注册成功并已自动登录”。
   - 检查 `authService.login` 被调用，且 Payload 包含 `remember_me: true`。
   - 确认跳转至 `/dashboard`。
2. **后端兼容性**: 
   - 确认后端 `LoginRequest` Schema 支持 `remember_me` 字段，前端传参不会引发 422 错误。

**提交人**: FrontendAgent(react)
