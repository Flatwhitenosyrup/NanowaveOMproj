import sqlite3
import json

# Load config
with open("config_local.json") as f:
    config = json.load(f)

db_path = config["test_db_path"] if not config["use_production_db"] else config["prod_db_path"]

def create_schema(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT NOT NULL,
        pc_name TEXT,
        added_time DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_id INTEGER,
        tag_category TEXT,
        tag_value TEXT,
        FOREIGN KEY(image_id) REFERENCES images(id)
    )
    """)

    conn.commit()
    conn.close()
    print(f"Database schema initialized at: {db_path}")

if __name__ == "__main__":
    create_schema(db_path)
