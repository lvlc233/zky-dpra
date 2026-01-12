'''
开发者: BackendAgent
当前版本: v0.1_papers
创建时间: 2026年01月02日 07:43
更新时间: 2026年01月02日 10:16
更新记录:
    [2026年01月02日 10:16:v0.1_papers:统一版本号]
    [2026年01月02日 08:54:v0.1_app_with_papers:注册papers路由，支持论文获取功能]
'''

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
from loguru import logger

# 导入papers路由
from controller.api.papers.router import router as papers_router

# 导入异常处理器
from controller.response import global_exception_handler
from common.logger import setup_logging

# 配置日志
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("System starting up...")
    yield
    # Shutdown
    logger.info("System shutting down...")

def create_app() -> FastAPI:
    app = FastAPI(
        title="DeepPaperResearcher Backend",
        version="0.1.0",
        lifespan=lifespan,
        description="基于 LangGraph 的 AI 辅助论文研究与管理平台 API"
    )

    # 注册全局异常处理器
    app.add_exception_handler(Exception, global_exception_handler)
    app.add_exception_handler(StarletteHTTPException, global_exception_handler)
    app.add_exception_handler(RequestValidationError, global_exception_handler)

    # 注册papers路由
    logger.info("注册papers路由")
    app.include_router(papers_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(reader_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(reports_router, prefix="/api/v1")

    @app.get("/")
    async def root():
        return {"message": "Hello from DeepPaperResearcher Backend!", "status": "running", "version": "0.1.0"}

    return app

app = create_app()
