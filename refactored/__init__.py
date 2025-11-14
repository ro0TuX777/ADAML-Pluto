#!/usr/bin/env python3
"""
Refactored Enhanced ADALM-Pluto SDR Toolkit

This package contains the refactored and improved version of the enhanced
ADALM-Pluto spectrum analyzer toolkit with better code organization,
error handling, and maintainability.

Key Improvements:
- Separated concerns into focused modules
- Comprehensive error handling with custom exceptions
- Type hints and documentation throughout
- Performance optimizations
- Configuration management
- Centralized constants and validation

Modules:
- constants: Centralized constants and configuration values
- exceptions: Custom exception classes for better error handling
- utils: Common utility functions and helpers
- device_manager: Device discovery, connection, and management
- signal_processing: FFT analysis and spectrum processing
- config_manager: Configuration and profile management

Author: Enhanced SDR Tools - Refactored
License: GPL-2 (compatible with original ADI scripts)
"""

# Version information
__version__ = "2.0.0"
__author__ = "Enhanced SDR Tools"
__license__ = "GPL-2"

# Import key classes and functions for easy access
from .constants import (
    ConnectionType, ColorMap, WindowFunction, FrequencyLimits, GainLimits,
    DEFAULT_SPECTRUM_CONFIG, DEFAULT_WATERFALL_CONFIG, DEFAULT_CALIBRATION_CONFIG
)

from .exceptions import (
    PlutoSDRError, DeviceError, DeviceNotFoundError, DeviceConnectionError,
    DeviceNotConnectedError, ConfigurationError, InvalidFrequencyError,
    InvalidSampleRateError, InvalidGainError, CalibrationError,
    SignalGenerationError, DataProcessingError, FileOperationError
)

from .utils import (
    format_frequency, parse_frequency, format_time_duration, format_data_size,
    clamp, linear_interpolate, db_to_linear, linear_to_db, moving_average,
    retry_on_failure, timeout_after, validate_range, PerformanceTimer, RateLimiter
)

from .device_manager import (
    DeviceInfo, TemperatureReading, PlutoSDRDevice, PlutoSDRManager
)

from .signal_processing import (
    SpectrumAnalysisResult, WindowFunctionProcessor, FFTProcessor,
    SpectrumAnalyzer, calculate_fft_spectrum, estimate_snr
)

from .config_manager import (
    DeviceConfiguration, SpectrumConfiguration, WaterfallConfiguration,
    CalibrationConfiguration, UserPreferences, ConfigurationProfile,
    ConfigurationManager
)

# Define what gets imported with "from refactored import *"
__all__ = [
    # Version info
    '__version__', '__author__', '__license__',
    
    # Constants and enums
    'ConnectionType', 'ColorMap', 'WindowFunction', 'FrequencyLimits', 'GainLimits',
    'DEFAULT_SPECTRUM_CONFIG', 'DEFAULT_WATERFALL_CONFIG', 'DEFAULT_CALIBRATION_CONFIG',
    
    # Exceptions
    'PlutoSDRError', 'DeviceError', 'DeviceNotFoundError', 'DeviceConnectionError',
    'DeviceNotConnectedError', 'ConfigurationError', 'InvalidFrequencyError',
    'InvalidSampleRateError', 'InvalidGainError', 'CalibrationError',
    'SignalGenerationError', 'DataProcessingError', 'FileOperationError',
    
    # Utilities
    'format_frequency', 'parse_frequency', 'format_time_duration', 'format_data_size',
    'clamp', 'linear_interpolate', 'db_to_linear', 'linear_to_db', 'moving_average',
    'retry_on_failure', 'timeout_after', 'validate_range', 'PerformanceTimer', 'RateLimiter',
    
    # Device management
    'DeviceInfo', 'TemperatureReading', 'PlutoSDRDevice', 'PlutoSDRManager',
    
    # Signal processing
    'SpectrumAnalysisResult', 'WindowFunctionProcessor', 'FFTProcessor',
    'SpectrumAnalyzer', 'calculate_fft_spectrum', 'estimate_snr',
    
    # Configuration management
    'DeviceConfiguration', 'SpectrumConfiguration', 'WaterfallConfiguration',
    'CalibrationConfiguration', 'UserPreferences', 'ConfigurationProfile',
    'ConfigurationManager'
]

