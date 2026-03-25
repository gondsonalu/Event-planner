import sqlite3
import os

def fix_roles():
    db_path = os.path.join('instance', 'dev.db')
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Checking current users and roles...")
    cursor.execute("SELECT id, username, role FROM users")
    users = cursor.fetchall()
    
    print(f"{'ID':<5} | {'Username':<15} | {'Old Role':<20} | {'New Role':<20}")
    print("-" * 65)

    updates = []
    for user_id, username, role in users:
        role_lower = role.lower()
        new_role = role # Default
        
        if any(x in role_lower for x in ["student"]):
            new_role = 'Student'
        elif any(x in role_lower for x in ["faculty"]):
            new_role = 'Faculty'
        elif any(x in role_lower for x in ["head", "dept", "hod"]):
            new_role = 'Department Head'
        elif any(x in role_lower for x in ["admin", "administrator"]):
            new_role = 'Admin'
        
        if new_role != role:
            updates.append((new_role, user_id))
            print(f"{user_id:<5} | {username:<15} | {role:<20} | {new_role:<20} (CHANGED)")
        else:
            print(f"{user_id:<5} | {username:<15} | {role:<20} | {new_role:<20}")

    if updates:
        print(f"\nApplying {len(updates)} updates...")
        cursor.executemany("UPDATE users SET role = ? WHERE id = ?", updates)
        conn.commit()
        print("Database updated successfully.")
    else:
        print("\nNo role updates needed.")

    conn.close()

if __name__ == "__main__":
    fix_roles()
