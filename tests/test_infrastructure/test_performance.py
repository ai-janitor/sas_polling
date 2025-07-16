"""
=============================================================================
INFRASTRUCTURE PERFORMANCE UNIT TESTS
=============================================================================
Purpose: Unit tests for performance monitoring and optimization
Module: infrastructure/performance.py

TEST CATEGORIES:
1. Performance Monitoring
2. Caching Systems
3. Database Optimization
4. Memory Management
=============================================================================
"""

import pytest
import time
import threading
import gc
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
from collections import defaultdict, OrderedDict
import weakref

class PerformanceMonitor:
    """Performance monitoring and metrics collection."""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.active_timers = {}
        self.counters = defaultdict(int)
        self.thresholds = {
            'response_time': 1.0,  # seconds
            'memory_usage': 100,   # MB
            'cpu_usage': 80        # percentage
        }
    
    def start_timer(self, operation_name):
        """Start timing an operation."""
        timer_id = f"{operation_name}_{threading.current_thread().ident}_{time.time()}"
        self.active_timers[timer_id] = {
            'operation': operation_name,
            'start_time': time.time(),
            'thread_id': threading.current_thread().ident
        }
        return timer_id
    
    def end_timer(self, timer_id):
        """End timing an operation and record the duration."""
        if timer_id not in self.active_timers:
            raise PerformanceError(f"Timer {timer_id} not found or already ended")
        
        timer_data = self.active_timers[timer_id]
        end_time = time.time()
        duration = end_time - timer_data['start_time']
        
        metric_entry = {
            'operation': timer_data['operation'],
            'duration': duration,
            'timestamp': datetime.now(),
            'thread_id': timer_data['thread_id']
        }
        
        self.metrics['response_times'].append(metric_entry)
        del self.active_timers[timer_id]
        
        # Check threshold
        if duration > self.thresholds['response_time']:
            self._record_threshold_violation('response_time', duration)
        
        return duration
    
    def record_memory_usage(self, operation=None):
        """Record current memory usage."""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
        except ImportError:
            # Fallback method using sys.getsizeof for basic estimation
            memory_mb = sys.getsizeof(gc.get_objects()) / 1024 / 1024
        
        metric_entry = {
            'operation': operation or 'general',
            'memory_mb': memory_mb,
            'timestamp': datetime.now()
        }
        
        self.metrics['memory_usage'].append(metric_entry)
        
        # Check threshold
        if memory_mb > self.thresholds['memory_usage']:
            self._record_threshold_violation('memory_usage', memory_mb)
        
        return memory_mb
    
    def increment_counter(self, counter_name, value=1):
        """Increment a performance counter."""
        self.counters[counter_name] += value
        
        counter_entry = {
            'counter': counter_name,
            'value': self.counters[counter_name],
            'increment': value,
            'timestamp': datetime.now()
        }
        
        self.metrics['counters'].append(counter_entry)
    
    def _record_threshold_violation(self, metric_type, value):
        """Record when a metric exceeds its threshold."""
        violation_entry = {
            'metric_type': metric_type,
            'value': value,
            'threshold': self.thresholds[metric_type],
            'timestamp': datetime.now()
        }
        
        self.metrics['threshold_violations'].append(violation_entry)
    
    def get_performance_summary(self, hours=1):
        """Get performance summary for the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter recent metrics
        recent_response_times = [
            m for m in self.metrics['response_times']
            if m['timestamp'] > cutoff_time
        ]
        
        recent_memory_usage = [
            m for m in self.metrics['memory_usage']
            if m['timestamp'] > cutoff_time
        ]
        
        recent_violations = [
            m for m in self.metrics['threshold_violations']
            if m['timestamp'] > cutoff_time
        ]
        
        summary = {
            'time_period_hours': hours,
            'response_time_stats': self._calculate_response_time_stats(recent_response_times),
            'memory_stats': self._calculate_memory_stats(recent_memory_usage),
            'counter_totals': dict(self.counters),
            'threshold_violations': len(recent_violations),
            'active_timers': len(self.active_timers)
        }
        
        return summary
    
    def _calculate_response_time_stats(self, response_times):
        """Calculate response time statistics."""
        if not response_times:
            return {'count': 0}
        
        durations = [rt['duration'] for rt in response_times]
        durations.sort()
        
        return {
            'count': len(durations),
            'min': min(durations),
            'max': max(durations),
            'avg': sum(durations) / len(durations),
            'p50': durations[len(durations) // 2],
            'p95': durations[int(len(durations) * 0.95)] if len(durations) > 20 else max(durations),
            'p99': durations[int(len(durations) * 0.99)] if len(durations) > 100 else max(durations)
        }
    
    def _calculate_memory_stats(self, memory_usage):
        """Calculate memory usage statistics."""
        if not memory_usage:
            return {'count': 0}
        
        usage_values = [mu['memory_mb'] for mu in memory_usage]
        
        return {
            'count': len(usage_values),
            'min_mb': min(usage_values),
            'max_mb': max(usage_values),
            'avg_mb': sum(usage_values) / len(usage_values),
            'current_mb': usage_values[-1] if usage_values else 0
        }


class LRUCache:
    """Least Recently Used cache implementation for performance optimization."""
    
    def __init__(self, max_size=1000):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.hits = 0
        self.misses = 0
    
    def get(self, key):
        """Get value from cache."""
        if key in self.cache:
            # Move to end (most recently used)
            value = self.cache.pop(key)
            self.cache[key] = value
            self.hits += 1
            return value
        else:
            self.misses += 1
            return None
    
    def put(self, key, value):
        """Put value in cache."""
        if key in self.cache:
            # Update existing key
            self.cache.pop(key)
        elif len(self.cache) >= self.max_size:
            # Remove least recently used
            self.cache.popitem(last=False)
        
        self.cache[key] = value
    
    def invalidate(self, key):
        """Remove key from cache."""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self):
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests) if total_requests > 0 else 0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'utilization': len(self.cache) / self.max_size
        }


class DatabaseOptimizer:
    """Database performance optimization utilities."""
    
    def __init__(self):
        self.query_stats = defaultdict(list)
        self.slow_query_threshold = 1.0  # seconds
        self.connection_pool_size = 10
        self.active_connections = 0
    
    def log_query_performance(self, query, duration, rows_affected=None):
        """Log query performance metrics."""
        query_entry = {
            'query_hash': hash(query) % 10000,  # Anonymized query identifier
            'duration': duration,
            'rows_affected': rows_affected,
            'timestamp': datetime.now(),
            'is_slow': duration > self.slow_query_threshold
        }
        
        self.query_stats['all_queries'].append(query_entry)
        
        if query_entry['is_slow']:
            self.query_stats['slow_queries'].append(query_entry)
    
    def get_query_analysis(self, hours=24):
        """Analyze query performance over time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_queries = [
            q for q in self.query_stats['all_queries']
            if q['timestamp'] > cutoff_time
        ]
        
        if not recent_queries:
            return {'total_queries': 0}
        
        durations = [q['duration'] for q in recent_queries]
        slow_queries = [q for q in recent_queries if q['is_slow']]
        
        # Group by query hash to find most common slow queries
        slow_query_counts = defaultdict(int)
        for sq in slow_queries:
            slow_query_counts[sq['query_hash']] += 1
        
        analysis = {
            'total_queries': len(recent_queries),
            'slow_queries': len(slow_queries),
            'slow_query_rate': len(slow_queries) / len(recent_queries),
            'avg_duration': sum(durations) / len(durations),
            'max_duration': max(durations),
            'min_duration': min(durations),
            'most_problematic_queries': dict(sorted(slow_query_counts.items(), 
                                                  key=lambda x: x[1], reverse=True)[:5])
        }
        
        return analysis
    
    def suggest_optimizations(self):
        """Suggest database optimizations based on collected metrics."""
        analysis = self.get_query_analysis()
        suggestions = []
        
        if analysis.get('slow_query_rate', 0) > 0.1:  # More than 10% slow queries
            suggestions.append({
                'type': 'INDEXING',
                'priority': 'HIGH',
                'description': 'High slow query rate detected. Consider adding indexes for frequent queries.',
                'metric': f"Slow query rate: {analysis['slow_query_rate']:.1%}"
            })
        
        if analysis.get('avg_duration', 0) > 0.5:  # Average duration > 500ms
            suggestions.append({
                'type': 'QUERY_OPTIMIZATION',
                'priority': 'MEDIUM',
                'description': 'Average query duration is high. Review query efficiency.',
                'metric': f"Average duration: {analysis['avg_duration']:.3f}s"
            })
        
        if self.active_connections / self.connection_pool_size > 0.8:
            suggestions.append({
                'type': 'CONNECTION_POOL',
                'priority': 'MEDIUM',
                'description': 'Connection pool utilization is high. Consider increasing pool size.',
                'metric': f"Utilization: {self.active_connections/self.connection_pool_size:.1%}"
            })
        
        return suggestions
    
    def simulate_connection_usage(self, connections_used):
        """Simulate database connection usage for testing."""
        self.active_connections = min(connections_used, self.connection_pool_size)


