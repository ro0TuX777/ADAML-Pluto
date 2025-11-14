#!/usr/bin/env python3
"""
Signal Processing Module for Enhanced ADALM-Pluto SDR Toolkit

This module provides signal processing functions including FFT analysis,
spectrum calculation, peak detection, and signal quality metrics with
improved performance and error handling.

Author: Enhanced SDR Tools - Refactored
License: GPL-2 (compatible with original ADI scripts)
"""

import logging
from typing import Tuple, Optional, List, Dict, Any
from enum import Enum

import numpy as np
from scipy import signal
from scipy.signal import find_peaks

from .constants import SignalProcessing, WindowFunction, ValidationRanges
from .exceptions import FFTProcessingError, SpectrumAnalysisError, InvalidParameterError
from .utils import validate_range, PerformanceTimer

# Configure logging
logger = logging.getLogger(__name__)


class SpectrumAnalysisResult:
    """Container for spectrum analysis results"""
    
    def __init__(self, frequencies: np.ndarray, spectrum: np.ndarray, 
                 sample_rate: float, fft_size: int):
        """
        Initialize spectrum analysis result
        
        Args:
            frequencies: Frequency array in Hz
            spectrum: Spectrum magnitude in dB
            sample_rate: Sample rate used for analysis
            fft_size: FFT size used
        """
        self.frequencies = frequencies
        self.spectrum = spectrum
        self.sample_rate = sample_rate
        self.fft_size = fft_size
        self.peaks = []
        self.noise_floor = None
        self.snr = None
        self.dynamic_range = None
        
        # Calculate basic metrics
        self._calculate_metrics()
    
    def _calculate_metrics(self) -> None:
        """Calculate basic spectrum metrics"""
        if len(self.spectrum) > 0:
            self.noise_floor = np.percentile(self.spectrum, 10)  # 10th percentile as noise floor
            self.dynamic_range = np.max(self.spectrum) - np.min(self.spectrum)
    
    def find_peaks(self, height_threshold: Optional[float] = None,
                   prominence: float = SignalProcessing.MIN_PEAK_PROMINENCE,
                   distance: int = SignalProcessing.MIN_PEAK_DISTANCE) -> List[Dict[str, float]]:
        """
        Find peaks in the spectrum
        
        Args:
            height_threshold: Minimum peak height (dB). If None, uses noise floor + 20 dB
            prominence: Minimum peak prominence (dB)
            distance: Minimum distance between peaks (bins)
            
        Returns:
            List of peak information dictionaries
        """
        if height_threshold is None:
            height_threshold = (self.noise_floor or -80) + 20
        
        try:
            peak_indices, properties = find_peaks(
                self.spectrum,
                height=height_threshold,
                prominence=prominence,
                distance=distance
            )
            
            peaks = []
            for i, idx in enumerate(peak_indices):
                peak_info = {
                    'frequency': self.frequencies[idx],
                    'amplitude': self.spectrum[idx],
                    'prominence': properties['prominences'][i],
                    'index': idx
                }
                peaks.append(peak_info)
            
            # Sort by amplitude (highest first)
            peaks.sort(key=lambda x: x['amplitude'], reverse=True)
            self.peaks = peaks
            
            return peaks
        
        except Exception as e:
            logger.error(f"Peak detection failed: {e}")
            return []
    
    def get_peak_summary(self, max_peaks: int = 10) -> str:
        """
        Get formatted summary of detected peaks
        
        Args:
            max_peaks: Maximum number of peaks to include
            
        Returns:
            Formatted peak summary string
        """
        if not self.peaks:
            return "No peaks detected"
        
        summary = f"Detected {len(self.peaks)} peaks:\n"
        for i, peak in enumerate(self.peaks[:max_peaks]):
            freq_mhz = peak['frequency'] / 1e6
            summary += f"  {i+1:2d}. {freq_mhz:8.3f} MHz: {peak['amplitude']:6.1f} dB\n"
        
        if len(self.peaks) > max_peaks:
            summary += f"  ... and {len(self.peaks) - max_peaks} more\n"
        
        return summary


class WindowFunctionProcessor:
    """Window function processor for FFT analysis"""
    
    @staticmethod
    def get_window(window_type: WindowFunction, size: int) -> np.ndarray:
        """
        Get window function array
        
        Args:
            window_type: Type of window function
            size: Window size
            
        Returns:
            Window function array
        """
        if window_type == WindowFunction.HANN:
            return np.hanning(size)
        elif window_type == WindowFunction.HAMMING:
            return np.hamming(size)
        elif window_type == WindowFunction.BLACKMAN:
            return np.blackman(size)
        elif window_type == WindowFunction.RECTANGULAR:
            return np.ones(size)
        else:
            logger.warning(f"Unknown window type {window_type}, using Hann")
            return np.hanning(size)
    
    @staticmethod
    def get_window_correction_factor(window_type: WindowFunction) -> float:
        """
        Get amplitude correction factor for window function
        
        Args:
            window_type: Type of window function
            
        Returns:
            Correction factor
        """
        # Correction factors for different windows
        corrections = {
            WindowFunction.HANN: 2.0,
            WindowFunction.HAMMING: 1.85,
            WindowFunction.BLACKMAN: 2.8,
            WindowFunction.RECTANGULAR: 1.0
        }
        return corrections.get(window_type, 2.0)


