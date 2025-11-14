#!/usr/bin/env python3
"""
Waterfall Display Module for Enhanced ADALM-Pluto Spectrum Analyzer

This module provides real-time waterfall spectrum visualization inspired by
the Stvff/waterfall repository, implemented in Python with PyQt6 and PyQtGraph.

Features:
- Real-time waterfall display with time history
- Interactive frequency and bandwidth control
- Colormap customization and intensity scaling
- Peak detection and frequency marking
- Integration with enhanced spectrum analyzer
- Configurable display parameters

Author: Enhanced integration inspired by Stvff/waterfall
License: GPL-2 (compatible with original projects)
"""

import sys
import time
import numpy as np
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QSlider, QComboBox, QSpinBox, 
    QDoubleSpinBox, QCheckBox, QGroupBox, QGridLayout
)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent

# Import our enhanced utilities
from pluto_utils import PlutoSDRManager, format_frequency


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


@dataclass
class WaterfallConfig:
    """Configuration parameters for waterfall display"""
    fft_size: int = 1024
    history_size: int = 800
    update_rate_ms: int = 50
    center_frequency: float = 100e6
    sample_rate: float = 20e6
    gain: float = 60.0
    colormap: ColorMap = ColorMap.VIRIDIS
    intensity_min: float = -80.0
    intensity_max: float = -20.0
    window_function: str = "hann"
    overlap_ratio: float = 0.5
    averaging_factor: float = 0.1


