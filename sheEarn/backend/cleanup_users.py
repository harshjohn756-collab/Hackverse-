import sqlite3

def delete_test_users():
    conn = sqlite3.connect('instance/sheEarn.db')
    c = conn.cursor()
    
    # Delete all users that have an email (except the admin account)
    c.execute('DELETE FROM users WHERE email IS NOT NULL AND email != "admin@sheearn.com"')
    deleted_count = c.rowcount
    
    conn.commit()
    conn.close()
    print(f"Successfully deleted {deleted_count} test users from the database.")

if __name__ == "__main__":
    delete_test_users()
