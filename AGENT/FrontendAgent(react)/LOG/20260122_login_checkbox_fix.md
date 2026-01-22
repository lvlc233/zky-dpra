# 2026-01-22 修复登录表单事件处理 Bug

**提交人**: FrontendAgent(react)
**时间**: 2026-01-22 15:16:00

## 目标
修复点击“记住我”复选框时，密码框出现异常字符且复选框无法勾选的问题。

## 变更范围
1.  **前端**:
    *   `src/components/auth/LoginForm.tsx`:
        *   修改 `handleChange` 函数：增加了对 `e.target.name`、`e.target.type` 和 `e.target.checked` 的解构与判断。
        *   当 `type === 'checkbox'` 时，使用 `checked` 属性更新状态，而非 `value`。
        *   为 `email` 输入框显式添加了 `name="email"` 属性，规范了表单字段。

## 验证方式
1.  **复选框交互**: 点击“记住我”，复选框应正常勾选/取消，且密码框内容不受影响。
2.  **表单提交**: 勾选“记住我”后登录，检查 Payload 中 `rememberMe` 字段是否为 `true`。