class WaterfallDisplay(QWidget):
    """
    Real-time waterfall spectrum display widget
    """
    
    # Signals
    frequency_changed = pyqtSignal(float)  # New center frequency
    sample_rate_changed = pyqtSignal(float)  # New sample rate
    peak_detected = pyqtSignal(float, float)  # Frequency, amplitude
    
    def __init__(self, pluto_manager: Optional[PlutoSDRManager] = None, 
                 config: Optional[WaterfallConfig] = None):
        """
        Initialize waterfall display
        
        Args:
            pluto_manager: Connected PlutoSDRManager instance
            config: Waterfall configuration parameters
        """
        super().__init__()
        
        self.pluto_manager = pluto_manager
        self.config = config or WaterfallConfig()
        
        # Display state
        self.is_running = False
        self.is_paused = False
        self.waterfall_data = np.zeros((self.config.history_size, self.config.fft_size))
        self.frequency_axis = np.linspace(-self.config.sample_rate/2, 
                                        self.config.sample_rate/2, 
                                        self.config.fft_size)
        self.time_axis = np.arange(self.config.history_size)
        
        # Peak detection
        self.peak_hold_data = np.full(self.config.fft_size, -120.0)
        self.peak_markers = []
        
        # Initialize UI
        self.init_ui()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        
        # Configure initial settings
        self.apply_configuration()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Control panel
        control_group = QGroupBox("Waterfall Controls")
        control_layout = QGridLayout(control_group)
        
        # Row 1: Basic controls
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.toggle_acquisition)
        control_layout.addWidget(self.start_button, 0, 0)
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.toggle_pause)
        control_layout.addWidget(self.pause_button, 0, 1)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_display)
        control_layout.addWidget(self.clear_button, 0, 2)
        
        self.peak_hold_checkbox = QCheckBox("Peak Hold")
        self.peak_hold_checkbox.setChecked(True)
        control_layout.addWidget(self.peak_hold_checkbox, 0, 3)
        
        # Row 2: Frequency controls
        control_layout.addWidget(QLabel("Center Freq (MHz):"), 1, 0)
        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setRange(70, 6000)
        self.freq_spin.setValue(self.config.center_frequency / 1e6)
        self.freq_spin.setSuffix(" MHz")
        self.freq_spin.valueChanged.connect(self.on_frequency_changed)
        control_layout.addWidget(self.freq_spin, 1, 1)
        
        control_layout.addWidget(QLabel("Sample Rate (MHz):"), 1, 2)
        self.sr_spin = QDoubleSpinBox()
        self.sr_spin.setRange(1, 61)
        self.sr_spin.setValue(self.config.sample_rate / 1e6)
        self.sr_spin.setSuffix(" MHz")
        self.sr_spin.valueChanged.connect(self.on_sample_rate_changed)
        control_layout.addWidget(self.sr_spin, 1, 3)
        
        # Row 3: Display controls
        control_layout.addWidget(QLabel("Colormap:"), 2, 0)
        self.colormap_combo = QComboBox()
        self.colormap_combo.addItems([cm.value for cm in ColorMap])
        self.colormap_combo.setCurrentText(self.config.colormap.value)
        self.colormap_combo.currentTextChanged.connect(self.on_colormap_changed)
        control_layout.addWidget(self.colormap_combo, 2, 1)
        
        control_layout.addWidget(QLabel("FFT Size:"), 2, 2)
        self.fft_size_combo = QComboBox()
        self.fft_size_combo.addItems(["256", "512", "1024", "2048", "4096"])
        self.fft_size_combo.setCurrentText(str(self.config.fft_size))
        self.fft_size_combo.currentTextChanged.connect(self.on_fft_size_changed)
        control_layout.addWidget(self.fft_size_combo, 2, 3)
        
        layout.addWidget(control_group)
        
        # Intensity controls
        intensity_group = QGroupBox("Intensity Controls")
        intensity_layout = QHBoxLayout(intensity_group)
        
        intensity_layout.addWidget(QLabel("Min:"))
        self.intensity_min_spin = QDoubleSpinBox()
        self.intensity_min_spin.setRange(-120, 0)
        self.intensity_min_spin.setValue(self.config.intensity_min)
        self.intensity_min_spin.setSuffix(" dB")
        self.intensity_min_spin.valueChanged.connect(self.update_intensity_range)
        intensity_layout.addWidget(self.intensity_min_spin)
        
        intensity_layout.addWidget(QLabel("Max:"))
        self.intensity_max_spin = QDoubleSpinBox()
        self.intensity_max_spin.setRange(-120, 0)
        self.intensity_max_spin.setValue(self.config.intensity_max)
        self.intensity_max_spin.setSuffix(" dB")
        self.intensity_max_spin.valueChanged.connect(self.update_intensity_range)
        intensity_layout.addWidget(self.intensity_max_spin)
        
        intensity_layout.addWidget(QLabel("Averaging:"))
        self.averaging_spin = QDoubleSpinBox()
        self.averaging_spin.setRange(0.01, 1.0)
        self.averaging_spin.setValue(self.config.averaging_factor)
        self.averaging_spin.setSingleStep(0.05)
        self.averaging_spin.valueChanged.connect(self.on_averaging_changed)
        intensity_layout.addWidget(self.averaging_spin)
        
        layout.addWidget(intensity_group)
        
        # Waterfall plot
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel('left', 'Time', units='samples')
        self.plot_widget.setLabel('bottom', 'Frequency', units='MHz')
        self.plot_widget.setTitle('Waterfall Spectrum Display')
        
        # Create image item for waterfall
        self.waterfall_image = pg.ImageItem()
        self.plot_widget.addItem(self.waterfall_image)
        
        # Add colorbar
        self.colorbar = pg.ColorBarItem(
            values=(self.config.intensity_min, self.config.intensity_max),
            colorMap=self.config.colormap.value
        )
        self.colorbar.setImageItem(self.waterfall_image)
        
        layout.addWidget(self.plot_widget)
        
        # Status display
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        # Set up keyboard shortcuts
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard shortcuts"""
        key = event.key()
        modifiers = event.modifiers()
        
        # Frequency control with arrow keys
        freq_step = 10e6 if modifiers & Qt.KeyboardModifier.ShiftModifier else 100e6
        sr_step = 1e6 if modifiers & Qt.KeyboardModifier.ShiftModifier else 10e6
        
        if key == Qt.Key.Key_Up:
            new_freq = min(self.config.center_frequency + freq_step, 6e9)
            self.set_center_frequency(new_freq)
        elif key == Qt.Key.Key_Down:
            new_freq = max(self.config.center_frequency - freq_step, 70e6)
            self.set_center_frequency(new_freq)
        elif key == Qt.Key.Key_Right:
            new_sr = min(self.config.sample_rate + sr_step, 61e6)
            self.set_sample_rate(new_sr)
        elif key == Qt.Key.Key_Left:
            new_sr = max(self.config.sample_rate - sr_step, 1e6)
            self.set_sample_rate(new_sr)
        elif key == Qt.Key.Key_Space:
            self.toggle_pause()
        elif key == Qt.Key.Key_C:
            self.clear_display()
        elif key == Qt.Key.Key_M:
            self.mark_peak()
        else:
            super().keyPressEvent(event)
    
    def apply_configuration(self):
        """Apply current configuration to PlutoSDR"""
        if not self.pluto_manager or not self.pluto_manager.is_connected:
            return False
        
        try:
            # Configure PlutoSDR
            success = self.pluto_manager.configure_basic_settings(
                rx_lo=int(self.config.center_frequency),
                sample_rate=int(self.config.sample_rate),
                rx_bandwidth=int(self.config.sample_rate),
                rx_gain=int(self.config.gain)
            )
            
            if success:
                # Update frequency axis
                self.frequency_axis = np.linspace(
                    self.config.center_frequency - self.config.sample_rate/2,
                    self.config.center_frequency + self.config.sample_rate/2,
                    self.config.fft_size
                ) / 1e6  # Convert to MHz for display
                
                # Reset waterfall data
                self.waterfall_data = np.zeros((self.config.history_size, self.config.fft_size))
                self.peak_hold_data = np.full(self.config.fft_size, -120.0)
                
                self.status_label.setText(f"Configured: {format_frequency(self.config.center_frequency)}, "
                                        f"SR: {format_frequency(self.config.sample_rate)}")
                return True
            else:
                self.status_label.setText("Configuration failed")
                return False
                
        except Exception as e:
            self.status_label.setText(f"Error: {e}")
            return False

    def toggle_acquisition(self):
        """Start or stop waterfall acquisition"""
        if self.is_running:
            self.stop_acquisition()
        else:
            self.start_acquisition()

    def start_acquisition(self):
        """Start waterfall data acquisition"""
        if not self.pluto_manager or not self.pluto_manager.is_connected:
            self.status_label.setText("No PlutoSDR connected")
            return

        if self.apply_configuration():
            self.is_running = True
            self.is_paused = False
            self.start_button.setText("Stop")
            self.update_timer.start(self.config.update_rate_ms)
            self.status_label.setText("Acquiring...")

    def stop_acquisition(self):
        """Stop waterfall data acquisition"""
        self.is_running = False
        self.update_timer.stop()
        self.start_button.setText("Start")
        self.status_label.setText("Stopped")

    def toggle_pause(self):
        """Toggle pause state"""
        if self.is_running:
            self.is_paused = not self.is_paused
            self.pause_button.setText("Resume" if self.is_paused else "Pause")
            self.status_label.setText("Paused" if self.is_paused else "Acquiring...")

    def clear_display(self):
        """Clear waterfall display and peak hold data"""
        self.waterfall_data.fill(self.config.intensity_min)
        self.peak_hold_data.fill(-120.0)
        self.clear_peak_markers()
        self.update_waterfall_image()
        self.status_label.setText("Display cleared")

    def update_display(self):
        """Main update loop for waterfall display"""
        if not self.is_running or self.is_paused:
            return

        if not self.pluto_manager or not self.pluto_manager.is_connected:
            self.stop_acquisition()
            return

        try:
            # Get new data from PlutoSDR
            samples = self.pluto_manager.sdr.rx()

            # Compute FFT
            spectrum_db = self.compute_fft_spectrum(samples)

            # Update waterfall data (scroll up)
            self.waterfall_data[1:] = self.waterfall_data[:-1]
            self.waterfall_data[0] = spectrum_db

            # Update peak hold
            if self.peak_hold_checkbox.isChecked():
                self.peak_hold_data = np.maximum(self.peak_hold_data, spectrum_db)

            # Update display
            self.update_waterfall_image()

            # Detect peaks
            self.detect_peaks(spectrum_db)

        except Exception as e:
            self.status_label.setText(f"Update error: {e}")

    def compute_fft_spectrum(self, samples: np.ndarray) -> np.ndarray:
        """
        Compute FFT spectrum from IQ samples

        Args:
            samples: Complex IQ samples

        Returns:
            Spectrum in dB
        """
        # Ensure we have enough samples
        if len(samples) < self.config.fft_size:
            # Pad with zeros if needed
            padded = np.zeros(self.config.fft_size, dtype=samples.dtype)
            padded[:len(samples)] = samples
            samples = padded
        else:
            # Take first N samples
            samples = samples[:self.config.fft_size]

        # Apply window function
        if self.config.window_function == "hann":
            window = np.hanning(self.config.fft_size)
        elif self.config.window_function == "hamming":
            window = np.hamming(self.config.fft_size)
        elif self.config.window_function == "blackman":
            window = np.blackman(self.config.fft_size)
        else:
            window = np.ones(self.config.fft_size)

        windowed_samples = samples * window

        # Compute FFT
        fft_result = np.fft.fftshift(np.fft.fft(windowed_samples))

        # Convert to dB
        magnitude = np.abs(fft_result)
        spectrum_db = 20 * np.log10(magnitude + 1e-12)  # Avoid log(0)

        # Apply averaging
        if hasattr(self, '_previous_spectrum'):
            alpha = self.config.averaging_factor
            spectrum_db = alpha * spectrum_db + (1 - alpha) * self._previous_spectrum

        self._previous_spectrum = spectrum_db.copy()

        return spectrum_db

    def update_waterfall_image(self):
        """Update the waterfall image display"""
        # Normalize data to intensity range
        normalized_data = np.clip(
            (self.waterfall_data - self.config.intensity_min) /
            (self.config.intensity_max - self.config.intensity_min),
            0, 1
        )

        # Update image
        self.waterfall_image.setImage(
            normalized_data,
            levels=(0, 1),
            scale=(
                (self.frequency_axis[-1] - self.frequency_axis[0]) / self.config.fft_size,
                1
            ),
            pos=(self.frequency_axis[0], 0)
        )

        # Update colormap
        self.waterfall_image.setColorMap(self.config.colormap.value)

    def detect_peaks(self, spectrum: np.ndarray):
        """
        Detect and mark spectral peaks

        Args:
            spectrum: Current spectrum in dB
        """
        # Simple peak detection
        threshold = self.config.intensity_max - 20  # 20 dB below max

        # Find peaks above threshold
        peak_indices = []
        for i in range(1, len(spectrum) - 1):
            if (spectrum[i] > threshold and
                spectrum[i] > spectrum[i-1] and
                spectrum[i] > spectrum[i+1]):
                peak_indices.append(i)

        # Emit peak signals
        for idx in peak_indices:
            freq = self.frequency_axis[idx] * 1e6  # Convert back to Hz
            amplitude = spectrum[idx]
            self.peak_detected.emit(freq, amplitude)

    def mark_peak(self):
        """Mark the highest peak in current spectrum"""
        if hasattr(self, '_previous_spectrum'):
            max_idx = np.argmax(self._previous_spectrum)
            max_freq = self.frequency_axis[max_idx] * 1e6
            max_amp = self._previous_spectrum[max_idx]

            # Add visual marker
            marker = pg.InfiniteLine(
                pos=self.frequency_axis[max_idx],
                angle=90,
                pen=pg.mkPen('r', width=2),
                label=f'{max_freq/1e6:.3f} MHz\n{max_amp:.1f} dB'
            )
            self.plot_widget.addItem(marker)
            self.peak_markers.append(marker)

            self.status_label.setText(f"Peak marked: {format_frequency(max_freq)}, {max_amp:.1f} dB")

    def clear_peak_markers(self):
        """Clear all peak markers"""
        for marker in self.peak_markers:
            self.plot_widget.removeItem(marker)
        self.peak_markers.clear()

    # Event handlers for UI controls
    def on_frequency_changed(self, value):
        """Handle frequency change from UI"""
        self.set_center_frequency(value * 1e6)

    def on_sample_rate_changed(self, value):
        """Handle sample rate change from UI"""
        self.set_sample_rate(value * 1e6)

    def on_colormap_changed(self, colormap_name):
        """Handle colormap change"""
        self.config.colormap = ColorMap(colormap_name)
        self.update_waterfall_image()

    def on_fft_size_changed(self, size_str):
        """Handle FFT size change"""
        new_size = int(size_str)
        if new_size != self.config.fft_size:
            self.config.fft_size = new_size
            # Reinitialize arrays
            self.waterfall_data = np.zeros((self.config.history_size, self.config.fft_size))
            self.peak_hold_data = np.full(self.config.fft_size, -120.0)
            self.apply_configuration()

    def on_averaging_changed(self, value):
        """Handle averaging factor change"""
        self.config.averaging_factor = value

    def update_intensity_range(self):
        """Update intensity range from UI controls"""
        self.config.intensity_min = self.intensity_min_spin.value()
        self.config.intensity_max = self.intensity_max_spin.value()

        # Update colorbar
        self.colorbar.setLevels((self.config.intensity_min, self.config.intensity_max))

        # Update display
        self.update_waterfall_image()

    def set_center_frequency(self, frequency: float):
        """Set center frequency and update display"""
        self.config.center_frequency = frequency
        self.freq_spin.setValue(frequency / 1e6)

        if self.is_running:
            self.apply_configuration()

        self.frequency_changed.emit(frequency)

    def set_sample_rate(self, sample_rate: float):
        """Set sample rate and update display"""
        self.config.sample_rate = sample_rate
        self.sr_spin.setValue(sample_rate / 1e6)

        if self.is_running:
            self.apply_configuration()

        self.sample_rate_changed.emit(sample_rate)

    def get_configuration(self) -> WaterfallConfig:
        """Get current configuration"""
        return self.config

    def set_configuration(self, config: WaterfallConfig):
        """Set new configuration"""
        self.config = config

        # Update UI controls
        self.freq_spin.setValue(config.center_frequency / 1e6)
        self.sr_spin.setValue(config.sample_rate / 1e6)
        self.colormap_combo.setCurrentText(config.colormap.value)
        self.fft_size_combo.setCurrentText(str(config.fft_size))
        self.intensity_min_spin.setValue(config.intensity_min)
        self.intensity_max_spin.setValue(config.intensity_max)
        self.averaging_spin.setValue(config.averaging_factor)

        # Apply configuration
        if self.is_running:
            self.apply_configuration()
