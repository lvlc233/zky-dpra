# 定义app启动相关的配置


from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

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
        lifespan=lifespan
    )

    @app.get("/")
    async def root():
        return {"message": "Hello from DeepPaperResearcher Backend!", "status": "running"}

    return app

app = create_app()
