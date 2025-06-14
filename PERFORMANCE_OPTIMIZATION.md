# Performance Optimization - Native Extensions & Polyglot Backend

**Goal**: Implement strategic performance optimizations using Rust/C++ extensions for compute-intensive operations while maintaining your Python development productivity.

## Performance Analysis of Current Application

### **Identified Performance Bottlenecks**

#### **1. Task Grid Operations (High Impact)**
```python
# Current slow operations in task_grid.py
def calculate_week_statistics(self, week_id):
    # Problem: Complex aggregations in Python
    tasks = self.get_all_tasks_for_week(week_id)  # Loads all data
    
    total_duration = sum(self.parse_duration(task.duration) for task in tasks)
    avg_score = sum(task.score for task in tasks) / len(tasks)
    project_breakdown = {}
    
    for task in tasks:  # O(n) iteration
        project = task.project_name
        if project not in project_breakdown:
            project_breakdown[project] = {'count': 0, 'duration': 0}
        project_breakdown[project]['count'] += 1
        project_breakdown[project]['duration'] += self.parse_duration(task.duration)
    
    # More complex calculations...
    return statistics
```

#### **2. Data Processing (Medium Impact)**
```python
# Current slow data operations
def parse_duration(self, duration_str):
    # Problem: String parsing in tight loops
    if ':' in duration_str:
        parts = duration_str.split(':')
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 0

def format_duration(self, seconds):
    # Problem: String formatting in tight loops
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
```

#### **3. File I/O Operations (Low Impact but Noticeable)**
```python
# Current I/O operations
def export_week_data(self, week_id, format='csv'):
    # Problem: Large dataset serialization
    tasks = self.get_all_tasks_for_week(week_id)
    
    if format == 'csv':
        # Python CSV writing can be slow for large datasets
        with open(filename, 'w') as f:
            writer = csv.writer(f)
            for task in tasks:
                writer.writerow([...])  # Many small writes
```

## Polyglot Backend Architecture

### **Language Selection Strategy**

| Operation Type | Current (Python) | Optimized With | Expected Speedup | Implementation Priority |
|---------------|------------------|----------------|------------------|------------------------|
| String parsing | Python loops | Rust | 10-50x | High |
| Mathematical calculations | Python/NumPy | Rust + SIMD | 5-20x | High |
| Data aggregations | Python dict/list | Rust HashMap | 3-10x | Medium |
| File I/O | Python stdlib | Rust/C++ | 2-5x | Low |
| JSON processing | Python json | Rust serde | 5-15x | Medium |

### **Rust Extension Implementation**

#### **Core Performance Module**
```toml
# Cargo.toml for Rust extension
[package]
name = "auditor_core"
version = "0.1.0"
edition = "2021"

[lib]
name = "auditor_core"
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.20", features = ["extension-module"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
chrono = { version = "0.4", features = ["serde"] }
rayon = "1.7"  # For parallel processing
hashbrown = "0.14"  # Faster HashMap
```

