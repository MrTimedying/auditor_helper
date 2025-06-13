#!/usr/bin/env python3
"""
Comprehensive test to verify all boundary calculation fixes
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta
sys.path.insert(0, 'src')

from ui.task_grid import TaskGrid
from core.settings.global_settings import global_settings
from core.db.db_schema import init_db, migrate_week_settings, migrate_week_bonus_settings, migrate_office_hours_settings
from PySide6 import QtCore, QtWidgets

class MockMainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.toaster_messages = []

def test_all_fixes():
    print("🔬 Comprehensive Boundary Calculation Fix Verification")
    print("=" * 60)
    
    # Initialize Qt
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication([])
    
    # Initialize database
    init_db()
    migrate_week_settings()
    migrate_week_bonus_settings()
    migrate_office_hours_settings()
    
    # Create mock main window and task grid
    main_window = MockMainWindow()
    task_grid = TaskGrid(main_window)
    task_grid.main_window = main_window
    
    # Create test weeks
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    
    # Clean up any existing test data
    for week_id in [8001, 8002, 8003]:
        c.execute("DELETE FROM weeks WHERE id = ?", (week_id,))
        c.execute("DELETE FROM tasks WHERE week_id = ?", (week_id,))
    
    test_cases = []
    
    # Test Case 1: Default Week (Monday 9am - Monday 9am)
    c.execute("""
        INSERT INTO weeks (
            id, week_label, week_start_day, week_start_hour, 
            week_end_day, week_end_hour, is_custom_duration,
            is_bonus_week, office_hour_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0)
    """, (8001, "13/01/2025 - 20/01/2025", None, None, None, None, 0))
    
    # Test various times for default week
    default_week_tests = [
        (datetime(2025, 1, 13, 8, 59, 59), True, "Before week start"),
        (datetime(2025, 1, 13, 9, 0, 0), False, "Exact week start"),
        (datetime(2025, 1, 15, 15, 30, 0), False, "Mid-week Wednesday"),
        (datetime(2025, 1, 20, 8, 59, 59), False, "End of week Monday before 9am"),
        (datetime(2025, 1, 20, 9, 0, 0), True, "After week end"),
    ]
    
    print("📋 Test 1: Default Week (Monday 9am - Monday 9am)")
    for test_time, expected_outside, description in default_week_tests:
        result = task_grid.is_task_outside_week_boundaries(8001, test_time)
        passed = result == expected_outside
        status = "✅ PASS" if passed else "❌ FAIL"
        test_cases.append((f"Default - {description}", passed))
        print(f"  {status}: {description} ({test_time}) -> {'OUTSIDE' if result else 'INSIDE'}")
    
    # Test Case 2: Custom Week (Wednesday 8am - Tuesday 10pm)
    c.execute("""
        INSERT INTO weeks (
            id, week_label, week_start_day, week_start_hour, 
            week_end_day, week_end_hour, is_custom_duration,
            is_bonus_week, office_hour_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0)
    """, (8002, "20/01/2025 - 26/01/2025", 3, 8, 2, 22, 1))  # Wed 8am - Tue 10pm
    
    custom_week_tests = [
        (datetime(2025, 1, 22, 7, 59, 59), True, "Before custom start"),
        (datetime(2025, 1, 22, 8, 0, 0), False, "Exact custom start"),
        (datetime(2025, 1, 25, 12, 0, 0), False, "Weekend in custom week"),
        (datetime(2025, 1, 28, 22, 0, 0), False, "Exact custom end"),
        (datetime(2025, 1, 28, 23, 0, 0), True, "After custom end"),
    ]
    
    print("\n📋 Test 2: Custom Week (Wednesday 8am - Tuesday 10pm)")
    for test_time, expected_outside, description in custom_week_tests:
        result = task_grid.is_task_outside_week_boundaries(8002, test_time)
        passed = result == expected_outside
        status = "✅ PASS" if passed else "❌ FAIL"
        test_cases.append((f"Custom - {description}", passed))
        print(f"  {status}: {description} ({test_time}) -> {'OUTSIDE' if result else 'INSIDE'}")
    
    # Test Case 3: Weekend Week (Friday 6pm - Monday 6am)
    c.execute("""
        INSERT INTO weeks (
            id, week_label, week_start_day, week_start_hour, 
            week_end_day, week_end_hour, is_custom_duration,
            is_bonus_week, office_hour_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0)
    """, (8003, "24/01/2025 - 27/01/2025", 5, 18, 1, 6, 1))  # Fri 6pm - Mon 6am
    
    weekend_week_tests = [
        (datetime(2025, 1, 24, 17, 59, 59), True, "Before weekend start"),
        (datetime(2025, 1, 24, 18, 0, 0), False, "Exact weekend start"),
        (datetime(2025, 1, 26, 2, 0, 0), False, "Weekend night"),
        (datetime(2025, 1, 27, 5, 59, 59), False, "End of weekend hour"),
        (datetime(2025, 1, 27, 6, 0, 0), True, "After weekend end"),
    ]
    
    print("\n📋 Test 3: Weekend Week (Friday 6pm - Monday 6am)")
    for test_time, expected_outside, description in weekend_week_tests:
        result = task_grid.is_task_outside_week_boundaries(8003, test_time)
        passed = result == expected_outside
        status = "✅ PASS" if passed else "❌ FAIL"
        test_cases.append((f"Weekend - {description}", passed))
        print(f"  {status}: {description} ({test_time}) -> {'OUTSIDE' if result else 'INSIDE'}")
    
    # Test Case 4: Validation Modes
    print("\n📋 Test 4: Validation Modes")
    
    validation_test_cases = [
        # No timestamps
        (88001, "", "", True, "No timestamps (should pass)"),
        # Valid time_begin only
        (88002, "2025-01-15 10:00:00", "", True, "Valid time_begin only"),
        # Invalid time_begin only  
        (88003, "2025-01-12 10:00:00", "", False, "Invalid time_begin only"),
        # Valid time_end only
        (88004, "", "2025-01-16 15:00:00", True, "Valid time_end only"),
        # Invalid time_end only
        (88005, "", "2025-01-21 10:00:00", False, "Invalid time_end only"),
        # Both valid
        (88006, "2025-01-15 10:00:00", "2025-01-15 11:00:00", True, "Both valid"),
        # Both invalid
        (88007, "2025-01-12 10:00:00", "2025-01-21 11:00:00", False, "Both invalid"),
    ]
    
    for task_id, time_begin, time_end, expected_valid, description in validation_test_cases:
        # Create test task
        c.execute("""
            INSERT INTO tasks (
                id, week_id, attempt_id, duration, project_id, project_name,
                operation_id, time_limit, date_audited, score, feedback, locale,
                time_begin, time_end
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_id, 8001, "TEST", "01:00:00", "TEST", "Test Project",
            "TEST", "02:00:00", "2025-01-15", 5, "Test feedback", "en",
            time_begin, time_end
        ))
        
        result = task_grid.validate_task_against_boundaries(task_id, 8001)
        passed = result == expected_valid
        status = "✅ PASS" if passed else "❌ FAIL"
        test_cases.append((f"Validation - {description}", passed))
        print(f"  {status}: {description} -> Valid: {result}")
    
    conn.commit()
    
    # Test Case 5: Edge Cases
    print("\n📋 Test 5: Edge Cases")
    
    # Non-existent week
    result = task_grid.is_task_outside_week_boundaries(99999, datetime.now())
    edge_case_1 = result == False
    status = "✅ PASS" if edge_case_1 else "❌ FAIL"
    test_cases.append(("Edge - Non-existent week", edge_case_1))
    print(f"  {status}: Non-existent week -> {result}")
    
    # Malformed week label
    c.execute("""
        INSERT INTO weeks (
            id, week_label, is_custom_duration, is_bonus_week, office_hour_count
        ) VALUES (?, ?, ?, ?, ?)
    """, (99998, "INVALID_DATE_FORMAT", 0, 0, 0))
    conn.commit()
    
    result = task_grid.is_task_outside_week_boundaries(99998, datetime.now())
    edge_case_2 = result == False
    status = "✅ PASS" if edge_case_2 else "❌ FAIL"
    test_cases.append(("Edge - Malformed week label", edge_case_2))
    print(f"  {status}: Malformed week label -> {result}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(test_cases)
    passed_tests = sum(1 for _, passed in test_cases if passed)
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "No tests run")
    
    if failed_tests > 0:
        print("\n❌ FAILED TESTS:")
        for name, passed in test_cases:
            if not passed:
                print(f"  • {name}")
    else:
        print("\n🎉 ALL TESTS PASSED! Boundary functionality is working correctly.")
    
    # Clean up
    for week_id in [8001, 8002, 8003, 99998]:
        c.execute("DELETE FROM weeks WHERE id = ?", (week_id,))
    for task_id in range(88001, 88008):
        c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    
    print("\n✅ Test data cleanup completed")
    return failed_tests == 0

if __name__ == "__main__":
    success = test_all_fixes() 