"""
Production Metrics Collection
Comprehensive metrics collection for monitoring and observability.
"""

import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import statistics

from app.core.logging import logger


@dataclass
class MetricPoint:
    """Single metric data point."""
    timestamp: float
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricSummary:
    """Summary statistics for a metric."""
    count: int
    sum: float
    min: float
    max: float
    mean: float
    median: float
    p95: float
    p99: float
    recent_rate: float  # Rate in last minute


class TimeWindowBuffer:
    """Thread-safe time window buffer for metrics."""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.buffer = deque(maxlen=max_size)
        self.lock = threading.RLock()
    
    def add(self, point: MetricPoint):
        """Add metric point to buffer."""
        with self.lock:
            self.buffer.append(point)
    
    def get_recent(self, seconds: float = 60.0) -> List[MetricPoint]:
        """Get metric points from recent time window."""
        cutoff_time = time.time() - seconds
        
        with self.lock:
            return [point for point in self.buffer if point.timestamp >= cutoff_time]
    
    def get_all(self) -> List[MetricPoint]:
        """Get all metric points."""
        with self.lock:
            return list(self.buffer)
    
    def clear(self):
        """Clear all metric points."""
        with self.lock:
            self.buffer.clear()
    
    def size(self) -> int:
        """Get buffer size."""
        with self.lock:
            return len(self.buffer)


