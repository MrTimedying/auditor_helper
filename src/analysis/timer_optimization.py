# timer_optimization.py - Optimized timer functionality with batched updates
import sqlite3
import time
from datetime import datetime
from PySide6 import QtCore, QtWidgets
from collections import defaultdict
from core.db.db_connection_pool import get_db_connection, time_db_operation

class BatchedTimerUpdates:
    """Batched timer updates to reduce database overhead"""
    
    def __init__(self, batch_interval_ms=5000):
        self.pending_updates = {}
        self.batch_interval_ms = batch_interval_ms
        
        # Timer for batching updates
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.flush_updates)
        self.update_timer.setSingleShot(False)
        self.update_timer.start(self.batch_interval_ms)
        
        self.stats = {
            'total_updates_queued': 0,
            'total_batches_flushed': 0,
            'last_flush_time': None,
            'average_batch_size': 0
        }
    
    def queue_duration_update(self, task_id, duration_seconds):
        """Queue a duration update instead of immediate execution"""
        self.pending_updates[task_id] = {
            'duration_seconds': duration_seconds,
            'timestamp': datetime.now()
        }
        self.stats['total_updates_queued'] += 1
    
    def queue_time_update(self, task_id, time_begin=None, time_end=None):
        """Queue time begin/end updates"""
        if task_id not in self.pending_updates:
            self.pending_updates[task_id] = {}
        
        if time_begin is not None:
            self.pending_updates[task_id]['time_begin'] = time_begin
        
        if time_end is not None:
            self.pending_updates[task_id]['time_end'] = time_end
        
        self.stats['total_updates_queued'] += 1
    
    @time_db_operation
    def flush_updates(self):
        """Flush all pending updates to database in a single transaction"""
        if not self.pending_updates:
            return
        
        start_time = time.time()
        updates_count = len(self.pending_updates)
        
        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                
                # Prepare batched updates
                duration_updates = []
                time_begin_updates = []
                time_end_updates = []
                
                for task_id, data in self.pending_updates.items():
                    # Duration updates
                    if 'duration_seconds' in data:
                        hours = data['duration_seconds'] // 3600
                        minutes = (data['duration_seconds'] % 3600) // 60
                        seconds = data['duration_seconds'] % 60
                        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        duration_updates.append((duration_str, task_id))
                    
                    # Time begin updates
                    if 'time_begin' in data:
                        time_begin_updates.append((data['time_begin'], task_id))
                    
                    # Time end updates
                    if 'time_end' in data:
                        time_end_updates.append((data['time_end'], task_id))
                
                # Execute batched updates
                if duration_updates:
                    c.executemany("UPDATE tasks SET duration=? WHERE id=?", duration_updates)
                
                if time_begin_updates:
                    c.executemany("UPDATE tasks SET time_begin=? WHERE id=?", time_begin_updates)
                
                if time_end_updates:
                    c.executemany("UPDATE tasks SET time_end=? WHERE id=?", time_end_updates)
                
                conn.commit()
                
                # Update statistics
                self.stats['total_batches_flushed'] += 1
                self.stats['last_flush_time'] = datetime.now()
                
                # Calculate average batch size
                total_batches = self.stats['total_batches_flushed']
                total_updates = self.stats['total_updates_queued']
                self.stats['average_batch_size'] = total_updates / total_batches if total_batches > 0 else 0
                
                # Clear pending updates
                self.pending_updates.clear()
                
                end_time = time.time()
                flush_time = (end_time - start_time) * 1000
                
                print(f"🔄 Batched {updates_count} timer updates in {flush_time:.2f}ms")
                
        except Exception as e:
            print(f"❌ Failed to flush timer updates: {e}")
    
    def get_stats(self):
        """Get batching statistics"""
        return self.stats.copy()
    
    def force_flush(self):
        """Force immediate flush of pending updates"""
        self.flush_updates()

class OptimizedTimerDisplay:
    """Optimized timer display that only updates when necessary"""
    
    def __init__(self):
        self.last_display_time = ""
        self.last_seconds = -1
        self.update_count = 0
        self.skip_count = 0
    
    def update_display(self, total_seconds, time_display_widget):
        """Only update display if the visible time has actually changed"""
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        new_display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # Only update UI if display actually changed
        if new_display != self.last_display_time:
            time_display_widget.setText(new_display)
            self.last_display_time = new_display
            self.update_count += 1
        else:
            self.skip_count += 1
        
        self.last_seconds = total_seconds
    
    def get_stats(self):
        """Get display update statistics"""
        total_calls = self.update_count + self.skip_count
        skip_percentage = (self.skip_count / total_calls * 100) if total_calls > 0 else 0
        
        return {
            'total_calls': total_calls,
            'actual_updates': self.update_count,
            'skipped_updates': self.skip_count,
            'skip_percentage': skip_percentage
        }

