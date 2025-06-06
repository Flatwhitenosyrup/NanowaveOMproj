import sqlite3
import json
import socket

# Load config
with open("config_local.json") as f:
    config = json.load(f)

DB_PATH = config["prod_db_path"] if config["use_production_db"] else config["test_db_path"]

def get_connection():
    return sqlite3.connect(DB_PATH)

def add_image(file_path, tags: dict):
    conn = get_connection()
    cur = conn.cursor()
    pc_name = socket.gethostname()

    cur.execute("INSERT INTO images (file_path, pc_name) VALUES (?, ?)",
                (file_path, pc_name))
    image_id = cur.lastrowid

    for category, value in tags.items():
        cur.execute("INSERT INTO tags (image_id, tag_category, tag_value) VALUES (?, ?, ?)",
                    (image_id, category, value))

    conn.commit()
    conn.close()
    print(f"Inserted image: {file_path} with tags: {tags}")
