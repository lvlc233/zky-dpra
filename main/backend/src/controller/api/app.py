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
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
from loguru import logger

# 导入papers路由
from controller.api.papers.router import router as papers_router
from controller.api.auth.router import router as auth_router, users_router
from controller.api.reader.router import router as reader_router
from controller.api.collections.router import router as collections_router
from controller.api.search.router import router as search_router
from controller.api.settings.settings_router import router as settings_router
from controller.api.jobs.router import router as jobs_router
from controller.api.agent.router import router as agent_router
from controller.api.admin.router import router as admin_router
from controller.api.admin.models_router import router as admin_models_router

# 导入异常处理器
from controller.response import global_exception_handler
from common.logger import setup_logging
from base.pg.service import engine
from base.redis.service import RedisService
from base.neo4j.service import Neo4jService

# 配置日志
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("System starting up...")
    
    # 任务恢复逻辑
    try:
        from base.pg.service import async_session_factory, JobRepository
        async with async_session_factory() as session:
            # 重置所有 running 状态的任务为 queued
            # 原因: 服务重启意味着内存中的任务丢失，需要重新调度或标记失败
            # 简单策略: 标记为 failed (用户手动重试) 或 queued (自动重试)
            # 根据需求: "异常的项目不自动回复,而是需要用户手动点击" -> 标记为 failed
            logger.info("Checking for interrupted jobs...")
            await JobRepository.reset_interrupted_jobs(session)
    except Exception as e:
        logger.error(f"Failed to recover jobs: {e}")

    yield
    # Shutdown
    logger.info("System shutting down...")

    await engine.dispose()
    logger.info("Database connection pool disposed")
    
    await RedisService.close()
    await Neo4jService.close()

def create_app() -> FastAPI:
    app = FastAPI(
        title="DeepPaperResearcher Backend",
        version="0.1.0",
        lifespan=lifespan,
        description="基于 LangGraph 的 AI 辅助论文研究与管理平台 API"
    )
    # 跨域
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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
    app.include_router(collections_router, prefix="/api/v1")
    app.include_router(search_router, prefix="/api/v1")
    app.include_router(settings_router, prefix="/api/v1")
    app.include_router(jobs_router, prefix="/api/v1")
    app.include_router(agent_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")
    app.include_router(admin_models_router, prefix="/api/v1")

    @app.get("/")
    async def root():
        return {"message": "Hello from DeepPaperResearcher Backend!", "status": "running", "version": "0.1.0"}

    return app

app = create_app()
