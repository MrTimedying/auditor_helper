import sqlite3
import os

DB_FILE = "tasks.db"

def backup_db():
    """Create a backup of the existing database if it exists"""
    if os.path.exists(DB_FILE):
        backup_file = f"{DB_FILE}.bak"
        i = 1
        while os.path.exists(backup_file):
            backup_file = f"{DB_FILE}.bak.{i}"
            i += 1
        
        try:
            with open(DB_FILE, 'rb') as src, open(backup_file, 'wb') as dst:
                dst.write(src.read())
            print(f"Created database backup: {backup_file}")
        except Exception as e:
            print(f"Failed to create backup: {e}")

def init_db():
    """Initialize the database with the required tables"""
    
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Create weeks table
    c.execute(
        """CREATE TABLE IF NOT EXISTS weeks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_label TEXT UNIQUE NOT NULL
        )"""
    )
    
    # Check if tasks table exists and if it has the old schema
    c.execute("PRAGMA table_info(tasks)")
    columns = [column[1] for column in c.fetchall()]
    
    # If the tasks table exists but has the old schema, rename it
    if columns and "title" in columns and "status" in columns:
        print("Migrating from old schema...")
        c.execute("ALTER TABLE tasks RENAME TO tasks_old")
        
        # Create new tasks table
        create_tasks_table(c)
        
        # Migrate data from old table (only week_id is preserved)
        c.execute("SELECT id, week_id FROM tasks_old")
        old_tasks = c.fetchall()
        for task_id, week_id in old_tasks:
            c.execute(
                "INSERT INTO tasks (week_id) VALUES (?)",
                (week_id,)
            )
        
        print(f"Migrated {len(old_tasks)} tasks to new schema")
    else:
        # Just create the table if it doesn't exist or already has new schema
        create_tasks_table(c)
        
        # Check if we need to add the bonus_paid column to an existing table
        if columns and "bonus_paid" not in columns:
            print("Adding bonus_paid column to existing tasks table...")
            try:
                c.execute("ALTER TABLE tasks ADD COLUMN bonus_paid INTEGER DEFAULT 0")
                print("Added bonus_paid column successfully")
            except Exception as e:
                print(f"Error adding bonus_paid column: {e}")
    
    # Create the feedback_files table for storing markdown files
    c.execute(
        """CREATE TABLE IF NOT EXISTS feedback_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            content TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
        )"""
    )
    
    conn.commit()
    conn.close()

def create_tasks_table(cursor):
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_id INTEGER NOT NULL,
            attempt_id TEXT,
            duration TEXT DEFAULT '00:00:00',
            project_id TEXT,
            project_name TEXT,
            operation_id TEXT,
            time_limit TEXT DEFAULT '00:00:00',
            date_audited TEXT,
            score INTEGER DEFAULT 0,
            feedback TEXT,
            locale TEXT,
            bonus_paid INTEGER DEFAULT 0,
            time_begin TEXT,
            time_end TEXT,
            FOREIGN KEY (week_id) REFERENCES weeks(id) ON DELETE CASCADE
        )"""
    )

def migrate_time_columns():
    """Add time_begin and time_end columns if they don't exist"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Check if the columns exist
    c.execute("PRAGMA table_info(tasks)")
    columns = [column[1] for column in c.fetchall()]
    
    if "time_begin" not in columns:
        print("Adding time_begin column to tasks table...")
        try:
            c.execute("ALTER TABLE tasks ADD COLUMN time_begin TEXT")
            print("Added time_begin column successfully")
        except Exception as e:
            print(f"Error adding time_begin column: {e}")
    
    if "time_end" not in columns:
        print("Adding time_end column to tasks table...")
        try:
            c.execute("ALTER TABLE tasks ADD COLUMN time_end TEXT")
            print("Added time_end column successfully")
        except Exception as e:
            print(f"Error adding time_end column: {e}")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    migrate_time_columns() 