class MemoryProfiler:
    """Memory usage profiling and leak detection."""
    
    def __init__(self):
        self.snapshots = []
        self.object_tracking = defaultdict(int)
    
    def take_snapshot(self, label=None):
        """Take a memory snapshot."""
        # Force garbage collection before snapshot
        gc.collect()
        
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_data = {
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024
            }
        except ImportError:
            # Fallback method
            memory_data = {
                'rss_mb': len(gc.get_objects()) * 64 / 1024 / 1024,  # Rough estimate
                'vms_mb': 0
            }
        
        snapshot = {
            'label': label or f"snapshot_{len(self.snapshots)}",
            'timestamp': datetime.now(),
            'memory': memory_data,
            'object_count': len(gc.get_objects()),
            'gc_stats': gc.get_stats() if hasattr(gc, 'get_stats') else []
        }
        
        self.snapshots.append(snapshot)
        return snapshot
    
    def detect_memory_leaks(self, threshold_mb=10):
        """Detect potential memory leaks by comparing snapshots."""
        if len(self.snapshots) < 2:
            return {'status': 'insufficient_data', 'snapshots_needed': 2}
        
        first_snapshot = self.snapshots[0]
        last_snapshot = self.snapshots[-1]
        
        memory_growth = last_snapshot['memory']['rss_mb'] - first_snapshot['memory']['rss_mb']
        object_growth = last_snapshot['object_count'] - first_snapshot['object_count']
        
        leak_analysis = {
            'memory_growth_mb': memory_growth,
            'object_growth': object_growth,
            'time_span_minutes': (last_snapshot['timestamp'] - first_snapshot['timestamp']).total_seconds() / 60,
            'growth_rate_mb_per_hour': memory_growth / max(1, (last_snapshot['timestamp'] - first_snapshot['timestamp']).total_seconds() / 3600),
            'potential_leak': memory_growth > threshold_mb
        }
        
        if leak_analysis['potential_leak']:
            leak_analysis['severity'] = 'HIGH' if memory_growth > 50 else 'MEDIUM'
            leak_analysis['recommendation'] = 'Investigate object lifecycle and garbage collection'
        
        return leak_analysis
    
    def track_object_type(self, obj_type_name):
        """Track object count by type."""
        self.object_tracking[obj_type_name] += 1
    
    def get_memory_report(self):
        """Generate comprehensive memory usage report."""
        if not self.snapshots:
            return {'status': 'no_snapshots'}
        
        latest_snapshot = self.snapshots[-1]
        
        report = {
            'current_memory_mb': latest_snapshot['memory']['rss_mb'],
            'current_object_count': latest_snapshot['object_count'],
            'snapshots_taken': len(self.snapshots),
            'object_tracking': dict(self.object_tracking),
            'leak_analysis': self.detect_memory_leaks()
        }
        
        if len(self.snapshots) >= 2:
            memory_trend = [s['memory']['rss_mb'] for s in self.snapshots[-10:]]  # Last 10 snapshots
            report['memory_trend'] = {
                'values': memory_trend,
                'trending_up': memory_trend[-1] > memory_trend[0] if len(memory_trend) > 1 else False
            }
        
        return report


