# Event-Driven Architecture - Qt Signals & Slots System

**Goal**: Implement a sophisticated event-driven architecture using Qt Signals & Slots to create loose coupling, real-time updates, and a plugin-ready system while maintaining your Python backend.

## Current State vs Event-Driven Design

### **Current Tight Coupling Issues**
```python
# Current problematic pattern in your codebase
class TaskGrid(QWidget):
    def update_task(self, task_id, new_data):
        # Direct database modification
        self.db_connection.execute("UPDATE tasks SET ... WHERE id = ?", ...)
        
        # Manual UI updates
        self.refresh_display()
        
        # Manual cache invalidation
        self.clear_week_cache()
        
        # Manual analytics update
        self.parent().analytics_widget.recalculate()
        
        # Manual timer synchronization
        if hasattr(self.parent(), 'timer_widget'):
            self.parent().timer_widget.sync_task_data()
```

### **New Event-Driven Pattern**
```python
# Clean event-driven pattern
class TaskGrid(QWidget):
    def update_task(self, task_id, new_data):
        # Single responsibility: emit event
        self.task_controller.update_task(task_id, new_data)
        # Everything else happens automatically via signals!
```

## Event Bus Architecture

### **Central Event Bus Implementation**
```python
# event_bus.py
from PySide6.QtCore import QObject, Signal, QTimer, Slot
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid

@dataclass
class Event:
    """Represents a system event"""
    id: str
    type: str
    source: str
    target: Optional[str]
    data: Dict[str, Any]
    timestamp: datetime
    priority: int = 0  # Higher = more priority
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now()

class EventBus(QObject):
    """Central event bus for loose coupling between components"""
    
    # Core system events
    taskCreated = Signal(int, dict)  # task_id, task_data
    taskUpdated = Signal(int, dict)  # task_id, changes
    taskDeleted = Signal(int)        # task_id
    
    weekCreated = Signal(int, str)   # week_id, week_label
    weekUpdated = Signal(int, dict)  # week_id, changes
    weekDeleted = Signal(int)        # week_id
    
    timerStarted = Signal(int)       # task_id
    timerStopped = Signal(int, int)  # task_id, duration_added
    timerPaused = Signal(int)        # task_id
    timerResumed = Signal(int)       # task_id
    
    dataRefreshNeeded = Signal(str)  # data_type: 'tasks', 'weeks', 'analytics'
    cacheInvalidated = Signal(str, str)  # cache_type, pattern
    
    analyticsUpdated = Signal(int, dict)  # week_id, analytics_data
    
    # UI events
    navigationRequested = Signal(str, dict)  # target_view, params
    themeChanged = Signal(str)               # theme_name
    settingsChanged = Signal(str, object)    # setting_name, new_value
    
    # System events
    applicationShutdown = Signal()
    errorOccurred = Signal(str, str, dict)   # error_type, message, context
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.event_history: List[Event] = []
        self.max_history = 1000
        
        # Event routing
        self.subscriptions: Dict[str, List[Callable]] = {}
        
        # Performance monitoring
        self.event_count = 0
        self.processing_times: Dict[str, float] = {}
        
        # Batch processing for high-frequency events
        self.batch_timer = QTimer()
        self.batch_timer.timeout.connect(self._process_batched_events)
        self.batch_timer.setSingleShot(True)
        self.batched_events: List[Event] = []
    
    def emit_event(self, event_type: str, source: str, data: Dict[str, Any] = None, 
                   target: str = None, priority: int = 0) -> Event:
        """Emit a custom event through the bus"""
        event = Event(
            id=str(uuid.uuid4()),
            type=event_type,
            source=source,
            target=target,
            data=data or {},
            timestamp=datetime.now(),
            priority=priority
        )
        
        self._record_event(event)
        self._route_event(event)
        return event
    
    def subscribe(self, event_type: str, callback: Callable[[Event], None]) -> None:
        """Subscribe to custom events"""
        if event_type not in self.subscriptions:
            self.subscriptions[event_type] = []
        self.subscriptions[event_type].append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable[[Event], None]) -> None:
        """Unsubscribe from events"""
        if event_type in self.subscriptions:
            try:
                self.subscriptions[event_type].remove(callback)
            except ValueError:
                pass  # Callback wasn't subscribed
    
    def _record_event(self, event: Event) -> None:
        """Record event for debugging and analytics"""
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]
        
        self.event_count += 1
    
    def _route_event(self, event: Event) -> None:
        """Route event to subscribers"""
        subscribers = self.subscriptions.get(event.type, [])
        for callback in subscribers:
            try:
                callback(event)
            except Exception as e:
                self.errorOccurred.emit(
                    "event_routing_error", 
                    f"Error in event subscriber: {str(e)}",
                    {"event_type": event.type, "callback": str(callback)}
                )
    
    def _process_batched_events(self) -> None:
        """Process events that were batched for performance"""
        if not self.batched_events:
            return
        
        # Process events by priority
        self.batched_events.sort(key=lambda e: e.priority, reverse=True)
        
        for event in self.batched_events:
            self._route_event(event)
        
        self.batched_events.clear()
    
    def get_event_statistics(self) -> Dict[str, Any]:
        """Get event bus performance statistics"""
        event_types = {}
        for event in self.event_history[-100:]:  # Last 100 events
            event_types[event.type] = event_types.get(event.type, 0) + 1
        
        return {
            "total_events": self.event_count,
            "recent_event_types": event_types,
            "average_processing_times": self.processing_times,
            "active_subscriptions": {k: len(v) for k, v in self.subscriptions.items()}
        }

# Global event bus instance
event_bus = EventBus()
```

