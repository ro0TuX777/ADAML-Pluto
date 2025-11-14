#!/usr/bin/env python3
"""
Constants and Configuration for Enhanced ADALM-Pluto SDR Toolkit

This module centralizes all constants, default values, and configuration
parameters used throughout the enhanced spectrum analyzer toolkit.

Author: Enhanced SDR Tools - Refactored
License: GPL-2 (compatible with original ADI scripts)
"""

from enum import Enum
from typing import Dict, Tuple


class ConnectionType(Enum):
    """Supported connection types for PlutoSDR"""
    USB = "usb"
    IP = "ip"
    ZEROCONF = "zeroconf"
    AUTO = "auto"


class ColorMap(Enum):
    """Available color maps for waterfall display"""
    VIRIDIS = "viridis"
    PLASMA = "plasma"
    INFERNO = "inferno"
    MAGMA = "magma"
    JET = "jet"
    HOT = "hot"
    COOL = "cool"
    GRAY = "gray"


class WindowFunction(Enum):
    """Available window functions for FFT processing"""
    HANN = "hann"
    HAMMING = "hamming"
    BLACKMAN = "blackman"
    RECTANGULAR = "rectangular"


# Device Discovery Constants
class DeviceDiscovery:
    """Constants for device discovery operations"""
    DEFAULT_IPS = ['192.168.2.1', '192.168.1.10']
    DISCOVERY_TIMEOUT = 5  # seconds
    ZEROCONF_HOSTNAME = 'pluto.local'
    USB_DEVICE_NAME = 'PLUTO'


# Frequency and Sample Rate Limits
class FrequencyLimits:
    """Frequency and sample rate limits for PlutoSDR"""
    MIN_FREQUENCY = 70e6      # 70 MHz
    MAX_FREQUENCY = 6e9       # 6 GHz
    MIN_SAMPLE_RATE = 1e6     # 1 MHz
    MAX_SAMPLE_RATE = 61e6    # 61 MHz
    DEFAULT_CENTER_FREQ = 100e6  # 100 MHz
    DEFAULT_SAMPLE_RATE = 20e6   # 20 MHz


# Gain Limits
class GainLimits:
    """Gain limits for PlutoSDR"""
    MIN_RX_GAIN = 0      # dB
    MAX_RX_GAIN = 76     # dB
    DEFAULT_RX_GAIN = 60 # dB
    MIN_TX_GAIN = -89    # dB
    MAX_TX_GAIN = 0      # dB
    DEFAULT_TX_GAIN = -30 # dB


# Temperature Thresholds
class TemperatureThresholds:
    """Temperature warning thresholds"""
    AD9361_WARNING = 70.0    # °C
    AD9361_CRITICAL = 80.0   # °C
    ZYNQ_WARNING = 75.0      # °C
    ZYNQ_CRITICAL = 85.0     # °C


# FFT and Signal Processing
class SignalProcessing:
    """Constants for signal processing operations"""
    DEFAULT_FFT_SIZE = 1024
    AVAILABLE_FFT_SIZES = [256, 512, 1024, 2048, 4096]
    DEFAULT_WINDOW = WindowFunction.HANN
    MIN_PEAK_PROMINENCE = 5.0  # dB
    MIN_PEAK_DISTANCE = 10     # bins
    NOISE_FLOOR_OFFSET = 1e-12 # To avoid log(0)


# Waterfall Display
class WaterfallDefaults:
    """Default values for waterfall display"""
    HISTORY_SIZE = 800
    UPDATE_RATE_MS = 50
    INTENSITY_MIN = -80.0  # dB
    INTENSITY_MAX = -20.0  # dB
    AVERAGING_FACTOR = 0.1
    OVERLAP_RATIO = 0.5


# GUI Constants
class GUIConstants:
    """Constants for GUI applications"""
    MAIN_WINDOW_WIDTH = 1600
    MAIN_WINDOW_HEIGHT = 1000
    STATUS_MESSAGE_TIMEOUT = 3000  # ms
    PLOT_UPDATE_INTERVAL = 50      # ms
    TEMPERATURE_UPDATE_INTERVAL = 5 # seconds


# Calibration Constants
class CalibrationDefaults:
    """Default values for calibration procedures"""
    DEFAULT_RX_LO = 2400000000  # 2.4 GHz
    DEFAULT_TX_LO = 2400000000  # 2.4 GHz
    DEFAULT_CAL_SAMPLE_RATE = 3000000  # 3 MHz
    PEAK_THRESHOLD_OFFSET = 20  # dB below max
    CORRELATION_THRESHOLD = 0.5 # For loopback test


# File and Data Constants
class FileConstants:
    """Constants for file operations"""
    CSV_HEADER = "Frequency_GHz,Amplitude_dB"
    DEFAULT_EXPORT_FORMAT = "csv"
    CONFIG_FILE_EXTENSION = ".json"
    LOG_FILE_EXTENSION = ".log"


# Network Constants
class NetworkConstants:
    """Constants for network operations"""
    CONNECTION_TIMEOUT = 10  # seconds
    RETRY_ATTEMPTS = 3
    RETRY_DELAY = 1  # seconds


