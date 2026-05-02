"""Migration: add weekly-plan-sync columns to existing SQLite databases.

Run this once on existing deployments that already have a sql_app.db:

    python scripts/migrate_weekly_plan_sync.py

New deployments are unaffected -- `Base.metadata.create_all()` handles
these columns automatically.
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "sql_app.db"

COLUMNS = [
    ("weekly_plan_days", "completed", "BOOLEAN NOT NULL DEFAULT 0"),
    ("weekly_plan_days", "completed_at", "DATETIME"),
    ("intake_records", "source_plan_day_id", "INTEGER"),
]


def column_exists(cursor: sqlite3.Cursor, table: str, column: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def main() -> None:
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH} -- nothing to migrate.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    for table, column, col_def in COLUMNS:
        if column_exists(cursor, table, column):
            print(f"  [skip] {table}.{column} already exists")
            continue
        sql = f"ALTER TABLE {table} ADD COLUMN {column} {col_def}"
        print(f"  [migrate] {sql}")
        cursor.execute(sql)

    conn.commit()
    conn.close()
    print("Migration complete.")


if __name__ == "__main__":
    main()