class FFTProcessor:
    """FFT processing with optimizations and error handling"""
    
    def __init__(self, fft_size: int = SignalProcessing.DEFAULT_FFT_SIZE,
                 window_type: WindowFunction = SignalProcessing.DEFAULT_WINDOW):
        """
        Initialize FFT processor
        
        Args:
            fft_size: FFT size
            window_type: Window function type
        """
        validate_range(fft_size, ValidationRanges.FFT_SIZE_RANGE[0], 
                      ValidationRanges.FFT_SIZE_RANGE[1], "fft_size")
        
        self.fft_size = fft_size
        self.window_type = window_type
        self.window = WindowFunctionProcessor.get_window(window_type, fft_size)
        self.window_correction = WindowFunctionProcessor.get_window_correction_factor(window_type)
        
        # Pre-calculate window normalization
        self.window_norm = np.sum(self.window)
    
    def process_samples(self, samples: np.ndarray, sample_rate: float) -> SpectrumAnalysisResult:
        """
        Process IQ samples to generate spectrum
        
        Args:
            samples: Complex IQ samples
            sample_rate: Sample rate in Hz
            
        Returns:
            SpectrumAnalysisResult object
            
        Raises:
            FFTProcessingError: If FFT processing fails
        """
        try:
            with PerformanceTimer("FFT processing"):
                # Validate inputs
                if len(samples) == 0:
                    raise FFTProcessingError(0, self.fft_size)
                
                # Prepare samples
                processed_samples = self._prepare_samples(samples)
                
                # Apply window
                windowed_samples = processed_samples * self.window
                
                # Compute FFT
                fft_result = np.fft.fftshift(np.fft.fft(windowed_samples, self.fft_size))
                
                # Convert to magnitude spectrum in dB
                magnitude = np.abs(fft_result)
                
                # Apply window correction and normalization
                magnitude = magnitude * self.window_correction / self.window_norm
                
                # Convert to dB with noise floor protection
                spectrum_db = 20 * np.log10(magnitude + SignalProcessing.NOISE_FLOOR_OFFSET)
                
                # Generate frequency axis
                frequencies = np.fft.fftshift(np.fft.fftfreq(self.fft_size, 1/sample_rate))
                
                return SpectrumAnalysisResult(frequencies, spectrum_db, sample_rate, self.fft_size)
        
        except Exception as e:
            raise FFTProcessingError(len(samples), self.fft_size) from e
    
    def _prepare_samples(self, samples: np.ndarray) -> np.ndarray:
        """
        Prepare samples for FFT processing
        
        Args:
            samples: Input samples
            
        Returns:
            Prepared samples array
        """
        # Ensure complex data type
        if not np.iscomplexobj(samples):
            # Convert real samples to complex
            samples = samples.astype(np.complex64)
        
        # Handle sample count vs FFT size
        if len(samples) < self.fft_size:
            # Zero-pad if too few samples
            padded = np.zeros(self.fft_size, dtype=samples.dtype)
            padded[:len(samples)] = samples
            return padded
        elif len(samples) > self.fft_size:
            # Take first N samples if too many
            return samples[:self.fft_size]
        else:
            return samples