```rust
// src/lib.rs - Main Rust extension
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::collections::HashMap;
use rayon::prelude::*;
use chrono::{DateTime, Utc, NaiveDateTime};

#[pyfunction]
fn fast_duration_parse(duration_str: &str) -> PyResult<i32> {
    if duration_str.is_empty() {
        return Ok(0);
    }
    
    let parts: Vec<&str> = duration_str.split(':').collect();
    match parts.len() {
        3 => {
            let hours: i32 = parts[0].parse().unwrap_or(0);
            let minutes: i32 = parts[1].parse().unwrap_or(0);
            let seconds: i32 = parts[2].parse().unwrap_or(0);
            Ok(hours * 3600 + minutes * 60 + seconds)
        }
        2 => {
            let minutes: i32 = parts[0].parse().unwrap_or(0);
            let seconds: i32 = parts[1].parse().unwrap_or(0);
            Ok(minutes * 60 + seconds)
        }
        1 => Ok(parts[0].parse().unwrap_or(0)),
        _ => Ok(0)
    }
}

#[pyfunction]
fn fast_duration_format(total_seconds: i32) -> String {
    let hours = total_seconds / 3600;
    let minutes = (total_seconds % 3600) / 60;
    let seconds = total_seconds % 60;
    format!("{:02}:{:02}:{:02}", hours, minutes, seconds)
}

#[pyfunction]
fn batch_duration_parse(duration_strings: Vec<&str>) -> Vec<i32> {
    // Parallel processing for large batches
    duration_strings
        .par_iter()
        .map(|&s| fast_duration_parse(s).unwrap_or(0))
        .collect()
}

#[pyfunction] 
fn batch_duration_format(durations: Vec<i32>) -> Vec<String> {
    durations
        .par_iter()
        .map(|&d| fast_duration_format(d))
        .collect()
}

#[derive(Clone)]
pub struct TaskData {
    pub id: i32,
    pub week_id: i32,
    pub duration_seconds: i32,
    pub score: Option<i32>,
    pub project_name: Option<String>,
    pub date_audited: Option<String>,
}

#[pyfunction]
fn calculate_week_statistics(tasks_data: Vec<(i32, i32, i32, Option<i32>, Option<String>, Option<String>)>) -> PyResult<PyObject> {
    let tasks: Vec<TaskData> = tasks_data
        .into_iter()
        .map(|(id, week_id, duration, score, project, date)| TaskData {
            id,
            week_id,
            duration_seconds: duration,
            score,
            project_name: project,
            date_audited: date,
        })
        .collect();
    
    // Fast aggregations using Rust
    let total_tasks = tasks.len();
    let total_duration: i32 = tasks.iter().map(|t| t.duration_seconds).sum();
    let avg_duration = if total_tasks > 0 { total_duration as f64 / total_tasks as f64 } else { 0.0 };
    
    // Score statistics
    let scores: Vec<i32> = tasks.iter().filter_map(|t| t.score).collect();
    let avg_score = if !scores.is_empty() { 
        scores.iter().sum::<i32>() as f64 / scores.len() as f64 
    } else { 0.0 };
    
    // Project breakdown using fast HashMap
    let mut project_breakdown: HashMap<String, (i32, i32)> = HashMap::new();
    for task in &tasks {
        if let Some(ref project) = task.project_name {
            let entry = project_breakdown.entry(project.clone()).or_insert((0, 0));
            entry.0 += 1;  // count
            entry.1 += task.duration_seconds;  // duration
        }
    }
    
    // Productivity score calculation (custom algorithm)
    let productivity_score = calculate_productivity_score(&tasks);
    
    Python::with_gil(|py| {
        let result = PyDict::new(py);
        result.set_item("total_tasks", total_tasks)?;
        result.set_item("total_duration", total_duration)?;
        result.set_item("avg_duration", avg_duration)?;
        result.set_item("avg_score", avg_score)?;
        result.set_item("productivity_score", productivity_score)?;
        
        // Convert project breakdown to Python dict
        let py_projects = PyDict::new(py);
        for (project, (count, duration)) in project_breakdown {
            let project_data = PyDict::new(py);
            project_data.set_item("count", count)?;
            project_data.set_item("duration", duration)?;
            py_projects.set_item(project, project_data)?;
        }
        result.set_item("project_breakdown", py_projects)?;
        
        Ok(result.into())
    })
}

fn calculate_productivity_score(tasks: &[TaskData]) -> f64 {
    if tasks.is_empty() {
        return 0.0;
    }
    
    // Advanced productivity algorithm
    let mut score_sum = 0.0;
    let mut weight_sum = 0.0;
    
    for task in tasks {
        if let Some(score) = task.score {
            let duration_weight = (task.duration_seconds as f64 / 3600.0).min(8.0); // Cap at 8 hours
            score_sum += score as f64 * duration_weight;
            weight_sum += duration_weight;
        }
    }
    
    if weight_sum > 0.0 {
        (score_sum / weight_sum) * 20.0  // Scale to 0-100
    } else {
        0.0
    }
}

#[pyfunction]
fn fast_time_series_analysis(events: Vec<(String, i32, String)>) -> PyResult<PyObject> {
    // events: (timestamp, duration_change, event_type)
    use std::collections::BTreeMap;
    
    let mut timeline: BTreeMap<String, i32> = BTreeMap::new();
    
    for (timestamp, duration_change, _event_type) in events {
        *timeline.entry(timestamp).or_insert(0) += duration_change;
    }
    
    // Calculate rolling statistics
    let mut cumulative_duration = 0;
    let mut daily_stats: Vec<(String, i32, i32)> = Vec::new();
    
    for (date, duration_change) in timeline {
        cumulative_duration += duration_change;
        daily_stats.push((date, duration_change, cumulative_duration));
    }
    
    Python::with_gil(|py| {
        let result = PyList::new(py, daily_stats);
        Ok(result.into())
    })
}

#[pymodule]
fn auditor_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(fast_duration_parse, m)?)?;
    m.add_function(wrap_pyfunction!(fast_duration_format, m)?)?;
    m.add_function(wrap_pyfunction!(batch_duration_parse, m)?)?;
    m.add_function(wrap_pyfunction!(batch_duration_format, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_week_statistics, m)?)?;
    m.add_function(wrap_pyfunction!(fast_time_series_analysis, m)?)?;
    Ok(())
}
```

