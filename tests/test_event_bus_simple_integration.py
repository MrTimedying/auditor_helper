"""
Simple integration tests for Event Bus functionality
"""

import pytest
import sys
from PySide6 import QtCore, QtWidgets

# Add src to path for imports
sys.path.insert(0, 'src')

from core.events.event_bus import get_event_bus, reset_event_bus
from core.events.event_types import EventType


class TestEventBusSimpleIntegration:
    """Test basic event bus functionality"""
    
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
    
    def teardown_method(self):
        """Clean up after tests"""
        reset_event_bus()
    
    def test_week_events_flow(self):
        """Test the complete flow of week-related events"""
        received_events = []
        
        def event_handler(event_data):
            received_events.append(event_data)
        
        # Connect to all week events
        self.event_bus.connect_handler(EventType.WEEK_CREATED, event_handler)
        self.event_bus.connect_handler(EventType.WEEK_CHANGED, event_handler)
        self.event_bus.connect_handler(EventType.WEEK_DELETED, event_handler)
        
        # Simulate week creation
        self.event_bus.emit_event(
            EventType.WEEK_CREATED,
            {
                'week_id': 1,
                'week_label': '01/01/2024 - 07/01/2024',
                'week_data': {'start_day': 1, 'end_day': 7}
            },
            'WeekWidget'
        )
        
        # Simulate week selection change
        self.event_bus.emit_event(
            EventType.WEEK_CHANGED,
            {
                'week_id': 1,
                'week_label': '01/01/2024 - 07/01/2024'
            },
            'WeekWidget'
        )
        
        # Simulate week deletion
        self.event_bus.emit_event(
            EventType.WEEK_DELETED,
            {
                'week_id': 1,
                'week_label': '01/01/2024 - 07/01/2024'
            },
            'WeekWidget'
        )
        
        # Process Qt events
        self.app.processEvents()
        
        # Verify all events were received
        assert len(received_events) == 3
        
        # Verify event types and order
        assert received_events[0].event_type == EventType.WEEK_CREATED
        assert received_events[1].event_type == EventType.WEEK_CHANGED
        assert received_events[2].event_type == EventType.WEEK_DELETED
        
        # Verify event data
        for event in received_events:
            assert event.data['week_id'] == 1
            assert event.data['week_label'] == '01/01/2024 - 07/01/2024'
            assert event.source == 'WeekWidget'
    
    def test_cross_component_communication(self):
        """Test communication between different components via event bus"""
        # Simulate different components
        week_widget_events = []
        task_grid_events = []
        analysis_widget_events = []
        
        def week_widget_handler(event_data):
            week_widget_events.append(event_data)
        
        def task_grid_handler(event_data):
            task_grid_events.append(event_data)
        
        def analysis_widget_handler(event_data):
            analysis_widget_events.append(event_data)
        
        # Each component listens to relevant events
        self.event_bus.connect_handler(EventType.WEEK_CHANGED, week_widget_handler)
        self.event_bus.connect_handler(EventType.WEEK_CHANGED, task_grid_handler)  # TaskGrid also needs to know
        self.event_bus.connect_handler(EventType.WEEK_CHANGED, analysis_widget_handler)  # Analysis too
        
        self.event_bus.connect_handler(EventType.TASK_CREATED, task_grid_handler)
        self.event_bus.connect_handler(EventType.TASK_CREATED, analysis_widget_handler)  # Analysis needs task updates
        
        # Simulate week change - should notify all components
        self.event_bus.emit_event(
            EventType.WEEK_CHANGED,
            {'week_id': 2, 'week_label': '08/01/2024 - 14/01/2024'},
            'WeekWidget'
        )
        
        # Simulate task creation - should notify task grid and analysis
        self.event_bus.emit_event(
            EventType.TASK_CREATED,
            {'task_id': 201, 'task_name': 'New Task', 'week_id': 2},
            'TaskGrid'
        )
        
        self.app.processEvents()
        
        # Verify cross-component communication
        assert len(week_widget_events) == 1  # Only week change
        assert len(task_grid_events) == 2     # Week change + task creation
        assert len(analysis_widget_events) == 2  # Week change + task creation
        
        # Verify event data consistency
        assert week_widget_events[0].data['week_id'] == 2
        assert task_grid_events[0].data['week_id'] == 2  # Week change
        assert task_grid_events[1].data['task_id'] == 201  # Task creation
        assert analysis_widget_events[1].data['task_id'] == 201  # Task creation


if __name__ == '__main__':
    pytest.main([__file__]) 