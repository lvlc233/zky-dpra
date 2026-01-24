import sys
import os
import asyncio
import traceback
import logging
from loguru import logger

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.append(src_dir)

# Configure loguru
logger.remove()
logger.add(sys.stderr, level="DEBUG")

# Configure standard logging for arq
logging.basicConfig(level=logging.DEBUG)

print("Starting run_worker_script.py...", flush=True)

try:
    from worker.tasks import run_worker
    logger.info("Imported run_worker from worker.tasks")
    
    if __name__ == "__main__":
        logger.info("Starting worker...")
        try:
            # Check redis connection first
            from base.config import settings
            logger.info(f"Redis URL: {settings.arq_redis_url}")
            
            asyncio.run(run_worker())
        except Exception as e:
            logger.exception(f"Worker crashed: {e}")
        logger.info("Worker finished (unexpected)")
except Exception:
    traceback.print_exc()
