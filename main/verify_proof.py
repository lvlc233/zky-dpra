import asyncio
import os
import sys
from uuid import UUID

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__name__))
src_dir = os.path.join(current_dir, "backend", "src")
sys.path.append(src_dir)

async def verify_everything():
    from base.pg.service import async_session_factory
    from base.pg.entity import SystemModelConfig, User
    from sqlalchemy import select
    
    print("--- 1. 数据库中的全局配置 (SystemModelConfig) ---")
    async with async_session_factory() as session:
        stmt = select(SystemModelConfig).where(SystemModelConfig.type == 'summary')
        c = (await session.execute(stmt)).scalar_one_or_none()
        if c:
            print(f"总结任务配置: 模型={c.model_name}, Provider={c.provider}, HasKey={'Yes' if c.api_key else 'No'}")
        else:
            print("警告: 数据库中没有 'summary' 类型的全局配置!")

    print("\n--- 2. 代码中的逻辑检查 ---")
    # 模拟获取配置
    from service.setting.setting_service import SettingService
    async with async_session_factory() as session:
        ss = SettingService(session)
        # 随便找个用户
        u = (await session.execute(select(User).limit(1))).scalar()
        if u:
            effective = await ss.get_effective_model_config(u.id, 'summary')
            print(f"代码逻辑返回的配置: 模型={effective.get('model_name')}, Key={effective.get('api_key')[:10] if effective.get('api_key') else 'None'}...")
        
    print("\n--- 3. 结论 ---")
    print("如果你在 Worker 日志中看到 'gpt-3.5-turbo'，说明它仍然在运行旧代码。")
    print("因为新代码会从数据库读取配置（如 gpt-4o-mini）。")
    print("请务必重启 run_worker_script.py！")

if __name__ == "__main__":
    asyncio.run(verify_everything())
