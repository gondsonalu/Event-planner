import sqlite3
import os

db_path = os.path.join('instance', 'dev.db')

def migrate():
    if not os.path.exists('instance'):
        os.makedirs('instance')
        print("Created instance directory.")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Migrating database...")

    # 1. Add columns to events table
    try:
        cursor.execute("ALTER TABLE events ADD COLUMN escalated_to_admin BOOLEAN DEFAULT 0 NOT NULL")
        print("Added escalated_to_admin to events table.")
    except sqlite3.OperationalError:
        print("Column escalated_to_admin already exists or error.")

    try:
        cursor.execute("ALTER TABLE events ADD COLUMN escalation_reason TEXT")
        print("Added escalation_reason to events table.")
    except sqlite3.OperationalError:
        print("Column escalation_reason already exists or error.")

    # 2. Add previous_hash to audit_logs table
    try:
        cursor.execute("ALTER TABLE audit_logs ADD COLUMN previous_hash VARCHAR(64)")
        print("Added previous_hash to audit_logs table.")
    except sqlite3.OperationalError:
        print("Column previous_hash already exists or error.")

    # 3. Create system_configuration table
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_configuration (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key VARCHAR(50) UNIQUE NOT NULL,
                value TEXT,
                description VARCHAR(255)
            )
        ''')
        print("Created system_configuration table.")
    except sqlite3.OperationalError as e:
        print(f"Error creating system_configuration table: {e}")

    # 4. Insert default config values
    configs = [
        ('maintenance_mode', 'False', 'Enable or disable system-wide maintenance mode'),
        ('maintenance_message', 'The system is currently undergoing scheduled maintenance. Please check back later.', 'Message shown to users during maintenance mode'),
        ('last_verified_hash', '', 'The hash of the last verified audit trail state')
    ]
    
    for key, value, desc in configs:
        try:
            cursor.execute("INSERT OR IGNORE INTO system_configuration (key, value, description) VALUES (?, ?, ?)", (key, value, desc))
        except sqlite3.Error as e:
            print(f"Error inserting config {key}: {e}")

    conn.commit()
    conn.close()
    print("Migration completed.")

if __name__ == "__main__":
    migrate()
