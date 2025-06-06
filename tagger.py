import os
import json
import socket
import sqlite3
from datetime import datetime

# === Load Config ===
CONFIG_PATH = "E:/NanowaveOMproj/config_local.json"
TAGS_LIST_PATH = "E:/NanowaveOMproj/tags_list.json"

with open(CONFIG_PATH) as f:
    config = json.load(f)

DB_PATH = config["prod_db_path"] if config["use_production_db"] else config["test_db_path"]

if os.path.exists(TAGS_LIST_PATH):
    with open(TAGS_LIST_PATH, "r") as f:
        TAGS_DICT = json.load(f)
else:
    TAGS_DICT = {}

# === DB Access ===
def get_connection():
    return sqlite3.connect(DB_PATH)

def image_exists(file_path):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM images WHERE file_path = ?", (file_path,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def get_tags_for_image(image_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT tag_category, tag_value FROM tags WHERE image_id = ?", (image_id,))
    rows = cur.fetchall()
    conn.close()
    return {cat: val for cat, val in rows}

def insert_image_with_tags(file_path, tags):
    conn = get_connection()
    cur = conn.cursor()
    pc_name = socket.gethostname()
    cur.execute("INSERT INTO images (file_path, pc_name) VALUES (?, ?)", (file_path, pc_name))
    image_id = cur.lastrowid
    for cat, val in tags.items():
        cur.execute("INSERT INTO tags (image_id, tag_category, tag_value) VALUES (?, ?, ?)",
                    (image_id, cat, val))
    conn.commit()
    conn.close()

# === Tag Input ===
def prompt_tags(last_tags=None):
    print("📝 Enter tag values (press Enter to reuse previous):")
    tags = {}
    fields = ['material', 'thickness', 'used', 'deviceID', 'note', 'operator']
    for key in fields:
        default = f"[{last_tags[key]}]" if last_tags and key in last_tags else ""
        val = input(f"{key.capitalize()} {default}: ").strip()
        if not val and last_tags:
            val = last_tags.get(key, "")
        if val:
            if key in TAGS_DICT and val not in TAGS_DICT[key]:
                print(f"⚠️  '{val}' not in allowed values for '{key}': {TAGS_DICT[key]}")
            tags[key] = val
    return tags

# === Tag Logic ===
def tag_image(file_path, last_tags=None):
    if not os.path.isfile(file_path):
        print(f"❌ File not found: {file_path}")
        return last_tags

    existing_id = image_exists(file_path)
    if existing_id:
        current_tags = get_tags_for_image(existing_id)
        print(f"⚠️  This image is already in the database. Existing tags:")
        for k, v in current_tags.items():
            print(f"  - {k}: {v}")
        action = input("Overwrite tags? [y/N]: ").strip().lower()
        if action != 'y':
            print("⏩ Skipping image.")
            return last_tags

    tags = prompt_tags(last_tags)

    print("\n🧾 Tag Summary:")
    print(f"📁 File: {file_path}")
    for k, v in tags.items():
        print(f"  - {k}: {v}")
    confirm = input("Save these tags? [Y/n]: ").strip().lower()
    if confirm == 'n':
        print("❌ Tagging canceled.")
        return last_tags

    try:
        insert_image_with_tags(file_path, tags)
        print("✅ Tags saved successfully.")
        return tags
    except Exception as e:
        print(f"❌ Failed to save tags: {e}")
        return last_tags

# === Batch Mode ===
def run_batch():
    folder = input("Enter folder path with images to tag: ").strip()
    if not os.path.isdir(folder):
        print("❌ Folder does not exist.")
        return

    files = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.png'))]
    if not files:
        print("⚠️ No image files found in folder.")
        return

    last_tags = {}
    for fname in files:
        print(f"\n🖼️ Tagging: {fname}")
        full_path = os.path.join(folder, fname)
        last_tags = tag_image(full_path, last_tags)

if __name__ == "__main__":
    print("📷 2D Image Tagger")
    print("------------------")
    run_batch()
