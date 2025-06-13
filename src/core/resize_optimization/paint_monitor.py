"""
Paint Event Monitor

This module provides monitoring capabilities for paint events during resize operations,
helping to identify performance bottlenecks and painting frequency issues.
"""

import time
from collections import deque, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from PySide6 import QtCore, QtGui, QtWidgets


@dataclass
class PaintEvent:
    """Individual paint event data"""
    timestamp: float
    widget_name: str
    paint_region_size: Tuple[int, int]
    paint_duration_ms: float
    event_source: str = "unknown"  # resize, update, expose, etc.
    additional_data: Dict = field(default_factory=dict)


@dataclass
class PaintSession:
    """Paint monitoring session data"""
    session_id: str
    start_time: float
    end_time: Optional[float] = None
    events: List[PaintEvent] = field(default_factory=list)
    widget_stats: Dict[str, Dict] = field(default_factory=dict)


class PaintMonitor(QtCore.QObject):
    """
    Monitors paint events during resize operations to identify performance issues.
    
    This class helps track:
    - Paint event frequency during resize
    - Paint duration and performance
    - Widget-specific painting patterns
    - Paint region analysis
    """
    
    # Signals for paint monitoring
    paintEventRecorded = QtCore.Signal(PaintEvent)
    sessionStarted = QtCore.Signal(str)
    sessionEnded = QtCore.Signal(str, dict)
    highPaintFrequency = QtCore.Signal(str, float)  # widget_name, frequency_hz
    
    def __init__(self, max_sessions: int = 50, max_events_per_session: int = 2000):
        super().__init__()
        self.max_sessions = max_sessions
        self.max_events_per_session = max_events_per_session
        
        # Current monitoring state
        self._monitoring_enabled = False
        self._current_session: Optional[PaintSession] = None
        self._session_counter = 0
        
        # Event tracking
        self._recent_events: deque = deque(maxlen=1000)
        self._sessions: Dict[str, PaintSession] = {}
        
        # Performance tracking per widget
        self._widget_paint_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self._widget_paint_counts: Dict[str, int] = defaultdict(int)
        
        # Frequency analysis
        self._paint_frequency_windows: Dict[str, deque] = defaultdict(lambda: deque(maxlen=20))
        
        # Configuration
        self._high_frequency_threshold = 30.0  # Hz threshold for high frequency warning
        self._debug_mode = False
        
        # Monitored widgets
        self._monitored_widgets: Dict[str, QtWidgets.QWidget] = {}
        self._original_paint_events: Dict[str, callable] = {}
    
    def set_debug_mode(self, debug: bool):
        """Enable or disable debug output"""
        self._debug_mode = debug
    
    def set_high_frequency_threshold(self, threshold_hz: float):
        """Set the threshold for high frequency paint warnings"""
        self._high_frequency_threshold = threshold_hz
    
    def add_monitored_widget(self, widget: QtWidgets.QWidget, name: str = None):
        """
        Add a widget to be monitored for paint events.
        
        Args:
            widget: The widget to monitor
            name: Optional name for the widget (defaults to class name)
        """
        if name is None:
            name = widget.__class__.__name__
        
        # Store widget reference
        self._monitored_widgets[name] = widget
        
        # Install event filter to capture paint events
        widget.installEventFilter(self)
        
        if self._debug_mode:
            print(f"PaintMonitor: Added monitoring for widget '{name}'")
    
    def remove_monitored_widget(self, name: str):
        """Remove a widget from monitoring"""
        if name in self._monitored_widgets:
            widget = self._monitored_widgets[name]
            widget.removeEventFilter(self)
            del self._monitored_widgets[name]
            
            if self._debug_mode:
                print(f"PaintMonitor: Removed monitoring for widget '{name}'")
    
    def start_monitoring_session(self, session_type: str = "paint") -> str:
        """
        Start a new paint monitoring session.
        
        Args:
            session_type: Type of monitoring session
            
        Returns:
            Session ID string
        """
        self._session_counter += 1
        session_id = f"{session_type}_{self._session_counter}_{int(time.time())}"
        
        self._current_session = PaintSession(
            session_id=session_id,
            start_time=time.time()
        )
        
        # Cleanup old sessions if needed
        if len(self._sessions) >= self.max_sessions:
            oldest_session = min(self._sessions.keys(), 
                               key=lambda k: self._sessions[k].start_time)
            del self._sessions[oldest_session]
        
        self._sessions[session_id] = self._current_session
        self._monitoring_enabled = True
        
        if self._debug_mode:
            print(f"PaintMonitor: Started session {session_id}")
        
        self.sessionStarted.emit(session_id)
        return session_id
    
    def end_monitoring_session(self, session_id: str = None) -> Dict:
        """
        End a paint monitoring session and return analysis.
        
        Args:
            session_id: Session to end (defaults to current session)
            
        Returns:
            Dictionary containing session analysis
        """
        if session_id is None and self._current_session:
            session_id = self._current_session.session_id
        
        if not session_id or session_id not in self._sessions:
            return {}
        
        session = self._sessions[session_id]
        session.end_time = time.time()
        
        # Generate analysis
        analysis = self._analyze_paint_session(session)
        
        if session_id == self._current_session.session_id:
            self._current_session = None
            self._monitoring_enabled = False
        
        if self._debug_mode:
            print(f"PaintMonitor: Ended session {session_id}")
            print(f"Analysis: {analysis}")
        
        self.sessionEnded.emit(session_id, analysis)
        return analysis
    
    def eventFilter(self, obj: QtCore.QObject, event: QtCore.QEvent) -> bool:
        """Event filter to capture paint events from monitored widgets"""
        if not self._monitoring_enabled or event.type() != QtCore.QEvent.Paint:
            return False
        
        # Find widget name
        widget_name = None
        for name, widget in self._monitored_widgets.items():
            if widget is obj:
                widget_name = name
                break
        
        if widget_name is None:
            return False
        
        # Record paint event timing
        start_time = time.time()
        
        # Let the original paint event proceed
        result = False  # Don't consume the event
        
        # Calculate paint duration (this is approximate since we can't easily hook into the actual painting)
        end_time = time.time()
        paint_duration_ms = (end_time - start_time) * 1000
        
        # Get paint region information
        paint_event = event
        if hasattr(paint_event, 'region'):
            region = paint_event.region()
            if region.isEmpty():
                paint_region_size = (0, 0)
            else:
                rect = region.boundingRect()
                paint_region_size = (rect.width(), rect.height())
        else:
            # Fallback to widget size
            widget = self._monitored_widgets[widget_name]
            paint_region_size = (widget.width(), widget.height())
        
        # Create paint event record
        paint_event_record = PaintEvent(
            timestamp=end_time,
            widget_name=widget_name,
            paint_region_size=paint_region_size,
            paint_duration_ms=paint_duration_ms,
            event_source="resize" if self._is_during_resize() else "update"
        )
        
        # Record the event
        self._record_paint_event(paint_event_record)
        
        return result
    
    def _is_during_resize(self) -> bool:
        """Check if we're currently during a resize operation (simplified)"""
        # This could be enhanced to integrate with ResizeAnalyzer
        return self._monitoring_enabled
    
    def _record_paint_event(self, paint_event: PaintEvent):
        """Record a paint event and update statistics"""
        # Add to recent events
        self._recent_events.append(paint_event)
        
        # Add to current session if active
        if self._current_session:
            self._current_session.events.append(paint_event)
            
            # Limit events per session
            if len(self._current_session.events) > self.max_events_per_session:
                self._current_session.events = self._current_session.events[-self.max_events_per_session:]
        
        # Update widget-specific tracking
        widget_name = paint_event.widget_name
        self._widget_paint_times[widget_name].append(paint_event.timestamp)
        self._widget_paint_counts[widget_name] += 1
        
        # Update frequency analysis
        self._update_paint_frequency_analysis(widget_name, paint_event.timestamp)
        
        if self._debug_mode:
            print(f"PaintMonitor: {widget_name} paint event, "
                  f"region: {paint_event.paint_region_size}, "
                  f"duration: {paint_event.paint_duration_ms:.2f}ms")
        
        self.paintEventRecorded.emit(paint_event)
    
    def _update_paint_frequency_analysis(self, widget_name: str, timestamp: float):
        """Update paint frequency analysis for a specific widget"""
        frequency_window = self._paint_frequency_windows[widget_name]
        frequency_window.append(timestamp)
        
        if len(frequency_window) >= 2:
            # Calculate frequency over the window
            time_span = frequency_window[-1] - frequency_window[0]
            if time_span > 0:
                frequency = (len(frequency_window) - 1) / time_span
                
                # Check for high frequency
                if frequency > self._high_frequency_threshold:
                    self.highPaintFrequency.emit(widget_name, frequency)
    
    def _analyze_paint_session(self, session: PaintSession) -> Dict:
        """Generate comprehensive analysis of a paint session"""
        if not session.events:
            return {
                'session_id': session.session_id,
                'duration_seconds': session.end_time - session.start_time if session.end_time else 0,
                'total_paint_events': 0,
                'widgets': {}
            }
        
        duration = session.end_time - session.start_time if session.end_time else 0
        
        # Group events by widget
        widget_events = defaultdict(list)
        for event in session.events:
            widget_events[event.widget_name].append(event)
        
        # Analyze each widget
        widget_analysis = {}
        for widget_name, events in widget_events.items():
            paint_durations = [e.paint_duration_ms for e in events]
            paint_regions = [e.paint_region_size for e in events]
            
            # Calculate timing statistics
            event_intervals = []
            for i in range(1, len(events)):
                interval = events[i].timestamp - events[i-1].timestamp
                event_intervals.append(interval)
            
            # Calculate frequency
            frequency = len(events) / duration if duration > 0 else 0
            
            # Calculate region statistics
            total_pixels_painted = sum(w * h for w, h in paint_regions)
            avg_region_size = (
                sum(w for w, h in paint_regions) / len(paint_regions) if paint_regions else 0,
                sum(h for w, h in paint_regions) / len(paint_regions) if paint_regions else 0
            )
            
            widget_analysis[widget_name] = {
                'event_count': len(events),
                'frequency_hz': frequency,
                'paint_duration_stats': {
                    'total_ms': sum(paint_durations),
                    'avg_ms': sum(paint_durations) / len(paint_durations) if paint_durations else 0,
                    'min_ms': min(paint_durations) if paint_durations else 0,
                    'max_ms': max(paint_durations) if paint_durations else 0
                },
                'timing_stats': {
                    'min_interval_ms': min(event_intervals) * 1000 if event_intervals else 0,
                    'max_interval_ms': max(event_intervals) * 1000 if event_intervals else 0,
                    'avg_interval_ms': sum(event_intervals) / len(event_intervals) * 1000 if event_intervals else 0
                },
                'region_stats': {
                    'total_pixels_painted': total_pixels_painted,
                    'avg_region_size': avg_region_size,
                    'largest_region': max(paint_regions, key=lambda x: x[0] * x[1]) if paint_regions else (0, 0)
                }
            }
        
        return {
            'session_id': session.session_id,
            'duration_seconds': duration,
            'total_paint_events': len(session.events),
            'widgets': widget_analysis,
            'overall_frequency_hz': len(session.events) / duration if duration > 0 else 0
        }
    
    def get_widget_statistics(self, widget_name: str = None) -> Dict:
        """Get paint statistics for a specific widget or all widgets"""
        if widget_name:
            if widget_name not in self._widget_paint_counts:
                return {}
            
            paint_times = list(self._widget_paint_times[widget_name])
            if len(paint_times) >= 2:
                time_span = paint_times[-1] - paint_times[0]
                frequency = (len(paint_times) - 1) / time_span if time_span > 0 else 0
            else:
                frequency = 0
            
            return {
                'widget_name': widget_name,
                'total_paint_events': self._widget_paint_counts[widget_name],
                'recent_frequency_hz': frequency,
                'recent_event_count': len(paint_times)
            }
        else:
            # Return statistics for all widgets
            stats = {}
            for widget_name in self._widget_paint_counts.keys():
                stats[widget_name] = self.get_widget_statistics(widget_name)
            return stats
    
    def get_recent_events(self, widget_name: str = None, limit: int = 100) -> List[PaintEvent]:
        """Get recent paint events, optionally filtered by widget"""
        events = list(self._recent_events)
        
        if widget_name:
            events = [e for e in events if e.widget_name == widget_name]
        
        return events[-limit:]
    
    def clear_data(self):
        """Clear all stored paint monitoring data"""
        self._sessions.clear()
        self._current_session = None
        self._recent_events.clear()
        self._widget_paint_times.clear()
        self._widget_paint_counts.clear()
        self._paint_frequency_windows.clear()
        self._session_counter = 0
        self._monitoring_enabled = False
        
        if self._debug_mode:
            print("PaintMonitor: All data cleared")
    
    def get_session_analysis(self, session_id: str) -> Dict:
        """Get analysis for a specific session"""
        if session_id not in self._sessions:
            return {}
        return self._analyze_paint_session(self._sessions[session_id]) 