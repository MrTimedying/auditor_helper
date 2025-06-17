"""
Comprehensive Startup Profiler for Auditor Helper
Measures and analyzes startup performance bottlenecks in real-time
"""

import time
import threading
import psutil
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from contextlib import contextmanager
from pathlib import Path
import json

@dataclass
class ProfilerEntry:
    """Single profiler measurement entry"""
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    memory_before: Optional[float] = None
    memory_after: Optional[float] = None
    memory_delta: Optional[float] = None
    cpu_percent: Optional[float] = None
    thread_id: int = field(default_factory=lambda: threading.get_ident())
    parent: Optional[str] = None
    level: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

class StartupProfiler:
    """
    Comprehensive startup profiler that tracks:
    - Time spent in each phase
    - Memory usage changes
    - CPU utilization
    - Thread activity
    - Component initialization order
    """
    
    def __init__(self):
        self.entries: List[ProfilerEntry] = []
        self.active_entries: Dict[str, ProfilerEntry] = {}
        self.start_time = time.time()
        self.process = psutil.Process()
        self._lock = threading.Lock()
        self.level_stack: List[str] = []
        
    @contextmanager
    def profile_phase(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """Context manager for profiling a phase"""
        entry = self.start_phase(name, metadata or {})
        try:
            yield entry
        finally:
            self.end_phase(name)
    
    def start_phase(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> ProfilerEntry:
        """Start profiling a phase"""
        with self._lock:
            current_time = time.time()
            
            # Get memory info
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            # Get CPU percent (non-blocking)
            try:
                cpu_percent = self.process.cpu_percent()
            except:
                cpu_percent = 0.0
            
            # Determine parent and level
            parent = self.level_stack[-1] if self.level_stack else None
            level = len(self.level_stack)
            
            entry = ProfilerEntry(
                name=name,
                start_time=current_time,
                memory_before=memory_mb,
                cpu_percent=cpu_percent,
                parent=parent,
                level=level,
                metadata=metadata or {}
            )
            
            self.active_entries[name] = entry
            self.level_stack.append(name)
            
            return entry
    
    def end_phase(self, name: str) -> Optional[ProfilerEntry]:
        """End profiling a phase"""
        with self._lock:
            if name not in self.active_entries:
                return None
            
            entry = self.active_entries[name]
            current_time = time.time()
            
            # Get memory info
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            # Complete the entry
            entry.end_time = current_time
            entry.duration = current_time - entry.start_time
            entry.memory_after = memory_mb
            entry.memory_delta = memory_mb - (entry.memory_before or 0)
            
            # Move to completed entries
            self.entries.append(entry)
            del self.active_entries[name]
            
            # Remove from level stack
            if self.level_stack and self.level_stack[-1] == name:
                self.level_stack.pop()
            
            return entry
    
    def get_total_startup_time(self) -> float:
        """Get total startup time so far"""
        return time.time() - self.start_time
    
    def get_phase_summary(self) -> Dict[str, Any]:
        """Get summary of all completed phases"""
        if not self.entries:
            return {"total_phases": 0, "total_time": 0}
        
        total_time = sum(entry.duration or 0 for entry in self.entries)
        memory_peak = max(entry.memory_after or 0 for entry in self.entries)
        
        # Group by top-level phases
        top_level_phases = [entry for entry in self.entries if entry.level == 0]
        
        phase_breakdown = []
        for entry in top_level_phases:
            phase_breakdown.append({
                "name": entry.name,
                "duration": entry.duration,
                "percentage": (entry.duration / total_time * 100) if total_time > 0 else 0,
                "memory_delta": entry.memory_delta,
                "metadata": entry.metadata
            })
        
        # Sort by duration
        phase_breakdown.sort(key=lambda x: x["duration"] or 0, reverse=True)
        
        return {
            "total_phases": len(self.entries),
            "total_time": total_time,
            "memory_peak": memory_peak,
            "phase_breakdown": phase_breakdown,
            "startup_time": self.get_total_startup_time()
        }
    
    def get_bottlenecks(self, min_duration: float = 0.1) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks"""
        bottlenecks = []
        
        for entry in self.entries:
            if (entry.duration or 0) >= min_duration:
                bottlenecks.append({
                    "name": entry.name,
                    "duration": entry.duration,
                    "memory_delta": entry.memory_delta,
                    "level": entry.level,
                    "parent": entry.parent,
                    "severity": self._classify_bottleneck(entry.duration or 0),
                    "metadata": entry.metadata
                })
        
        # Sort by duration
        bottlenecks.sort(key=lambda x: x["duration"] or 0, reverse=True)
        return bottlenecks
    
    def _classify_bottleneck(self, duration: float) -> str:
        """Classify bottleneck severity"""
        if duration >= 2.0:
            return "CRITICAL"
        elif duration >= 1.0:
            return "HIGH"
        elif duration >= 0.5:
            return "MEDIUM"
        else:
            return "LOW"
    
    def get_recommendations(self) -> List[str]:
        """Get optimization recommendations based on profiling data"""
        recommendations = []
        bottlenecks = self.get_bottlenecks()
        
        for bottleneck in bottlenecks[:5]:  # Top 5 bottlenecks
            name = bottleneck["name"]
            duration = bottleneck["duration"]
            
            if "NetworkCache" in name and duration > 1.0:
                recommendations.append(f"Network cache taking too long (saves ~{duration:.1f}s)")
            elif "Database" in name and duration > 0.5:
                recommendations.append(f"Optimize database initialization (saves ~{duration:.1f}s)")
            elif "UI" in name or "Widget" in name and duration > 0.5:
                recommendations.append(f"Implement async UI loading (saves ~{duration:.1f}s)")
            elif "Import" in name and duration > 0.3:
                recommendations.append(f"Optimize import operations (saves ~{duration:.1f}s)")
        
        return recommendations
    
    def generate_report(self) -> str:
        """Generate a comprehensive startup performance report"""
        summary = self.get_phase_summary()
        bottlenecks = self.get_bottlenecks()
        recommendations = self.get_recommendations()
        
        report = []
        report.append("STARTUP PERFORMANCE REPORT")
        report.append("=" * 50)
        report.append(f"Total Startup Time: {summary['startup_time']:.2f}s")
        report.append(f"Memory Peak: {summary['memory_peak']:.1f} MB")
        report.append(f"Total Phases: {summary['total_phases']}")
        report.append("")
        
        # Phase breakdown
        report.append("PHASE BREAKDOWN:")
        report.append("-" * 30)
        for phase in summary["phase_breakdown"][:10]:  # Top 10 phases
            duration = phase["duration"] or 0
            percentage = phase["percentage"]
            memory = phase["memory_delta"] or 0
            report.append(f"  {phase['name']:<30} {duration:>6.2f}s ({percentage:>5.1f}%) [{memory:>+5.1f}MB]")
        
        report.append("")
        
        # Bottlenecks
        if bottlenecks:
            report.append("PERFORMANCE BOTTLENECKS:")
            report.append("-" * 35)
            for bottleneck in bottlenecks[:8]:  # Top 8 bottlenecks
                duration = bottleneck["duration"] or 0
                severity = bottleneck["severity"]
                name = bottleneck["name"]
                report.append(f"  [{severity:<8}] {name:<25} {duration:>6.2f}s")
        
        report.append("")
        
        # Recommendations
        if recommendations:
            report.append("OPTIMIZATION RECOMMENDATIONS:")
            report.append("-" * 40)
            for rec in recommendations:
                report.append(f"  {rec}")
        
        report.append("")
        report.append("Target: <3.0s startup time for optimal user experience")
        
        return "\n".join(report)
    
    def save_report(self, filepath: Optional[str] = None) -> str:
        """Save performance report to file"""
        if filepath is None:
            filepath = f"startup_performance_{int(time.time())}.txt"
        
        report = self.generate_report()
        
        # Use UTF-8 encoding to handle Unicode characters
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return filepath
    
    def export_json(self, filepath: Optional[str] = None) -> str:
        """Export profiling data as JSON"""
        if filepath is None:
            filepath = f"startup_profile_{int(time.time())}.json"
        
        data = {
            "timestamp": time.time(),
            "startup_time": self.get_total_startup_time(),
            "summary": self.get_phase_summary(),
            "bottlenecks": self.get_bottlenecks(),
            "recommendations": self.get_recommendations(),
            "entries": [
                {
                    "name": entry.name,
                    "duration": entry.duration,
                    "memory_before": entry.memory_before,
                    "memory_after": entry.memory_after,
                    "memory_delta": entry.memory_delta,
                    "cpu_percent": entry.cpu_percent,
                    "level": entry.level,
                    "parent": entry.parent,
                    "metadata": entry.metadata
                }
                for entry in self.entries
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filepath

# Global profiler instance
_startup_profiler = None

def get_startup_profiler() -> StartupProfiler:
    """Get the global startup profiler instance"""
    global _startup_profiler
    if _startup_profiler is None:
        _startup_profiler = StartupProfiler()
    return _startup_profiler

def profile_startup_phase(name: str, metadata: Optional[Dict[str, Any]] = None):
    """Decorator for profiling startup phases"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            profiler = get_startup_profiler()
            with profiler.profile_phase(name, metadata):
                return func(*args, **kwargs)
        return wrapper
    return decorator

# Context manager for easy profiling
@contextmanager
def profile_phase(name: str, metadata: Optional[Dict[str, Any]] = None):
    """Context manager for profiling phases"""
    profiler = get_startup_profiler()
    with profiler.profile_phase(name, metadata):
        yield

def print_startup_report():
    """Print startup performance report"""
    profiler = get_startup_profiler()
    print(profiler.generate_report())

def save_startup_report(filepath: Optional[str] = None) -> str:
    """Save startup performance report"""
    profiler = get_startup_profiler()
    return profiler.save_report(filepath) 