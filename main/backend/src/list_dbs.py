
import asyncio
from sqlalchemy import create_engine, text
from base.config import settings

def list_dbs():
    # Use synchronous engine for listing DBs
    url = settings.database_url.replace("+asyncpg", "")
    engine = create_engine(url.rsplit("/", 1)[0] + "/postgres")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT datname FROM pg_database WHERE datistemplate = false;"))
        for row in result:
            print(f"DB: {row[0]}")

if __name__ == "__main__":
    list_dbs()
