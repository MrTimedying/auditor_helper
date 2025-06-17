# Technical Specifications: Multi-Tier Cache & Startup Optimization

## 1. Multi-Tier Cache System Architecture

### 1.1 Cache Hierarchy Design

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
├─────────────────────────────────────────────────────────────┤
│                Multi-Tier Cache Manager                     │
├─────────────────┬─────────────────┬─────────────────────────┤
│   L1: Memory    │   L2: SQLite    │      L3: File           │
│   Cache         │   Cache         │      Cache              │
│                 │                 │                         │
│ • UI State      │ • Week Data     │ • Analytics Results     │
│ • Preferences   │ • Task Lists    │ • Chart Data           │
│ • Current Week  │ • Aggregations  │ • Export Data          │
│                 │ • Bonus Calc    │ • Statistical Analysis │
│                 │                 │                         │
│ 0.001-0.01ms    │ 0.1-0.5ms      │ 1-5ms                  │
│ 500 items max   │ Unlimited       │ Compressed storage      │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### 1.2 Cache Routing Rules

```python
CACHE_ROUTING_RULES = {
    # L1 Cache (Memory) - Ultra-fast access
    'ui_state': {
        'tier': 'l1',
        'ttl': 300,  # 5 minutes
        'max_size': '1MB',
        'description': 'Window positions, UI preferences, current selections'
    },
    'user_preferences': {
        'tier': 'l1',
        'ttl': 3600,  # 1 hour
        'max_size': '100KB',
        'description': 'User settings, theme preferences'
    },
    'current_week': {
        'tier': 'l1',
        'ttl': 1800,  # 30 minutes
        'max_size': '500KB',
        'description': 'Currently selected week data'
    },
    
    # L2 Cache (SQLite) - Persistent structured data
    'week_data': {
        'tier': 'l2',
        'ttl': 7200,  # 2 hours
        'max_size': 'unlimited',
        'description': 'Week information, task lists, aggregated data'
    },
    'task_lists': {
        'tier': 'l2',
        'ttl': 3600,  # 1 hour
        'max_size': 'unlimited',
        'description': 'Task queries, filtered lists'
    },
    'aggregated_stats': {
        'tier': 'l2',
        'ttl': 1800,  # 30 minutes
        'max_size': 'unlimited',
        'description': 'Calculated statistics, bonus calculations'
    },
    
    # L3 Cache (File) - Large objects with compression
    'analytics_results': {
        'tier': 'l3',
        'ttl': 86400,  # 24 hours
        'max_size': '100MB',
        'compression': 'lz4',
        'description': 'Statistical analysis results, ML models'
    },
    'chart_data': {
        'tier': 'l3',
        'ttl': 3600,  # 1 hour
        'max_size': '50MB',
        'compression': 'lz4',
        'description': 'Chart datasets, visualization data'
    },
    'export_data': {
        'tier': 'l3',
        'ttl': 1800,  # 30 minutes
        'max_size': '20MB',
        'compression': 'zstd',
        'description': 'CSV/Excel export data'
    }
}
```

## 2. Component Specifications

### 2.1 Memory Cache (L1)

```python
class MemoryCache(BaseCache):
    """
    Ultra-fast in-memory cache with LRU eviction
    
    Features:
    - Sub-millisecond access times
    - Thread-safe operations
    - Automatic TTL expiration
    - Memory usage monitoring
    - LRU eviction policy
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache = OrderedDict()
        self._expiry = {}
        self._lock = threading.RLock()
        self._stats = CacheStats()
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            # Check expiration
            if key in self._expiry and time.time() > self._expiry[key]:
                self._remove_expired(key)
                self._stats.record_miss()
                return None
            
            # Get and move to end (LRU)
            if key in self._cache:
                value = self._cache.pop(key)
                self._cache[key] = value
                self._stats.record_hit()
                return value
            
            self._stats.record_miss()
            return None
    
    def set(self, key: str, value: Any, ttl: int = None):
        with self._lock:
            ttl = ttl or self.default_ttl
            
            # Remove oldest if at capacity
            if len(self._cache) >= self.max_size and key not in self._cache:
                oldest_key = next(iter(self._cache))
                self._remove_key(oldest_key)
            
            # Set value and expiry
            self._cache[key] = value
            self._expiry[key] = time.time() + ttl
            self._stats.record_set()
```

### 2.2 SQLite Cache (L2)

