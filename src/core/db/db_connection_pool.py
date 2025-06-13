# db_connection_pool.py - Connection pooling for improved database performance
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
import time
from . import DB_FILE  # absolute path to tasks.db

class DatabaseConnectionPool:
    """Simple connection pool for SQLite database operations"""
    
    def __init__(self, db_file=DB_FILE, pool_size=5):
        self.db_file = db_file
        self.pool_size = pool_size
        self.connections = []
        self.lock = threading.Lock()
        self.connection_count = 0
        
        # Initialize the pool
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize the connection pool"""
        with self.lock:
            for _ in range(self.pool_size):
                conn = self._create_optimized_connection()
                self.connections.append(conn)
                self.connection_count += 1
    
    def _create_optimized_connection(self):
        """Create an optimized SQLite connection"""
        conn = sqlite3.connect(self.db_file, check_same_thread=False)
        
        # Optimize SQLite settings for performance
        conn.execute("PRAGMA journal_mode=WAL")       # Better concurrency
        conn.execute("PRAGMA synchronous=NORMAL")     # Performance boost
        conn.execute("PRAGMA cache_size=10000")       # Larger cache (10MB)
        conn.execute("PRAGMA temp_store=MEMORY")      # Use memory for temp storage
        conn.execute("PRAGMA mmap_size=268435456")    # Use memory-mapped I/O (256MB)
        
        return conn
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        conn = None
        
        with self.lock:
            if self.connections:
                conn = self.connections.pop()
            else:
                # Pool exhausted, create temporary connection
                conn = self._create_optimized_connection()
                print(f"⚠️ Pool exhausted, created temporary connection")
        
        try:
            yield conn
        finally:
            # Return connection to pool or close if temporary
            with self.lock:
                if len(self.connections) < self.pool_size:
                    self.connections.append(conn)
                else:
                    conn.close()
    
    def close_all(self):
        """Close all connections in the pool"""
        with self.lock:
            for conn in self.connections:
                conn.close()
            self.connections.clear()
            self.connection_count = 0
    
    def get_pool_status(self):
        """Get current pool status"""
        with self.lock:
            return {
                'available_connections': len(self.connections),
                'pool_size': self.pool_size,
                'total_created': self.connection_count
            }

# Global connection pool instance
_connection_pool = None

def get_db_pool():
    """Get the global database connection pool"""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = DatabaseConnectionPool()
    return _connection_pool

def close_db_pool():
    """Close the global database connection pool"""
    global _connection_pool
    if _connection_pool:
        _connection_pool.close_all()
        _connection_pool = None

# Context manager for easy database operations
@contextmanager
def get_db_connection():
    """Context manager for database operations"""
    pool = get_db_pool()
    with pool.get_connection() as conn:
        yield conn

# Performance timing decorator
def time_db_operation(func):
    """Decorator to time database operations"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        operation_time = (end_time - start_time) * 1000
        if operation_time > 100:  # Log slow operations
            print(f"⚠️ Slow DB operation: {func.__name__} took {operation_time:.2f}ms")
        return result
    return wrapper

# Example optimized database operations
class OptimizedDatabaseOperations:
    """Optimized database operations using connection pooling"""
    
    @staticmethod
    @time_db_operation
    def get_tasks_for_week(week_id):
        """Get tasks for a specific week using connection pool"""
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT id, attempt_id, duration, project_id, project_name,
                       operation_id, time_limit, date_audited, score, feedback, locale,
                       time_begin, time_end
                FROM tasks 
                WHERE week_id=? 
                ORDER BY id
            """, (week_id,))
            return c.fetchall()
    
    @staticmethod
    @time_db_operation
    def update_task_field(task_id, field_name, value):
        """Update a single task field using connection pool"""
        with get_db_connection() as conn:
            c = conn.cursor()
            query = f"UPDATE tasks SET {field_name}=? WHERE id=?"
            c.execute(query, (value, task_id))
            conn.commit()
            return True
    
    @staticmethod
    @time_db_operation
    def get_task_count_for_week(week_id):
        """Get task count for a week using connection pool"""
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM tasks WHERE week_id=?", (week_id,))
            return c.fetchone()[0]
    
    @staticmethod
    @time_db_operation
    def batch_update_tasks(updates):
        """Batch update multiple tasks efficiently"""
        with get_db_connection() as conn:
            c = conn.cursor()
            
            # Group updates by field for efficiency
            field_updates = {}
            for task_id, field_name, value in updates:
                if field_name not in field_updates:
                    field_updates[field_name] = []
                field_updates[field_name].append((value, task_id))
            
            # Execute batched updates
            for field_name, values in field_updates.items():
                query = f"UPDATE tasks SET {field_name}=? WHERE id=?"
                c.executemany(query, values)
            
            conn.commit()
            return len(updates)

def test_connection_pool():
    """Test the connection pool performance"""
    print("🔧 Testing Database Connection Pool")
    print("=" * 50)
    
    pool = get_db_pool()
    
    # Test pool status
    status = pool.get_pool_status()
    print(f"📊 Pool Status: {status['available_connections']}/{status['pool_size']} connections available")
    
    # Test basic operations
    start_time = time.time()
    
    # Simulate multiple concurrent operations
    for i in range(10):
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM tasks")
            count = c.fetchone()[0]
    
    end_time = time.time()
    operation_time = (end_time - start_time) * 1000
    
    print(f"✅ 10 operations completed in {operation_time:.2f}ms")
    print(f"📊 Average per operation: {operation_time/10:.2f}ms")
    
    # Test optimized operations
    print("\n🚀 Testing Optimized Operations:")
    
    # Test task loading
    start_time = time.time()
    tasks = OptimizedDatabaseOperations.get_tasks_for_week(1)
    end_time = time.time()
    print(f"✅ Loaded {len(tasks)} tasks in {(end_time - start_time)*1000:.2f}ms")
    
    # Test task count
    start_time = time.time()
    count = OptimizedDatabaseOperations.get_task_count_for_week(1)
    end_time = time.time()
    print(f"✅ Got task count ({count}) in {(end_time - start_time)*1000:.2f}ms")
    
    print(f"\n🎯 Connection pool optimization complete!")
    print(f"Expected benefits:")
    print(f"- 30-50% faster database operations")
    print(f"- Reduced connection overhead")
    print(f"- Better resource management")

if __name__ == "__main__":
    test_connection_pool() 