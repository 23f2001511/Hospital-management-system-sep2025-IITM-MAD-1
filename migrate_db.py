"""One-off migration helper: adds new columns to an existing SQLite database
without destroying data. Safe to run multiple times (skips existing columns).

Usage:
    python migrate_db.py
"""
import sqlite3
import os
import sys

INSTANCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
DB_PATH = os.path.join(INSTANCE_DIR, 'hospital_management.db')

MIGRATIONS = [
    ("user", "is_deleted", "BOOLEAN DEFAULT 0"),
    ("doctor", "max_appointments_per_day", "INTEGER DEFAULT 20"),
    ("appointment", "reassigned_from_doctor_id", "INTEGER REFERENCES doctor(id)"),
    ("appointment", "needs_reassignment", "BOOLEAN DEFAULT 0"),
    ("appointment", "reassigned_at", "DATETIME"),
]

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"No database found at {DB_PATH}. Nothing to migrate "
              "(a fresh DB is created automatically on first run).")
        return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    applied = 0
    for table, column, definition in MIGRATIONS:
        if column_exists(cursor, table, column):
            print(f"  - skip {table}.{column} (already exists)")
        else:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            applied += 1
            print(f"  + added {table}.{column} {definition}")
    conn.commit()
    conn.close()
    print(f"Migration complete. {applied} column(s) added.")

if __name__ == '__main__':
    migrate()