### **Controller Base Class with Event Integration**
```python
# base_controller.py
from PySide6.QtCore import QObject, Slot
from typing import Dict, Any, Optional

class BaseController(QObject):
    """Base class for all controllers with event bus integration"""
    
    def __init__(self, name: str, data_service, cache_service, parent=None):
        super().__init__(parent)
        self.name = name
        self.data_service = data_service
        self.cache_service = cache_service
        self.event_bus = event_bus
        
        # Connect to relevant signals
        self._setup_event_connections()
    
    def _setup_event_connections(self) -> None:
        """Override in subclasses to set up specific event connections"""
        pass
    
    def emit_event(self, event_type: str, data: Dict[str, Any] = None, 
                   target: str = None, priority: int = 0) -> None:
        """Convenience method to emit events"""
        self.event_bus.emit_event(event_type, self.name, data, target, priority)
    
    @Slot(str, dict)
    def handle_settings_change(self, setting_name: str, new_value: Any) -> None:
        """Handle global settings changes - override in subclasses"""
        pass
    
    @Slot()
    def handle_application_shutdown(self) -> None:
        """Handle application shutdown - override in subclasses"""
        pass
```

## Controller Implementations

### **Task Controller with Events**
```python
# task_controller.py
from base_controller import BaseController
from PySide6.QtCore import Slot, Signal
from typing import Dict, Any, List

class TaskController(BaseController):
    """Controller for task operations with event-driven updates"""
    
    # Controller-specific signals
    taskValidationFailed = Signal(int, list)  # task_id, validation_errors
    bulkOperationCompleted = Signal(str, int)  # operation_type, affected_count
    
    def __init__(self, data_service, cache_service, parent=None):
        super().__init__("TaskController", data_service, cache_service, parent)
        
        # Internal state
        self.active_operations = set()
    
    def _setup_event_connections(self) -> None:
        """Set up task-specific event connections"""
        # Connect to timer events
        self.event_bus.timerStopped.connect(self._handle_timer_stopped)
        self.event_bus.weekDeleted.connect(self._handle_week_deleted)
        self.event_bus.settingsChanged.connect(self.handle_settings_change)
        
        # Subscribe to custom events
        self.event_bus.subscribe("task_import_started", self._handle_import_started)
        self.event_bus.subscribe("task_export_requested", self._handle_export_requested)
    
    def create_task(self, week_id: int, task_data: Dict[str, Any]) -> int:
        """Create a new task with full event propagation"""
        try:
            # Validate data
            validation_errors = self._validate_task_data(task_data)
            if validation_errors:
                self.taskValidationFailed.emit(-1, validation_errors)
                return -1
            
            # Create task through data service
            task_id = self.data_service.create_task(week_id, task_data)
            
            # Emit events (data service already emits taskCreated)
            self.emit_event("task_created_with_details", {
                "task_id": task_id,
                "week_id": week_id,
                "creation_method": task_data.get("creation_method", "manual"),
                "has_timer_data": "time_begin" in task_data
            })
            
            return task_id
            
        except Exception as e:
            self.event_bus.errorOccurred.emit(
                "task_creation_error",
                f"Failed to create task: {str(e)}",
                {"week_id": week_id, "task_data": task_data}
            )
            return -1
    
    def update_task(self, task_id: int, changes: Dict[str, Any]) -> bool:
        """Update task with change tracking and events"""
        try:
            # Get current task data for change detection
            current_task = self.data_service.get_task(task_id)
            if not current_task:
                return False
            
            # Detect significant changes
            significant_changes = self._detect_significant_changes(current_task, changes)
            
            # Update through data service
            success = self.data_service.update_task(task_id, changes)
            
            if success and significant_changes:
                self.emit_event("task_significant_change", {
                    "task_id": task_id,
                    "changes": significant_changes,
                    "old_values": {k: current_task.get(k) for k in significant_changes.keys()}
                })
            
            return success
            
        except Exception as e:
            self.event_bus.errorOccurred.emit(
                "task_update_error",
                f"Failed to update task {task_id}: {str(e)}",
                {"task_id": task_id, "changes": changes}
            )
            return False
    
    def bulk_delete_tasks(self, task_ids: List[int]) -> int:
        """Delete multiple tasks with batch events"""
        if not task_ids:
            return 0
        
        self.active_operations.add("bulk_delete")
        deleted_count = 0
        
        try:
            # Collect week_ids for cache invalidation
            affected_weeks = set()
            
            for task_id in task_ids:
                task_data = self.data_service.get_task(task_id)
                if task_data:
                    affected_weeks.add(task_data['week_id'])
                    
                if self.data_service.delete_task(task_id):
                    deleted_count += 1
            
            # Emit bulk completion event
            self.bulkOperationCompleted.emit("delete", deleted_count)
            
            # Emit cache invalidation for affected weeks
            for week_id in affected_weeks:
                self.event_bus.dataRefreshNeeded.emit(f"week_tasks_{week_id}")
            
            return deleted_count
            
        except Exception as e:
            self.event_bus.errorOccurred.emit(
                "bulk_delete_error",
                f"Bulk delete failed: {str(e)}",
                {"task_ids": task_ids, "deleted_count": deleted_count}
            )
            return deleted_count
            
        finally:
            self.active_operations.discard("bulk_delete")
    
    @Slot(int, int)
    def _handle_timer_stopped(self, task_id: int, duration_added: int) -> None:
        """Handle timer stop events"""
        if duration_added > 0:
            self.emit_event("task_timer_contribution", {
                "task_id": task_id,
                "duration_added": duration_added,
                "timestamp": datetime.now().isoformat()
            })
    
    @Slot(int)
    def _handle_week_deleted(self, week_id: int) -> None:
        """Handle week deletion - cleanup related tasks"""
        # This would be handled by database CASCADE, but we can emit cleanup events
        self.emit_event("week_tasks_cleanup", {"week_id": week_id})
    
    def _validate_task_data(self, task_data: Dict[str, Any]) -> List[str]:
        """Validate task data before creation"""
        errors = []
        
        if not task_data.get('project_name'):
            errors.append("Project name is required")
        
        if task_data.get('score') and not (1 <= task_data['score'] <= 5):
            errors.append("Score must be between 1 and 5")
        
        # Add more validation rules as needed
        return errors
    
    def _detect_significant_changes(self, old_data: Dict[str, Any], 
                                  new_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect changes that should trigger special events"""
        significant_fields = ['score', 'project_name', 'duration_seconds']
        significant_changes = {}
        
        for field in significant_fields:
            if field in new_data and old_data.get(field) != new_data[field]:
                significant_changes[field] = new_data[field]
        
        return significant_changes
```

