import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.controllers.task_controller import TaskController
from core.controllers.week_controller import WeekController
from core.controllers.timer_controller import TimerController
from core.controllers.office_hours_controller import OfficeHoursController
from core.controllers.analytics_controller import AnalyticsController
from core.repositories.task_repository import TaskRepository
from core.repositories.week_repository import WeekRepository
from core.repositories.analytics_repository import AnalyticsRepository

class TestTaskController(unittest.TestCase):
    """Test TaskController functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_repository = Mock()
        self.mock_event_bus = Mock()
        
        with patch('core.controllers.task_controller.get_event_bus', 
                  return_value=self.mock_event_bus):
            self.controller = TaskController(self.mock_repository)
    
    def test_create_task_success(self):
        """Test successful task creation"""
        # Arrange
        week_id = 1
        expected_task_id = 123
        self.mock_repository.create.return_value = expected_task_id
        self.mock_repository.transaction.return_value.__enter__ = Mock()
        self.mock_repository.transaction.return_value.__exit__ = Mock(return_value=None)
        
        # Act
        result = self.controller.create_task(week_id)
        
        # Assert
        self.assertEqual(result, expected_task_id)
        self.mock_repository.create.assert_called_once_with(week_id)
        self.mock_event_bus.emit_event.assert_called()
    
    def test_update_task_field_success(self):
        """Test successful task field update"""
        # Arrange
        task_id = 123
        field_name = "project_name"
        value = "New Project"
        self.mock_repository.update.return_value = True
        
        # Act
        result = self.controller.update_task_field(task_id, field_name, value)
        
        # Assert
        self.assertTrue(result)
        self.mock_repository.update.assert_called_once_with(task_id, **{field_name: value})
        self.mock_event_bus.emit_event.assert_called()
    
    def test_delete_tasks_success(self):
        """Test successful bulk task deletion"""
        # Arrange
        task_ids = [1, 2, 3]
        week_id = 1
        self.mock_repository.delete_multiple.return_value = 3
        self.mock_repository.transaction.return_value.__enter__ = Mock()
        self.mock_repository.transaction.return_value.__exit__ = Mock(return_value=None)
        
        # Act
        result = self.controller.delete_tasks(task_ids, week_id)
        
        # Assert
        self.assertTrue(result)
        self.mock_repository.delete_multiple.assert_called_once_with(task_ids)
        self.mock_event_bus.emit_event.assert_called()

class TestWeekController(unittest.TestCase):
    """Test WeekController functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_repository = Mock(spec=WeekRepository)
        self.mock_event_bus = Mock()
        
        with patch('core.controllers.week_controller.get_event_bus', 
                  return_value=self.mock_event_bus):
            self.controller = WeekController(self.mock_repository)
    
    def test_create_week_success(self):
        """Test successful week creation"""
        # Arrange
        start_date = "2024-01-01"
        end_date = "2024-01-07"
        expected_week_id = 456
        self.mock_repository.create.return_value = expected_week_id
        self.mock_repository.transaction.return_value.__enter__ = Mock()
        self.mock_repository.transaction.return_value.__exit__ = Mock(return_value=None)
        
        # Act
        result = self.controller.create_week(start_date, end_date)
        
        # Assert
        self.assertEqual(result, expected_week_id)
        self.mock_repository.create.assert_called_once_with(start_date, end_date)
        self.mock_event_bus.emit_event.assert_called()
    
    def test_toggle_week_bonus_success(self):
        """Test successful week bonus toggle"""
        # Arrange
        week_id = 1
        is_bonus_enabled = True
        self.mock_repository.update_bonus_status.return_value = True
        
        # Act
        result = self.controller.toggle_week_bonus(week_id, is_bonus_enabled)
        
        # Assert
        self.assertTrue(result)
        self.mock_repository.update_bonus_status.assert_called_once_with(week_id, is_bonus_enabled)
        self.mock_event_bus.emit_event.assert_called()
    
    def test_is_bonus_week(self):
        """Test bonus week check"""
        # Arrange
        week_id = 1
        self.mock_repository.get_by_id.return_value = {'is_bonus_week': 1}
        
        # Act
        result = self.controller.is_bonus_week(week_id)
        
        # Assert
        self.assertTrue(result)
        self.mock_repository.get_by_id.assert_called_once_with(week_id)

