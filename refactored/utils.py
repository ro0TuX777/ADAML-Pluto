#!/usr/bin/env python3
"""
Utility Functions for Enhanced ADALM-Pluto SDR Toolkit

This module provides common utility functions used throughout the
enhanced spectrum analyzer toolkit, including formatting, validation,
and helper functions.

Author: Enhanced SDR Tools - Refactored
License: GPL-2 (compatible with original ADI scripts)
"""

import re
import time
import logging
import functools
from typing import Union, Optional, Tuple, List, Any, Callable
from pathlib import Path

import numpy as np

from .constants import UnitConversion, ValidationRanges
from .exceptions import InvalidParameterError


# Configure logging
logger = logging.getLogger(__name__)


def format_frequency(freq_hz: float) -> str:
    """
    Format frequency for human-readable display
    
    Args:
        freq_hz: Frequency in Hz
        
    Returns:
        Formatted frequency string with appropriate units
        
    Examples:
        >>> format_frequency(1000)
        '1.000 kHz'
        >>> format_frequency(2400000000)
        '2.400 GHz'
    """
    if freq_hz >= 1e9:
        return f"{freq_hz * UnitConversion.HZ_TO_GHZ:.3f} GHz"
    elif freq_hz >= 1e6:
        return f"{freq_hz * UnitConversion.HZ_TO_MHZ:.3f} MHz"
    elif freq_hz >= 1e3:
        return f"{freq_hz / 1e3:.3f} kHz"
    else:
        return f"{freq_hz:.1f} Hz"


def parse_frequency(freq_str: str) -> float:
    """
    Parse frequency string to Hz
    
    Args:
        freq_str: Frequency string (e.g., "2.4 GHz", "100 MHz")
        
    Returns:
        Frequency in Hz
        
    Raises:
        InvalidParameterError: If frequency string is invalid
        
    Examples:
        >>> parse_frequency("2.4 GHz")
        2400000000.0
        >>> parse_frequency("100 MHz")
        100000000.0
    """
    freq_str = freq_str.strip().upper()
    
    # Regular expression to match number and optional unit
    pattern = r'^(\d+(?:\.\d+)?)\s*(GHZ|G|MHZ|M|KHZ|K|HZ|H)?$'
    match = re.match(pattern, freq_str)
    
    if not match:
        raise InvalidParameterError("frequency", freq_str, "number with optional unit (GHz, MHz, kHz, Hz)")
    
    value = float(match.group(1))
    unit = match.group(2) or ""
    
    # Convert to Hz based on unit
    if unit in ['GHZ', 'G']:
        return value * UnitConversion.GHZ_TO_HZ
    elif unit in ['MHZ', 'M']:
        return value * UnitConversion.MHZ_TO_HZ
    elif unit in ['KHZ', 'K']:
        return value * 1e3
    else:  # Hz or no unit
        return value


def format_time_duration(seconds: float) -> str:
    """
    Format time duration for human-readable display
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
        
    Examples:
        >>> format_time_duration(3661)
        '1h 1m 1s'
        >>> format_time_duration(125.5)
        '2m 5.5s'
    """
    if seconds >= 3600:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.1f}s"
    elif seconds >= 60:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        return f"{seconds:.1f}s"


def format_data_size(bytes_size: int) -> str:
    """
    Format data size for human-readable display
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Formatted size string
        
    Examples:
        >>> format_data_size(1024)
        '1.0 KB'
        >>> format_data_size(1048576)
        '1.0 MB'
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"


def clamp(value: float, min_value: float, max_value: float) -> float:
    """
    Clamp value to specified range
    
    Args:
        value: Value to clamp
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        
    Returns:
        Clamped value
    """
    return max(min_value, min(value, max_value))


def linear_interpolate(x: float, x1: float, y1: float, x2: float, y2: float) -> float:
    """
    Linear interpolation between two points
    
    Args:
        x: Input value
        x1, y1: First point
        x2, y2: Second point
        
    Returns:
        Interpolated y value
    """
    if x2 == x1:
        return y1
    return y1 + (y2 - y1) * (x - x1) / (x2 - x1)


def db_to_linear(db_value: float) -> float:
    """Convert dB to linear scale"""
    return 10 ** (db_value / 10)


def linear_to_db(linear_value: float) -> float:
    """Convert linear to dB scale"""
    return 10 * np.log10(max(linear_value, 1e-12))


def moving_average(data: np.ndarray, window_size: int) -> np.ndarray:
    """
    Calculate moving average of data
    
    Args:
        data: Input data array
        window_size: Size of moving average window
        
    Returns:
        Moving average array
    """
    if window_size <= 1:
        return data
    
    # Use convolution for efficient moving average
    kernel = np.ones(window_size) / window_size
    return np.convolve(data, kernel, mode='same')


def find_peaks_simple(data: np.ndarray, threshold: float, min_distance: int = 1) -> List[int]:
    """
    Simple peak detection algorithm
    
    Args:
        data: Input data array
        threshold: Minimum peak height
        min_distance: Minimum distance between peaks
        
    Returns:
        List of peak indices
    """
    peaks = []
    
    for i in range(1, len(data) - 1):
        if (data[i] > threshold and 
            data[i] > data[i-1] and 
            data[i] > data[i+1]):
            
            # Check minimum distance from previous peaks
            if not peaks or i - peaks[-1] >= min_distance:
                peaks.append(i)
    
    return peaks


def retry_on_failure(max_attempts: int = 3, delay: float = 1.0, 
                    exceptions: Tuple = (Exception,)) -> Callable:
    """
    Decorator to retry function on failure
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Delay between attempts in seconds
        exceptions: Tuple of exceptions to catch and retry
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_attempts} attempts failed")
            
            raise last_exception
        return wrapper
    return decorator


