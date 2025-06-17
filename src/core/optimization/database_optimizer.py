"""
Database Optimization System for Auditor Helper
Optimizes database initialization, connections, and migrations for faster startup
"""

import sqlite3
import time
import threading
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
from contextlib import contextmanager
from .startup_profiler import profile_phase
from ..db.database_config import DATABASE_FILE, ensure_database_directory, detect_and_migrate_legacy_databases

class OptimizedDatabaseManager:
    """
    Optimized database manager that provides:
    - Fast connection pooling
    - Lazy migration execution
    - Optimized database settings
    - Connection reuse
    """
    
    def __init__(self, db_path: str = None):
        """Initialize optimized database manager"""
        if db_path is None:
            db_path = DATABASE_FILE
        self.db_path = Path(db_path).resolve()
        self.connection_pool = []
        self.pool_lock = threading.Lock()
        self.max_pool_size = 5
        self.migrations_run = False
        self._setup_optimized_database()
    
    def _setup_optimized_database(self):
        """Set up database with optimized settings"""
        with profile_phase("Database Setup", {"db_path": str(self.db_path)}):
            # Ensure database directory exists
            ensure_database_directory()
            
            # Check for legacy databases and migrate them
            migration_messages = detect_and_migrate_legacy_databases(auto_migrate=True)
            legacy_migrated = any("Successfully migrated" in msg for msg in migration_messages)
            for message in migration_messages:
                print(f"Optimized DB Setup - Legacy DB: {message}")
            
            # If we migrated a legacy database, we need to run full migrations
            if legacy_migrated:
                print("Legacy database migrated - running full schema migrations...")
                from ..db.db_schema import run_all_migrations
                run_all_migrations()
                print("Full schema migrations completed after legacy migration")
            
            # Create initial connection with optimized settings
            conn = self._create_optimized_connection()
            
            # Apply performance optimizations
            self._apply_performance_settings(conn)
            
            # Return connection to pool
            self._return_connection(conn)
    
    def _create_optimized_connection(self) -> sqlite3.Connection:
        """Create a new database connection with optimized settings"""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,
            check_same_thread=False,
            isolation_level=None  # Autocommit mode for better performance
        )
        
        # Enable row factory for better data access
        conn.row_factory = sqlite3.Row
        
        return conn
    
    def _apply_performance_settings(self, conn: sqlite3.Connection):
        """Apply performance optimization settings to connection"""
        with profile_phase("Database Performance Settings"):
            # Performance optimizations
            performance_settings = [
                "PRAGMA journal_mode = WAL",           # Write-Ahead Logging for better concurrency
                "PRAGMA synchronous = NORMAL",         # Balance between safety and speed
                "PRAGMA cache_size = -64000",          # 64MB cache
                "PRAGMA temp_store = MEMORY",          # Store temp tables in memory
                "PRAGMA mmap_size = 268435456",        # 256MB memory-mapped I/O
                "PRAGMA optimize",                     # Optimize database
                "PRAGMA analysis_limit = 1000",       # Limit analysis for faster startup
                "PRAGMA threads = 4"                   # Use multiple threads
            ]
            
            for setting in performance_settings:
                try:
                    conn.execute(setting)
                except sqlite3.Error:
                    # Some settings might not be available in all SQLite versions
                    pass
    
    @contextmanager
    def get_connection(self):
        """Get an optimized database connection from the pool"""
        conn = self._get_connection()
        try:
            yield conn
        finally:
            self._return_connection(conn)
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a connection from the pool or create a new one"""
        with self.pool_lock:
            if self.connection_pool:
                return self.connection_pool.pop()
            else:
                return self._create_optimized_connection()
    
    def _return_connection(self, conn: sqlite3.Connection):
        """Return a connection to the pool"""
        with self.pool_lock:
            if len(self.connection_pool) < self.max_pool_size:
                self.connection_pool.append(conn)
            else:
                conn.close()
    
    def run_lazy_migrations(self, migration_functions: List[Callable]):
        """Run database migrations lazily (only when needed)"""
        if self.migrations_run:
            return
        
        with profile_phase("Database Migrations", {"count": len(migration_functions)}):
            with self.get_connection() as conn:
                for migration_func in migration_functions:
                    try:
                        migration_func(conn)
                    except Exception as e:
                        print(f"Migration warning: {e}")
                        # Continue with other migrations
                
                self.migrations_run = True
    
    def execute_optimized_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute a query with optimizations"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()
    
    def execute_optimized_update(self, query: str, params: tuple = ()) -> int:
        """Execute an update/insert query with optimizations"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.rowcount
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database performance statistics"""
        with self.get_connection() as conn:
            stats = {}
            
            # Get database size
            stats["db_size_mb"] = self.db_path.stat().st_size / 1024 / 1024
            
            # Get table counts
            tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
            tables = [row[0] for row in conn.execute(tables_query)]
            stats["table_count"] = len(tables)
            
            # Get cache statistics
            try:
                cache_stats = conn.execute("PRAGMA cache_size").fetchone()
                stats["cache_size"] = cache_stats[0] if cache_stats else 0
            except:
                stats["cache_size"] = 0
            
            # Connection pool stats
            stats["pool_size"] = len(self.connection_pool)
            stats["max_pool_size"] = self.max_pool_size
            
            return stats

class FastMigrationRunner:
    """
    Fast migration runner that optimizes database schema updates
    """
    
    def __init__(self, db_manager: OptimizedDatabaseManager):
        self.db_manager = db_manager
        self.completed_migrations = set()
    
    def add_migration(self, name: str, migration_func: Callable):
        """Add a migration to be run"""
        if name not in self.completed_migrations:
            with profile_phase(f"Migration: {name}"):
                try:
                    with self.db_manager.get_connection() as conn:
                        migration_func(conn)
                    self.completed_migrations.add(name)
                except Exception as e:
                    print(f"Migration '{name}' failed: {e}")
    
    def run_essential_migrations_only(self):
        """Run only essential migrations for startup"""
        with profile_phase("Essential Migrations"):
            essential_migrations = [
                ("create_tables", self._create_essential_tables),
                ("create_indexes", self._create_essential_indexes)
            ]
            
            for name, migration_func in essential_migrations:
                self.add_migration(name, migration_func)
    
    def _create_essential_tables(self, conn: sqlite3.Connection):
        """Create only essential tables needed for startup"""
        essential_tables = [
            """CREATE TABLE IF NOT EXISTS weeks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_label TEXT UNIQUE NOT NULL,
                is_bonus_week INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            """CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_id INTEGER NOT NULL,
                attempt_id TEXT,
                duration TEXT,
                project_id TEXT,
                project_name TEXT,
                operation_id TEXT,
                time_limit TEXT,
                date_audited TEXT,
                score REAL,
                locale TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (week_id) REFERENCES weeks (id) ON DELETE CASCADE
            )"""
        ]
        
        for table_sql in essential_tables:
            conn.execute(table_sql)
    
    def _create_essential_indexes(self, conn: sqlite3.Connection):
        """Create only essential indexes needed for performance"""
        essential_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_tasks_week_id ON tasks(week_id)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_date_audited ON tasks(date_audited)",
            "CREATE INDEX IF NOT EXISTS idx_weeks_week_label ON weeks(week_label)"
        ]
        
        for index_sql in essential_indexes:
            conn.execute(index_sql)