class SpectrumAnalyzer:
    """High-level spectrum analyzer with multiple processing options"""
    
    def __init__(self, fft_size: int = SignalProcessing.DEFAULT_FFT_SIZE,
                 window_type: WindowFunction = SignalProcessing.DEFAULT_WINDOW,
                 averaging_factor: float = 0.1):
        """
        Initialize spectrum analyzer
        
        Args:
            fft_size: FFT size for analysis
            window_type: Window function type
            averaging_factor: Exponential averaging factor (0-1)
        """
        self.fft_processor = FFTProcessor(fft_size, window_type)
        self.averaging_factor = averaging_factor
        self.averaged_spectrum = None
        self.peak_hold_spectrum = None
        
        validate_range(averaging_factor, 0.0, 1.0, "averaging_factor")
    
    def analyze_samples(self, samples: np.ndarray, sample_rate: float,
                       enable_averaging: bool = True,
                       enable_peak_hold: bool = False) -> SpectrumAnalysisResult:
        """
        Analyze IQ samples and return spectrum
        
        Args:
            samples: Complex IQ samples
            sample_rate: Sample rate in Hz
            enable_averaging: Whether to apply exponential averaging
            enable_peak_hold: Whether to update peak hold
            
        Returns:
            SpectrumAnalysisResult object
        """
        # Process samples
        result = self.fft_processor.process_samples(samples, sample_rate)
        
        # Apply averaging if enabled
        if enable_averaging:
            if self.averaged_spectrum is None:
                self.averaged_spectrum = result.spectrum.copy()
            else:
                alpha = self.averaging_factor
                self.averaged_spectrum = (alpha * result.spectrum + 
                                        (1 - alpha) * self.averaged_spectrum)
                result.spectrum = self.averaged_spectrum.copy()
        
        # Update peak hold if enabled
        if enable_peak_hold:
            if self.peak_hold_spectrum is None:
                self.peak_hold_spectrum = result.spectrum.copy()
            else:
                self.peak_hold_spectrum = np.maximum(self.peak_hold_spectrum, result.spectrum)
        
        return result
    
    def get_peak_hold_spectrum(self) -> Optional[np.ndarray]:
        """Get current peak hold spectrum"""
        return self.peak_hold_spectrum.copy() if self.peak_hold_spectrum is not None else None
    
    def reset_averaging(self) -> None:
        """Reset exponential averaging"""
        self.averaged_spectrum = None
    
    def reset_peak_hold(self) -> None:
        """Reset peak hold data"""
        self.peak_hold_spectrum = None
    
    def estimate_snr(self, result: SpectrumAnalysisResult,
                    signal_frequency: float, signal_bandwidth: float = 1000) -> Optional[float]:
        """
        Estimate Signal-to-Noise Ratio

        Args:
            result: Spectrum analysis result
            signal_frequency: Expected signal frequency in Hz
            signal_bandwidth: Signal bandwidth for SNR calculation in Hz

        Returns:
            Estimated SNR in dB, or None if calculation fails
        """
        try:
            # Validate inputs
            if len(result.spectrum) == 0 or len(result.frequencies) == 0:
                logger.warning("Empty spectrum data for SNR estimation")
                return None

            # Find frequency bin closest to signal frequency
            freq_resolution = result.sample_rate / result.fft_size

            # Convert signal frequency to relative frequency (centered around 0)
            relative_signal_freq = signal_frequency

            # Find the closest frequency bin
            freq_diff = np.abs(result.frequencies - relative_signal_freq)
            signal_bin = np.argmin(freq_diff)

            # Define signal region (±bandwidth/2 around signal)
            bandwidth_bins = max(1, int(signal_bandwidth / freq_resolution))
            signal_start = max(0, signal_bin - bandwidth_bins // 2)
            signal_end = min(len(result.spectrum), signal_bin + bandwidth_bins // 2 + 1)

            # Ensure we have valid signal region
            if signal_start >= signal_end or signal_end > len(result.spectrum):
                logger.warning("Invalid signal region for SNR estimation")
                return None

            # Calculate signal power (max in signal region)
            signal_region = result.spectrum[signal_start:signal_end]
            if len(signal_region) == 0:
                logger.warning("Empty signal region for SNR estimation")
                return None

            signal_power = np.max(signal_region)

            # Calculate noise power (exclude signal region)
            noise_mask = np.ones(len(result.spectrum), dtype=bool)
            noise_mask[signal_start:signal_end] = False

            noise_region = result.spectrum[noise_mask]
            if len(noise_region) == 0:
                logger.warning("Empty noise region for SNR estimation")
                return None

            noise_power = np.mean(noise_region)

            snr = signal_power - noise_power
            return snr

        except Exception as e:
            logger.error(f"SNR estimation failed: {e}")
            return None


# Convenience functions for backward compatibility
def calculate_fft_spectrum(samples: np.ndarray, sample_rate: float,
                          fft_size: int = SignalProcessing.DEFAULT_FFT_SIZE,
                          window_type: WindowFunction = SignalProcessing.DEFAULT_WINDOW) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate FFT spectrum from IQ samples (backward compatibility function)
    
    Args:
        samples: Complex IQ samples
        sample_rate: Sample rate in Hz
        fft_size: FFT size
        window_type: Window function type
        
    Returns:
        Tuple of (frequencies, spectrum_db)
    """
    processor = FFTProcessor(fft_size, window_type)
    result = processor.process_samples(samples, sample_rate)
    return result.frequencies, result.spectrum


def estimate_snr(samples: np.ndarray, signal_frequency: float, sample_rate: float,
                signal_bandwidth: float = 1000) -> Optional[float]:
    """
    Estimate SNR from IQ samples (backward compatibility function)

    Args:
        samples: Complex IQ samples
        signal_frequency: Expected signal frequency in Hz (relative to center)
        sample_rate: Sample rate in Hz
        signal_bandwidth: Signal bandwidth in Hz

    Returns:
        Estimated SNR in dB, or None if calculation fails
    """
    try:
        analyzer = SpectrumAnalyzer()
        result = analyzer.analyze_samples(samples, sample_rate, enable_averaging=False)

        # For backward compatibility, convert absolute frequency to relative frequency
        # The signal_frequency parameter is expected to be relative to the center frequency
        relative_freq = signal_frequency

        return analyzer.estimate_snr(result, relative_freq, signal_bandwidth)
    except Exception as e:
        logger.error(f"SNR estimation failed in compatibility function: {e}")
        return None
