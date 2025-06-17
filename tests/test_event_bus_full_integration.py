"""
Comprehensive integration tests for the fully integrated Event Bus system.
Tests the complete event flow between MainWindow, QMLTaskGrid, TimerDialog, and AnalysisWidget.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.events import get_event_bus, reset_event_bus, EventType
from core.events.event_bus import EventData


class TestFullEventBusIntegration:
    """Test complete event bus integration across all components"""
    
    def setup_method(self):
        """Reset event bus before each test"""
        reset_event_bus()
        self.event_bus = get_event_bus()
        
        # Mock components
        self.main_window = Mock()
        self.task_grid = Mock()
        self.timer_dialog = Mock()
        self.analysis_widget = Mock()
        
        # Track events received by each component
        self.main_window_events = []
        self.task_grid_events = []
        self.timer_dialog_events = []
        self.analysis_widget_events = []
        
        # Setup event handlers for each component
        self._setup_component_handlers()
    
    def _setup_component_handlers(self):
        """Setup event handlers to track events received by each component"""
        
        # MainWindow handlers
        def main_window_handler(event_data):
            self.main_window_events.append(event_data)
        
        # TaskGrid handlers
        def task_grid_handler(event_data):
            self.task_grid_events.append(event_data)
        
        # TimerDialog handlers
        def timer_dialog_handler(event_data):
            self.timer_dialog_events.append(event_data)
        
        # AnalysisWidget handlers
        def analysis_widget_handler(event_data):
            self.analysis_widget_events.append(event_data)
        
        # Connect handlers for different event types
        
        # MainWindow listens to most events
        self.event_bus.connect_handler(EventType.WEEK_CHANGED, main_window_handler)
        self.event_bus.connect_handler(EventType.TASK_CREATED, main_window_handler)
        self.event_bus.connect_handler(EventType.TASK_UPDATED, main_window_handler)
        self.event_bus.connect_handler(EventType.TASK_DELETED, main_window_handler)
        self.event_bus.connect_handler(EventType.TASK_SELECTION_CHANGED, main_window_handler)
        self.event_bus.connect_handler(EventType.TIMER_STOPPED, main_window_handler)
        
        # TaskGrid listens to UI refresh requests
        self.event_bus.connect_handler(EventType.UI_REFRESH_REQUESTED, task_grid_handler)
        self.event_bus.connect_handler(EventType.DELETE_BUTTON_UPDATE_REQUESTED, task_grid_handler)
        
        # TimerDialog listens to timer events
        self.event_bus.connect_handler(EventType.TIMER_STARTED, timer_dialog_handler)
        self.event_bus.connect_handler(EventType.TIMER_PAUSED, timer_dialog_handler)
        self.event_bus.connect_handler(EventType.TIMER_STOPPED, timer_dialog_handler)
        
        # AnalysisWidget listens to data change events
        self.event_bus.connect_handler(EventType.TASK_CREATED, analysis_widget_handler)
        self.event_bus.connect_handler(EventType.TASK_UPDATED, analysis_widget_handler)
        self.event_bus.connect_handler(EventType.TASK_DELETED, analysis_widget_handler)
        self.event_bus.connect_handler(EventType.TASKS_BULK_UPDATED, analysis_widget_handler)
        self.event_bus.connect_handler(EventType.WEEK_CREATED, analysis_widget_handler)
        self.event_bus.connect_handler(EventType.WEEK_DELETED, analysis_widget_handler)
        self.event_bus.connect_handler(EventType.TIMER_STOPPED, analysis_widget_handler)
        self.event_bus.connect_handler(EventType.ANALYSIS_REFRESH_REQUESTED, analysis_widget_handler)
    
    def test_task_creation_workflow(self):
        """Test complete task creation workflow through event bus"""
        
        # Simulate task creation from QMLTaskGrid
        self.event_bus.emit_event(
            EventType.TASK_CREATED,
            {
                'task_id': 123,
                'week_id': 1,
                'action': 'created'
            },
            'QMLTaskGrid'
        )
        
        # Verify MainWindow received the event
        assert len(self.main_window_events) == 1
        event = self.main_window_events[0]
        assert event.event_type == EventType.TASK_CREATED
        assert event.data['task_id'] == 123
        assert event.source == 'QMLTaskGrid'
        
        # Verify AnalysisWidget received the event
        assert len(self.analysis_widget_events) == 1
        event = self.analysis_widget_events[0]
        assert event.event_type == EventType.TASK_CREATED
        assert event.data['task_id'] == 123
    
    def test_task_selection_workflow(self):
        """Test task selection change workflow"""
        
        # Simulate task selection change from QMLTaskGrid
        self.event_bus.emit_event(
            EventType.TASK_SELECTION_CHANGED,
            {
                'selected_count': 2,
                'selected_task_ids': [123, 124]
            },
            'QMLTaskGrid'
        )
        
        # Verify MainWindow received the event
        assert len(self.main_window_events) == 1
        event = self.main_window_events[0]
        assert event.event_type == EventType.TASK_SELECTION_CHANGED
        assert event.data['selected_count'] == 2
        assert event.data['selected_task_ids'] == [123, 124]
    
    def test_timer_workflow(self):
        """Test complete timer workflow through event bus"""
        
        # 1. Timer started
        self.event_bus.emit_event(
            EventType.TIMER_STARTED,
            {
                'task_id': 123,
                'current_seconds': 0,
                'is_first_start': True,
                'start_timestamp': datetime.now().isoformat()
            },
            'TimerDialog'
        )
        
        # Verify TimerDialog received the event
        assert len(self.timer_dialog_events) == 1
        event = self.timer_dialog_events[0]
        assert event.event_type == EventType.TIMER_STARTED
        assert event.data['task_id'] == 123
        
        # 2. Timer paused
        self.event_bus.emit_event(
            EventType.TIMER_PAUSED,
            {
                'task_id': 123,
                'current_seconds': 300,
                'duration_changed': True
            },
            'TimerDialog'
        )
        
        # Verify TimerDialog received the pause event
        assert len(self.timer_dialog_events) == 2
        event = self.timer_dialog_events[1]
        assert event.event_type == EventType.TIMER_PAUSED
        assert event.data['current_seconds'] == 300
        
        # 3. Timer stopped
        self.event_bus.emit_event(
            EventType.TIMER_STOPPED,
            {
                'task_id': 123,
                'final_seconds': 600,
                'duration_changed': True,
                'was_first_start': True
            },
            'TimerDialog'
        )
        
        # Verify multiple components received the stop event
        assert len(self.timer_dialog_events) == 3
        assert len(self.main_window_events) == 1
        assert len(self.analysis_widget_events) == 1
        
        # Check MainWindow received timer stop
        main_event = self.main_window_events[0]
        assert main_event.event_type == EventType.TIMER_STOPPED
        assert main_event.data['final_seconds'] == 600
        
        # Check AnalysisWidget received timer stop
        analysis_event = self.analysis_widget_events[0]
        assert analysis_event.event_type == EventType.TIMER_STOPPED
        assert analysis_event.data['duration_changed'] is True
    
    def test_week_change_workflow(self):
        """Test week change workflow through event bus"""
        
        # Simulate week change from WeekWidget
        self.event_bus.emit_event(
            EventType.WEEK_CHANGED,
            {
                'week_id': 5,
                'week_label': 'Week 5 - Test Week'
            },
            'WeekWidget'
        )
        
        # Verify MainWindow received the event
        assert len(self.main_window_events) == 1
        event = self.main_window_events[0]
        assert event.event_type == EventType.WEEK_CHANGED
        assert event.data['week_id'] == 5
        assert event.data['week_label'] == 'Week 5 - Test Week'
        assert event.source == 'WeekWidget'
    
    def test_bulk_task_operations(self):
        """Test bulk task operations workflow"""
        
        # Simulate bulk task deletion
        self.event_bus.emit_event(
            EventType.TASKS_BULK_UPDATED,
            {
                'action': 'deleted',
                'task_ids': [123, 124, 125],
                'count': 3,
                'week_id': 1
            },
            'QMLTaskGrid'
        )
        
        # Verify AnalysisWidget received the bulk update event
        assert len(self.analysis_widget_events) == 1
        event = self.analysis_widget_events[0]
        assert event.event_type == EventType.TASKS_BULK_UPDATED
        assert event.data['action'] == 'deleted'
        assert event.data['count'] == 3
        assert len(event.data['task_ids']) == 3
    
    def test_analysis_refresh_workflow(self):
        """Test analysis refresh request workflow"""
        
        # Simulate analysis refresh request
        self.event_bus.emit_event(
            EventType.ANALYSIS_REFRESH_REQUESTED,
            {
                'reason': 'task_data_changed',
                'source_event': 'TASK_UPDATED',
                'week_id': 1
            },
            'AnalysisWidget'
        )
        
        # Verify AnalysisWidget received the refresh request
        assert len(self.analysis_widget_events) == 1
        event = self.analysis_widget_events[0]
        assert event.event_type == EventType.ANALYSIS_REFRESH_REQUESTED
        assert event.data['reason'] == 'task_data_changed'
        assert event.data['week_id'] == 1
    
    def test_ui_refresh_workflow(self):
        """Test UI refresh request workflow"""
        
        # Simulate UI refresh request from MainWindow
        self.event_bus.emit_event(
            EventType.UI_REFRESH_REQUESTED,
            {
                'reason': 'week_changed',
                'week_id': 3,
                'week_label': 'Week 3'
            },
            'MainWindow'
        )
        
        # Verify TaskGrid received the UI refresh request
        assert len(self.task_grid_events) == 1
        event = self.task_grid_events[0]
        assert event.event_type == EventType.UI_REFRESH_REQUESTED
        assert event.data['reason'] == 'week_changed'
        assert event.data['week_id'] == 3
    
    def test_delete_button_update_workflow(self):
        """Test delete button update request workflow"""
        
        # Simulate delete button update request
        self.event_bus.emit_event(
            EventType.DELETE_BUTTON_UPDATE_REQUESTED,
            {'trigger': 'selection_changed'},
            'QMLTaskGrid'
        )
        
        # Verify TaskGrid received the delete button update request
        assert len(self.task_grid_events) == 1
        event = self.task_grid_events[0]
        assert event.event_type == EventType.DELETE_BUTTON_UPDATE_REQUESTED
        assert event.data['trigger'] == 'selection_changed'
    
    def test_cross_component_communication_chain(self):
        """Test a complex chain of events across multiple components"""
        
        # 1. Week changes (WeekWidget -> MainWindow)
        self.event_bus.emit_event(
            EventType.WEEK_CHANGED,
            {'week_id': 2, 'week_label': 'Week 2'},
            'WeekWidget'
        )
        
        # 2. Task is created (QMLTaskGrid -> MainWindow, AnalysisWidget)
        self.event_bus.emit_event(
            EventType.TASK_CREATED,
            {'task_id': 456, 'week_id': 2, 'action': 'created'},
            'QMLTaskGrid'
        )
        
        # 3. Timer is used (TimerDialog -> MainWindow, AnalysisWidget)
        self.event_bus.emit_event(
            EventType.TIMER_STOPPED,
            {
                'task_id': 456,
                'final_seconds': 1800,
                'duration_changed': True,
                'was_first_start': True
            },
            'TimerDialog'
        )
        
        # 4. Task is updated (QMLTaskGrid -> MainWindow, AnalysisWidget)
        self.event_bus.emit_event(
            EventType.TASK_UPDATED,
            {
                'task_id': 456,
                'action': 'timer_update',
                'duration': '00:30:00',
                'week_id': 2
            },
            'QMLTaskGrid'
        )
        
        # Verify event counts
        assert len(self.main_window_events) == 4  # All events
        assert len(self.analysis_widget_events) == 3  # Task created, timer stopped, task updated
        assert len(self.timer_dialog_events) == 1  # Timer stopped
        
        # Verify event sequence in MainWindow
        main_events = [e.event_type for e in self.main_window_events]
        expected_main_events = [
            EventType.WEEK_CHANGED,
            EventType.TASK_CREATED,
            EventType.TIMER_STOPPED,
            EventType.TASK_UPDATED
        ]
        assert main_events == expected_main_events
        
        # Verify event sequence in AnalysisWidget
        analysis_events = [e.event_type for e in self.analysis_widget_events]
        expected_analysis_events = [
            EventType.TASK_CREATED,
            EventType.TIMER_STOPPED,
            EventType.TASK_UPDATED
        ]
        assert analysis_events == expected_analysis_events
    
    def test_event_data_integrity(self):
        """Test that event data maintains integrity across the bus"""
        
        complex_data = {
            'task_id': 789,
            'metadata': {
                'duration': '01:15:30',
                'project': 'Test Project',
                'nested': {
                    'score': 95,
                    'feedback': 'Excellent work'
                }
            },
            'timestamps': [
                '2024-01-01T10:00:00',
                '2024-01-01T11:15:30'
            ]
        }
        
        # Emit event with complex data
        self.event_bus.emit_event(
            EventType.TASK_UPDATED,
            complex_data,
            'TestComponent'
        )
        
        # Verify data integrity in received events
        assert len(self.main_window_events) == 1
        assert len(self.analysis_widget_events) == 1
        
        # Check MainWindow received data
        main_event = self.main_window_events[0]
        assert main_event.data == complex_data
        assert main_event.data['metadata']['nested']['score'] == 95
        assert len(main_event.data['timestamps']) == 2
        
        # Check AnalysisWidget received same data
        analysis_event = self.analysis_widget_events[0]
        assert analysis_event.data == complex_data
        assert analysis_event.data['metadata']['project'] == 'Test Project'
    
    def test_event_bus_performance_with_multiple_handlers(self):
        """Test event bus performance with many handlers"""
        
        # Add many handlers for the same event type
        handler_call_count = 0
        
        def counting_handler(event_data):
            nonlocal handler_call_count
            handler_call_count += 1
        
        # Connect 10 additional handlers
        for i in range(10):
            self.event_bus.connect_handler(EventType.TASK_CREATED, counting_handler)
        
        # Emit event
        self.event_bus.emit_event(
            EventType.TASK_CREATED,
            {'task_id': 999, 'week_id': 1},
            'TestComponent'
        )
        
        # Verify all handlers were called
        assert handler_call_count == 10
        
        # Verify original handlers still work
        assert len(self.main_window_events) == 1
        assert len(self.analysis_widget_events) == 1
    
    def teardown_method(self):
        """Clean up after each test"""
        reset_event_bus() 