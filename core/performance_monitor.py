#!/usr/bin/env python3
"""
Performance Monitoring Module
Provides decorators and utilities for monitoring system performance
"""

import time
import psutil
from functools import wraps
from config import config


def monitor_performance(func):
    """Decorator to monitor function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        
        # Use config for performance threshold
        if end_time - start_time > config.Performance.PERFORMANCE_LOG_THRESHOLD:
            print(f"Performance warning: {func.__name__} took {end_time - start_time:.2f}s")
        
        return result
    return wrapper


class PerformanceMonitor:
    """System performance monitoring utilities"""
    
    @staticmethod
    def get_memory_usage():
        """Get current memory usage in MB"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    @staticmethod
    def get_cpu_usage():
        """Get current CPU usage percentage"""
        return psutil.cpu_percent(interval=1)
    
    @staticmethod
    def check_resource_limits():
        """Check if resource usage is within configured limits"""
        memory_mb = PerformanceMonitor.get_memory_usage()
        cpu_percent = PerformanceMonitor.get_cpu_usage()
        
        issues = []
        
        if memory_mb > config.Safety.MAX_MEMORY_USAGE_MB:
            issues.append(f"Memory usage ({memory_mb:.1f} MB) exceeds limit ({config.Safety.MAX_MEMORY_USAGE_MB} MB)")
        
        if cpu_percent > config.Safety.MAX_CPU_USAGE_PERCENT:
            issues.append(f"CPU usage ({cpu_percent:.1f}%) exceeds limit ({config.Safety.MAX_CPU_USAGE_PERCENT}%)")
        
        return issues
    
    @staticmethod
    def log_performance_stats():
        """Log current performance statistics"""
        memory_mb = PerformanceMonitor.get_memory_usage()
        cpu_percent = PerformanceMonitor.get_cpu_usage()
        
        if config.Logging.ENABLE_PERFORMANCE_LOGGING:
            print(f"Performance Stats - Memory: {memory_mb:.1f} MB, CPU: {cpu_percent:.1f}%")
        
        return {
            'memory_mb': memory_mb,
            'cpu_percent': cpu_percent,
            'timestamp': time.time()
        }
