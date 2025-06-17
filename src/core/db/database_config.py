"""
Centralized Database Configuration for Auditor Helper
Provides consistent database path management across the entire application
"""

from pathlib import Path
import os
import shutil
from typing import List, Optional
import logging

# Get logger for this module
logger = logging.getLogger(__name__)

# Absolute path to the application database (current location)
DATABASE_PATH = Path(__file__).resolve().parent / 'tasks.db'
DATABASE_FILE = str(DATABASE_PATH)

# Legacy database paths to check for migration
LEGACY_DATABASE_PATHS = [
    Path.cwd() / 'tasks.db',  # Root directory
    Path.cwd() / 'data' / 'tasks.db',  # Data directory (if it exists)
]

def get_database_path() -> str:
    """Get the absolute path to the application database"""
    return DATABASE_FILE

def get_database_directory() -> str:
    """Get the directory containing the database"""
    return str(DATABASE_PATH.parent)

def ensure_database_directory() -> None:
    """Ensure the database directory exists"""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

def find_legacy_databases() -> List[Path]:
    """Find any legacy databases that need to be migrated"""
    legacy_dbs = []
    for legacy_path in LEGACY_DATABASE_PATHS:
        if legacy_path.exists() and legacy_path.resolve() != DATABASE_PATH.resolve():
            # Check if it's actually a SQLite database
            if is_sqlite_database(legacy_path):
                legacy_dbs.append(legacy_path)
                logger.info(f"Found legacy database: {legacy_path}")
    return legacy_dbs

def is_sqlite_database(file_path: Path) -> bool:
    """Check if a file is a valid SQLite database"""
    try:
        if not file_path.exists() or file_path.stat().st_size < 100:
            return False
        
        # Check SQLite file header
        with open(file_path, 'rb') as f:
            header = f.read(16)
            return header.startswith(b'SQLite format 3\x00')
    except Exception as e:
        logger.warning(f"Could not check if {file_path} is SQLite database: {e}")
        return False

def backup_database(backup_suffix: str = None) -> Optional[str]:
    """Create a backup of the current database"""
    if not DATABASE_PATH.exists():
        logger.warning("No database to backup")
        return None
    
    try:
        if backup_suffix is None:
            from datetime import datetime
            backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        backup_path = DATABASE_PATH.with_suffix(f'.backup_{backup_suffix}.db')
        shutil.copy2(DATABASE_PATH, backup_path)
        logger.info(f"Database backed up to: {backup_path}")
        return str(backup_path)
    except Exception as e:
        logger.error(f"Failed to backup database: {e}")
        return None

def migrate_legacy_database(legacy_path: Path, create_backup: bool = True) -> bool:
    """Migrate a legacy database to the current location"""
    try:
        logger.info(f"Starting migration of legacy database: {legacy_path}")
        
        # Ensure target directory exists
        ensure_database_directory()
        
        # Create backup of current database if it exists
        if DATABASE_PATH.exists() and create_backup:
            backup_path = backup_database("pre_legacy_migration")
            if backup_path:
                logger.info(f"Current database backed up to: {backup_path}")
        
        # Copy legacy database to current location
        shutil.copy2(legacy_path, DATABASE_PATH)
        logger.info(f"Legacy database migrated from {legacy_path} to {DATABASE_PATH}")
        
        # Create backup of the legacy file before removing it
        legacy_backup = legacy_path.with_suffix(f'.migrated_{legacy_path.stat().st_mtime_ns}.db')
        shutil.copy2(legacy_path, legacy_backup)
        logger.info(f"Legacy database backed up to: {legacy_backup}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to migrate legacy database {legacy_path}: {e}")
        return False

def detect_and_migrate_legacy_databases(auto_migrate: bool = False) -> List[str]:
    """
    Detect legacy databases and optionally migrate them
    
    Args:
        auto_migrate: If True, automatically migrate found databases
        
    Returns:
        List of messages about what was found/done
    """
    messages = []
    legacy_dbs = find_legacy_databases()
    
    if not legacy_dbs:
        messages.append("No legacy databases found")
        return messages
    
    for legacy_db in legacy_dbs:
        message = f"Found legacy database: {legacy_db}"
        messages.append(message)
        logger.info(message)
        
        if auto_migrate:
            if migrate_legacy_database(legacy_db):
                message = f"Successfully migrated: {legacy_db}"
                messages.append(message)
                logger.info(message)
            else:
                message = f"Failed to migrate: {legacy_db}"
                messages.append(message)
                logger.error(message)
        else:
            message = f"Legacy database found but auto-migration disabled: {legacy_db}"
            messages.append(message)
            logger.info(message)
    
    return messages

def get_database_info() -> dict:
    """Get information about the current database"""
    info = {
        'database_path': DATABASE_FILE,
        'database_exists': DATABASE_PATH.exists(),
        'database_size_bytes': 0,
        'database_size_mb': 0,
        'legacy_databases_found': []
    }
    
    if DATABASE_PATH.exists():
        stat = DATABASE_PATH.stat()
        info['database_size_bytes'] = stat.st_size
        info['database_size_mb'] = stat.st_size / (1024 * 1024)
        info['last_modified'] = stat.st_mtime
    
    # Check for legacy databases
    legacy_dbs = find_legacy_databases()
    info['legacy_databases_found'] = [str(db) for db in legacy_dbs]
    
    return info

# Backward compatibility - export the main constants
DB_FILE = DATABASE_FILE
DB_PATH = DATABASE_PATH 