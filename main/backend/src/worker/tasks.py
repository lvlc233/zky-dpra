'''
开发者: BackendAgent
当前版本: v1.0_arq_tasks
创建时间: 2026年01月08日 14:30
更新时间: 2026年01月08日 14:30
更新记录:
    [2026年01月08日 14:30:v1.0_arq_tasks:创建Arq异步任务，集成PDF解析和向量化处理]
'''


from typing import Any, Dict, Optional
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import select
from arq import create_pool, cron
from arq.connections import RedisSettings
from arq.worker import Worker

from base.config import settings
from base.pg.service import async_session_factory
from base.pg.entity import Job
from service.papers.paper_service import PaperProcessingService


from loguru import logger


class ArqRedisSettings(RedisSettings):
    """自定义Redis设置，支持从配置读取"""

    def __init__(self):
        # 从settings中读取Redis配置
        super().__init__(
            host=settings.arq_redis_url.split('//')[1].split(':')[0],
            port=int(settings.arq_redis_url.split(':')[-1].split('/')[0]),
            database=int(settings.arq_redis_url.split('/')[-1])
        )


# 异步任务定义
async def parse_text_task(ctx: Dict[str, Any], paper_id: str, job_id: str) -> Dict[str, Any]:
    """
    解析PDF正文任务 (parse_text)
    """
    logger.info(f"开始解析PDF正文: {paper_id}, JobID: {job_id}")
    try:
        uuid_paper_id = UUID(paper_id)
        uuid_job_id = UUID(job_id)
        
        processing_service = PaperProcessingService()
        success = await processing_service.parse_text(uuid_paper_id, uuid_job_id, redis=ctx.get('redis'))
        
        if success:
            # 任务链: parse_text 完成后，触发后续任务
            logger.info(f"解析完成，触发后续任务链: {paper_id}")
            # 这里我们不直接 await enqueue，而是调用 service 层的方法来触发，或者在这里直接触发
            # 简化起见，直接使用 task_queue (需要解决循环导入，或者在 ProcessingService 内部触发)
            # 更好的方式是 PaperProcessingService.parse_text 成功后，由 Service 层负责触发后续
            # 但 Worker 是执行者。我们可以在 Service 中编排。
            # 目前 PaperProcessingService.parse_text 内部已经有了 _trigger_next_tasks 的逻辑占位
            return {"status": "success", "message": "PDF解析完成"}
        else:
            return {"status": "failed", "message": "PDF解析失败"}
    except Exception as e:
        logger.error(f"解析任务异常: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

async def vectorize_task(ctx: Dict[str, Any], paper_id: str, job_id: str) -> Dict[str, Any]:
    """
    向量化任务 (vectorize)
    """
    logger.info(f"开始向量化任务: {paper_id}, JobID: {job_id}")
    try:
        uuid_paper_id = UUID(paper_id)
        uuid_job_id = UUID(job_id)
        
        processing_service = PaperProcessingService()
        success = await processing_service.vectorize(uuid_paper_id, uuid_job_id, redis=ctx.get('redis'))
        
        return {"status": "success" if success else "failed"}
    except Exception as e:
        logger.error(f"向量化任务异常: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


async def summary_task(ctx: Dict[str, Any], paper_id: str, job_id: str) -> Dict[str, Any]:
    """
    总结任务 (summary)
    """
    logger.info(f"开始总结任务: {paper_id}, JobID: {job_id}")
    try:
        uuid_paper_id = UUID(paper_id)
        uuid_job_id = UUID(job_id)
        
        processing_service = PaperProcessingService()
        success = await processing_service.summary(uuid_paper_id, uuid_job_id, redis=ctx.get('redis'))
        
        return {"status": "success" if success else "failed"}
    except Exception as e:
        logger.error(f"总结任务异常: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

async def mind_map_task(ctx: Dict[str, Any], paper_id: str, job_id: str) -> Dict[str, Any]:
    """
    脑图生成任务 (mind_map)
    """
    logger.info(f"开始脑图任务: {paper_id}, JobID: {job_id}")
    try:
        uuid_paper_id = UUID(paper_id)
        uuid_job_id = UUID(job_id)
        
        processing_service = PaperProcessingService()
        success = await processing_service.mind_map(uuid_paper_id, uuid_job_id, redis=ctx.get('redis'))
        
        return {"status": "success" if success else "failed"}
    except Exception as e:
        logger.error(f"脑图任务异常: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

# 保留旧的 process_pdf_task 以兼容（或者标记为废弃）
async def process_pdf_task(ctx: Dict[str, Any], paper_id: str, job_id: Optional[str] = None) -> Dict[str, Any]:
    logger.warning("process_pdf_task is deprecated, use parse_text_task instead.")
    return await parse_text_task(ctx, paper_id, job_id or str(UUID(int=0)))


async def generate_embeddings_task(
    ctx: Dict[str, Any],
    chunks: list,
    model: str = "text-embedding-ada-002"
) -> Dict[str, Any]:
    """
    生成文本向量嵌入的异步任务

    参数:
    - ctx: 任务上下文
    - chunks: 文本块列表
    - model: 嵌入模型名称

    返回:
    - dict: 包含生成的向量列表

    TODO:
    - 集成OpenAI或其他嵌入模型
    - 支持批量处理优化性能
    """
    logger.info(f"开始生成向量嵌入，chunks数量: {len(chunks)}")

    try:
        # TODO: 实现向量生成逻辑
        # 临时返回模拟数据
        embeddings = []
        for i, chunk in enumerate(chunks):
            # 模拟向量生成（实际应调用嵌入模型API）
            embedding = [0.1 * (i + 1)] * 1536  # 1536维向量
            embeddings.append(embedding)

        logger.info(f"向量嵌入生成完成，数量: {len(embeddings)}")
        return {
            "status": "success",
            "embeddings": embeddings,
            "count": len(embeddings)
        }

    except Exception as e:
        logger.error(f"向量生成任务失败: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"向量生成失败: {str(e)}"
        }


async def cleanup_failed_tasks(ctx: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理失败任务的定时任务

        参数:
        - ctx: 任务上下文

        返回:
        - dict: 清理结果

        功能:
        - 标记超过1小时未完成的"running"任务为failed
        - (可选) 删除超过7天的失败任务记录
        """
        logger.info("开始清理失败任务")

        try:
            async with async_session_factory() as session:
                # 1. 查找并标记“僵尸”任务 (状态为 running 但创建超过 1 小时)
                # 注意: 这里的超时时间可以根据实际任务平均耗时调整
                cutoff_time = datetime.now() - timedelta(hours=1)
                
                # 查询所有 running 且创建时间早于 cutoff_time 的任务
                stmt = select(Job).where(Job.status == "running", Job.created_at < cutoff_time)
                result = await session.execute(stmt)
                stuck_jobs = result.scalars().all()
                
                cleaned_count = 0
                for job in stuck_jobs:
                    logger.warning(f"Found stuck job {job.id} (created at {job.created_at}), marking as failed.")
                    job.status = "failed"
                    job.error = "Task execution timed out or worker crashed (cleanup)"
                    job.end_at = datetime.now()
                    session.add(job)
                    cleaned_count += 1
                
                if cleaned_count > 0:
                    await session.commit()
                    logger.info(f"已清理 {cleaned_count} 个僵尸任务")
                else:
                    logger.info("未发现僵尸任务")

            logger.info("失败任务清理完成")
            return {
                "status": "success",
                "message": f"清理完成, 处理了 {cleaned_count} 个僵尸任务"
            }

        except Exception as e:
            logger.error(f"清理任务失败: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"清理失败: {str(e)}"
            }


# 任务配置
class WorkerSettings:
    """Arq Worker配置"""

    # Redis连接设置
    redis_settings = ArqRedisSettings()

    # 任务函数注册
    functions = [
        process_pdf_task,
        parse_text_task,
        vectorize_task,
        summary_task,
        mind_map_task,
        generate_embeddings_task,
        cleanup_failed_tasks
    ]

    # 定时任务（cron jobs）
    cron_jobs = [
        # 每15分钟清理一次失败/僵尸任务
        cron(
            cleanup_failed_tasks,
            minute={0, 15, 30, 45}
        )
    ]

    # Worker配置
    max_jobs = 10  # 最大并发任务数
    job_timeout = 600  # 任务超时时间（秒）
    keep_result = 86400  # 保留任务结果时间（秒）
    max_tries = 3  # 最大重试次数
    retry_delay = 10  # 重试延迟（秒）
    
    # 显式声明监听的队列 (包括默认队列和自定义队列)
    queues = ['arq:queue', 'pdf_processing', 'embeddings', 'llm_tasks']


# 任务队列管理器
class TaskQueue:
    """任务队列管理器，提供任务入队接口"""

    def __init__(self):
        self._pool = None

    async def init(self):
        """初始化Redis连接池"""
        if not self._pool:
            self._pool = await create_pool(ArqRedisSettings())
            logger.info("任务队列初始化完成")

    async def close(self):
        """关闭连接池"""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("任务队列已关闭")

    async def enqueue_parse_text(self, paper_id: str, job_id: str) -> str:
        """入队：正文解析"""
        await self.init()
        job = await self._pool.enqueue_job(
            'parse_text_task',
            paper_id,
            job_id,
            _queue_name='pdf_processing',
            _job_id=f"parse_text:{job_id}"
        )
        logger.info(f"解析任务已入队: {job.job_id if job else 'None (Duplicate?)'}")
        return job.job_id if job else None

    async def enqueue_vectorize(self, paper_id: str, job_id: str) -> str:
        """入队：向量化"""
        await self.init()
        job = await self._pool.enqueue_job(
            'vectorize_task',
            paper_id,
            job_id,
            _queue_name='embeddings',
             _job_id=f"vectorize:{job_id}"
        )
        logger.info(f"向量化任务已入队: {job.job_id if job else 'None (Duplicate?)'}")
        return job.job_id if job else None

    async def enqueue_summary(self, paper_id: str, job_id: str) -> str:
        """入队：总结"""
        await self.init()
        job = await self._pool.enqueue_job(
            'summary_task',
            paper_id,
            job_id,
            _queue_name='llm_tasks',
            _job_id=f"summary:{job_id}"
        )
        return job.job_id if job else None

    async def enqueue_mind_map(self, paper_id: str, job_id: str) -> str:
        """入队：脑图"""
        await self.init()
        job = await self._pool.enqueue_job(
            'mind_map_task',
            paper_id,
            job_id,
            _queue_name='llm_tasks',
            _job_id=f"mind_map:{job_id}"
        )
        return job.job_id if job else None

    async def enqueue_process_pdf(self, paper_id: str, job_id: Optional[str] = None) -> str:
        """
        入队PDF处理任务

        参数:
        - paper_id: 论文ID
        - job_id: 任务ID (可选)

        返回:
        - str: 任务ID
        """
        await self.init()
        job = await self._pool.enqueue_job(
            'process_pdf_task',
            paper_id,
            job_id,
            _queue_name='pdf_processing'
        )
        logger.info(f"PDF处理任务已入队: {job.job_id}")
        return job.job_id

    async def enqueue_generate_embeddings(
        self,
        chunks: list,
        model: str = "text-embedding-ada-002"
    ) -> str:
        """
        入队向量生成任务

        参数:
        - chunks: 文本块列表
        - model: 嵌入模型

        返回:
        - str: 任务ID
        """
        await self.init()
        job = await self._pool.enqueue_job(
            'generate_embeddings_task',
            chunks,
            model,
            _queue_name='embeddings'
        )
        logger.info(f"向量生成任务已入队: {job.job_id}")
        return job.job_id

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        获取任务状态

        参数:
        - job_id: 任务ID

        返回:
        - dict: 任务状态信息
        """
        await self.init()
        job = await self._pool.get_job_result(job_id)

        if job:
            return {
                "job_id": job_id,
                "status": job.status,
                "result": job.result,
                "error": job.error
            }
        else:
            return {
                "job_id": job_id,
                "status": "not_found",
                "message": "任务不存在或结果已过期"
            }


# 全局任务队列实例
task_queue = TaskQueue()


import asyncio

# 启动Worker的函数
def create_worker(queue_name: str = 'arq:queue') -> Worker:
    """
    创建Arq Worker实例
    
    参数:
    - queue_name: 监听的队列名称

    返回:
    - Worker: Worker实例
    """
    return Worker(
        redis_settings=ArqRedisSettings(),
        functions=WorkerSettings.functions,
        cron_jobs=WorkerSettings.cron_jobs,
        max_jobs=WorkerSettings.max_jobs,
        job_timeout=WorkerSettings.job_timeout,
        keep_result=WorkerSettings.keep_result,
        max_tries=WorkerSettings.max_tries,
        queue_name=queue_name
    )


# 运行Worker（用于命令行启动）
async def run_worker():
    """运行Worker，支持多队列"""
    queues = WorkerSettings.queues
    logger.info(f"Starting workers for queues: {queues}")
    
    workers = [create_worker(q) for q in queues]
    
    # 并发运行所有 Worker
    await asyncio.gather(*[w.main() for w in workers])