class PerformanceError(Exception):
    """Performance-related error."""
    pass


class TestPerformanceMonitor:
    @pytest.fixture
    def monitor(self):
        return PerformanceMonitor()
    
    @pytest.mark.unit
    def test_timer_operations(self, monitor):
        # Start timer
        timer_id = monitor.start_timer("test_operation")
        assert timer_id in monitor.active_timers
        
        # Simulate some work
        time.sleep(0.1)
        
        # End timer
        duration = monitor.end_timer(timer_id)
        assert duration >= 0.1
        assert timer_id not in monitor.active_timers
        assert len(monitor.metrics['response_times']) == 1
    
    @pytest.mark.unit
    def test_timer_not_found_error(self, monitor):
        with pytest.raises(PerformanceError):
            monitor.end_timer("nonexistent_timer")
    
    @pytest.mark.unit
    def test_memory_usage_recording(self, monitor):
        memory_mb = monitor.record_memory_usage("test_operation")
        
        assert memory_mb > 0
        assert len(monitor.metrics['memory_usage']) == 1
        assert monitor.metrics['memory_usage'][0]['operation'] == "test_operation"
    
    @pytest.mark.unit
    def test_counter_increment(self, monitor):
        monitor.increment_counter("test_counter", 5)
        monitor.increment_counter("test_counter", 3)
        
        assert monitor.counters["test_counter"] == 8
        assert len(monitor.metrics['counters']) == 2
    
    @pytest.mark.unit
    def test_threshold_violation_detection(self, monitor):
        # Set low threshold for testing
        monitor.thresholds['response_time'] = 0.05
        
        timer_id = monitor.start_timer("slow_operation")
        time.sleep(0.1)  # Intentionally exceed threshold
        monitor.end_timer(timer_id)
        
        assert len(monitor.metrics['threshold_violations']) == 1
        violation = monitor.metrics['threshold_violations'][0]
        assert violation['metric_type'] == 'response_time'
        assert violation['value'] > violation['threshold']
    
    @pytest.mark.unit
    def test_performance_summary(self, monitor):
        # Generate some test data
        timer_id = monitor.start_timer("operation1")
        time.sleep(0.1)
        monitor.end_timer(timer_id)
        
        monitor.record_memory_usage("operation1")
        monitor.increment_counter("requests", 10)
        
        summary = monitor.get_performance_summary(hours=1)
        
        assert summary['response_time_stats']['count'] == 1
        assert summary['memory_stats']['count'] == 1
        assert summary['counter_totals']['requests'] == 10
        assert summary['active_timers'] == 0