class TestTimerController(unittest.TestCase):
    """Test TimerController functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_repository = Mock(spec=TaskRepository)
        self.mock_event_bus = Mock()
        
        with patch('core.controllers.timer_controller.get_event_bus', 
                  return_value=self.mock_event_bus):
            self.controller = TimerController(self.mock_repository)
    
    def test_start_timer_success(self):
        """Test successful timer start"""
        # Arrange
        task_id = 123
        self.mock_repository.update.return_value = True
        
        # Act
        self.controller.start_timer(task_id)
        
        # Assert
        self.assertTrue(task_id in self.controller._active_timers)
        self.mock_repository.update.assert_called()
        self.mock_event_bus.emit_event.assert_called()
    
    def test_stop_timer_success(self):
        """Test successful timer stop"""
        # Arrange
        task_id = 123
        self.controller._active_timers[task_id] = {
            'start_time': datetime.now(),
            'rust_timer': False
        }
        self.mock_repository.update.return_value = True
        
        # Act
        self.controller.stop_timer(task_id, 3600)  # 1 hour
        
        # Assert
        self.assertFalse(task_id in self.controller._active_timers)
        self.mock_repository.update.assert_called()
        self.mock_event_bus.emit_event.assert_called()
    
    def test_is_timer_active(self):
        """Test timer active check"""
        # Arrange
        task_id = 123
        self.controller._active_timers[task_id] = {'start_time': datetime.now()}
        
        # Act & Assert
        self.assertTrue(self.controller.is_timer_active(task_id))
        self.assertFalse(self.controller.is_timer_active(999))

class TestOfficeHoursController(unittest.TestCase):
    """Test OfficeHoursController functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_repository = Mock(spec=WeekRepository)
        self.mock_event_bus = Mock()
        
        with patch('core.controllers.office_hours_controller.get_event_bus', 
                  return_value=self.mock_event_bus):
            self.controller = OfficeHoursController(self.mock_repository)
    
    def test_add_office_hour_session_success(self):
        """Test successful office hour session addition"""
        # Arrange
        week_id = 1
        self.mock_repository.get_office_hour_count.return_value = 2
        self.mock_repository.update_office_hour_count.return_value = True
        
        # Act
        result = self.controller.add_office_hour_session(week_id)
        
        # Assert
        self.assertTrue(result)
        self.mock_repository.update_office_hour_count.assert_called_once_with(week_id, 3)
        self.mock_event_bus.emit_event.assert_called()
    
    def test_remove_office_hour_session_success(self):
        """Test successful office hour session removal"""
        # Arrange
        week_id = 1
        self.mock_repository.get_office_hour_count.return_value = 2
        self.mock_repository.update_office_hour_count.return_value = True
        
        # Act
        result = self.controller.remove_office_hour_session(week_id)
        
        # Assert
        self.assertTrue(result)
        self.mock_repository.update_office_hour_count.assert_called_once_with(week_id, 1)
        self.mock_event_bus.emit_event.assert_called()
    
    def test_remove_office_hour_session_at_zero(self):
        """Test office hour session removal when count is zero"""
        # Arrange
        week_id = 1
        self.mock_repository.get_office_hour_count.return_value = 0
        
        # Act
        result = self.controller.remove_office_hour_session(week_id)
        
        # Assert
        self.assertFalse(result)
        self.mock_repository.update_office_hour_count.assert_not_called()

class TestAnalyticsController(unittest.TestCase):
    """Test AnalyticsController functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_repository = Mock(spec=AnalyticsRepository)
        self.mock_event_bus = Mock()
        
        with patch('core.controllers.analytics_controller.get_event_bus', 
                  return_value=self.mock_event_bus):
            self.controller = AnalyticsController(self.mock_repository)
    
    def test_get_task_statistics_success(self):
        """Test successful task statistics retrieval"""
        # Arrange
        week_id = 1
        expected_stats = {
            'total_tasks': 10,
            'completed_tasks': 8,
            'unique_projects': 3,
            'avg_duration_minutes': 45.5
        }
        self.mock_repository.get_task_statistics.return_value = expected_stats
        
        # Act
        result = self.controller.get_task_statistics(week_id)
        
        # Assert
        self.assertEqual(result, expected_stats)
        self.mock_repository.get_task_statistics.assert_called_once_with(week_id)
        self.mock_event_bus.emit_event.assert_called()
    
    def test_get_project_statistics_success(self):
        """Test successful project statistics retrieval"""
        # Arrange
        week_id = 1
        expected_stats = [
            {'project_name': 'Project A', 'task_count': 5, 'completed_count': 4},
            {'project_name': 'Project B', 'task_count': 3, 'completed_count': 2}
        ]
        self.mock_repository.get_project_statistics.return_value = expected_stats
        
        # Act
        result = self.controller.get_project_statistics(week_id)
        
        # Assert
        self.assertEqual(result, expected_stats)
        self.mock_repository.get_project_statistics.assert_called_once_with(week_id)
        self.mock_event_bus.emit_event.assert_called()
    
    def test_refresh_all_analytics(self):
        """Test analytics refresh request"""
        # Act
        self.controller.refresh_all_analytics()
        
        # Assert
        self.mock_event_bus.emit_event.assert_called()

def run_controller_tests():
    """Run all controller tests"""
    print("🧪 Running Python Backend Controllers Tests...")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestTaskController,
        TestWeekController,
        TestTimerController,
        TestOfficeHoursController,
        TestAnalyticsController
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total_tests - failures - errors
    
    print(f"\n📊 Controller Tests Summary:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {passed}")
    print(f"   Failed: {failures}")
    print(f"   Errors: {errors}")
    print(f"   Success Rate: {(passed/total_tests)*100:.1f}%")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_controller_tests()
    sys.exit(0 if success else 1) 