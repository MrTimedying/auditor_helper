from PySide6.QtCore import QObject, Slot
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, Optional
from ..events.event_bus import get_event_bus
from ..events.event_types import EventType
from ..repositories.task_repository import TaskRepository

class TimerController(QObject):
    """Controller for timer-related operations"""
    
    def __init__(self, task_repository: TaskRepository, parent=None):
        super().__init__(parent)
        self._repository = task_repository
        self._event_bus = get_event_bus()
        self._logger = logging.getLogger(__name__)
        self._active_timers = {}  # task_id -> start_time mapping
        
        # Connect to events
        self._event_bus.connect_handler(EventType.TIMER_STARTED, self._on_timer_started)
        self._event_bus.connect_handler(EventType.TIMER_STOPPED, self._on_timer_stopped)
        self._event_bus.connect_handler(EventType.TIMER_PAUSED, self._on_timer_paused)
        self._event_bus.connect_handler(EventType.TIMER_RESUMED, self._on_timer_resumed)
        
        # Try to import Rust Timer Engine for high-performance operations
        try:
            from ..performance.rust_timer_engine import RustTimerEngine
            self._rust_timer = RustTimerEngine()
            self._use_rust = True
            self._logger.info("Rust Timer Engine loaded successfully")
        except ImportError:
            self._rust_timer = None
            self._use_rust = False
            self._logger.warning("Rust Timer Engine not available, using Python fallback")
    
    @Slot(int)
    def start_timer(self, task_id: int):
        """Start timer for task"""
        try:
            start_time = datetime.now()
            
            if self._use_rust and self._rust_timer:
                # Use high-precision Rust timer
                timer_id = self._rust_timer.create_high_precision_timer()
                self._active_timers[task_id] = {
                    'start_time': start_time,
                    'timer_id': timer_id,
                    'rust_timer': True
                }
            else:
                # Python fallback
                self._active_timers[task_id] = {
                    'start_time': start_time,
                    'rust_timer': False
                }
            
            # Update task with start time
            start_time_str = start_time.strftime("%H:%M:%S")
            self._repository.update(task_id, time_begin=start_time_str)
            
            self._event_bus.emit_event(
                EventType.TIMER_STARTED,
                {'task_id': task_id, 'start_time': start_time_str},
                'TimerController'
            )
            self._logger.info(f"Started timer for task {task_id}")
            
        except Exception as e:
            self._logger.error(f"Failed to start timer: {e}")
            self._event_bus.emit_event(
                EventType.ERROR_OCCURRED,
                {'operation': 'start_timer', 'error': str(e), 'task_id': task_id},
                'TimerController'
            )
    
    @Slot(int, int)
    def stop_timer(self, task_id: int, duration_seconds: int = None):
        """Stop timer for task"""
        try:
            if task_id not in self._active_timers:
                self._logger.warning(f"No active timer found for task {task_id}")
                return
            
            timer_info = self._active_timers[task_id]
            end_time = datetime.now()
            
            if duration_seconds is None:
                # Calculate duration
                if timer_info.get('rust_timer') and self._rust_timer:
                    # Use Rust high-precision calculation
                    duration_seconds = self._rust_timer.calculate_elapsed_time(
                        timer_info['timer_id']
                    )
                else:
                    # Python fallback
                    duration_delta = end_time - timer_info['start_time']
                    duration_seconds = int(duration_delta.total_seconds())
            
            # Format duration as HH:MM:SS
            duration_str = str(timedelta(seconds=duration_seconds))
            end_time_str = end_time.strftime("%H:%M:%S")
            
            # Update task with end time and duration
            self._repository.update(task_id, 
                                  time_end=end_time_str, 
                                  duration=duration_str)
            
            # Clean up timer
            del self._active_timers[task_id]
            
            self._event_bus.emit_event(
                EventType.TIMER_STOPPED,
                {'task_id': task_id, 'duration_seconds': duration_seconds, 'duration': duration_str},
                'TimerController'
            )
            self._logger.info(f"Stopped timer for task {task_id}, duration: {duration_str}")
            
        except Exception as e:
            self._logger.error(f"Failed to stop timer: {e}")
            self._event_bus.emit_event(
                EventType.ERROR_OCCURRED,
                {'operation': 'stop_timer', 'error': str(e), 'task_id': task_id},
                'TimerController'
            )
    
    @Slot(int)
    def pause_timer(self, task_id: int):
        """Pause timer for task"""
        try:
            if task_id not in self._active_timers:
                self._logger.warning(f"No active timer found for task {task_id}")
                return
            
            timer_info = self._active_timers[task_id]
            pause_time = datetime.now()
            
            # Calculate elapsed time so far
            if timer_info.get('rust_timer') and self._rust_timer:
                elapsed_seconds = self._rust_timer.calculate_elapsed_time(
                    timer_info['timer_id']
                )
            else:
                elapsed_delta = pause_time - timer_info['start_time']
                elapsed_seconds = int(elapsed_delta.total_seconds())
            
            # Store paused state
            timer_info['paused_at'] = pause_time
            timer_info['elapsed_seconds'] = elapsed_seconds
            
            self._event_bus.emit_with_error_handling(
                self._event_bus.timer_paused, task_id, elapsed_seconds
            )
            self._logger.info(f"Paused timer for task {task_id}")
            
        except Exception as e:
            self._logger.error(f"Failed to pause timer: {e}")
            self._event_bus.emit_with_error_handling(
                self._event_bus.operation_failed,
                "pause_timer", str(e), {"task_id": task_id}
            )
    
    @Slot(int)
    def resume_timer(self, task_id: int):
        """Resume paused timer for task"""
        try:
            if task_id not in self._active_timers:
                self._logger.warning(f"No active timer found for task {task_id}")
                return
            
            timer_info = self._active_timers[task_id]
            if 'paused_at' not in timer_info:
                self._logger.warning(f"Timer for task {task_id} is not paused")
                return
            
            resume_time = datetime.now()
            
            # Adjust start time to account for pause duration
            pause_duration = resume_time - timer_info['paused_at']
            timer_info['start_time'] += pause_duration
            
            # Remove pause markers
            del timer_info['paused_at']
            if 'elapsed_seconds' in timer_info:
                del timer_info['elapsed_seconds']
            
            self._event_bus.emit_with_error_handling(
                self._event_bus.timer_resumed, task_id
            )
            self._logger.info(f"Resumed timer for task {task_id}")
            
        except Exception as e:
            self._logger.error(f"Failed to resume timer: {e}")
            self._event_bus.emit_with_error_handling(
                self._event_bus.operation_failed,
                "resume_timer", str(e), {"task_id": task_id}
            )
    
    @Slot(int, result=bool)
    def is_timer_active(self, task_id: int) -> bool:
        """Check if timer is active for task"""
        return task_id in self._active_timers
    
    @Slot(int, result=int)
    def get_elapsed_time(self, task_id: int) -> int:
        """Get elapsed time in seconds for active timer"""
        if task_id not in self._active_timers:
            return 0
        
        try:
            timer_info = self._active_timers[task_id]
            
            if 'paused_at' in timer_info:
                # Timer is paused, return stored elapsed time
                return timer_info.get('elapsed_seconds', 0)
            
            if timer_info.get('rust_timer') and self._rust_timer:
                # Use Rust high-precision calculation
                return self._rust_timer.calculate_elapsed_time(timer_info['timer_id'])
            else:
                # Python fallback
                current_time = datetime.now()
                elapsed_delta = current_time - timer_info['start_time']
                return int(elapsed_delta.total_seconds())
                
        except Exception as e:
            self._logger.error(f"Failed to get elapsed time: {e}")
            return 0
    
    @Slot(result='QVariant')
    def get_active_timers(self) -> Dict[int, Dict[str, Any]]:
        """Get all active timers"""
        active_timers = {}
        for task_id, timer_info in self._active_timers.items():
            active_timers[task_id] = {
                'start_time': timer_info['start_time'].isoformat(),
                'elapsed_seconds': self.get_elapsed_time(task_id),
                'is_paused': 'paused_at' in timer_info,
                'rust_timer': timer_info.get('rust_timer', False)
            }
        return active_timers
    
    # Event handlers
    def _on_timer_started(self, event_data):
        """Handle timer started event"""
        pass  # Additional processing if needed
    
    def _on_timer_stopped(self, event_data):
        """Handle timer stopped event"""
        if hasattr(self._repository._data_service, 'clear_cache'):
            self._repository._data_service.clear_cache()
    
    def _on_timer_paused(self, event_data):
        """Handle timer paused event"""
        pass  # Additional processing if needed
    
    def _on_timer_resumed(self, event_data):
        """Handle timer resumed event"""
        pass  # Additional processing if needed 