def timeout_after(seconds: float) -> Callable:
    """
    Decorator to add timeout to function execution

    Args:
        seconds: Timeout in seconds

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                import signal

                def timeout_handler(signum, frame):
                    raise TimeoutError(f"Function {func.__name__} timed out after {seconds}s")

                # Set up timeout (only works on Unix-like systems)
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(seconds))

                try:
                    result = func(*args, **kwargs)
                    signal.alarm(0)  # Cancel timeout
                    return result
                finally:
                    signal.signal(signal.SIGALRM, old_handler)

            except (AttributeError, OSError):
                # SIGALRM not available (Windows) or other OS error
                # Fall back to simple execution without timeout
                logger.debug(f"Timeout not supported on this platform, executing {func.__name__} without timeout")
                return func(*args, **kwargs)

        return wrapper
    return decorator


def validate_range(value: Union[int, float], min_val: Union[int, float], 
                  max_val: Union[int, float], name: str = "value") -> None:
    """
    Validate that value is within specified range
    
    Args:
        value: Value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        name: Name of the parameter for error messages
        
    Raises:
        InvalidParameterError: If value is outside range
    """
    if not (min_val <= value <= max_val):
        raise InvalidParameterError(name, value, f"{min_val}-{max_val}")


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safe division that handles division by zero
    
    Args:
        numerator: Numerator value
        denominator: Denominator value
        default: Default value to return if denominator is zero
        
    Returns:
        Division result or default value
    """
    return numerator / denominator if denominator != 0 else default


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if necessary
    
    Args:
        path: Directory path
        
    Returns:
        Path object for the directory
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def get_timestamp_string(include_microseconds: bool = False) -> str:
    """
    Get current timestamp as string
    
    Args:
        include_microseconds: Whether to include microseconds
        
    Returns:
        Timestamp string
    """
    if include_microseconds:
        return time.strftime("%Y%m%d_%H%M%S") + f"_{int(time.time() * 1000000) % 1000000:06d}"
    else:
        return time.strftime("%Y%m%d_%H%M%S")


def chunks(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks of specified size
    
    Args:
        lst: Input list
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_list(nested_list: List[List[Any]]) -> List[Any]:
    """
    Flatten nested list
    
    Args:
        nested_list: Nested list to flatten
        
    Returns:
        Flattened list
    """
    return [item for sublist in nested_list for item in sublist]


class PerformanceTimer:
    """Context manager for measuring execution time"""
    
    def __init__(self, name: str = "Operation", logger_func: Optional[Callable] = None):
        self.name = name
        self.logger_func = logger_func or logger.info
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        duration = self.end_time - self.start_time
        self.logger_func(f"{self.name} completed in {duration:.3f}s")
    
    @property
    def duration(self) -> Optional[float]:
        """Get duration if measurement is complete"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


class RateLimiter:
    """Rate limiter for controlling operation frequency"""
    
    def __init__(self, max_calls: int, time_window: float):
        """
        Initialize rate limiter
        
        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def can_proceed(self) -> bool:
        """Check if operation can proceed without exceeding rate limit"""
        now = time.time()
        
        # Remove old calls outside the time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        return len(self.calls) < self.max_calls
    
    def record_call(self) -> None:
        """Record a call for rate limiting"""
        self.calls.append(time.time())
    
    def wait_if_needed(self) -> None:
        """Wait if necessary to respect rate limit"""
        if not self.can_proceed():
            # Calculate how long to wait
            oldest_call = min(self.calls)
            wait_time = self.time_window - (time.time() - oldest_call)
            if wait_time > 0:
                time.sleep(wait_time)
        
        self.record_call()
