import asyncio
import sys
import os
from uuid import uuid4

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.append(src_dir)

from sqlalchemy import select
from base.pg.service import async_session_factory
from base.pg.entity import Job, Paper
from worker.tasks import task_queue
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")

async def main():
    print("DEBUG: Script started", flush=True)
    logger.info("开始诊断...")
    
    try:
        async with async_session_factory() as session:
            # 1. 检查最近的 Jobs
            logger.info("正在查询最近的 Job 记录...")
            stmt = select(Job).order_by(Job.created_at.desc()).limit(5)
            result = await session.execute(stmt)
            jobs = result.scalars().all()
            
            if not jobs:
                logger.warning("数据库中没有 Job 记录！")
            else:
                for job in jobs:
                    logger.info(f"Job: {job.job_id} | Type: {job.type} | Status: {job.status} | PaperID: {job.paper_id}")
                    
                    # 如果发现 queued/running 的任务，尝试手动触发
                    if job.status in ['queued', 'running'] and job.type == 'parse_text':
                        logger.info(f"尝试手动 Re-enqueue Job: {job.job_id}")
                        try:
                            await task_queue.enqueue_parse_text(str(job.paper_id), str(job.job_id))
                            logger.info("Re-enqueue 成功！请检查 Worker 日志。")
                        except Exception as e:
                            logger.error(f"Re-enqueue 失败: {e}")
    except Exception as e:
        logger.exception(f"数据库操作失败: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception(f"诊断脚本出错: {e}")