```python
class SQLiteCache(BaseCache):
    """
    Persistent SQLite-based cache with optimized performance
    
    Features:
    - ACID compliance
    - Efficient indexing
    - Automatic cleanup
    - Compression support
    - Transaction batching
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
        self._stats = CacheStats()
    
    def _init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            # Performance optimizations
            conn.execute("PRAGMA journal_mode=MEMORY")
            conn.execute("PRAGMA synchronous=OFF")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA cache_size=50000")
            conn.execute("PRAGMA mmap_size=268435456")  # 256MB
            
            # Create cache table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    category TEXT,
                    created_at REAL,
                    expires_at REAL,
                    access_count INTEGER DEFAULT 0,
                    size_bytes INTEGER,
                    compressed BOOLEAN DEFAULT 0
                ) WITHOUT ROWID
            """)
            
            # Optimized indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_expires ON cache_entries(expires_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_category ON cache_entries(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_access ON cache_entries(access_count DESC)")
    
    def get(self, key: str) -> Optional[Any]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT value, compressed FROM cache_entries 
                    WHERE key = ? AND (expires_at IS NULL OR expires_at > ?)
                """, (key, time.time()))
                
                row = cursor.fetchone()
                if row:
                    # Update access statistics
                    conn.execute("""
                        UPDATE cache_entries 
                        SET access_count = access_count + 1
                        WHERE key = ?
                    """, (key,))
                    
                    # Decompress if needed
                    value_data = row[0]
                    if row[1]:  # compressed
                        value_data = lz4.frame.decompress(value_data)
                    
                    self._stats.record_hit()
                    return pickle.loads(value_data)
                
                self._stats.record_miss()
                return None
                
        except Exception as e:
            self._stats.record_error()
            return None
```

### 2.3 File Cache (L3)

```python
class FileCache(BaseCache):
    """
    File-based cache with compression for large objects
    
    Features:
    - LZ4/Zstandard compression
    - Automatic cleanup
    - Directory organization
    - Metadata tracking
    - Concurrent access safety
    """
    
    def __init__(self, cache_dir: str, compression: str = 'lz4'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.compression = compression
        self.metadata_file = self.cache_dir / "metadata.json"
        self._metadata = self._load_metadata()
        self._lock = threading.RLock()
        self._stats = CacheStats()
        
        # Initialize compressor
        if compression == 'lz4':
            self.compressor = lz4.frame
        elif compression == 'zstd':
            self.compressor = zstd.ZstdCompressor(level=3)
            self.decompressor = zstd.ZstdDecompressor()
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            # Check metadata for expiration
            if key in self._metadata:
                expires_at = self._metadata[key].get('expires_at')
                if expires_at and time.time() > expires_at:
                    self._remove_expired(key)
                    self._stats.record_miss()
                    return None
            
            file_path = self._get_file_path(key)
            if not file_path.exists():
                self._stats.record_miss()
                return None
            
            try:
                with open(file_path, 'rb') as f:
                    compressed_data = f.read()
                
                # Decompress
                if self.compression == 'lz4':
                    data = self.compressor.decompress(compressed_data)
                elif self.compression == 'zstd':
                    data = self.decompressor.decompress(compressed_data)
                
                # Update access statistics
                self._metadata[key]['access_count'] = self._metadata[key].get('access_count', 0) + 1
                self._metadata[key]['last_accessed'] = time.time()
                self._save_metadata()
                
                self._stats.record_hit()
                return pickle.loads(data)
                
            except Exception as e:
                self._stats.record_error()
                return None
```

## 3. Startup Optimization Components

### 3.1 Lazy Import System

```python
class LazyImporter:
    """
    Lazy import system for heavy scientific libraries
    
    Features:
    - On-demand loading
    - Import caching
    - Error handling
    - Performance monitoring
    """
    
    def __init__(self, module_name: str, submodules: List[str] = None):
        self.module_name = module_name
        self.submodules = submodules or []
        self._module = None
        self._submodule_cache = {}
        self._import_time = None
    
    def __getattr__(self, name: str):
        if self._module is None:
            start_time = time.time()
            try:
                self._module = __import__(self.module_name, fromlist=[''])
                self._import_time = time.time() - start_time
                print(f"Lazy loaded {self.module_name} in {self._import_time:.3f}s")
            except ImportError as e:
                raise ImportError(f"Failed to lazy load {self.module_name}: {e}")
        
        return getattr(self._module, name)
    
    def preload(self):
        """Preload the module (for background loading)"""
        if self._module is None:
            _ = self.__getattr__('__name__')  # Trigger loading

# Usage examples
pandas = LazyImporter('pandas')
matplotlib = LazyImporter('matplotlib.pyplot')
seaborn = LazyImporter('seaborn')
sklearn = LazyImporter('sklearn')
numpy = LazyImporter('numpy')
```

### 3.2 Migration Optimization System

