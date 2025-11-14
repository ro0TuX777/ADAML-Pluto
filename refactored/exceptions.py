#!/usr/bin/env python3
"""
Custom Exceptions for Enhanced ADALM-Pluto SDR Toolkit

This module defines custom exception classes for better error handling
and debugging throughout the enhanced spectrum analyzer toolkit.

Author: Enhanced SDR Tools - Refactored
License: GPL-2 (compatible with original ADI scripts)
"""

from typing import Optional, Any, Dict


class PlutoSDRError(Exception):
    """Base exception class for all PlutoSDR-related errors"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize PlutoSDR error
        
        Args:
            message: Human-readable error message
            error_code: Optional error code for programmatic handling
            details: Optional dictionary with additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self) -> str:
        """Return formatted error message"""
        base_msg = self.message
        if self.error_code:
            base_msg = f"[{self.error_code}] {base_msg}"
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            base_msg = f"{base_msg} (Details: {detail_str})"
        return base_msg


class DeviceError(PlutoSDRError):
    """Base class for device-related errors"""
    pass


class DeviceNotFoundError(DeviceError):
    """Raised when no PlutoSDR device is found"""
    
    def __init__(self, search_criteria: Optional[str] = None):
        message = "No PlutoSDR device found"
        if search_criteria:
            message += f" matching criteria: {search_criteria}"
        super().__init__(message, "DEVICE_NOT_FOUND", {"search_criteria": search_criteria})


class DeviceConnectionError(DeviceError):
    """Raised when device connection fails"""
    
    def __init__(self, uri: str, reason: Optional[str] = None):
        message = f"Failed to connect to PlutoSDR at {uri}"
        if reason:
            message += f": {reason}"
        super().__init__(message, "CONNECTION_FAILED", {"uri": uri, "reason": reason})


class DeviceNotConnectedError(DeviceError):
    """Raised when attempting operations on a disconnected device"""
    
    def __init__(self, operation: Optional[str] = None):
        message = "PlutoSDR device is not connected"
        if operation:
            message += f" (attempted operation: {operation})"
        super().__init__(message, "DEVICE_NOT_CONNECTED", {"operation": operation})


class DeviceTimeoutError(DeviceError):
    """Raised when device operations timeout"""
    
    def __init__(self, operation: str, timeout: float):
        message = f"Device operation '{operation}' timed out after {timeout}s"
        super().__init__(message, "DEVICE_TIMEOUT", {"operation": operation, "timeout": timeout})


class ConfigurationError(PlutoSDRError):
    """Base class for configuration-related errors"""
    pass


class InvalidFrequencyError(ConfigurationError):
    """Raised when an invalid frequency is specified"""
    
    def __init__(self, frequency: float, min_freq: float, max_freq: float):
        message = f"Invalid frequency {frequency/1e6:.1f} MHz (valid range: {min_freq/1e6:.1f}-{max_freq/1e6:.1f} MHz)"
        super().__init__(message, "INVALID_FREQUENCY", {
            "frequency": frequency,
            "min_frequency": min_freq,
            "max_frequency": max_freq
        })


class InvalidSampleRateError(ConfigurationError):
    """Raised when an invalid sample rate is specified"""
    
    def __init__(self, sample_rate: float, min_rate: float, max_rate: float):
        message = f"Invalid sample rate {sample_rate/1e6:.1f} MHz (valid range: {min_rate/1e6:.1f}-{max_rate/1e6:.1f} MHz)"
        super().__init__(message, "INVALID_SAMPLE_RATE", {
            "sample_rate": sample_rate,
            "min_sample_rate": min_rate,
            "max_sample_rate": max_rate
        })


class InvalidGainError(ConfigurationError):
    """Raised when an invalid gain is specified"""
    
    def __init__(self, gain: float, min_gain: float, max_gain: float, gain_type: str = ""):
        gain_type_str = f" {gain_type}" if gain_type else ""
        message = f"Invalid{gain_type_str} gain {gain} dB (valid range: {min_gain}-{max_gain} dB)"
        super().__init__(message, "INVALID_GAIN", {
            "gain": gain,
            "min_gain": min_gain,
            "max_gain": max_gain,
            "gain_type": gain_type
        })


class InvalidParameterError(ConfigurationError):
    """Raised when an invalid parameter value is provided"""
    
    def __init__(self, parameter: str, value: Any, valid_range: Optional[str] = None):
        message = f"Invalid value for parameter '{parameter}': {value}"
        if valid_range:
            message += f" (valid range: {valid_range})"
        super().__init__(message, "INVALID_PARAMETER", {
            "parameter": parameter,
            "value": value,
            "valid_range": valid_range
        })


class CalibrationError(PlutoSDRError):
    """Base class for calibration-related errors"""
    pass


class CalibrationFailedError(CalibrationError):
    """Raised when device calibration fails"""
    
    def __init__(self, stage: Optional[str] = None, reason: Optional[str] = None):
        message = "Device calibration failed"
        if stage:
            message += f" at stage: {stage}"
        if reason:
            message += f" ({reason})"
        super().__init__(message, "CALIBRATION_FAILED", {"stage": stage, "reason": reason})


class LoopbackTestError(CalibrationError):
    """Raised when loopback test fails"""
    
    def __init__(self, correlation: Optional[float] = None, threshold: Optional[float] = None):
        message = "Loopback test failed"
        if correlation is not None and threshold is not None:
            message += f" (correlation: {correlation:.3f}, threshold: {threshold:.3f})"
        super().__init__(message, "LOOPBACK_FAILED", {
            "correlation": correlation,
            "threshold": threshold
        })


class SignalGenerationError(PlutoSDRError):
    """Base class for signal generation errors"""
    pass


class WaveformGenerationError(SignalGenerationError):
    """Raised when waveform generation fails"""
    
    def __init__(self, waveform_type: str, reason: Optional[str] = None):
        message = f"Failed to generate {waveform_type} waveform"
        if reason:
            message += f": {reason}"
        super().__init__(message, "WAVEFORM_GENERATION_FAILED", {
            "waveform_type": waveform_type,
            "reason": reason
        })


class TransmissionError(SignalGenerationError):
    """Raised when signal transmission fails"""
    
    def __init__(self, reason: Optional[str] = None):
        message = "Signal transmission failed"
        if reason:
            message += f": {reason}"
        super().__init__(message, "TRANSMISSION_FAILED", {"reason": reason})


class DDSConfigurationError(SignalGenerationError):
    """Raised when DDS configuration fails"""
    
    def __init__(self, frequency: Optional[float] = None, reason: Optional[str] = None):
        message = "DDS configuration failed"
        if frequency:
            message += f" for frequency {frequency/1000:.1f} kHz"
        if reason:
            message += f": {reason}"
        super().__init__(message, "DDS_CONFIG_FAILED", {
            "frequency": frequency,
            "reason": reason
        })


class DataProcessingError(PlutoSDRError):
    """Base class for data processing errors"""
    pass


class FFTProcessingError(DataProcessingError):
    """Raised when FFT processing fails"""
    
    def __init__(self, samples_length: Optional[int] = None, fft_size: Optional[int] = None):
        message = "FFT processing failed"
        if samples_length and fft_size:
            message += f" (samples: {samples_length}, FFT size: {fft_size})"
        super().__init__(message, "FFT_PROCESSING_FAILED", {
            "samples_length": samples_length,
            "fft_size": fft_size
        })


class SpectrumAnalysisError(DataProcessingError):
    """Raised when spectrum analysis fails"""
    
    def __init__(self, analysis_type: str, reason: Optional[str] = None):
        message = f"Spectrum analysis failed: {analysis_type}"
        if reason:
            message += f" ({reason})"
        super().__init__(message, "SPECTRUM_ANALYSIS_FAILED", {
            "analysis_type": analysis_type,
            "reason": reason
        })


class FileOperationError(PlutoSDRError):
    """Base class for file operation errors"""
    pass


class ConfigurationFileError(FileOperationError):
    """Raised when configuration file operations fail"""
    
    def __init__(self, filename: str, operation: str, reason: Optional[str] = None):
        message = f"Configuration file {operation} failed: {filename}"
        if reason:
            message += f" ({reason})"
        super().__init__(message, "CONFIG_FILE_ERROR", {
            "filename": filename,
            "operation": operation,
            "reason": reason
        })


class DataExportError(FileOperationError):
    """Raised when data export fails"""
    
    def __init__(self, filename: str, format_type: str, reason: Optional[str] = None):
        message = f"Data export failed: {filename} ({format_type})"
        if reason:
            message += f" - {reason}"
        super().__init__(message, "DATA_EXPORT_FAILED", {
            "filename": filename,
            "format": format_type,
            "reason": reason
        })


class TemperatureError(PlutoSDRError):
    """Base class for temperature-related errors"""
    pass


class TemperatureReadError(TemperatureError):
    """Raised when temperature reading fails"""
    
    def __init__(self, sensor: str, reason: Optional[str] = None):
        message = f"Failed to read {sensor} temperature"
        if reason:
            message += f": {reason}"
        super().__init__(message, "TEMPERATURE_READ_FAILED", {
            "sensor": sensor,
            "reason": reason
        })


class OvertemperatureError(TemperatureError):
    """Raised when device temperature exceeds safe limits"""
    
    def __init__(self, sensor: str, temperature: float, threshold: float):
        message = f"{sensor} temperature ({temperature:.1f}°C) exceeds threshold ({threshold:.1f}°C)"
        super().__init__(message, "OVERTEMPERATURE", {
            "sensor": sensor,
            "temperature": temperature,
            "threshold": threshold
        })


class GUIError(PlutoSDRError):
    """Base class for GUI-related errors"""
    pass


class WidgetInitializationError(GUIError):
    """Raised when GUI widget initialization fails"""
    
    def __init__(self, widget_name: str, reason: Optional[str] = None):
        message = f"Failed to initialize widget: {widget_name}"
        if reason:
            message += f" ({reason})"
        super().__init__(message, "WIDGET_INIT_FAILED", {
            "widget_name": widget_name,
            "reason": reason
        })


class PlotUpdateError(GUIError):
    """Raised when plot update fails"""
    
    def __init__(self, plot_type: str, reason: Optional[str] = None):
        message = f"Failed to update {plot_type} plot"
        if reason:
            message += f": {reason}"
        super().__init__(message, "PLOT_UPDATE_FAILED", {
            "plot_type": plot_type,
            "reason": reason
        })


# Exception handling utilities
def handle_device_error(func):
    """Decorator to handle common device errors"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if "not found" in str(e).lower():
                raise DeviceNotFoundError() from e
            elif "connection" in str(e).lower() or "timeout" in str(e).lower():
                raise DeviceConnectionError("unknown", str(e)) from e
            else:
                raise DeviceError(str(e)) from e
    return wrapper


def validate_frequency(frequency: float, min_freq: float, max_freq: float) -> None:
    """Validate frequency range"""
    if not (min_freq <= frequency <= max_freq):
        raise InvalidFrequencyError(frequency, min_freq, max_freq)


def validate_sample_rate(sample_rate: float, min_rate: float, max_rate: float) -> None:
    """Validate sample rate range"""
    if not (min_rate <= sample_rate <= max_rate):
        raise InvalidSampleRateError(sample_rate, min_rate, max_rate)


def validate_gain(gain: float, min_gain: float, max_gain: float, gain_type: str = "") -> None:
    """Validate gain range"""
    if not (min_gain <= gain <= max_gain):
        raise InvalidGainError(gain, min_gain, max_gain, gain_type)


def validate_parameter(parameter: str, value: Any, valid_range: tuple) -> None:
    """Validate parameter within range"""
    min_val, max_val = valid_range
    if not (min_val <= value <= max_val):
        raise InvalidParameterError(parameter, value, f"{min_val}-{max_val}")
