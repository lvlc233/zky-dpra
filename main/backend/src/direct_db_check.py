
import asyncio
from sqlalchemy import create_engine, text
import os

def direct_check():
    # Read .env manually
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    db_url = None
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("DATABASE_URL="):
                db_url = line.split("=", 1)[1].strip()
    
    if not db_url:
        print("DATABASE_URL not found in .env")
        return

    print(f"Connecting to: {db_url}")
    engine = create_engine(db_url.replace("+asyncpg", ""))
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, title, analysis_status FROM papers;"))
        rows = result.fetchall()
        print(f"Total Papers in DB: {len(rows)}")
        for row in rows:
            print(f"ID: {row[0]} | Status: {row[1]} | Title: {row[2]}")

if __name__ == "__main__":
    direct_check()
