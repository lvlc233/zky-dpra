import asyncio
from redis.asyncio import Redis
from base.config import settings
from loguru import logger

async def clear_arq_queue():
    """
    清理 Arq 相关的 Redis keys
    """
    redis_url = settings.arq_redis_url
    logger.info(f"Connecting to Redis at {redis_url}")
    
    redis = Redis.from_url(redis_url)
    
    try:
        # 匹配所有 arq 相关的 keys
        # arq 默认前缀通常是 'arq:'
        keys = await redis.keys("arq:*")
        
        if not keys:
            logger.info("No arq keys found.")
            return

        logger.info(f"Found {len(keys)} arq keys. Deleting...")
        await redis.delete(*keys)
        logger.info("Successfully cleared arq keys.")
        
    except Exception as e:
        logger.error(f"Error clearing redis: {e}")
    finally:
        await redis.close()

if __name__ == "__main__":
    asyncio.run(clear_arq_queue())
