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
from contextlib import asynccontextmanager
import logging

# 导入papers路由
from .papers.router import router as papers_router

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

    # 注册papers路由
    logger.info("注册papers路由")
    app.include_router(papers_router)

    @app.get("/")
    async def root():
        return {"message": "Hello from DeepPaperResearcher Backend!", "status": "running", "version": "0.1.0"}

    return app

app = create_app()