### **Timer Controller with Real-time Events**
```python
# timer_controller.py
from base_controller import BaseController
from PySide6.QtCore import QTimer, Slot, Signal
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class TimerController(BaseController):
    """Controller for timer operations with real-time events"""
    
    # Timer-specific signals
    timerTick = Signal(int, int)  # task_id, current_seconds
    timerFinished = Signal(int)   # task_id (when time limit reached)
    
    def __init__(self, data_service, cache_service, parent=None):
        super().__init__("TimerController", data_service, cache_service, parent)
        
        # Timer state
        self.active_timers: Dict[int, QTimer] = {}
        self.timer_start_times: Dict[int, datetime] = {}
        self.accumulated_durations: Dict[int, int] = {}  # seconds
        
        # Global timer for UI updates
        self.ui_update_timer = QTimer()
        self.ui_update_timer.timeout.connect(self._update_active_timers)
        self.ui_update_timer.start(1000)  # Update every second
    
    def _setup_event_connections(self) -> None:
        """Set up timer-specific event connections"""
        self.event_bus.taskDeleted.connect(self._handle_task_deleted)
        self.event_bus.applicationShutdown.connect(self._handle_shutdown)
    
    def start_timer(self, task_id: int) -> bool:
        """Start timer for a task"""
        try:
            # Stop any existing timer for this task
            self.stop_timer(task_id)
            
            # Get current task duration
            task_data = self.data_service.get_task(task_id)
            if not task_data:
                return False
            
            current_duration = task_data.get('duration_seconds', 0)
            self.accumulated_durations[task_id] = current_duration
            self.timer_start_times[task_id] = datetime.now()
            
            # Create and start timer
            timer = QTimer()
            timer.timeout.connect(lambda: self._timer_tick(task_id))
            timer.start(1000)  # Tick every second
            self.active_timers[task_id] = timer
            
            # Emit events
            self.event_bus.timerStarted.emit(task_id)
            self.emit_event("timer_session_started", {
                "task_id": task_id,
                "start_time": self.timer_start_times[task_id].isoformat(),
                "initial_duration": current_duration
            })
            
            return True
            
        except Exception as e:
            self.event_bus.errorOccurred.emit(
                "timer_start_error",
                f"Failed to start timer for task {task_id}: {str(e)}",
                {"task_id": task_id}
            )
            return False
    
    def stop_timer(self, task_id: int, save_duration: bool = True) -> int:
        """Stop timer and optionally save duration"""
        if task_id not in self.active_timers:
            return 0
        
        try:
            # Stop the timer
            timer = self.active_timers[task_id]
            timer.stop()
            timer.deleteLater()
            del self.active_timers[task_id]
            
            # Calculate session duration
            start_time = self.timer_start_times.get(task_id)
            session_duration = 0
            
            if start_time:
                session_duration = int((datetime.now() - start_time).total_seconds())
                del self.timer_start_times[task_id]
            
            # Update total duration
            if save_duration and session_duration > 0:
                new_total = self.accumulated_durations.get(task_id, 0) + session_duration
                self.data_service.update_task_duration(task_id, new_total, method='timer')
                
                # Emit events
                self.event_bus.timerStopped.emit(task_id, session_duration)
                self.emit_event("timer_session_completed", {
                    "task_id": task_id,
                    "session_duration": session_duration,
                    "total_duration": new_total,
                    "end_time": datetime.now().isoformat()
                })
            
            # Cleanup
            self.accumulated_durations.pop(task_id, None)
            
            return session_duration
            
        except Exception as e:
            self.event_bus.errorOccurred.emit(
                "timer_stop_error",
                f"Failed to stop timer for task {task_id}: {str(e)}",
                {"task_id": task_id}
            )
            return 0
    
    def pause_timer(self, task_id: int) -> bool:
        """Pause timer (stop but save current session)"""
        if task_id not in self.active_timers:
            return False
        
        session_duration = self.stop_timer(task_id, save_duration=True)
        
        if session_duration > 0:
            self.event_bus.timerPaused.emit(task_id)
            self.emit_event("timer_paused", {
                "task_id": task_id,
                "session_duration": session_duration
            })
        
        return True
    
    def _timer_tick(self, task_id: int) -> None:
        """Handle timer tick"""
        if task_id not in self.timer_start_times:
            return
        
        start_time = self.timer_start_times[task_id]
        elapsed = int((datetime.now() - start_time).total_seconds())
        total_duration = self.accumulated_durations.get(task_id, 0) + elapsed
        
        # Emit tick event
        self.timerTick.emit(task_id, total_duration)
        
        # Check time limit
        task_data = self.data_service.get_task(task_id)
        if task_data and task_data.get('time_limit_seconds', 0) > 0:
            if total_duration >= task_data['time_limit_seconds']:
                self.timerFinished.emit(task_id)
                self.stop_timer(task_id)
    
    def _update_active_timers(self) -> None:
        """Update all active timers for UI synchronization"""
        for task_id in list(self.active_timers.keys()):
            self._timer_tick(task_id)
    
    @Slot(int)
    def _handle_task_deleted(self, task_id: int) -> None:
        """Handle task deletion - stop any active timers"""
        if task_id in self.active_timers:
            self.stop_timer(task_id, save_duration=False)
    
    @Slot()
    def _handle_shutdown(self) -> None:
        """Handle application shutdown - save all active timers"""
        for task_id in list(self.active_timers.keys()):
            self.stop_timer(task_id, save_duration=True)
    
    def get_active_timers(self) -> List[int]:
        """Get list of task IDs with active timers"""
        return list(self.active_timers.keys())
    
    def is_timer_active(self, task_id: int) -> bool:
        """Check if timer is active for a task"""
        return task_id in self.active_timers
```