class TestLRUCache:
    @pytest.fixture
    def cache(self):
        return LRUCache(max_size=3)
    
    @pytest.mark.unit
    def test_basic_cache_operations(self, cache):
        # Test put and get
        cache.put("key1", "value1")
        assert cache.get("key1") == "value1"
        assert cache.get("nonexistent") is None
    
    @pytest.mark.unit
    def test_lru_eviction(self, cache):
        # Fill cache to capacity
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # Access key1 to make it recently used
        cache.get("key1")
        
        # Add new item, should evict key2 (least recently used)
        cache.put("key4", "value4")
        
        assert cache.get("key1") == "value1"  # Still there
        assert cache.get("key2") is None      # Evicted
        assert cache.get("key3") == "value3"  # Still there
        assert cache.get("key4") == "value4"  # New item
    
    @pytest.mark.unit
    def test_cache_invalidation(self, cache):
        cache.put("key1", "value1")
        assert cache.invalidate("key1") is True
        assert cache.get("key1") is None
        assert cache.invalidate("nonexistent") is False
    
    @pytest.mark.unit
    def test_cache_statistics(self, cache):
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        
        # Generate hits and misses
        cache.get("key1")  # hit
        cache.get("key1")  # hit
        cache.get("key3")  # miss
        
        stats = cache.get_stats()
        assert stats['size'] == 2
        assert stats['hits'] == 2
        assert stats['misses'] == 1
        assert stats['hit_rate'] == 2/3
    
    @pytest.mark.unit
    def test_cache_clear(self, cache):
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.get("key1")  # Generate some stats
        
        cache.clear()
        
        assert cache.get("key1") is None
        stats = cache.get_stats()
        assert stats['size'] == 0
        assert stats['hits'] == 0
        assert stats['misses'] == 1  # From the get above


