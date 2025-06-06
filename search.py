import sqlite3
import json
import os
import datetime
import subprocess

# Load from config
with open("config_local.json") as f:
    config = json.load(f)

db_path = config["test_db_path"]

def get_connection():
    return sqlite3.connect(db_path)

def list_tag_categories():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT tag_category FROM tags")
    categories = [row[0] for row in cur.fetchall()]
    conn.close()
    return categories

def list_values_for_category(category):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT tag_value FROM tags WHERE tag_category = ?", (category,))
    values = [row[0] for row in cur.fetchall()]
    conn.close()
    return values

def group_by_tag(tag_category):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT tag_value, COUNT(DISTINCT image_id)
        FROM tags
        WHERE tag_category = ?
        GROUP BY tag_value
        ORDER BY COUNT(*) DESC
    """, (tag_category,))
    rows = cur.fetchall()
    conn.close()
    print(f"\n📊 Image counts grouped by '{tag_category}':")
    for val, count in rows:
        print(f"  - {val}: {count} image(s)")

def get_all_tags_for_image(cur, image_id):
    cur.execute("SELECT tag_category, tag_value FROM tags WHERE image_id = ?", (image_id,))
    return {cat: val for cat, val in cur.fetchall()}

def search_images_by_tags(filters, pc_name=None, date_after=None):
    conn = get_connection()
    cur = conn.cursor()

    # Build dynamic WHERE clause
    conditions = []
    params = []

    for tag_cat, tag_val in filters.items():
        conditions.append(f"""
            EXISTS (
                SELECT 1 FROM tags t
                WHERE t.image_id = images.id AND t.tag_category = ? AND t.tag_value = ?
            )
        """)
        params.extend([tag_cat, tag_val])

    if pc_name:
        conditions.append("images.pc_name = ?")
        params.append(pc_name)

    if date_after:
        conditions.append("images.added_time >= ?")
        params.append(date_after)

    where_clause = " AND ".join(conditions)
    query = f"""
        SELECT DISTINCT images.id, images.file_path, images.pc_name, images.added_time
        FROM images
        WHERE {where_clause}
        ORDER BY images.added_time DESC
    """

    cur.execute(query, params)
    results = cur.fetchall()

    if not results:
        print("\n❌ No images found.")
    else:
        print(f"\n✅ Found {len(results)} image(s):")
        for row in results:
            image_id, path, pc, added_time = row
            print(f"\n🔹 ID {image_id} | {path} | {pc} | {added_time}")
            tags = get_all_tags_for_image(cur, image_id)
            for cat, val in tags.items():
                print(f"   - {cat}: {val}")

            open_choice = input("   Open this image? [y/N]: ").strip().lower()
            if open_choice == 'y':
                if os.name == 'nt':  # Windows
                    subprocess.run(['start', '', path], shell=True)
                elif os.name == 'posix':  # macOS/Linux
                    subprocess.run(['open', path])
    conn.close()

def prompt_filters():
    raw = input("\nEnter tag filters as key=value pairs (comma separated, e.g. material=WS2,thickness=monolayer): ").strip()
    pairs = [item.strip() for item in raw.split(',') if '=' in item]
    return {k.strip(): v.strip() for k, v in (p.split('=') for p in pairs)}

def main():
    print("🔍 Enhanced Image Search Tool")
    print("-----------------------------")

    while True:
        print("\nOptions:")
        print("1. Search images by tag filters")
        print("2. List all tag categories")
        print("3. List values for a category")
        print("4. Show image count by tag value")
        print("5. Quit")

        choice = input("\nChoose an option (1-5): ").strip()

        if choice == '1':
            filters = prompt_filters()
            pc_filter = input("Filter by PC name? (leave blank to skip): ").strip()
            date_filter = input("Filter by date after (YYYY-MM-DD)? (leave blank to skip): ").strip()
            if date_filter:
                try:
                    datetime.datetime.strptime(date_filter, '%Y-%m-%d')
                except ValueError:
                    print("Invalid date format, skipping date filter.")
                    date_filter = None
            search_images_by_tags(filters, pc_filter or None, date_filter or None)

        elif choice == '2':
            categories = list_tag_categories()
            print("\n📂 Available Tag Categories:")
            for cat in categories:
                print(f"  - {cat}")

        elif choice == '3':
            category = input("Enter category name: ").strip()
            values = list_values_for_category(category)
            print(f"\n🔖 Values for category '{category}':")
            for val in values:
                print(f"  - {val}")

        elif choice == '4':
            category = input("Group by which tag category? ").strip()
            group_by_tag(category)

        elif choice == '5':
            print("Exiting.")
            break

        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
