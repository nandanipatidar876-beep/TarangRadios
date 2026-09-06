import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db

conn = get_db()
cursor = conn.cursor()
cursor.execute("SELECT id, username, name FROM admins")
rows = cursor.fetchall()
print("ADMIN USERS:")
for r in rows:
    print(r)
