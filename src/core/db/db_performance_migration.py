# db_performance_migration.py
import sqlite3
import time
import os
import shutil
from datetime import datetime

DB_FILE = "tasks.db"

def backup_database():
    """Create a timestamped backup of the database"""
    if not os.path.exists(DB_FILE):
        print(f"❌ Database not found: {DB_FILE}")
        return None
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{DB_FILE}_backup_{timestamp}"
    
    try:
        shutil.copy2(DB_FILE, backup_file)
        print(f"✓ Database backup created: {backup_file}")
        return backup_file
    except Exception as e:
        print(f"✗ Backup failed: {e}")
        return None

def analyze_query_performance():
    """Analyze current query performance before optimization"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    print("=== BEFORE OPTIMIZATION ===")
    
    # Test queries and measure time
    test_queries = [
        ("Week-based task lookup", "SELECT COUNT(*) FROM tasks WHERE week_id = 1"),
        ("Date range query", "SELECT COUNT(*) FROM tasks WHERE date_audited BETWEEN '2024-01-01' AND '2024-12-31'"),
        ("Time-based filtering", "SELECT COUNT(*) FROM tasks WHERE time_begin IS NOT NULL"),
        ("Complex analysis query", """
            SELECT project_id, COUNT(*), AVG(score) 
            FROM tasks 
            WHERE week_id IN (1,2,3,4,5) 
            GROUP BY project_id
        """)
    ]
    
    results = []
    for name, query in test_queries:
        try:
            start_time = time.time()
            c.execute(query)
            result = c.fetchall()
            end_time = time.time()
            query_time = (end_time - start_time) * 1000
            results.append((name, query_time))
            print(f"{name}: {query_time:.2f}ms")
        except Exception as e:
            print(f"{name}: ERROR - {e}")
            results.append((name, float('inf')))
    
    conn.close()
    return results

def check_existing_indexes():
    """Check what indexes already exist"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='tasks'")
    existing_indexes = c.fetchall()
    
    print("\n=== EXISTING INDEXES ===")
    if existing_indexes:
        for name, sql in existing_indexes:
            if sql:  # Skip auto-indexes (they have NULL sql)
                print(f"✓ {name}")
    else:
        print("❌ No indexes found on tasks table")
    
    conn.close()
    return existing_indexes

def create_performance_indexes():
    """Create all performance-critical indexes"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    indexes = [
        ("idx_tasks_week_id", "CREATE INDEX IF NOT EXISTS idx_tasks_week_id ON tasks(week_id)"),
        ("idx_tasks_date_audited", "CREATE INDEX IF NOT EXISTS idx_tasks_date_audited ON tasks(date_audited)"),
        ("idx_tasks_time_begin", "CREATE INDEX IF NOT EXISTS idx_tasks_time_begin ON tasks(time_begin)"),
        ("idx_tasks_time_end", "CREATE INDEX IF NOT EXISTS idx_tasks_time_end ON tasks(time_end)"),
        ("idx_tasks_project_id", "CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id)"),
        ("idx_tasks_composite_week_date", "CREATE INDEX IF NOT EXISTS idx_tasks_composite_week_date ON tasks(week_id, date_audited)"),
        ("idx_weeks_label", "CREATE INDEX IF NOT EXISTS idx_weeks_label ON weeks(week_label)"),
    ]
    
    print("\n=== CREATING INDEXES ===")
    created_count = 0
    
    for name, sql in indexes:
        start_time = time.time()
        try:
            c.execute(sql)
            end_time = time.time()
            print(f"✓ {name}: {(end_time - start_time)*1000:.2f}ms")
            created_count += 1
        except Exception as e:
            print(f"✗ {name}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Created {created_count}/{len(indexes)} indexes successfully")
    return created_count

def verify_index_usage():
    """Verify that indexes are being used by queries"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    print("\n=== VERIFYING INDEX USAGE ===")
    
    test_queries = [
        ("Week lookup", "EXPLAIN QUERY PLAN SELECT * FROM tasks WHERE week_id = 1"),
        ("Date range", "EXPLAIN QUERY PLAN SELECT * FROM tasks WHERE date_audited BETWEEN '2024-01-01' AND '2024-12-31'"),
        ("Composite index", "EXPLAIN QUERY PLAN SELECT * FROM tasks WHERE week_id = 1 AND date_audited = '2024-01-01'"),
    ]
    
    for name, query in test_queries:
        print(f"\n{name}:")
        try:
            c.execute(query)
            for row in c.fetchall():
                plan = row[3] if len(row) > 3 else str(row)
                if "USING INDEX" in plan:
                    print(f"  ✓ {plan}")
                else:
                    print(f"  ❌ {plan}")
        except Exception as e:
            print(f"  ERROR: {e}")
    
    conn.close()

def run_migration():
    """Execute the complete migration process"""
    print("🚀 Starting Performance Migration")
    print("=" * 50)
    
    # Check if database exists
    if not os.path.exists(DB_FILE):
        print(f"❌ Database not found: {DB_FILE}")
        print("   Make sure you're in the correct directory with tasks.db")
        return False
    
    # Step 1: Check existing state
    check_existing_indexes()
    
    # Step 2: Backup
    backup_file = backup_database()
    if not backup_file:
        print("❌ Migration aborted - backup failed")
        return False
    
    # Step 3: Analyze current performance
    print("\n" + "=" * 30)
    baseline_results = analyze_query_performance()
    
    # Step 4: Create indexes
    print("\n" + "=" * 30)
    created_count = create_performance_indexes()
    
    if created_count == 0:
        print("⚠️  No indexes were created - they may already exist")
    
    # Step 5: Verify index usage
    verify_index_usage()
    
    # Step 6: Re-test performance
    print("\n" + "=" * 30)
    optimized_results = analyze_query_performance()
    
    # Step 7: Calculate improvements
    print("\n=== PERFORMANCE IMPROVEMENTS ===")
    for i, (name, baseline_time) in enumerate(baseline_results):
        if i < len(optimized_results) and baseline_time != float('inf') and optimized_results[i][1] != float('inf'):
            optimized_time = optimized_results[i][1]
            if optimized_time > 0 and baseline_time > 0:
                improvement = ((baseline_time - optimized_time) / baseline_time) * 100
                speedup = baseline_time / optimized_time
                print(f"{name}: {improvement:.1f}% faster ({speedup:.1f}x speedup)")
            else:
                print(f"{name}: Optimized to near-instant")
        elif baseline_time == 0:
            print(f"{name}: Already optimized (near-instant)")
        else:
            print(f"{name}: Could not calculate improvement")
    
    print(f"\n✅ Migration completed successfully!")
    print(f"📁 Backup stored at: {backup_file}")
    print(f"🎯 Next step: Run performance tests to validate improvements")
    
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Database performance migration for Auditor Helper')
    parser.add_argument('--check-only', action='store_true',
                       help='Only check current performance, do not create indexes')
    parser.add_argument('--force', action='store_true',
                       help='Force migration even if indexes exist')
    
    args = parser.parse_args()
    
    if args.check_only:
        print("🔍 Performance Check Only Mode")
        print("=" * 40)
        check_existing_indexes()
        analyze_query_performance()
    else:
        success = run_migration()
        if success:
            print("\n🚀 Ready for next step: Run 'python performance_tests.py --quick' to validate improvements!")
        else:
            print("\n❌ Migration failed. Check errors above.") 