class MetricsCollector:
    """
    Production-grade metrics collector.
    
    Tracks performance, error rates, and operational metrics
    with configurable retention and aggregation.
    """
    
    def __init__(self, name: str, retention_hours: int = 24, buffer_size: int = 10000):
        self.name = name
        self.retention_seconds = retention_hours * 3600
        self.buffer_size = buffer_size
        
        # Metric storage
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.timers: Dict[str, TimeWindowBuffer] = defaultdict(lambda: TimeWindowBuffer(buffer_size))
        self.histograms: Dict[str, TimeWindowBuffer] = defaultdict(lambda: TimeWindowBuffer(buffer_size))
        
        # Lock for thread safety
        self.lock = threading.RLock()
        
        logger.info_structured(
            "Metrics collector initialized",
            name=name,
            retention_hours=retention_hours,
            buffer_size=buffer_size
        )
    
    def increment_counter(self, metric_name: str, value: float = 1.0, tags: Dict[str, str] = None):
        """Increment a counter metric."""
        with self.lock:
            self.counters[metric_name] += value
            logger.debug_structured(
                f"Counter incremented",
                metric=metric_name,
                value=value,
                total=self.counters[metric_name]
            )
    
    def set_gauge(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """Set a gauge metric."""
        with self.lock:
            self.gauges[metric_name] = value
            logger.debug_structured(
                f"Gauge set",
                metric=metric_name,
                value=value
            )
    
    def record_timer(self, metric_name: str, duration_ms: float, tags: Dict[str, str] = None):
        """Record a timer metric."""
        point = MetricPoint(
            timestamp=time.time(),
            value=duration_ms,
            tags=tags or {}
        )
        
        self.timers[metric_name].add(point)
        
        logger.debug_structured(
            f"Timer recorded",
            metric=metric_name,
            duration_ms=duration_ms
        )
    
    def record_histogram(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """Record a histogram metric."""
        point = MetricPoint(
            timestamp=time.time(),
            value=value,
            tags=tags or {}
        )
        
        self.histograms[metric_name].add(point)
        
        logger.debug_structured(
            f"Histogram recorded",
            metric=metric_name,
            value=value
        )
    
    def record_execution(self, duration_ms: float, success: bool, tags: Dict[str, str] = None):
        """Record execution metrics."""
        # Record execution time
        self.record_timer(f"{self.name}.execution_time", duration_ms, tags)
        
        # Record success/failure
        if success:
            self.increment_counter(f"{self.name}.success", 1.0, tags)
        else:
            self.increment_counter(f"{self.name}.failure", 1.0, tags)
        
        # Record total executions
        self.increment_counter(f"{self.name}.total", 1.0, tags)
    
    def record_pipeline_execution(self, duration_ms: float, success: bool, tags: Dict[str, str] = None):
        """Record pipeline execution metrics."""
        self.record_execution(duration_ms, success, tags)
        
        # Additional pipeline-specific metrics
        if success:
            self.record_histogram(f"{self.name}.successful_pipeline_duration", duration_ms, tags)
        else:
            self.record_histogram(f"{self.name}.failed_pipeline_duration", duration_ms, tags)
    
    def get_counter(self, metric_name: str) -> float:
        """Get counter value."""
        with self.lock:
            return self.counters.get(metric_name, 0.0)
    
    def get_gauge(self, metric_name: str) -> float:
        """Get gauge value."""
        with self.lock:
            return self.gauges.get(metric_name, 0.0)
    
    def get_timer_summary(self, metric_name: str, seconds: float = 300.0) -> Optional[MetricSummary]:
        """Get timer summary for recent time window."""
        recent_points = self.timers[metric_name].get_recent(seconds)
        
        if not recent_points:
            return None
        
        values = [point.value for point in recent_points]
        
        # Calculate rate (points per second)
        time_window = seconds
        recent_rate = len(recent_points) / time_window if time_window > 0 else 0.0
        
        return MetricSummary(
            count=len(values),
            sum=sum(values),
            min=min(values),
            max=max(values),
            mean=statistics.mean(values),
            median=statistics.median(values),
            p95=self._percentile(values, 95),
            p99=self._percentile(values, 99),
            recent_rate=recent_rate
        )
    
    def get_histogram_summary(self, metric_name: str, seconds: float = 300.0) -> Optional[MetricSummary]:
        """Get histogram summary for recent time window."""
        recent_points = self.histograms[metric_name].get_recent(seconds)
        
        if not recent_points:
            return None
        
        values = [point.value for point in recent_points]
        
        # Calculate rate
        time_window = seconds
        recent_rate = len(recent_points) / time_window if time_window > 0 else 0.0
        
        return MetricSummary(
            count=len(values),
            sum=sum(values),
            min=min(values),
            max=max(values),
            mean=statistics.mean(values),
            median=statistics.median(values),
            p95=self._percentile(values, 95),
            p99=self._percentile(values, 99),
            recent_rate=recent_rate
        )
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics summary."""
        with self.lock:
            metrics = {
                "name": self.name,
                "timestamp": datetime.utcnow().isoformat(),
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "timers": {},
                "histograms": {}
            }
            
            # Add timer summaries
            for timer_name in self.timers:
                summary = self.get_timer_summary(timer_name)
                if summary:
                    metrics["timers"][timer_name] = {
                        "count": summary.count,
                        "mean_ms": round(summary.mean, 2),
                        "p95_ms": round(summary.p95, 2),
                        "p99_ms": round(summary.p99, 2),
                        "recent_rate": round(summary.recent_rate, 2)
                    }
            
            # Add histogram summaries
            for hist_name in self.histograms:
                summary = self.get_histogram_summary(hist_name)
                if summary:
                    metrics["histograms"][hist_name] = {
                        "count": summary.count,
                        "mean": round(summary.mean, 2),
                        "p95": round(summary.p95, 2),
                        "p99": round(summary.p99, 2),
                        "recent_rate": round(summary.recent_rate, 2)
                    }
            
            return metrics
    
    def get_health_metrics(self) -> Dict[str, Any]:
        """Get health-related metrics."""
        with self.lock:
            total_executions = self.get_counter(f"{self.name}.total")
            successful_executions = self.get_counter(f"{self.name}.success")
            failed_executions = self.get_counter(f"{self.name}.failure")
            
            success_rate = 0.0
            if total_executions > 0:
                success_rate = (successful_executions / total_executions) * 100
            
            # Get recent execution time
            execution_timer = self.get_timer_summary(f"{self.name}.execution_time")
            avg_execution_time = execution_timer.mean if execution_timer else 0.0
            
            return {
                "name": self.name,
                "total_executions": int(total_executions),
                "successful_executions": int(successful_executions),
                "failed_executions": int(failed_executions),
                "success_rate": round(success_rate, 2),
                "avg_execution_time_ms": round(avg_execution_time, 2),
                "health_status": "healthy" if success_rate >= 95 else "degraded" if success_rate >= 80 else "unhealthy"
            }
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        index = min(index, len(sorted_values) - 1)
        
        return sorted_values[index]
    
    def cleanup_old_metrics(self):
        """Clean up metrics older than retention period."""
        cutoff_time = time.time() - self.retention_seconds
        
        with self.lock:
            # Clean timers
            for timer_name, buffer in self.timers.items():
                with buffer.lock:
                    # Remove old points
                    while buffer.buffer and buffer.buffer[0].timestamp < cutoff_time:
                        buffer.buffer.popleft()
            
            # Clean histograms
            for hist_name, buffer in self.histograms.items():
                with buffer.lock:
                    # Remove old points
                    while buffer.buffer and buffer.buffer[0].timestamp < cutoff_time:
                        buffer.buffer.popleft()
        
        logger.debug_structured(
            "Old metrics cleaned up",
            name=self.name,
            cutoff_time=cutoff_time
        )
    
    def reset(self):
        """Reset all metrics."""
        with self.lock:
            self.counters.clear()
            self.gauges.clear()
            self.timers.clear()
            self.histograms.clear()
        
        logger.info_structured(
            "Metrics reset",
            name=self.name
        )


class MetricsRegistry:
    """Registry for managing multiple metrics collectors."""
    
    def __init__(self):
        self.collectors: Dict[str, MetricsCollector] = {}
        self.lock = threading.RLock()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
    
    def get_collector(self, name: str, **kwargs) -> MetricsCollector:
        """Get or create metrics collector."""
        with self.lock:
            if name not in self.collectors:
                self.collectors[name] = MetricsCollector(name, **kwargs)
            return self.collectors[name]
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get metrics from all collectors."""
        with self.lock:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "collectors": {
                    name: collector.get_all_metrics()
                    for name, collector in self.collectors.items()
                }
            }
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary from all collectors."""
        with self.lock:
            health_metrics = {}
            total_executions = 0
            total_successful = 0
            
            for name, collector in self.collectors.items():
                health = collector.get_health_metrics()
                health_metrics[name] = health
                
                total_executions += health["total_executions"]
                total_successful += health["successful_executions"]
            
            # Calculate overall health
            overall_success_rate = 0.0
            if total_executions > 0:
                overall_success_rate = (total_successful / total_executions) * 100
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "total_collectors": len(self.collectors),
                "total_executions": total_executions,
                "total_successful": total_successful,
                "overall_success_rate": round(overall_success_rate, 2),
                "overall_health": "healthy" if overall_success_rate >= 95 else "degraded" if overall_success_rate >= 80 else "unhealthy",
                "collectors": health_metrics
            }
    
    def _cleanup_loop(self):
        """Background cleanup loop."""
        while True:
            try:
                time.sleep(300)  # Clean every 5 minutes
                
                with self.lock:
                    for collector in self.collectors.values():
                        collector.cleanup_old_metrics()
                        
            except Exception as e:
                logger.error_structured(
                    "Metrics cleanup failed",
                    error=str(e)
                )
    
    def reset_all(self):
        """Reset all collectors."""
        with self.lock:
            for collector in self.collectors.values():
                collector.reset()


# Global metrics registry
metrics_registry = MetricsRegistry()