# Known Frequency Bands
KNOWN_FREQUENCY_BANDS: Dict[str, Tuple[float, float]] = {
    "FM Radio": (88e6, 108e6),
    "LTE 700": (699e6, 760e6),
    "GSM 850": (869e6, 894e6),
    "GPS L1": (1575e6, 1576e6),
    "GSM 1800": (1710e6, 1880e6),
    "GSM 1900": (1930e6, 1990e6),
    "AWS (LTE 1700/2100)": (1710e6, 2155e6),
    "Wi-Fi 2.4 GHz": (2400e6, 2500e6),
    "Bluetooth": (2400e6, 2483.5e6),
    "Wi-Fi 5 GHz": (5150e6, 5850e6),
}


# Error Messages
class ErrorMessages:
    """Standardized error messages"""
    DEVICE_NOT_FOUND = "No PlutoSDR device found"
    DEVICE_NOT_CONNECTED = "PlutoSDR device not connected"
    CONNECTION_FAILED = "Failed to connect to PlutoSDR device"
    INVALID_FREQUENCY = "Invalid frequency value"
    INVALID_SAMPLE_RATE = "Invalid sample rate value"
    INVALID_GAIN = "Invalid gain value"
    CALIBRATION_FAILED = "Device calibration failed"
    SIGNAL_GENERATION_FAILED = "Signal generation failed"
    FILE_SAVE_FAILED = "Failed to save file"
    FILE_LOAD_FAILED = "Failed to load file"


# Success Messages
class SuccessMessages:
    """Standardized success messages"""
    DEVICE_CONNECTED = "Successfully connected to PlutoSDR"
    DEVICE_DISCONNECTED = "Device disconnected successfully"
    CALIBRATION_COMPLETE = "Calibration completed successfully"
    SIGNAL_TRANSMITTED = "Signal transmission started"
    FILE_SAVED = "File saved successfully"
    CONFIG_LOADED = "Configuration loaded successfully"


# Application Metadata
class AppMetadata:
    """Application metadata and version information"""
    NAME = "Enhanced ADALM-Pluto SDR Toolkit"
    VERSION = "2.0.0"
    AUTHOR = "Enhanced SDR Tools"
    LICENSE = "GPL-2"
    DESCRIPTION = "Comprehensive SDR toolkit integrating multiple ADI repositories"
    
    # Integrated repositories
    INTEGRATED_REPOS = [
        "ADALM-Pluto-Spectrum-Analyzer (original)",
        "plutosdr_scripts (Analog Devices)",
        "plutosdr-fw (Analog Devices)",
        "waterfall display (inspired by Stvff/waterfall)"
    ]


# Logging Configuration
class LoggingConfig:
    """Logging configuration constants"""
    DEFAULT_LEVEL = "INFO"
    FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
    BACKUP_COUNT = 5


# Performance Constants
class PerformanceConstants:
    """Constants for performance optimization"""
    MAX_BUFFER_SIZE = 1024 * 1024  # 1 MB
    CHUNK_SIZE = 4096
    THREAD_POOL_SIZE = 4
    CACHE_SIZE = 100  # Number of items to cache


# Validation Ranges
class ValidationRanges:
    """Validation ranges for various parameters"""
    AMPLITUDE_RANGE = (0.0, 1.0)
    PHASE_RANGE = (0.0, 360.0)
    DURATION_RANGE = (0.001, 10.0)  # seconds
    FFT_SIZE_RANGE = (256, 4096)
    HISTORY_SIZE_RANGE = (100, 2000)
    UPDATE_RATE_RANGE = (10, 1000)  # ms


# Unit Conversion Factors
class UnitConversion:
    """Unit conversion factors"""
    HZ_TO_MHZ = 1e-6
    HZ_TO_GHZ = 1e-9
    MHZ_TO_HZ = 1e6
    GHZ_TO_HZ = 1e9
    MS_TO_S = 1e-3
    S_TO_MS = 1e3


# Default Configurations
DEFAULT_SPECTRUM_CONFIG = {
    'sample_rate': FrequencyLimits.DEFAULT_SAMPLE_RATE,
    'center_frequency': FrequencyLimits.DEFAULT_CENTER_FREQ,
    'rx_gain': GainLimits.DEFAULT_RX_GAIN,
    'tx_gain': GainLimits.DEFAULT_TX_GAIN,
    'fft_size': SignalProcessing.DEFAULT_FFT_SIZE,
    'window_function': SignalProcessing.DEFAULT_WINDOW.value,
}

DEFAULT_WATERFALL_CONFIG = {
    'fft_size': SignalProcessing.DEFAULT_FFT_SIZE,
    'history_size': WaterfallDefaults.HISTORY_SIZE,
    'update_rate_ms': WaterfallDefaults.UPDATE_RATE_MS,
    'center_frequency': FrequencyLimits.DEFAULT_CENTER_FREQ,
    'sample_rate': FrequencyLimits.DEFAULT_SAMPLE_RATE,
    'gain': GainLimits.DEFAULT_RX_GAIN,
    'colormap': ColorMap.VIRIDIS.value,
    'intensity_min': WaterfallDefaults.INTENSITY_MIN,
    'intensity_max': WaterfallDefaults.INTENSITY_MAX,
    'averaging_factor': WaterfallDefaults.AVERAGING_FACTOR,
}

DEFAULT_CALIBRATION_CONFIG = {
    'rx_lo': CalibrationDefaults.DEFAULT_RX_LO,
    'tx_lo': CalibrationDefaults.DEFAULT_TX_LO,
    'sample_rate': CalibrationDefaults.DEFAULT_CAL_SAMPLE_RATE,
    'correlation_threshold': CalibrationDefaults.CORRELATION_THRESHOLD,
}
