
import asyncio
from sqlalchemy import create_engine, text
import os

def check_pending():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    db_url = None
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("DATABASE_URL="):
                db_url = line.split("=", 1)[1].strip()
    
    if not db_url: return

    engine = create_engine(db_url.replace("+asyncpg", ""))
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, title, analysis_status, file_key FROM papers WHERE analysis_status = 'pending';"))
        for row in result:
            print(f"ID: {row[0]} | Title: {repr(row[1])} | Status: {row[2]} | File: {row[3]}")

if __name__ == "__main__":
    check_pending()