### **Python Integration Layer**

#### **Performance Service with Native Extensions**
```python
# performance_service.py
from typing import List, Dict, Any, Optional, Union
import importlib.util
import os
from PySide6.QtCore import QObject, Signal

class PerformanceService(QObject):
    """Service for managing performance-critical operations"""
    
    performanceImprovement = Signal(str, float)  # operation_name, speedup_factor
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rust_core = None
        self.fallback_mode = False
        
        self._load_native_extensions()
    
    def _load_native_extensions(self) -> None:
        """Load Rust extensions with fallback to Python"""
        try:
            import auditor_core
            self.rust_core = auditor_core
            print("✅ Rust extensions loaded successfully")
        except ImportError as e:
            print(f"⚠️  Rust extensions not available: {e}")
            print("📝 Falling back to Python implementations")
            self.fallback_mode = True
    
    def parse_duration(self, duration_str: str) -> int:
        """Parse duration string to seconds with native optimization"""
        if self.rust_core and not self.fallback_mode:
            return self.rust_core.fast_duration_parse(duration_str)
        else:
            return self._python_parse_duration(duration_str)
    
    def format_duration(self, seconds: int) -> str:
        """Format seconds to duration string with native optimization"""
        if self.rust_core and not self.fallback_mode:
            return self.rust_core.fast_duration_format(seconds)
        else:
            return self._python_format_duration(seconds)
    
    def batch_parse_durations(self, duration_strings: List[str]) -> List[int]:
        """Parse multiple duration strings with parallel processing"""
        if self.rust_core and not self.fallback_mode:
            return self.rust_core.batch_duration_parse(duration_strings)
        else:
            return [self._python_parse_duration(s) for s in duration_strings]
    
    def batch_format_durations(self, durations: List[int]) -> List[str]:
        """Format multiple durations with parallel processing"""
        if self.rust_core and not self.fallback_mode:
            return self.rust_core.batch_duration_format(durations)
        else:
            return [self._python_format_duration(d) for d in durations]
    
    def calculate_week_statistics_fast(self, tasks_data: List[tuple]) -> Dict[str, Any]:
        """Calculate week statistics with native optimization"""
        if self.rust_core and not self.fallback_mode:
            return self.rust_core.calculate_week_statistics(tasks_data)
        else:
            return self._python_calculate_statistics(tasks_data)
    
    def analyze_time_series_fast(self, events: List[tuple]) -> List[tuple]:
        """Analyze time series data with native optimization"""
        if self.rust_core and not self.fallback_mode:
            return self.rust_core.fast_time_series_analysis(events)
        else:
            return self._python_time_series_analysis(events)
    
    # Fallback Python implementations
    def _python_parse_duration(self, duration_str: str) -> int:
        """Python fallback for duration parsing"""
        if not duration_str or duration_str == '00:00:00':
            return 0
        
        try:
            parts = duration_str.split(':')
            if len(parts) == 3:
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds
            else:
                return int(parts[0])
        except (ValueError, IndexError):
            return 0
    
    def _python_format_duration(self, seconds: int) -> str:
        """Python fallback for duration formatting"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def _python_calculate_statistics(self, tasks_data: List[tuple]) -> Dict[str, Any]:
        """Python fallback for statistics calculation"""
        if not tasks_data:
            return {
                'total_tasks': 0,
                'total_duration': 0,
                'avg_duration': 0.0,
                'avg_score': 0.0,
                'project_breakdown': {},
                'productivity_score': 0.0
            }
        
        total_tasks = len(tasks_data)
        total_duration = sum(task[2] for task in tasks_data)  # duration_seconds
        avg_duration = total_duration / total_tasks if total_tasks > 0 else 0.0
        
        # Score statistics
        scores = [task[3] for task in tasks_data if task[3] is not None]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        # Project breakdown
        project_breakdown = {}
        for task in tasks_data:
            project = task[4]  # project_name
            if project:
                if project not in project_breakdown:
                    project_breakdown[project] = {'count': 0, 'duration': 0}
                project_breakdown[project]['count'] += 1
                project_breakdown[project]['duration'] += task[2]
        
        return {
            'total_tasks': total_tasks,
            'total_duration': total_duration,
            'avg_duration': avg_duration,
            'avg_score': avg_score,
            'project_breakdown': project_breakdown,
            'productivity_score': self._calculate_productivity_score_python(tasks_data)
        }
    
    def _calculate_productivity_score_python(self, tasks_data: List[tuple]) -> float:
        """Python fallback for productivity score calculation"""
        if not tasks_data:
            return 0.0
        
        score_sum = 0.0
        weight_sum = 0.0
        
        for task in tasks_data:
            duration_seconds = task[2]
            score = task[3]
            
            if score is not None:
                duration_weight = min(duration_seconds / 3600.0, 8.0)  # Cap at 8 hours
                score_sum += score * duration_weight
                weight_sum += duration_weight
        
        if weight_sum > 0.0:
            return (score_sum / weight_sum) * 20.0  # Scale to 0-100
        else:
            return 0.0
    
    def _python_time_series_analysis(self, events: List[tuple]) -> List[tuple]:
        """Python fallback for time series analysis"""
        timeline = {}
        
        for timestamp, duration_change, event_type in events:
            if timestamp not in timeline:
                timeline[timestamp] = 0
            timeline[timestamp] += duration_change
        
        cumulative_duration = 0
        daily_stats = []
        
        for date in sorted(timeline.keys()):
            duration_change = timeline[date]
            cumulative_duration += duration_change
            daily_stats.append((date, duration_change, cumulative_duration))
        
        return daily_stats
    
    def benchmark_operations(self) -> Dict[str, Dict[str, float]]:
        """Benchmark native vs Python implementations"""
        import time
        import random
        
        # Generate test data
        test_durations = [f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}" 
                         for _ in range(1000)]
        test_seconds = [random.randint(0, 86400) for _ in range(1000)]
        
        results = {}
        
        # Benchmark duration parsing
        start_time = time.perf_counter()
        if self.rust_core and not self.fallback_mode:
            self.rust_core.batch_duration_parse(test_durations)
        rust_parse_time = time.perf_counter() - start_time
        
        start_time = time.perf_counter()
        [self._python_parse_duration(d) for d in test_durations]
        python_parse_time = time.perf_counter() - start_time
        
        results['duration_parsing'] = {
            'rust_time': rust_parse_time,
            'python_time': python_parse_time,
            'speedup': python_parse_time / rust_parse_time if rust_parse_time > 0 else 1.0
        }
        
        # Benchmark duration formatting
        start_time = time.perf_counter()
        if self.rust_core and not self.fallback_mode:
            self.rust_core.batch_duration_format(test_seconds)
        rust_format_time = time.perf_counter() - start_time
        
        start_time = time.perf_counter()
        [self._python_format_duration(s) for s in test_seconds]
        python_format_time = time.perf_counter() - start_time
        
        results['duration_formatting'] = {
            'rust_time': rust_format_time,
            'python_time': python_format_time,
            'speedup': python_format_time / rust_format_time if rust_format_time > 0 else 1.0
        }
        
        return results
```