class DatabaseConnectionOptimizer:
    """
    Optimizes database connections throughout the application
    """
    
    def __init__(self):
        self.optimized_managers = {}
        self.default_manager = None
    
    def get_optimized_manager(self, db_path: str = None) -> OptimizedDatabaseManager:
        """Get or create an optimized database manager"""
        if db_path is None:
            db_path = DATABASE_FILE
        if db_path not in self.optimized_managers:
            with profile_phase("Create DB Manager", {"db_path": db_path}):
                self.optimized_managers[db_path] = OptimizedDatabaseManager(db_path)
        
        return self.optimized_managers[db_path]
    
    def set_default_manager(self, db_path: str = None):
        """Set the default database manager"""
        self.default_manager = self.get_optimized_manager(db_path)
    
    def get_default_connection(self):
        """Get a connection from the default manager"""
        if self.default_manager is None:
            self.set_default_manager()
        return self.default_manager.get_connection()
    
    def optimize_all_connections(self):
        """Apply optimizations to all database connections"""
        with profile_phase("Optimize All DB Connections"):
            for manager in self.optimized_managers.values():
                # Ensure all connections in pool are optimized
                with manager.get_connection() as conn:
                    manager._apply_performance_settings(conn)

# Global database optimizer instance
_db_optimizer = None

def get_database_optimizer() -> DatabaseConnectionOptimizer:
    """Get the global database optimizer"""
    global _db_optimizer
    if _db_optimizer is None:
        _db_optimizer = DatabaseConnectionOptimizer()
    return _db_optimizer

def optimize_database_startup(db_path: str = None) -> OptimizedDatabaseManager:
    """Optimize database for fast startup"""
    with profile_phase("Database Startup Optimization"):
        optimizer = get_database_optimizer()
        manager = optimizer.get_optimized_manager(db_path)
        
        # Run essential migrations only
        migration_runner = FastMigrationRunner(manager)
        migration_runner.run_essential_migrations_only()
        
        # Set as default
        optimizer.set_default_manager(db_path)
        
        return manager

@contextmanager
def optimized_db_connection(db_path: str = None):
    """Context manager for optimized database connections"""
    optimizer = get_database_optimizer()
    manager = optimizer.get_optimized_manager(db_path)
    
    with manager.get_connection() as conn:
        yield conn 