class SmartAlertChecker:
    """Smart alert checking that doesn't run on every timer tick"""
    
    def __init__(self):
        self.last_check_minute = -1
        self.alert_intervals = [15, 30, 45, 60]  # Minutes
        self.alerts_sent = set()
    
    def check_alerts(self, total_seconds, task_id, alert_callback=None):
        """Check for alerts only when necessary (every minute)"""
        current_minute = total_seconds // 60
        
        # Only check alerts once per minute
        if current_minute != self.last_check_minute:
            self.last_check_minute = current_minute
            
            # Check if we need to send any alerts
            for alert_min in self.alert_intervals:
                alert_key = f"{task_id}_{alert_min}"
                
                if current_minute >= alert_min and alert_key not in self.alerts_sent:
                    self.alerts_sent.add(alert_key)
                    
                    if alert_callback:
                        alert_callback(alert_min, current_minute)
                    
                    print(f"⏰ Alert: Task {task_id} has been running for {alert_min} minutes")
    
    def reset_alerts(self, task_id):
        """Reset alerts for a task when it's stopped/restarted"""
        keys_to_remove = [key for key in self.alerts_sent if key.startswith(f"{task_id}_")]
        for key in keys_to_remove:
            self.alerts_sent.remove(key)

# Global instances
_batched_updates = None
_alert_checker = None

def get_batched_updates():
    """Get the global batched updates instance"""
    global _batched_updates
    if _batched_updates is None:
        _batched_updates = BatchedTimerUpdates()
    return _batched_updates

def get_alert_checker():
    """Get the global alert checker instance"""
    global _alert_checker
    if _alert_checker is None:
        _alert_checker = SmartAlertChecker()
    return _alert_checker

def cleanup_timer_optimization():
    """Clean up timer optimization resources"""
    global _batched_updates
    if _batched_updates:
        _batched_updates.force_flush()
        _batched_updates = None

# Example usage class - how to integrate with existing timer dialogs
class OptimizedTimerExample:
    """Example of how to use optimized timer functionality"""
    
    def __init__(self, task_id):
        self.task_id = task_id
        self.total_seconds = 0
        self.is_running = False
        
        # Use optimized components
        self.display = OptimizedTimerDisplay()
        self.batched_updates = get_batched_updates()
        self.alert_checker = get_alert_checker()
        
        # Create a simple label for demonstration
        self.time_label = QtWidgets.QLabel("00:00:00")
        
        # Timer for regular updates
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.on_timer_tick)
    
    def start_timer(self):
        """Start the optimized timer"""
        self.is_running = True
        self.timer.start(1000)  # Update every second
        
        # Queue time begin update
        current_time = datetime.now().strftime("%H:%M:%S")
        self.batched_updates.queue_time_update(self.task_id, time_begin=current_time)
        
        print(f"▶️ Started optimized timer for task {self.task_id}")
    
    def stop_timer(self):
        """Stop the optimized timer"""
        self.is_running = False
        self.timer.stop()
        
        # Queue final updates
        current_time = datetime.now().strftime("%H:%M:%S")
        self.batched_updates.queue_time_update(self.task_id, time_end=current_time)
        self.batched_updates.queue_duration_update(self.task_id, self.total_seconds)
        
        # Force immediate flush for stop events
        self.batched_updates.force_flush()
        
        # Reset alerts
        self.alert_checker.reset_alerts(self.task_id)
        
        print(f"⏹️ Stopped optimized timer for task {self.task_id}")
    
    def on_timer_tick(self):
        """Handle timer tick with optimizations"""
        if not self.is_running:
            return
        
        self.total_seconds += 1
        
        # Update display (only if changed)
        self.display.update_display(self.total_seconds, self.time_label)
        
        # Queue duration update (batched)
        self.batched_updates.queue_duration_update(self.task_id, self.total_seconds)
        
        # Check alerts (smart checking)
        self.alert_checker.check_alerts(self.total_seconds, self.task_id, self.on_alert)
    
    def on_alert(self, alert_minutes, current_minutes):
        """Handle timer alert"""
        print(f"🔔 Alert callback: {alert_minutes}min alert for task {self.task_id}")

def test_timer_optimization():
    """Test the timer optimization functionality"""
    print("⏱️ Testing Timer Optimization")
    print("=" * 50)
    
    # Create test timer
    timer_example = OptimizedTimerExample(task_id=1)
    
    print("🚀 Starting optimized timer test...")
    timer_example.start_timer()
    
    # Simulate timer running for a bit
    for i in range(10):
        timer_example.on_timer_tick()
        time.sleep(0.1)  # Simulate timer ticks quickly
    
    timer_example.stop_timer()
    
    # Show statistics
    print("\n📊 Timer Optimization Statistics:")
    
    display_stats = timer_example.display.get_stats()
    print(f"Display Updates:")
    print(f"  - Total calls: {display_stats['total_calls']}")
    print(f"  - Actual updates: {display_stats['actual_updates']}")
    print(f"  - Skipped updates: {display_stats['skipped_updates']}")
    print(f"  - Skip percentage: {display_stats['skip_percentage']:.1f}%")
    
    batch_stats = timer_example.batched_updates.get_stats()
    print(f"\nBatched Updates:")
    print(f"  - Total updates queued: {batch_stats['total_updates_queued']}")
    print(f"  - Total batches flushed: {batch_stats['total_batches_flushed']}")
    print(f"  - Average batch size: {batch_stats['average_batch_size']:.1f}")
    
    print(f"\n🎯 Timer optimization benefits:")
    print(f"  - Reduced UI updates by ~{display_stats['skip_percentage']:.0f}%")
    print(f"  - Batched database operations")
    print(f"  - Smart alert checking")
    print(f"  - Improved timer responsiveness")

if __name__ == "__main__":
    # Initialize Qt application for testing
    app = QtWidgets.QApplication([])
    test_timer_optimization()
    app.exec() 