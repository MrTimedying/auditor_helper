"""
Integration tests for Event Bus with UI components
"""

import pytest
import sys
from unittest.mock import Mock, patch
from PySide6 import QtCore, QtWidgets

# Add src to path for imports
sys.path.insert(0, 'src')

from core.events.event_bus import get_event_bus, reset_event_bus
from core.events.event_types import EventType


class TestEventBusIntegration:
    """Test event bus integration with UI components"""
    
    def setup_method(self):
        """Set up test environment"""
        # Create a QApplication if it doesn't exist
        if not QtWidgets.QApplication.instance():
            self.app = QtWidgets.QApplication([])
        else:
            self.app = QtWidgets.QApplication.instance()
        
        # Reset event bus for clean tests
        reset_event_bus()
        self.event_bus = get_event_bus()
        
        # Track received events
        self.received_events = []
        
        def event_handler(event_data):
            self.received_events.append(event_data)
        
        # Connect to all week-related events
        self.event_bus.connect_handler(EventType.WEEK_CHANGED, event_handler)
        self.event_bus.connect_handler(EventType.WEEK_CREATED, event_handler)
        self.event_bus.connect_handler(EventType.WEEK_DELETED, event_handler)
    
    def teardown_method(self):
        """Clean up after tests"""
        reset_event_bus()
    
    @patch('ui.week_widget.DataService')
    @patch('ui.week_widget.WeekDAO')
    def test_week_widget_event_emission(self, mock_week_dao_class, mock_data_service_class):
        """Test that WeekWidget emits events correctly"""
        # Mock the data service and DAO
        mock_data_service = Mock()
        mock_week_dao = Mock()
        mock_data_service_class.return_value = mock_data_service
        mock_week_dao_class.return_value = mock_week_dao
        
        # Mock DAO methods
        mock_week_dao.get_all_weeks.return_value = [
            {'id': 1, 'week_label': '01/01/2024 - 07/01/2024'},
            {'id': 2, 'week_label': '08/01/2024 - 14/01/2024'}
        ]
        mock_week_dao.create_week.return_value = 3
        
        # Import and create WeekWidget after mocking
        from ui.week_widget import WeekWidget
        
        widget = WeekWidget()
        widget.main_window = Mock()  # Mock main window
        
        # Process Qt events
        self.app.processEvents()
        
        # Test week selection change
        widget.week_list.setCurrentRow(0)
        self.app.processEvents()
        
        # Should have received a WEEK_CHANGED event
        week_changed_events = [e for e in self.received_events if e.event_type == EventType.WEEK_CHANGED]
        assert len(week_changed_events) >= 1
        
        # Verify event data
        event = week_changed_events[0]
        assert event.data['week_id'] == 1
        assert event.data['week_label'] == '01/01/2024 - 07/01/2024'
        assert event.source == 'WeekWidget'
    
    @patch('ui.week_widget.global_settings')
    @patch('ui.week_widget.DataService')
    @patch('ui.week_widget.WeekDAO')
    def test_week_creation_event(self, mock_week_dao_class, mock_data_service_class, mock_global_settings):
        """Test that week creation emits the correct event"""
        # Mock global settings to disable week duration enforcement
        mock_global_settings.should_enforce_week_duration.return_value = False
        
        # Mock the data service and DAO
        mock_data_service = Mock()
        mock_week_dao = Mock()
        mock_data_service_class.return_value = mock_data_service
        mock_week_dao_class.return_value = mock_week_dao
        
        # Mock DAO methods
        mock_week_dao.get_all_weeks.return_value = []
        mock_week_dao.create_week.return_value = 1
        
        # Import and create WeekWidget after mocking
        from ui.week_widget import WeekWidget
        
        widget = WeekWidget()
        widget.main_window = Mock()  # Mock main window
        
        # Set valid dates (7 days apart to satisfy validation if it runs)
        from PySide6.QtCore import QDate
        start_date = QDate(2024, 1, 1)  # Monday
        end_date = QDate(2024, 1, 7)    # Sunday (7 days)
        widget.start_date.setDate(start_date)
        widget.end_date.setDate(end_date)
        
        # Clear any initial events
        self.received_events.clear()
        
        # Trigger week creation
        widget.add_week()
        self.app.processEvents()
        
        # Should have received a WEEK_CREATED event
        week_created_events = [e for e in self.received_events if e.event_type == EventType.WEEK_CREATED]
        assert len(week_created_events) == 1
        
        # Verify event data
        event = week_created_events[0]
        assert event.data['week_id'] == 1
        assert 'week_label' in event.data
        assert 'week_data' in event.data
        assert event.source == 'WeekWidget'
    
    def test_event_bus_singleton_consistency(self):
        """Test that all components use the same event bus instance"""
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        
        assert bus1 is bus2
        assert bus1 is self.event_bus
    
    def test_multiple_event_handlers(self):
        """Test that multiple handlers can listen to the same event"""
        handler1_calls = []
        handler2_calls = []
        
        def handler1(event_data):
            handler1_calls.append(event_data)
        
        def handler2(event_data):
            handler2_calls.append(event_data)
        
        # Connect both handlers to the same event
        self.event_bus.connect_handler(EventType.WEEK_CHANGED, handler1)
        self.event_bus.connect_handler(EventType.WEEK_CHANGED, handler2)
        
        # Emit an event
        self.event_bus.emit_event(
            EventType.WEEK_CHANGED,
            {'week_id': 123, 'week_label': 'Test Week'},
            'TestSource'
        )
        
        self.app.processEvents()
        
        # Both handlers should have been called
        assert len(handler1_calls) == 1
        assert len(handler2_calls) == 1
        assert handler1_calls[0].data['week_id'] == 123
        assert handler2_calls[0].data['week_id'] == 123
    
    def test_event_data_integrity(self):
        """Test that event data is preserved correctly"""
        test_data = {
            'week_id': 42,
            'week_label': 'Test Week Label',
            'complex_data': {
                'nested': True,
                'list': [1, 2, 3],
                'string': 'test'
            }
        }
        
        received_data = None
        
        def handler(event_data):
            nonlocal received_data
            received_data = event_data
        
        self.event_bus.connect_handler(EventType.WEEK_CREATED, handler)
        
        # Emit event with complex data
        self.event_bus.emit_event(
            EventType.WEEK_CREATED,
            test_data,
            'TestSource'
        )
        
        self.app.processEvents()
        
        # Verify data integrity
        assert received_data is not None
        assert received_data.event_type == EventType.WEEK_CREATED
        assert received_data.source == 'TestSource'
        assert received_data.data == test_data
        assert received_data.data['complex_data']['nested'] is True
        assert received_data.data['complex_data']['list'] == [1, 2, 3]


if __name__ == '__main__':
    pytest.main([__file__]) 