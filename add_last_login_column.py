import sqlite3
import os

db_path = os.path.join('instance', 'dev.db')

def migrate():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}. Skipping migration.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Adding last_login column to users table...")

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN last_login DATETIME")
        print("Added last_login to users table.")
    except sqlite3.OperationalError:
        print("Column last_login already exists or error.")

    conn.commit()
    conn.close()
    print("Migration completed.")

if __name__ == "__main__":
    migrate()