### **Enhanced Data Service with Performance Integration**

```python
# enhanced_data_service.py
from data_service import DataService
from performance_service import PerformanceService
from PySide6.QtCore import Slot
import time

class EnhancedDataService(DataService):
    """Data service with performance optimizations"""
    
    def __init__(self, db_file: str, cache_service, parent=None):
        self.performance_service = PerformanceService()
        super().__init__(db_file, cache_service, parent)
        
        # Monitor performance improvements
        self.performance_service.performanceImprovement.connect(
            self._log_performance_improvement
        )
    
    def get_week_analytics_optimized(self, week_id: int) -> Dict[str, Any]:
        """Get week analytics with native performance optimizations"""
        start_time = time.perf_counter()
        
        # Get raw task data
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, week_id, duration_seconds, score, project_name, date_audited
                FROM tasks_optimized 
                WHERE week_id = ?
                ORDER BY created_at
            """, (week_id,))
            
            # Convert to tuples for Rust processing
            tasks_data = [(
                row['id'],
                row['week_id'], 
                row['duration_seconds'] or 0,
                row['score'],
                row['project_name'],
                row['date_audited']
            ) for row in cursor.fetchall()]
        
        # Use performance service for calculations
        analytics = self.performance_service.calculate_week_statistics_fast(tasks_data)
        
        processing_time = time.perf_counter() - start_time
        
        # Add metadata
        analytics['processing_time'] = processing_time
        analytics['optimization_used'] = not self.performance_service.fallback_mode
        analytics['task_count'] = len(tasks_data)
        
        return analytics
    
    def batch_process_task_durations(self, task_ids: List[int], duration_strings: List[str]) -> bool:
        """Process multiple task duration updates with batch optimization"""
        if len(task_ids) != len(duration_strings):
            return False
        
        try:
            # Parse all durations at once with native optimization
            duration_seconds_list = self.performance_service.batch_parse_durations(duration_strings)
            format_strings = self.performance_service.batch_format_durations(duration_seconds_list)
            
            # Batch database update
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                update_data = [
                    (seconds, formatted, task_id) 
                    for task_id, seconds, formatted in zip(task_ids, duration_seconds_list, format_strings)
                ]
                
                cursor.executemany("""
                    UPDATE tasks_optimized 
                    SET duration_seconds = ?, duration_display = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, update_data)
                
                conn.commit()
            
            # Emit batch update event
            for task_id in task_ids:
                self.taskUpdated.emit(task_id)
            
            return True
            
        except Exception as e:
            self.errorOccurred.emit(
                "batch_duration_update_error",
                f"Batch duration update failed: {str(e)}",
                {"task_ids": task_ids, "duration_strings": duration_strings}
            )
            return False
    
    @Slot(str, float)
    def _log_performance_improvement(self, operation: str, speedup: float) -> None:
        """Log performance improvements for monitoring"""
        print(f"🚀 Performance: {operation} is {speedup:.1f}x faster with native optimization")
```

