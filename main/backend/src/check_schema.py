
import asyncio
from sqlalchemy import create_engine, text
import os

def check_schema():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    db_url = None
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("DATABASE_URL="):
                db_url = line.split("=", 1)[1].strip()
    
    if not db_url: return

    engine = create_engine(db_url.replace("+asyncpg", ""))
    with engine.connect() as conn:
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'jobs';"))
        for row in result:
            print(f"Col: {row[0]}")
            
        print("\nDATA SAMPLE (Last 3):")
        result = conn.execute(text("SELECT * FROM jobs ORDER BY created_at DESC LIMIT 3;"))
        for row in result:
            print(row)

if __name__ == "__main__":
    check_schema()
