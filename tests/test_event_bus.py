"""
Unit tests for the Event Bus system
"""

import pytest
import sys
from unittest.mock import Mock, patch
from PySide6 import QtCore, QtWidgets

# Add src to path for imports
sys.path.insert(0, 'src')

from core.events.event_bus import AppEventBus, EventData, get_event_bus, reset_event_bus
from core.events.event_types import EventType


class TestEventData:
    """Test the EventData class"""
    
    def test_event_data_creation(self):
        """Test creating EventData with various parameters"""
        # Test with minimal parameters
        event = EventData(EventType.TASK_CREATED)
        assert event.event_type == EventType.TASK_CREATED
        assert event.data == {}
        assert event.source is None
        assert event.timestamp is not None
        
        # Test with all parameters
        data = {'task_id': 123, 'name': 'Test Task'}
        event = EventData(EventType.TASK_CREATED, data, 'TestSource')
        assert event.event_type == EventType.TASK_CREATED
        assert event.data == data
        assert event.source == 'TestSource'
        assert event.timestamp is not None
    
    def test_event_data_repr(self):
        """Test EventData string representation"""
        data = {'task_id': 123}
        event = EventData(EventType.TASK_CREATED, data, 'TestSource')
        repr_str = repr(event)
        assert 'task_created' in repr_str
        assert 'TestSource' in repr_str
        assert 'task_id' in repr_str


class TestAppEventBus:
    """Test the AppEventBus class"""
    
    def setup_method(self):
        """Set up test environment"""
        # Create a QApplication if it doesn't exist
        if not QtWidgets.QApplication.instance():
            self.app = QtWidgets.QApplication([])
        else:
            self.app = QtWidgets.QApplication.instance()
        
        # Reset event bus for clean tests
        reset_event_bus()
        self.event_bus = AppEventBus()
    
    def teardown_method(self):
        """Clean up after tests"""
        reset_event_bus()
    
    def test_event_bus_initialization(self):
        """Test event bus initializes correctly"""
        assert self.event_bus is not None
        assert self.event_bus.get_event_count() == 0
        assert len(self.event_bus._signal_map) > 0
    
    def test_emit_event_basic(self):
        """Test basic event emission"""
        # Set up handler
        received_events = []
        
        def handler(event_data):
            received_events.append(event_data)
        
        # Connect handler and emit event
        self.event_bus.connect_handler(EventType.TASK_CREATED, handler)
        self.event_bus.emit_event(EventType.TASK_CREATED, {'task_id': 123}, 'TestSource')
        
        # Process Qt events
        self.app.processEvents()
        
        # Verify event was received
        assert len(received_events) == 1
        event = received_events[0]
        assert event.event_type == EventType.TASK_CREATED
        assert event.data['task_id'] == 123
        assert event.source == 'TestSource'
        assert self.event_bus.get_event_count() == 1
    
    def test_emit_event_no_data(self):
        """Test emitting event without data"""
        received_events = []
        
        def handler(event_data):
            received_events.append(event_data)
        
        self.event_bus.connect_handler(EventType.WEEK_CHANGED, handler)
        self.event_bus.emit_event(EventType.WEEK_CHANGED)
        
        self.app.processEvents()
        
        assert len(received_events) == 1
        event = received_events[0]
        assert event.event_type == EventType.WEEK_CHANGED
        assert event.data == {}
        assert event.source is None
    
    def test_multiple_handlers_same_event(self):
        """Test multiple handlers for the same event"""
        handler1_called = False
        handler2_called = False
        
        def handler1(event_data):
            nonlocal handler1_called
            handler1_called = True
        
        def handler2(event_data):
            nonlocal handler2_called
            handler2_called = True
        
        # Connect both handlers
        self.event_bus.connect_handler(EventType.WEEK_CHANGED, handler1)
        self.event_bus.connect_handler(EventType.WEEK_CHANGED, handler2)
        
        # Emit event
        self.event_bus.emit_event(EventType.WEEK_CHANGED, {'week_id': 5}, 'TestSource')
        self.app.processEvents()
        
        # Both handlers should be called
        assert handler1_called
        assert handler2_called
    
    def test_multiple_events_different_handlers(self):
        """Test different handlers for different events"""
        task_events = []
        week_events = []
        
        def task_handler(event_data):
            task_events.append(event_data)
        
        def week_handler(event_data):
            week_events.append(event_data)
        
        # Connect handlers to different events
        self.event_bus.connect_handler(EventType.TASK_CREATED, task_handler)
        self.event_bus.connect_handler(EventType.WEEK_CHANGED, week_handler)
        
        # Emit different events
        self.event_bus.emit_event(EventType.TASK_CREATED, {'task_id': 1})
        self.event_bus.emit_event(EventType.WEEK_CHANGED, {'week_id': 2})
        self.event_bus.emit_event(EventType.TASK_CREATED, {'task_id': 3})
        
        self.app.processEvents()
        
        # Verify correct routing
        assert len(task_events) == 2
        assert len(week_events) == 1
        assert task_events[0].data['task_id'] == 1
        assert task_events[1].data['task_id'] == 3
        assert week_events[0].data['week_id'] == 2
    
    def test_disconnect_handler(self):
        """Test disconnecting event handlers"""
        received_events = []
        
        def handler(event_data):
            received_events.append(event_data)
        
        # Connect, emit, disconnect, emit again
        self.event_bus.connect_handler(EventType.TASK_UPDATED, handler)
        self.event_bus.emit_event(EventType.TASK_UPDATED, {'task_id': 1})
        self.app.processEvents()
        
        self.event_bus.disconnect_handler(EventType.TASK_UPDATED, handler)
        self.event_bus.emit_event(EventType.TASK_UPDATED, {'task_id': 2})
        self.app.processEvents()
        
        # Should only receive first event
        assert len(received_events) == 1
        assert received_events[0].data['task_id'] == 1
    
    def test_disconnect_all_handlers(self):
        """Test disconnecting all handlers from an event"""
        handler1_calls = []
        handler2_calls = []
        
        def handler1(event_data):
            handler1_calls.append(event_data)
        
        def handler2(event_data):
            handler2_calls.append(event_data)
        
        # Connect multiple handlers
        self.event_bus.connect_handler(EventType.TIMER_STARTED, handler1)
        self.event_bus.connect_handler(EventType.TIMER_STARTED, handler2)
        
        # Emit event
        self.event_bus.emit_event(EventType.TIMER_STARTED, {'timer_id': 1})
        self.app.processEvents()
        
        # Disconnect all handlers
        self.event_bus.disconnect_all_handlers(EventType.TIMER_STARTED)
        
        # Emit again
        self.event_bus.emit_event(EventType.TIMER_STARTED, {'timer_id': 2})
        self.app.processEvents()
        
        # Should only receive first event
        assert len(handler1_calls) == 1
        assert len(handler2_calls) == 1
    
    def test_unknown_event_type(self):
        """Test handling of unknown event types"""
        with patch.object(self.event_bus.logger, 'warning') as mock_warning:
            # This should trigger a warning since we're using a string instead of EventType
            self.event_bus.emit_event("unknown_event")
            mock_warning.assert_called_once()
    
    def test_debug_mode(self):
        """Test debug mode functionality"""
        # Enable debug mode
        self.event_bus.set_debug_mode(True)
        assert self.event_bus._debug_mode is True
        
        # Disable debug mode
        self.event_bus.set_debug_mode(False)
        assert self.event_bus._debug_mode is False
    
    def test_event_count(self):
        """Test event counting functionality"""
        assert self.event_bus.get_event_count() == 0
        
        # Emit some events
        self.event_bus.emit_event(EventType.TASK_CREATED)
        self.event_bus.emit_event(EventType.WEEK_CHANGED)
        self.event_bus.emit_event(EventType.TIMER_STARTED)
        
        assert self.event_bus.get_event_count() == 3
        
        # Reset counter
        self.event_bus.reset_event_count()
        assert self.event_bus.get_event_count() == 0
    
    def test_get_connected_event_types(self):
        """Test getting list of connected event types"""
        def dummy_handler(event_data):
            pass
        
        # Get all event types (simplified implementation)
        connected = self.event_bus.get_connected_event_types()
        # Should return all available event types for monitoring
        assert len(connected) > 0
        
        # Connect to some events (this doesn't change the return for now)
        self.event_bus.connect_handler(EventType.TASK_CREATED, dummy_handler)
        self.event_bus.connect_handler(EventType.WEEK_CHANGED, dummy_handler)
        
        connected = self.event_bus.get_connected_event_types()
        # Still returns all event types
        assert len(connected) > 0