# Module-level convenience functions
def get_version_info():
    """Get version information as dictionary"""
    return {
        'version': __version__,
        'author': __author__,
        'license': __license__
    }

def create_default_device_manager(auto_discover=True):
    """Create a device manager with default settings"""
    return PlutoSDRManager(auto_discover=auto_discover)

def create_default_spectrum_analyzer(fft_size=1024):
    """Create a spectrum analyzer with default settings"""
    return SpectrumAnalyzer(fft_size=fft_size)

def create_default_config_manager():
    """Create a configuration manager with default settings"""
    return ConfigurationManager()

# Logging setup
import logging

def setup_logging(level='INFO', format_string=None):
    """
    Set up logging for the refactored toolkit
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string for log messages
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set specific loggers
    logger = logging.getLogger(__name__)
    logger.info(f"Enhanced ADALM-Pluto SDR Toolkit v{__version__} initialized")

# Initialize logging with default settings
setup_logging()

# Compatibility layer for existing code
def get_legacy_pluto_manager(*args, **kwargs):
    """
    Create PlutoSDRManager with legacy interface compatibility
    
    This function provides backward compatibility for existing code
    that uses the original PlutoSDRManager interface.
    """
    import warnings
    warnings.warn(
        "Using legacy interface. Consider migrating to refactored.PlutoSDRManager",
        DeprecationWarning,
        stacklevel=2
    )
    return PlutoSDRManager(*args, **kwargs)

def get_legacy_signal_processing():
    """
    Get signal processing functions with legacy interface
    
    Returns dictionary of legacy-compatible functions.
    """
    import warnings
    warnings.warn(
        "Using legacy interface. Consider migrating to refactored.signal_processing",
        DeprecationWarning,
        stacklevel=2
    )
    
    return {
        'calculate_fft_spectrum': calculate_fft_spectrum,
        'estimate_snr': estimate_snr,
        'format_frequency': format_frequency,
        'parse_frequency': parse_frequency
    }

# Performance monitoring
class PerformanceMonitor:
    """Simple performance monitoring for the toolkit"""
    
    def __init__(self):
        self.timers = {}
        self.counters = {}
    
    def start_timer(self, name):
        """Start a performance timer"""
        import time
        self.timers[name] = time.perf_counter()
    
    def stop_timer(self, name):
        """Stop a performance timer and return duration"""
        import time
        if name in self.timers:
            duration = time.perf_counter() - self.timers[name]
            del self.timers[name]
            return duration
        return None
    
    def increment_counter(self, name, value=1):
        """Increment a performance counter"""
        self.counters[name] = self.counters.get(name, 0) + value
    
    def get_stats(self):
        """Get current performance statistics"""
        return {
            'active_timers': list(self.timers.keys()),
            'counters': self.counters.copy()
        }
    
    def reset(self):
        """Reset all performance monitoring data"""
        self.timers.clear()
        self.counters.clear()

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Module initialization
def initialize_toolkit():
    """Initialize the enhanced toolkit with optimal settings"""
    logger = logging.getLogger(__name__)
    
    try:
        # Check for required dependencies
        import numpy
        import scipy
        logger.debug("Core scientific libraries available")
        
        # Check for optional dependencies
        try:
            import adi
            logger.debug("PyADI-IIO available")
        except ImportError:
            logger.warning("PyADI-IIO not available - device functionality limited")
        
        try:
            import iio
            logger.debug("libiio Python bindings available")
        except ImportError:
            logger.warning("libiio Python bindings not available")
        
        try:
            import PyQt6
            logger.debug("PyQt6 available for GUI applications")
        except ImportError:
            logger.warning("PyQt6 not available - GUI functionality limited")
        
        logger.info("Enhanced ADALM-Pluto SDR Toolkit initialization complete")
        return True
        
    except ImportError as e:
        logger.error(f"Failed to initialize toolkit: {e}")
        return False

# Auto-initialize when module is imported
_initialized = initialize_toolkit()
