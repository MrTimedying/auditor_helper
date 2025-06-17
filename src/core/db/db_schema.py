import sqlite3
import os
from .database_config import DATABASE_FILE, ensure_database_directory, detect_and_migrate_legacy_databases

DB_FILE = DATABASE_FILE

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

def migrate_tasks_table_columns():
    """Add missing columns to tasks table for legacy database compatibility"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Check if the columns exist
    c.execute("PRAGMA table_info(tasks)")
    columns = [column[1] for column in c.fetchall()]
    
    # Define all columns that should exist in the modern tasks table
    required_columns = {
        "feedback": "TEXT",
        "bonus_paid": "INTEGER DEFAULT 0",
        "audited_timestamp": "DATETIME"
    }
    
    for column_name, column_def in required_columns.items():
        if column_name not in columns:
            print(f"Adding {column_name} column to tasks table...")
            try:
                c.execute(f"ALTER TABLE tasks ADD COLUMN {column_name} {column_def}")
                print(f"Added {column_name} column successfully")
            except Exception as e:
                print(f"Error adding {column_name} column: {e}")
    
    # Also ensure score column is INTEGER (legacy might have REAL)
    if "score" in columns:
        # Check current type
        c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='tasks'")
        table_sql = c.fetchone()[0]
        if "score REAL" in table_sql:
            print("Note: score column is REAL type (legacy), but application expects INTEGER")
    
    conn.commit()
    conn.close()

def migrate_feedback_files_table():
    """Create feedback_files table if it doesn't exist"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Check if table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='feedback_files'")
    table_exists = c.fetchone() is not None
    
    if not table_exists:
        print("Creating feedback_files table...")
        try:
            c.execute(
                """CREATE TABLE feedback_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    content TEXT,
                    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
                )"""
            )
            print("Created feedback_files table successfully")
        except Exception as e:
            print(f"Error creating feedback_files table: {e}")
    
    conn.commit()
    conn.close()

def migrate_week_settings():
    """Add week-specific settings columns to weeks table"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Check if the columns exist
    c.execute("PRAGMA table_info(weeks)")
    columns = [column[1] for column in c.fetchall()]
    
    week_settings_columns = {
        "week_start_day": "INTEGER DEFAULT 1",  # Monday = 1, Sunday = 7
        "week_start_hour": "INTEGER DEFAULT 0",  # 0-23
        "week_end_day": "INTEGER DEFAULT 7",    # Sunday = 7
        "week_end_hour": "INTEGER DEFAULT 23",  # 0-23
        "is_custom_duration": "INTEGER DEFAULT 0",  # Boolean flag
        "is_bonus_week": "INTEGER DEFAULT 0"    # Boolean flag for bonus weeks
    }
    
    for column_name, column_def in week_settings_columns.items():
        if column_name not in columns:
            print(f"Adding {column_name} column to weeks table...")
            try:
                c.execute(f"ALTER TABLE weeks ADD COLUMN {column_name} {column_def}")
                print(f"Added {column_name} column successfully")
            except Exception as e:
                print(f"Error adding {column_name} column: {e}")
    
    conn.commit()
    conn.close()

def migrate_week_bonus_settings():
    """Add week-specific bonus settings columns to weeks table"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Check if the columns exist
    c.execute("PRAGMA table_info(weeks)")
    columns = [column[1] for column in c.fetchall()]
    
    week_bonus_columns = {
        "week_specific_bonus_payrate": "REAL DEFAULT NULL",
        "week_specific_bonus_start_day": "INTEGER DEFAULT NULL",
        "week_specific_bonus_start_time": "TEXT DEFAULT NULL",
        "week_specific_bonus_end_day": "INTEGER DEFAULT NULL", 
        "week_specific_bonus_end_time": "TEXT DEFAULT NULL",
        "week_specific_enable_task_bonus": "INTEGER DEFAULT NULL",
        "week_specific_bonus_task_threshold": "INTEGER DEFAULT NULL",
        "week_specific_bonus_additional_amount": "REAL DEFAULT NULL",
        "use_global_bonus_settings": "INTEGER DEFAULT 1"
    }
    
    for column_name, column_def in week_bonus_columns.items():
        if column_name not in columns:
            print(f"Adding {column_name} column to weeks table...")
            try:
                c.execute(f"ALTER TABLE weeks ADD COLUMN {column_name} {column_def}")
                print(f"Added {column_name} column successfully")
            except Exception as e:
                print(f"Error adding {column_name} column: {e}")
    
    conn.commit()
    conn.close()

