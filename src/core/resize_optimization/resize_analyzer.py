"""
Resize Event Analyzer

This module provides analysis capabilities for window resize events,
tracking frequency, patterns, and timing to understand resize behavior.
"""

import time
from collections import deque
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
from PySide6 import QtCore, QtGui


class ResizeState(Enum):
    """Resize operation states"""
    IDLE = "idle"
    STARTING = "starting"
    ACTIVE = "active"
    SETTLING = "settling"
    COMPLETE = "complete"


@dataclass
class ResizeEvent:
    """Individual resize event data"""
    timestamp: float
    old_size: Tuple[int, int]
    new_size: Tuple[int, int]
    size_delta: Tuple[int, int]
    time_since_last: float
    event_source: str = "unknown"  # user_drag, programmatic, snap, etc.


@dataclass
class ResizeSession:
    """Complete resize session analysis"""
    session_id: str
    start_time: float
    end_time: Optional[float] = None
    events: List[ResizeEvent] = field(default_factory=list)
    initial_state: ResizeState = ResizeState.IDLE
    final_state: ResizeState = ResizeState.COMPLETE
    peak_frequency: float = 0.0
    total_size_change: Tuple[int, int] = (0, 0)


class ResizeAnalyzer(QtCore.QObject):
    """
    Analyzes resize event patterns and frequency to understand resize behavior.
    
    This class helps identify:
    - Resize event frequency and timing patterns
    - User vs programmatic resize detection
    - Resize session boundaries
    - Performance impact patterns
    """
    
    # Signals for resize state changes
    stateChanged = QtCore.Signal(ResizeState, ResizeState)  # old_state, new_state
    sessionStarted = QtCore.Signal(str)  # session_id
    sessionEnded = QtCore.Signal(str, dict)  # session_id, analysis
    highFrequencyDetected = QtCore.Signal(float)  # frequency_hz
    
    def __init__(self, max_sessions: int = 50, event_history_size: int = 1000):
        super().__init__()
        self.max_sessions = max_sessions
        self.event_history_size = event_history_size
        
        # Current state
        self._current_state = ResizeState.IDLE
        self._current_session: Optional[ResizeSession] = None
        self._last_resize_time = 0.0
        self._last_size = (0, 0)
        
        # Event tracking
        self._recent_events: deque = deque(maxlen=event_history_size)
        self._sessions: Dict[str, ResizeSession] = {}
        self._session_counter = 0
        
        # Frequency analysis
        self._frequency_window = deque(maxlen=20)  # Track last 20 events for frequency
        self._current_frequency = 0.0
        
        # Configuration thresholds
        self._starting_threshold_ms = 200  # Time to consider resize "starting"
        self._active_threshold_hz = 2.0    # Frequency to consider "active" resizing
        self._settling_threshold_ms = 300  # Time to consider resize "settling"
        self._complete_threshold_ms = 500  # Time to consider resize "complete"
        self._high_frequency_threshold = 10.0  # Hz threshold for high frequency warning
        
        # State transition timer
        self._state_timer = QtCore.QTimer()
        self._state_timer.setSingleShot(True)
        self._state_timer.timeout.connect(self._check_state_transition)
        
        # Debug mode
        self._debug_mode = False
    
    def set_debug_mode(self, debug: bool):
        """Enable or disable debug output"""
        self._debug_mode = debug
    
    def get_current_state(self) -> ResizeState:
        """Get the current resize state"""
        return self._current_state
    
    def get_current_frequency(self) -> float:
        """Get the current resize frequency in Hz"""
        return self._current_frequency
    
    def analyze_resize_event(self, old_size: Tuple[int, int], new_size: Tuple[int, int], 
                           event_source: str = "unknown") -> ResizeEvent:
        """
        Analyze a new resize event and update state.
        
        Args:
            old_size: Previous window size (width, height)
            new_size: New window size (width, height)
            event_source: Source of the resize event
            
        Returns:
            ResizeEvent object with analysis data
        """
        current_time = time.time()
        time_since_last = current_time - self._last_resize_time if self._last_resize_time > 0 else 0
        
        # Create resize event
        resize_event = ResizeEvent(
            timestamp=current_time,
            old_size=old_size,
            new_size=new_size,
            size_delta=(new_size[0] - old_size[0], new_size[1] - old_size[1]),
            time_since_last=time_since_last,
            event_source=event_source
        )
        
        # Update frequency tracking
        self._update_frequency_analysis(current_time)
        
        # Add to event history
        self._recent_events.append(resize_event)
        
        # Update state based on new event
        self._update_resize_state(resize_event)
        
        # Update tracking variables
        self._last_resize_time = current_time
        self._last_size = new_size
        
        if self._debug_mode:
            print(f"ResizeAnalyzer: Event {old_size} -> {new_size}, "
                  f"frequency: {self._current_frequency:.1f}Hz, state: {self._current_state.value}")
        
        return resize_event
    
    def _update_frequency_analysis(self, current_time: float):
        """Update resize frequency analysis"""
        self._frequency_window.append(current_time)
        
        if len(self._frequency_window) >= 2:
            # Calculate frequency over the window
            time_span = self._frequency_window[-1] - self._frequency_window[0]
            if time_span > 0:
                self._current_frequency = (len(self._frequency_window) - 1) / time_span
            else:
                self._current_frequency = 0.0
    
    def _update_resize_state(self, event: ResizeEvent):
        """Update the current resize state based on the new event"""
        old_state = self._current_state
        
        # Simple state logic for now
        if self._current_state == ResizeState.IDLE:
            self._current_state = ResizeState.STARTING
        elif self._current_frequency >= self._active_threshold_hz:
            self._current_state = ResizeState.ACTIVE
        
        if old_state != self._current_state:
            self.stateChanged.emit(old_state, self._current_state)
    
    def _check_state_transition(self):
        """Check if we should transition states based on time"""
        # Simplified for now
        pass
    
    def reset(self):
        """Reset the analyzer to initial state"""
        self._current_state = ResizeState.IDLE
        self._last_resize_time = 0.0
        self._last_size = (0, 0)
        self._current_frequency = 0.0
        self._frequency_window.clear()
        
        if self._debug_mode:
            print("ResizeAnalyzer: Reset to initial state") 