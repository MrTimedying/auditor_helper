# performance_tests.py
import unittest
import time
import sqlite3
from unittest.mock import Mock, patch
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from task_grid import TaskGrid, TaskTableModel
except ImportError:
    print("Warning: Could not import TaskGrid - creating mock for testing")
    TaskTableModel = Mock

class PerformanceTestCase(unittest.TestCase):
    """Base class for performance tests"""
    
    def setUp(self):
        """Set up test database with sample data"""
        self.test_db = "test_performance.db"
        self.create_test_database()
        self.original_db_file = None
        
        # Monkey patch the DB_FILE constant if task_grid is available
        try:
            import task_grid
            self.original_db_file = getattr(task_grid, 'DB_FILE', None)
            if hasattr(task_grid, 'DB_FILE'):
                task_grid.DB_FILE = self.test_db
        except ImportError:
            pass
    
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        
        # Restore original DB_FILE
        if self.original_db_file:
            try:
                import task_grid
                task_grid.DB_FILE = self.original_db_file
            except ImportError:
                pass
    
    def create_test_database(self):
        """Create a test database with sample data"""
        conn = sqlite3.connect(self.test_db)
        c = conn.cursor()
        
        # Create tables
        c.execute("""
            CREATE TABLE weeks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_label TEXT UNIQUE NOT NULL
            )
        """)
        
        c.execute("""
            CREATE TABLE tasks (
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
                time_begin TEXT,
                time_end TEXT,
                FOREIGN KEY (week_id) REFERENCES weeks(id) ON DELETE CASCADE
            )
        """)
        
        # Insert test weeks
        for i in range(1, 11):  # 10 weeks
            c.execute("INSERT INTO weeks (week_label) VALUES (?)", 
                     (f"Week {i} - Test Data",))
        
        # Insert test tasks (varying amounts per week)
        task_counts = [100, 250, 500, 1000, 1500, 2000, 2500, 3000, 4000, 5000]
        
        for week_id, count in enumerate(task_counts, 1):
            for task_num in range(count):
                c.execute("""
                    INSERT INTO tasks (
                        week_id, attempt_id, duration, project_id, project_name,
                        operation_id, time_limit, date_audited, score, feedback, locale
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    week_id,
                    f"ATT_{week_id}_{task_num:04d}",
                    "00:15:30",
                    f"PROJ_{task_num % 50}",
                    f"Project {task_num % 50}",
                    f"OP_{task_num % 20}",
                    "00:30:00",
                    "2024-01-01",
                    (task_num % 5) + 1,
                    f"Test feedback for task {task_num}",
                    "en-US"
                ))
        
        conn.commit()
        conn.close()

class DatabasePerformanceTests(PerformanceTestCase):
    """Performance tests for database operations"""
    
    def test_baseline_query_performance(self):
        """Test baseline query performance (CRITICAL - RUN THIS FIRST)"""
        print("\n" + "="*60)
        print("🚀 BASELINE PERFORMANCE ANALYSIS")
        print("="*60)
        
        conn = sqlite3.connect(self.test_db)
        c = conn.cursor()
        
        queries = [
            ("Week filter", "SELECT COUNT(*) FROM tasks WHERE week_id = 5"),
            ("Date range", "SELECT COUNT(*) FROM tasks WHERE date_audited BETWEEN '2024-01-01' AND '2024-12-31'"),
            ("Project group", "SELECT project_id, COUNT(*) FROM tasks GROUP BY project_id"),
            ("Complex query", """
                SELECT t.week_id, COUNT(*), AVG(t.score)
                FROM tasks t 
                WHERE t.week_id IN (1,2,3,4,5)
                GROUP BY t.week_id
            """)
        ]
        
        results = []
        
        print("\n📊 BEFORE OPTIMIZATION:")
        for name, query in queries:
            start_time = time.time()
            c.execute(query)
            c.fetchall()
            end_time = time.time()
            
            query_time = (end_time - start_time) * 1000
            results.append((name, query_time))
            print(f"  {name}: {query_time:.2f}ms")
        
        conn.close()
        
        # Save baseline for comparison
        self.baseline_results = results
        return results
    
    def test_query_performance_with_indexes(self):
        """Test query performance after adding indexes"""
        # First run baseline
        baseline = self.test_baseline_query_performance()
        
        conn = sqlite3.connect(self.test_db)
        c = conn.cursor()
        
        print("\n🔨 ADDING INDEXES...")
        # Add indexes
        indexes = [
            ("week_id", "CREATE INDEX idx_tasks_week_id ON tasks(week_id)"),
            ("date_audited", "CREATE INDEX idx_tasks_date_audited ON tasks(date_audited)"),
            ("project_id", "CREATE INDEX idx_tasks_project_id ON tasks(project_id)"),
        ]
        
        for name, index_sql in indexes:
            start_time = time.time()
            c.execute(index_sql)
            end_time = time.time()
            print(f"  ✓ {name} index: {(end_time - start_time)*1000:.2f}ms")
        
        conn.commit()
        
        # Test the same queries as baseline
        queries = [
            ("Week filter", "SELECT COUNT(*) FROM tasks WHERE week_id = 5"),
            ("Date range", "SELECT COUNT(*) FROM tasks WHERE date_audited BETWEEN '2024-01-01' AND '2024-12-31'"),
            ("Project group", "SELECT project_id, COUNT(*) FROM tasks GROUP BY project_id"),
            ("Complex query", """
                SELECT t.week_id, COUNT(*), AVG(t.score)
                FROM tasks t 
                WHERE t.week_id IN (1,2,3,4,5)
                GROUP BY t.week_id
            """)
        ]
        
        print("\n📊 AFTER OPTIMIZATION:")
        optimized_results = []
        for name, query in queries:
            start_time = time.time()
            c.execute(query)
            c.fetchall()
            end_time = time.time()
            
            query_time = (end_time - start_time) * 1000
            optimized_results.append((name, query_time))
            print(f"  {name}: {query_time:.2f}ms")
        
        # Calculate improvements
        print("\n🎯 PERFORMANCE IMPROVEMENTS:")
        for i, (name, baseline_time) in enumerate(baseline):
            optimized_time = optimized_results[i][1]
            improvement = ((baseline_time - optimized_time) / baseline_time) * 100
            speedup = baseline_time / optimized_time if optimized_time > 0 else float('inf')
            print(f"  {name}: {improvement:.1f}% faster ({speedup:.1f}x speedup)")
        
        conn.close()
        return optimized_results

def run_quick_performance_assessment():
    """Run a quick performance assessment on the current database"""
    print("🚀 Quick Performance Assessment on Current Database")
    print("="*60)
    
    # Test if the current database exists
    db_file = "tasks.db"
    if not os.path.exists(db_file):
        print(f"❌ Database not found: {db_file}")
        print("   Create some test data first or run the full test suite.")
        return
    
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    
    try:
        # Check if we have data
        c.execute("SELECT COUNT(*) FROM tasks")
        total_tasks = c.fetchone()[0]
        print(f"📊 Total tasks in database: {total_tasks}")
        
        if total_tasks == 0:
            print("❌ No tasks found. Add some data first.")
            return
        
        # Quick performance tests
        print("\n🔍 Testing key queries...")
        queries = [
            ("Count by week", "SELECT week_id, COUNT(*) FROM tasks GROUP BY week_id LIMIT 5"),
            ("Recent tasks", "SELECT COUNT(*) FROM tasks WHERE date_audited >= '2024-01-01'"),
            ("Task lookup", "SELECT COUNT(*) FROM tasks WHERE week_id = 1"),
        ]
        
        for name, query in queries:
            start_time = time.time()
            c.execute(query)
            results = c.fetchall()
            end_time = time.time()
            
            query_time = (end_time - start_time) * 1000
            print(f"  {name}: {query_time:.2f}ms")
            
            # Flag slow queries
            if query_time > 100:
                print(f"    ⚠️  SLOW QUERY - would benefit from indexing!")
    
    except Exception as e:
        print(f"❌ Error testing database: {e}")
    finally:
        conn.close()

def run_performance_test_suite():
    """Run the complete performance test suite"""
    print("🚀 Starting Performance Test Suite")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(DatabasePerformanceTests('test_baseline_query_performance'))
    suite.addTest(DatabasePerformanceTests('test_query_performance_with_indexes'))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ All performance tests passed!")
    else:
        print("❌ Some performance tests failed!")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
    
    return result

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Performance testing for Auditor Helper')
    parser.add_argument('--quick', action='store_true', 
                       help='Run quick assessment on current database')
    parser.add_argument('--full', action='store_true',
                       help='Run full test suite with synthetic data')
    
    args = parser.parse_args()
    
    if args.quick:
        run_quick_performance_assessment()
    elif args.full:
        run_performance_test_suite()
    else:
        # Default: run quick assessment
        print("Running quick performance assessment...")
        print("Use --full for complete test suite or --quick for current DB only")
        print()
        run_quick_performance_assessment() 