def migrate_app_settings_table():
    """Create app_settings table for global application settings"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Check if table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='app_settings'")
    table_exists = c.fetchone() is not None
    
    if not table_exists:
        print("Creating app_settings table...")
        try:
            c.execute(
                """CREATE TABLE app_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT UNIQUE NOT NULL,
                    setting_value TEXT,
                    setting_type TEXT DEFAULT 'string'
                )"""
            )
            
            # Insert default bonus settings
            default_settings = [
                ('bonus_start_day', '0', 'integer'),          # Monday
                ('bonus_end_day', '6', 'integer'),            # Sunday
                ('bonus_start_time', '00:00', 'time'),
                ('bonus_end_time', '23:59', 'time'),
                ('bonus_payrate', '0.0', 'float'),            # Modified payrate for bonus period
                ('enable_task_bonus', 'false', 'boolean'),    # Enable task-based bonus
                ('bonus_task_threshold', '20', 'integer'),    # Number of tasks needed for bonus
                ('bonus_additional_amount', '0.0', 'float')   # Additional bonus amount
            ]
            
            for key, value, setting_type in default_settings:
                c.execute(
                    "INSERT OR IGNORE INTO app_settings (setting_key, setting_value, setting_type) VALUES (?, ?, ?)",
                    (key, value, setting_type)
                )
            
            print("Created app_settings table with default bonus settings")
        except Exception as e:
            print(f"Error creating app_settings table: {e}")
    
    conn.commit()
    conn.close()

def migrate_office_hours_settings():
    """Add office hours settings columns to weeks table"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Check if the columns exist
    c.execute("PRAGMA table_info(weeks)")
    columns = [column[1] for column in c.fetchall()]

    office_hours_columns = {
        "office_hour_count": "INTEGER DEFAULT 0",
        "office_hour_payrate": "REAL DEFAULT NULL",
        "office_hour_session_duration_minutes": "INTEGER DEFAULT NULL",
        "use_global_office_hours_settings": "INTEGER DEFAULT 1"
    }

    for column_name, column_def in office_hours_columns.items():
        if column_name not in columns:
            print(f"Adding {column_name} column to weeks table...")
            try:
                c.execute(f"ALTER TABLE weeks ADD COLUMN {column_name} {column_def}")
                print(f"Added {column_name} column successfully")
            except Exception as e:
                print(f"Error adding {column_name} column: {e}")

    conn.commit()
    conn.close()

def get_app_setting(setting_key, default_value=None):
    """Get an application setting value"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    try:
        c.execute("SELECT setting_value, setting_type FROM app_settings WHERE setting_key=?", (setting_key,))
        result = c.fetchone()
        
        if result:
            value, setting_type = result
            # Convert value based on type
            if setting_type == 'integer':
                return int(value)
            elif setting_type == 'float':
                return float(value)
            elif setting_type == 'boolean':
                return value.lower() in ('true', '1', 'yes')
            else:
                return value
        else:
            return default_value
    except Exception as e:
        print(f"Error getting app setting {setting_key}: {e}")
        return default_value
    finally:
        conn.close()

def set_app_setting(setting_key, setting_value, setting_type='string'):
    """Set an application setting value"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    try:
        # Convert value to string for storage
        if setting_type == 'boolean':
            value_str = str(setting_value).lower()
        else:
            value_str = str(setting_value)
        
        c.execute(
            """INSERT OR REPLACE INTO app_settings (setting_key, setting_value, setting_type) 
               VALUES (?, ?, ?)""",
            (setting_key, value_str, setting_type)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error setting app setting {setting_key}: {e}")
        return False
    finally:
        conn.close()

def run_all_migrations():
    """Run all database migrations in the correct order"""
    # Ensure database directory exists
    ensure_database_directory()
    
    # Check for and handle legacy databases
    print("Checking for legacy databases...")
    migration_messages = detect_and_migrate_legacy_databases(auto_migrate=True)
    for message in migration_messages:
        print(f"Legacy DB: {message}")
    
    # Run all migrations in order
    init_db()
    migrate_time_columns()
    migrate_tasks_table_columns()
    migrate_feedback_files_table()
    migrate_week_settings()
    migrate_week_bonus_settings()
    migrate_app_settings_table()
    migrate_office_hours_settings()

if __name__ == "__main__":
    run_all_migrations()