## Build & Deployment Strategy

### **Development Setup Script**
```python
# setup_performance.py
import subprocess
import sys
import os
from pathlib import Path

def setup_rust_extension():
    """Set up Rust extension for development"""
    print("🔧 Setting up Rust performance extensions...")
    
    # Check if Rust is installed
    try:
        result = subprocess.run(['rustc', '--version'], capture_output=True, text=True)
        print(f"✅ Rust found: {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ Rust not found. Please install Rust from https://rustup.rs/")
        return False
    
    # Check if maturin is installed
    try:
        subprocess.run(['maturin', '--version'], capture_output=True, check=True)
        print("✅ Maturin found")
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("📦 Installing maturin...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'maturin'], check=True)
    
    # Build the Rust extension
    rust_dir = Path(__file__).parent / "rust_extensions"
    if rust_dir.exists():
        print("🔨 Building Rust extension...")
        subprocess.run(['maturin', 'develop'], cwd=rust_dir, check=True)
        print("✅ Rust extension built successfully!")
        return True
    else:
        print(f"❌ Rust extension directory not found: {rust_dir}")
        return False

def benchmark_performance():
    """Run performance benchmarks"""
    from performance_service import PerformanceService
    
    print("\n📊 Running performance benchmarks...")
    
    perf_service = PerformanceService()
    results = perf_service.benchmark_operations()
    
    print("\n🏃‍♂️ Benchmark Results:")
    for operation, metrics in results.items():
        print(f"\n  {operation}:")
        print(f"    Rust time:   {metrics['rust_time']:.4f}s")
        print(f"    Python time: {metrics['python_time']:.4f}s")
        print(f"    Speedup:     {metrics['speedup']:.1f}x")
        
        if metrics['speedup'] > 1.5:
            print("    Status: 🚀 Significant improvement!")
        elif metrics['speedup'] > 1.1:
            print("    Status: ✅ Good improvement")
        else:
            print("    Status: 📝 Minimal improvement")

if __name__ == "__main__":
    if setup_rust_extension():
        benchmark_performance()
    else:
        print("\n⚠️  Performance extensions not available. Application will use Python fallbacks.")
```

## Expected Performance Improvements

### **Benchmark Results (Estimated)**

| Operation | Current Python | With Rust Extensions | Speedup | Impact |
|-----------|---------------|---------------------|---------|---------|
| Duration parsing (1000 items) | 15ms | 0.8ms | 18.7x | High |
| Duration formatting (1000 items) | 12ms | 0.6ms | 20.0x | High |
| Week statistics calculation | 85ms | 8ms | 10.6x | Very High |
| Time series analysis | 45ms | 4ms | 11.2x | Medium |
| Bulk data processing | 200ms | 25ms | 8.0x | High |

### **Real-World Performance Gains**
- **Task Grid Scrolling**: From choppy to buttery smooth
- **Analytics Updates**: From 500ms to 50ms (10x faster)
- **Large Dataset Handling**: Support for 10,000+ tasks without lag
- **Export Operations**: 5-8x faster for large datasets
- **Memory Usage**: 30-40% reduction through efficient Rust algorithms

This performance optimization strategy provides significant speed improvements while maintaining development productivity and offering graceful fallbacks to pure Python when needed. 