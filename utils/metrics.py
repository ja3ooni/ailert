import time
import logging
import asyncio
from typing import Dict, Any
from functools import wraps
from collections import defaultdict, deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SimpleMetrics:
    """Simple metrics collection without external dependencies"""
    def __init__(self):
        self.counters = defaultdict(int)
        self.histograms = defaultdict(list)
        self.gauges = defaultdict(float)
        self.timings = defaultdict(deque)
    
    def increment_counter(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        """Increment a counter metric"""
        key = f"{name}:{labels}" if labels else name
        self.counters[key] += value
    
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram value"""
        key = f"{name}:{labels}" if labels else name
        self.histograms[key].append(value)
        # Keep only last 1000 values
        if len(self.histograms[key]) > 1000:
            self.histograms[key] = self.histograms[key][-1000:]
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge value"""
        key = f"{name}:{labels}" if labels else name
        self.gauges[key] = value
    
    def record_timing(self, name: str, duration: float):
        """Record timing information"""
        timestamp = datetime.now()
        self.timings[name].append((timestamp, duration))
        # Keep only last hour of timings
        cutoff = timestamp - timedelta(hours=1)
        while self.timings[name] and self.timings[name][0][0] < cutoff:
            self.timings[name].popleft()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        return {
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'histogram_stats': {
                name: {
                    'count': len(values),
                    'avg': sum(values) / len(values) if values else 0,
                    'min': min(values) if values else 0,
                    'max': max(values) if values else 0
                }
                for name, values in self.histograms.items()
            },
            'timing_stats': {
                name: {
                    'count': len(timings),
                    'avg_duration': sum(t[1] for t in timings) / len(timings) if timings else 0,
                    'recent_count': len([t for t in timings if t[0] > datetime.now() - timedelta(minutes=5)])
                }
                for name, timings in self.timings.items()
            }
        }

# Global metrics instance
metrics = SimpleMetrics()

def track_time(metric_name: str):
    """Decorator to track function execution time"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                metrics.increment_counter(f"{metric_name}_success")
                return result
            except Exception as e:
                metrics.increment_counter(f"{metric_name}_error")
                raise
            finally:
                duration = time.time() - start_time
                metrics.record_histogram(f"{metric_name}_duration", duration)
                metrics.record_timing(metric_name, duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                metrics.increment_counter(f"{metric_name}_success")
                return result
            except Exception as e:
                metrics.increment_counter(f"{metric_name}_error")
                raise
            finally:
                duration = time.time() - start_time
                metrics.record_histogram(f"{metric_name}_duration", duration)
                metrics.record_timing(metric_name, duration)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator