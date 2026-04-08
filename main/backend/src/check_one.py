
import asyncio
from sqlalchemy import create_engine, text
import os

def check_one():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    db_url = None
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("DATABASE_URL="):
                db_url = line.split("=", 1)[1].strip()
    
    if not db_url: return

    engine = create_engine(db_url.replace("+asyncpg", ""))
    pid = "a6e27c30-7507-44d9-8c18-daa75f5b42fd"
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT * FROM papers WHERE id = '{pid}';"))
        row = result.fetchone()
        if row:
            print(f"ROW: {row}")
            # Try to print title and authors specifically
            idx_title = -1
            idx_authors = -1
            for i, col in enumerate(result.keys()):
                if col == "title": idx_title = i
                if col == "authors": idx_authors = i
            
            if idx_title != -1: print(f"TITLE: {repr(row[idx_title])}")
            if idx_authors != -1: print(f"AUTHORS: {repr(row[idx_authors])}")
        else:
            print("Paper not found")

if __name__ == "__main__":
    check_one()
