#!/usr/bin/env python3
import sqlite3
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Test basic database connectivity first
try:
    print("🔍 Testing basic database connectivity...")
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM tasks')
    task_count = c.fetchone()[0]
    print(f"✅ Database connected successfully. Tasks found: {task_count}")
    conn.close()
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)

# Test our connection pool
try:
    print("\n🔧 Testing Database Connection Pool...")
    from core.db.db_connection_pool import test_connection_pool
    test_connection_pool()
except Exception as e:
    print(f"❌ Connection pool test failed: {e}")
    import traceback
    traceback.print_exc() 