class TestDatabaseOptimizer:
    @pytest.fixture
    def optimizer(self):
        return DatabaseOptimizer()
    
    @pytest.mark.unit
    def test_query_performance_logging(self, optimizer):
        optimizer.log_query_performance("SELECT * FROM users", 0.5, 100)
        optimizer.log_query_performance("SELECT * FROM orders", 1.5, 50)  # Slow query
        
        assert len(optimizer.query_stats['all_queries']) == 2
        assert len(optimizer.query_stats['slow_queries']) == 1
        
        slow_query = optimizer.query_stats['slow_queries'][0]
        assert slow_query['is_slow'] is True
        assert slow_query['duration'] == 1.5
    
    @pytest.mark.unit
    def test_query_analysis(self, optimizer):
        # Log various queries
        optimizer.log_query_performance("SELECT * FROM table1", 0.2)
        optimizer.log_query_performance("SELECT * FROM table2", 1.2)  # Slow
        optimizer.log_query_performance("SELECT * FROM table3", 0.8)
        optimizer.log_query_performance("SELECT * FROM table2", 1.5)  # Slow, same query
        
        analysis = optimizer.get_query_analysis()
        
        assert analysis['total_queries'] == 4
        assert analysis['slow_queries'] == 2
        assert analysis['slow_query_rate'] == 0.5
        assert analysis['avg_duration'] == (0.2 + 1.2 + 0.8 + 1.5) / 4
    
    @pytest.mark.unit
    def test_optimization_suggestions(self, optimizer):
        # Create conditions that should trigger suggestions
        # High slow query rate
        for _ in range(10):
            optimizer.log_query_performance("SELECT * FROM slow_table", 2.0)  # All slow
        
        # High connection usage
        optimizer.simulate_connection_usage(9)  # 90% of pool
        
        suggestions = optimizer.suggest_optimizations()
        
        assert len(suggestions) >= 2
        suggestion_types = [s['type'] for s in suggestions]
        assert 'INDEXING' in suggestion_types
        assert 'CONNECTION_POOL' in suggestion_types
    
    @pytest.mark.unit
    def test_connection_usage_simulation(self, optimizer):
        optimizer.simulate_connection_usage(5)
        assert optimizer.active_connections == 5
        
        # Test exceeding pool size
        optimizer.simulate_connection_usage(15)
        assert optimizer.active_connections == optimizer.connection_pool_size


