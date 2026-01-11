
========================
操作时间: 2026年01月10日 12:35
操作内容: 优化日志系统与修复arXiv客户端重定向问题
操作目标: 提升日志可读性，修复HTTP 301错误
操作结果: 成功
备注:
- 引入 loguru 库替代标准 logging 模块，提供更美观的彩色日志输出
- 创建 src/common/logger.py，配置 Loguru 并拦截标准库日志
- 更新 src/controller/api/app.py，系统启动时初始化新的日志配置
- 修复 src/base/arxiv/client.py:
    - 基础URL从 http 变更为 https，避免 301 重定向
    - 启用 httpx 的 follow_redirects=True 选项作为保险
    - 迁移至 loguru logger
- 更新 src/service/papers/arxiv_service.py 迁移至 loguru logger
