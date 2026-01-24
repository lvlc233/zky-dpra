
import asyncio
from uuid import uuid4, UUID
from typing import List, Optional
from unittest.mock import MagicMock, AsyncMock, patch
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Mock pgvector and sqlmodel
mock_pgvector = MagicMock()
mock_pgvector.sqlalchemy = MagicMock()
mock_pgvector.sqlalchemy.Vector = MagicMock()

mock_sqlmodel = MagicMock()
class MockSQLModel:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    def __init_subclass__(cls, **kwargs):
        pass

mock_sqlmodel.SQLModel = MockSQLModel
mock_sqlmodel.Field = MagicMock
mock_sqlmodel.Relationship = MagicMock

# Mock other dependencies
mock_loguru = MagicMock()
mock_aiofiles = MagicMock()
mock_langchain_text_splitters = MagicMock()
mock_arq = MagicMock()
mock_redis = MagicMock()

with patch.dict('sys.modules', {
    'pgvector': mock_pgvector, 
    'pgvector.sqlalchemy': mock_pgvector.sqlalchemy,
    'sqlmodel': mock_sqlmodel,
    'loguru': mock_loguru,
    'aiofiles': mock_aiofiles,
    'langchain_text_splitters': mock_langchain_text_splitters,
    'arq': mock_arq,
    'arq.connections': mock_arq.connections,
    'redis': mock_redis,
    'redis.asyncio': mock_redis
}):
    from base.pg.entity import PaperChunk

    async def reproduce():
        print("Starting reproduction...")
        
        paper_id = uuid4()
        chunks = ["test chunk"]
        embeddings = [[0.1] * 1536]
        
        try:
            # Simulate _save_chunks logic
            paper_chunks = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                print(f"Creating chunk {i}")
                # This is where PaperChunk is instantiated
                pc = PaperChunk(
                    paper_id=paper_id,
                    content=chunk,
                    chunk_index=i,
                    embedding=embedding
                )
                paper_chunks.append(pc)
                print("Chunk created successfully")
            
            print("All chunks created")
        except KeyError as e:
            print(f"Caught KeyError: {e}")
        except Exception as e:
            print(f"Caught Exception: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(reproduce())