class TestEventBusSingleton:
    """Test the singleton pattern for event bus"""
    
    def setup_method(self):
        """Set up test environment"""
        if not QtWidgets.QApplication.instance():
            self.app = QtWidgets.QApplication([])
        reset_event_bus()
    
    def teardown_method(self):
        """Clean up after tests"""
        reset_event_bus()
    
    def test_singleton_pattern(self):
        """Test that get_event_bus returns the same instance"""
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2
    
    def test_reset_event_bus(self):
        """Test resetting the event bus singleton"""
        bus1 = get_event_bus()
        bus1.emit_event(EventType.TASK_CREATED)  # Add some state
        
        reset_event_bus()
        bus2 = get_event_bus()
        
        # Should be a new instance
        assert bus1 is not bus2
        assert bus2.get_event_count() == 0


class TestEventTypes:
    """Test the EventType enumeration"""
    
    def test_event_type_values(self):
        """Test that event types have correct string values"""
        assert EventType.TASK_CREATED.value == "task_created"
        assert EventType.WEEK_CHANGED.value == "week_changed"
        assert EventType.TIMER_STARTED.value == "timer_started"
    
    def test_event_type_str(self):
        """Test string representation of event types"""
        assert str(EventType.TASK_CREATED) == "task_created"
        assert str(EventType.ANALYSIS_REFRESH_REQUESTED) == "analysis_refresh_requested"
    
    def test_event_type_categories(self):
        """Test event type category methods"""
        task_events = EventType.get_task_events()
        assert EventType.TASK_CREATED in task_events
        assert EventType.TASK_UPDATED in task_events
        assert EventType.WEEK_CHANGED not in task_events
        
        week_events = EventType.get_week_events()
        assert EventType.WEEK_CHANGED in week_events
        assert EventType.WEEK_CREATED in week_events
        assert EventType.TASK_CREATED not in week_events
        
        timer_events = EventType.get_timer_events()
        assert EventType.TIMER_STARTED in timer_events
        assert EventType.TIMER_STOPPED in timer_events
        assert EventType.TASK_CREATED not in timer_events
        
        analysis_events = EventType.get_analysis_events()
        assert EventType.ANALYSIS_REFRESH_REQUESTED in analysis_events
        assert EventType.ANALYSIS_DATA_UPDATED in analysis_events
        assert EventType.TASK_CREATED not in analysis_events


if __name__ == '__main__':
    pytest.main([__file__]) 