## QML Integration with Events

### **Event-Aware QML Components**
```qml
// TaskListView.qml
import QtQuick 2.15
import QtQuick.Controls 2.15

ListView {
    id: taskListView
    
    property TaskController taskController
    property bool autoRefresh: true
    
    // Connect to controller signals
    Connections {
        target: taskController
        
        function onTaskCreated(taskId, taskData) {
            if (autoRefresh) {
                model.refresh()
            }
            // Animate new item appearance
            addItemAnimation.start()
        }
        
        function onTaskUpdated(taskId, changes) {
            // Find and update specific item
            for (let i = 0; i < model.count; i++) {
                if (model.get(i).id === taskId) {
                    // Update only changed properties
                    for (let prop in changes) {
                        model.setProperty(i, prop, changes[prop])
                    }
                    break
                }
            }
        }
        
        function onTaskDeleted(taskId) {
            // Remove item with animation
            for (let i = 0; i < model.count; i++) {
                if (model.get(i).id === taskId) {
                    removeItemAnimation.itemIndex = i
                    removeItemAnimation.start()
                    break
                }
            }
        }
        
        function onBulkOperationCompleted(operationType, affectedCount) {
            if (operationType === "delete") {
                // Show success message
                statusMessage.showMessage(`${affectedCount} tasks deleted`)
                model.refresh()
            }
        }
    }
    
    // Animation for new items
    PropertyAnimation {
        id: addItemAnimation
        target: taskListView
        property: "contentY"
        duration: 300
        easing.type: Easing.OutQuad
    }
    
    // Animation for removed items
    SequentialAnimation {
        id: removeItemAnimation
        property int itemIndex: -1
        
        PropertyAnimation {
            target: taskListView.itemAtIndex(removeItemAnimation.itemIndex)
            property: "opacity"
            to: 0
            duration: 200
        }
        
        ScriptAction {
            script: {
                if (removeItemAnimation.itemIndex >= 0) {
                    model.remove(removeItemAnimation.itemIndex)
                }
            }
        }
    }
    
    delegate: TaskItemDelegate {
        width: taskListView.width
        
        // Pass controller reference
        taskController: taskListView.taskController
        
        // Handle item-specific events
        onEditRequested: {
            taskController.editTask(model.id)
        }
        
        onDeleteRequested: {
            taskController.deleteTask(model.id)
        }
        
        onTimerToggleRequested: {
            if (model.timerActive) {
                taskController.timerController.stopTimer(model.id)
            } else {
                taskController.timerController.startTimer(model.id)
            }
        }
    }
}
```

## Benefits of This Architecture

### **1. Loose Coupling**
- Components don't know about each other directly
- Easy to add/remove features without breaking existing code
- Testable in isolation

### **2. Real-time Responsiveness**
- UI updates automatically when data changes
- No manual refresh required
- Smooth animations and transitions

### **3. Scalability**
- Easy to add new controllers
- Plugin architecture ready
- Event-driven performance optimizations

### **4. Debugging & Monitoring**
- Full event history for debugging
- Performance metrics built-in
- Error tracking and reporting

This event-driven architecture transforms your application into a responsive, maintainable, and extensible system while preserving all existing functionality. 