import asyncio
import os
import sys
from uuid import uuid4
from loguru import logger
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, text
from pydantic import BaseModel
import sys

# Append path to import modules
sys.path.append(os.path.join(os.getcwd(), "src"))

from base.config import settings as global_settings
from base.pg.entity import User
from service.setting.schema import AgentSettings, Settings
from service.setting.setting_service import SettingService
from service.reader.retrieval_service import RetrievalService

# Database configuration
DATABASE_URL = global_settings.database_url.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

async def test_settings_flow():
    """
    Test flow:
    1. Create a mock user
    2. Update AgentSettings via SettingService (simulating API call)
    3. Verify settings are persisted in DB
    4. Instantiate RetrievalService with this user
    5. Verify RetrievalService picks up the correct provider/model
    """
    
    # Mock User ID
    user_id = uuid4()
    username = f"test_user_{user_id}"
    
    print(f"Starting test for user: {username}")
    
    async with async_session_factory() as session:
        # 1. Create User
        print(f"Creating test user: {username}")
        user = User(
            id=user_id,
            username=username,
            email=f"{username}@example.com",
            hashed_password="mock_password",
            is_active=True
        )
        session.add(user)
        await session.commit()
        
        try:
            # 2. Update Settings
            setting_service = SettingService(session)
            
            # Simulate request data from frontend
            # Scenario: User sets provider to 'siliconflow'
            new_agent_settings = AgentSettings(
                embedding_provider="siliconflow",
                embedding_model="Qwen/Qwen3-Embedding-0.6B",
                embedding_api_key="sk-test-key-123",
                embedding_base_url="https://api.siliconflow.cn/v1",
                rag_provider="siliconflow",
                rag_base_model="deepseek-ai/DeepSeek-V3",
                rag_api_key="sk-test-key-123",
                rag_base_url="https://api.siliconflow.cn/v1"
            )
            
            logger.info("Updating Agent Settings...")
            updated_settings = await setting_service.update_agent_settings(user_id, new_agent_settings)
            
            # 3. Verify Persistence
            # Fetch user again to be sure
            result = await session.execute(select(User).where(User.id == user_id))
            fetched_user = result.scalars().first()
            
            persisted_settings = fetched_user.settings
            if not persisted_settings:
                logger.error("Settings column is empty!")
                return
            
            persisted_agent = persisted_settings.agent_settings
            
            logger.info(f"Persisted Provider: {persisted_agent.embedding_provider}")
            logger.info(f"Persisted Model: {persisted_agent.embedding_model}")
            
            assert persisted_agent.embedding_provider == "siliconflow"
            assert persisted_agent.embedding_model == "Qwen/Qwen3-Embedding-0.6B"
            # Note: API key might be masked in get_agent_settings but in DB it should be raw or handled.
            # In our schema it's stored as JSON, so it's raw text.
            assert persisted_agent.embedding_api_key == "sk-test-key-123"
            
            print("✅ Settings Persistence Verified.")
            
            # 4. Verify RetrievalService Factory Logic
            print("Testing RetrievalService Factory...")
            retrieval_service = RetrievalService(session, user_id=user_id)
            
            # We can't easily check the internal embeddings object without calling private method
            # or mocking. We will call the private method _get_embeddings_model
            
            model = await retrieval_service._get_embeddings_model()
            
            from langchain_openai import OpenAIEmbeddings
            from base.embedding.local_embeddings import LocalOnnxEmbeddings
            
            print(f"Instantiated Model Type: {type(model)}")
            
            if isinstance(model, OpenAIEmbeddings):
                print(f"Model Name: {model.model}")
                print(f"Base URL: {model.openai_api_base}")
                
                api_key_val = model.openai_api_key
                if hasattr(api_key_val, 'get_secret_value'):
                    api_key_val = api_key_val.get_secret_value()
                
                print(f"API Key: {api_key_val[:4]}****")
                
                assert model.model == "Qwen/Qwen3-Embedding-0.6B"
                assert model.openai_api_base == "https://api.siliconflow.cn/v1"
                assert api_key_val == "sk-test-key-123"
                print("✅ RetrievalService correctly configured with SiliconFlow settings.")
                
            elif isinstance(model, LocalOnnxEmbeddings):
                print("❌ RetrievalService fell back to LocalOnnxEmbeddings! Factory logic failed.")
            else:
                print(f"❌ Unknown model type: {type(model)}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.exception("Test failed with exception")
        finally:
            # Cleanup
            logger.info("Cleaning up test user...")
            await session.delete(user)
            await session.commit()

if __name__ == "__main__":
    asyncio.run(test_settings_flow())