class TestMemoryProfiler:
    @pytest.fixture
    def profiler(self):
        return MemoryProfiler()
    
    @pytest.mark.unit
    def test_snapshot_creation(self, profiler):
        snapshot = profiler.take_snapshot("initial")
        
        assert snapshot['label'] == "initial"
        assert 'memory' in snapshot
        assert 'object_count' in snapshot
        assert snapshot['memory']['rss_mb'] > 0
        assert len(profiler.snapshots) == 1
    
    @pytest.mark.unit
    def test_memory_leak_detection_insufficient_data(self, profiler):
        profiler.take_snapshot("snapshot1")
        
        leak_analysis = profiler.detect_memory_leaks()
        assert leak_analysis['status'] == 'insufficient_data'
    
    @pytest.mark.unit
    def test_memory_leak_detection_with_growth(self, profiler):
        # Take initial snapshot
        profiler.take_snapshot("initial")
        
        # Simulate memory growth by creating objects
        large_list = [f"item_{i}" for i in range(10000)]
        
        # Take second snapshot
        profiler.take_snapshot("after_growth")
        
        leak_analysis = profiler.detect_memory_leaks(threshold_mb=1)
        
        assert 'memory_growth_mb' in leak_analysis
        assert 'object_growth' in leak_analysis
        assert leak_analysis['object_growth'] > 0
    
    @pytest.mark.unit
    def test_object_tracking(self, profiler):
        profiler.track_object_type("MyClass")
        profiler.track_object_type("MyClass")
        profiler.track_object_type("AnotherClass")
        
        report = profiler.get_memory_report()
        assert report['object_tracking']['MyClass'] == 2
        assert report['object_tracking']['AnotherClass'] == 1
    
    @pytest.mark.unit
    def test_memory_report_no_snapshots(self, profiler):
        report = profiler.get_memory_report()
        assert report['status'] == 'no_snapshots'
    
    @pytest.mark.unit
    def test_memory_report_with_snapshots(self, profiler):
        profiler.take_snapshot("snapshot1")
        profiler.track_object_type("TestObject")
        
        report = profiler.get_memory_report()
        
        assert 'current_memory_mb' in report
        assert 'current_object_count' in report
        assert report['snapshots_taken'] == 1
        assert 'TestObject' in report['object_tracking']
    
    @pytest.mark.performance
    def test_performance_monitoring_integration(self):
        """Integration test combining multiple performance monitoring components."""
        monitor = PerformanceMonitor()
        cache = LRUCache(max_size=100)
        profiler = MemoryProfiler()
        
        # Take initial memory snapshot
        profiler.take_snapshot("initial")
        
        # Simulate application workload
        for i in range(50):
            # Start timing an operation
            timer_id = monitor.start_timer(f"operation_{i % 5}")
            
            # Simulate cache usage
            cache_key = f"data_{i % 20}"
            cached_value = cache.get(cache_key)
            if cached_value is None:
                # Simulate expensive computation
                time.sleep(0.001)
                cache.put(cache_key, f"computed_value_{i}")
                monitor.increment_counter("cache_misses")
            else:
                monitor.increment_counter("cache_hits")
            
            # Track memory objects
            profiler.track_object_type("ProcessedItem")
            
            # End timing
            monitor.end_timer(timer_id)
            
            # Record memory usage periodically
            if i % 10 == 0:
                monitor.record_memory_usage(f"batch_{i//10}")
        
        # Take final memory snapshot
        profiler.take_snapshot("final")
        
        # Analyze results
        perf_summary = monitor.get_performance_summary()
        cache_stats = cache.get_stats()
        memory_report = profiler.get_memory_report()
        
        # Assertions
        assert perf_summary['response_time_stats']['count'] == 50
        assert cache_stats['hit_rate'] > 0  # Should have some cache hits
        assert memory_report['snapshots_taken'] == 2
        assert monitor.counters['cache_hits'] + monitor.counters['cache_misses'] == 50
        
        # Performance should be reasonable
        assert perf_summary['response_time_stats']['avg'] < 0.1  # Average under 100ms
        assert cache_stats['hit_rate'] > 0.5  # At least 50% hit rate