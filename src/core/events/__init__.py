"""
Event System for Auditor Helper

This package provides a centralized event bus system for decoupling components
and enabling clean communication between different parts of the application.

Key Components:
- EventBus: Central event dispatcher using Qt signals/slots
- EventType: Enumeration of all application events
- EventData: Container for event information
"""

from .event_bus import AppEventBus, get_event_bus, reset_event_bus, EventData
from .event_types import EventType

__all__ = [
    'AppEventBus',
    'get_event_bus',
    'reset_event_bus',
    'EventData',
    'EventType'
]

# Version info
__version__ = '1.0.0' 