```python
class OptimizedMigrationRunner:
    """
    Optimized database migration system
    
    Features:
    - Version-based migration checking
    - Batch operations
    - Progress tracking
    - Rollback support
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.current_version = self._get_current_version()
        self.target_version = LATEST_SCHEMA_VERSION
    
    def run_migrations(self) -> bool:
        """Run only necessary migrations"""
        if not self._migrations_needed():
            return True
        
        start_time = time.time()
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("BEGIN TRANSACTION")
                
                for version in range(self.current_version + 1, self.target_version + 1):
                    migration_func = self._get_migration_function(version)
                    if migration_func:
                        migration_func(conn)
                        self._update_version(conn, version)
                
                conn.execute("COMMIT")
                
            migration_time = time.time() - start_time
            print(f"Migrations completed in {migration_time:.3f}s")
            return True
            
        except Exception as e:
            print(f"Migration failed: {e}")
            return False
    
    def _migrations_needed(self) -> bool:
        """Quick check if migrations are needed"""
        return self.current_version < self.target_version
    
    def _get_current_version(self) -> int:
        """Get current schema version"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT version FROM schema_version LIMIT 1")
                row = cursor.fetchone()
                return row[0] if row else 0
        except sqlite3.OperationalError:
            return 0  # No version table exists
```

### 3.3 Asynchronous Component Loader

```python
class AsyncComponentLoader:
    """
    Asynchronous component loading system
    
    Features:
    - Progressive loading
    - Dependency management
    - Error handling
    - Progress tracking
    """
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.loaded_components = set()
        self.loading_queue = []
        self.dependencies = {}
    
    def register_component(self, name: str, loader_func: callable, 
                          dependencies: List[str] = None, delay_ms: int = 0):
        """Register a component for async loading"""
        self.loading_queue.append({
            'name': name,
            'loader': loader_func,
            'dependencies': dependencies or [],
            'delay': delay_ms,
            'loaded': False
        })
    
    def start_loading(self):
        """Start the async loading process"""
        for component in self.loading_queue:
            if self._dependencies_satisfied(component):
                QTimer.singleShot(component['delay'], 
                                lambda c=component: self._load_component(c))
    
    def _load_component(self, component: dict):
        """Load a single component"""
        try:
            start_time = time.time()
            component['loader']()
            load_time = time.time() - start_time
            
            component['loaded'] = True
            self.loaded_components.add(component['name'])
            
            print(f"✅ {component['name']} loaded in {load_time:.3f}s")
            
            # Check if other components can now be loaded
            self._check_pending_components()
            
        except Exception as e:
            print(f"❌ Failed to load {component['name']}: {e}")
    
    def _dependencies_satisfied(self, component: dict) -> bool:
        """Check if component dependencies are satisfied"""
        return all(dep in self.loaded_components for dep in component['dependencies'])

# Usage in MainWindow
def setup_async_loading(self):
    loader = AsyncComponentLoader(self)
    
    # Register components with dependencies and delays
    loader.register_component("analysis_widget", self.load_analysis_widget, delay_ms=0)
    loader.register_component("rust_extensions", self.load_rust_extensions, delay_ms=100)
    loader.register_component("advanced_features", self.setup_advanced_features, 
                            dependencies=["analysis_widget"], delay_ms=200)
    
    loader.start_loading()
```

## 4. Implementation Files Structure

```
src/
├── core/
│   ├── cache/
│   │   ├── __init__.py
│   │   ├── base_cache.py
│   │   ├── memory_cache.py
│   │   ├── sqlite_cache.py
│   │   ├── file_cache.py
│   │   ├── multi_tier_cache.py
│   │   └── cache_stats.py
│   ├── optimization/
│   │   ├── __init__.py
│   │   ├── lazy_imports.py
│   │   ├── migration_optimizer.py
│   │   ├── async_loader.py
│   │   └── startup_monitor.py
│   └── services/
│       ├── data_service_v2.py
│       └── session_manager_v2.py
├── scripts/
│   ├── migrate_redis_to_multitier.py
│   └── performance_benchmark.py
└── tests/
    ├── test_cache_performance.py
    ├── test_startup_optimization.py
    └── test_migration_integrity.py
```

## 5. Configuration Settings

```python
# Cache Configuration
CACHE_CONFIG = {
    'memory_cache': {
        'max_size': 1000,
        'default_ttl': 300,
        'cleanup_interval': 60
    },
    'sqlite_cache': {
        'db_path': 'cache/cache.db',
        'pragma_settings': {
            'journal_mode': 'MEMORY',
            'synchronous': 'OFF',
            'temp_store': 'MEMORY',
            'cache_size': 50000,
            'mmap_size': 268435456
        }
    },
    'file_cache': {
        'cache_dir': 'cache/files',
        'compression': 'lz4',
        'max_file_size': '10MB'
    }
}

# Startup Configuration
STARTUP_CONFIG = {
    'lazy_imports': {
        'enabled': True,
        'defer_heavy': ['pandas', 'matplotlib', 'seaborn', 'sklearn']
    },
    'async_loading': {
        'enabled': True,
        'component_delays': {
            'analysis_widget': 0,
            'rust_extensions': 100,
            'advanced_features': 200
        }
    },
    'migration_optimization': {
        'enabled': True,
        'batch_size': 1000,
        'timeout': 30
    }
}
```

This technical specification provides the foundation for implementing both the multi-tier cache system and startup optimization components. 