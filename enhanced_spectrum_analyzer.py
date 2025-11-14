#!/usr/bin/env python3
"""
Enhanced ADALM-Pluto Spectrum Analyzer

This enhanced version integrates features from plutosdr_scripts and plutosdr-fw
repositories to provide comprehensive SDR functionality including:

- Automatic device discovery and connection management
- Temperature monitoring and diagnostics
- Calibration routines
- Signal generation capabilities
- Configuration management
- Advanced measurement modes

Author: Enhanced integration from multiple ADI sources
License: GPL-2 (compatible with original ADI scripts)
"""

import sys
import numpy as np
import time
from scipy.signal import (firwin, lfilter, kaiserord, find_peaks)
import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QPushButton, QHBoxLayout, QLabel, QFileDialog, QStatusBar,
    QLineEdit, QComboBox, QGroupBox, QGridLayout, QTabWidget,
    QTextEdit, QProgressBar, QCheckBox, QSpinBox, QDoubleSpinBox
)
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QCursor, QFont

# Import our enhanced utility library
from pluto_utils import (
    PlutoSDRManager, SignalGenerator, CalibrationManager,
    ConfigurationManager, format_frequency, parse_frequency,
    calculate_fft_spectrum, estimate_snr
)

# Import waterfall display
from waterfall_display import WaterfallDisplay, WaterfallConfig, ColorMap

# Import the original draggable text item
from spectrum_analyzer import DraggableTextItem


class DeviceMonitorThread(QThread):
    """Background thread for monitoring device status and temperatures"""
    
    temperature_update = pyqtSignal(dict)
    connection_status = pyqtSignal(bool)
    
    def __init__(self, pluto_manager):
        super().__init__()
        self.pluto_manager = pluto_manager
        self.running = True
        self.monitor_interval = 5  # seconds
    
    def run(self):
        while self.running:
            if self.pluto_manager and self.pluto_manager.is_connected:
                # Check connection status
                self.connection_status.emit(True)
                
                # Get temperatures
                temps = self.pluto_manager.get_temperatures()
                if temps:
                    self.temperature_update.emit(temps)
            else:
                self.connection_status.emit(False)
            
            # Sleep in small increments to allow quick shutdown
            for _ in range(self.monitor_interval * 10):
                if not self.running:
                    break
                self.msleep(100)
    
    def stop(self):
        self.running = False
        self.wait()


class EnhancedMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enhanced ADALM-Pluto Spectrum Analyzer")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Initialize enhanced PlutoSDR manager
        self.pluto_manager = None
        self.signal_generator = None
        self.calibration_manager = None
        self.config_manager = None
        self.device_monitor = None
        
        # Original spectrum analyzer parameters
        self.sample_rate = 1.0e6
        self.rf_bw = 1.0e6
        self.cutoff_hz = 400e3
        self.sweep_start = 100e6
        self.sweep_stop = 6e9
        self.sweep_steps = 2000
        
        # Data storage
        self.freq_list = []
        self.amp_list = []
        self.peak_hold_data = {}
        self.sweep_index = 0
        self.sweep_complete = False
        self.pause_counter = 0
        self.is_paused = False
        
        # Known bands
        self.all_known_bands = {
            "LTE 700": (0.699, 0.76),
            "GSM 850": (0.869, 0.894),
            "GSM 1900": (1.93, 1.99),
            "AWS (LTE 1700/2100)": (1.71, 2.155),
            "Wi-Fi 2.4 GHz": (2.4, 2.5),
            "Bluetooth": (2.4, 2.4835),
            "Wi-Fi 5 GHz": (5.0, 5.9),
        }
        self.regions_and_labels = []
        self.amplitude_markers = []
        
        # Initialize UI
        self.init_ui()
        
        # Initialize device connection
        self.init_device_connection()
        
        # Start monitoring
        self.start_device_monitoring()
        
        # Timer for spectrum updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(50)
    
    def init_ui(self):
        """Initialize the enhanced user interface"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # Create tab widget for organized interface
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Tab 1: Spectrum Analyzer (original functionality)
        self.spectrum_tab = QWidget()
        self.tab_widget.addTab(self.spectrum_tab, "Spectrum Analyzer")
        self.init_spectrum_tab()
        
        # Tab 2: Device Management
        self.device_tab = QWidget()
        self.tab_widget.addTab(self.device_tab, "Device Management")
        self.init_device_tab()
        
        # Tab 3: Signal Generator
        self.generator_tab = QWidget()
        self.tab_widget.addTab(self.generator_tab, "Signal Generator")
        self.init_generator_tab()
        
        # Tab 4: Calibration & Diagnostics
        self.calibration_tab = QWidget()
        self.tab_widget.addTab(self.calibration_tab, "Calibration & Diagnostics")
        self.init_calibration_tab()

        # Tab 5: Waterfall Display
        self.waterfall_tab = QWidget()
        self.tab_widget.addTab(self.waterfall_tab, "Waterfall Display")
        self.init_waterfall_tab()
        
        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        
        # Add connection status indicator
        self.connection_label = QLabel("🔴 Disconnected")
        self.connection_label.setStyleSheet("color: red; font-weight: bold;")
        self.status.addPermanentWidget(self.connection_label)
        
        # Add temperature display
        self.temp_label = QLabel("Temp: N/A")
        self.status.addPermanentWidget(self.temp_label)
    
    def init_spectrum_tab(self):
        """Initialize the spectrum analyzer tab (enhanced version of original)"""
        layout = QVBoxLayout(self.spectrum_tab)
        
        # Control panel (enhanced)
        control_group = QGroupBox("Spectrum Analyzer Controls")
        control_layout = QGridLayout(control_group)
        
        # Row 1: Basic controls
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.toggle_pause)
        control_layout.addWidget(self.pause_button, 0, 0)
        
        self.clear_markers_button = QPushButton("Clear Markers")
        self.clear_markers_button.clicked.connect(self.clear_all_markers)
        control_layout.addWidget(self.clear_markers_button, 0, 1)
        
        self.save_button = QPushButton("Save Data")
        self.save_button.clicked.connect(self.save_data)
        control_layout.addWidget(self.save_button, 0, 2)
        
        self.reset_peak_button = QPushButton("Reset Peak Hold")
        self.reset_peak_button.clicked.connect(self.reset_peak_hold)
        control_layout.addWidget(self.reset_peak_button, 0, 3)
        
        # Row 2: Threshold and frequency display
        control_layout.addWidget(QLabel("Alert Threshold (dB):"), 1, 0)
        self.threshold_edit = QLineEdit("-20")
        control_layout.addWidget(self.threshold_edit, 1, 1)
        
        self.freq_label = QLabel("Current Frequency: N/A")
        control_layout.addWidget(self.freq_label, 1, 2, 1, 2)
        
        layout.addWidget(control_group)
        
        # Parameter panel (enhanced)
        param_group = QGroupBox("Sweep Parameters")
        param_layout = QGridLayout(param_group)
        
        # Sample rate
        param_layout.addWidget(QLabel("Sample Rate (Hz):"), 0, 0)
        self.sr_edit = QLineEdit(str(int(self.sample_rate)))
        param_layout.addWidget(self.sr_edit, 0, 1)
        
        # Cutoff frequency
        param_layout.addWidget(QLabel("Cutoff (Hz):"), 0, 2)
        self.cutoff_edit = QLineEdit(str(int(self.cutoff_hz)))
        param_layout.addWidget(self.cutoff_edit, 0, 3)
        
        # Sweep parameters
        param_layout.addWidget(QLabel("Sweep Start (Hz):"), 1, 0)
        self.sweep_start_edit = QLineEdit(str(int(self.sweep_start)))
        param_layout.addWidget(self.sweep_start_edit, 1, 1)
        
        param_layout.addWidget(QLabel("Sweep Stop (Hz):"), 1, 2)
        self.sweep_stop_edit = QLineEdit(str(int(self.sweep_stop)))
        param_layout.addWidget(self.sweep_stop_edit, 1, 3)
        
        param_layout.addWidget(QLabel("# of Points:"), 2, 0)
        self.sweep_steps_edit = QLineEdit(str(int(self.sweep_steps)))
        param_layout.addWidget(self.sweep_steps_edit, 2, 1)
        
        # Apply button
        self.apply_button = QPushButton("Apply Settings")
        self.apply_button.clicked.connect(self.apply_sdr_settings)
        param_layout.addWidget(self.apply_button, 2, 2, 1, 2)
        
        layout.addWidget(param_group)
        
        # Plot widget (same as original but enhanced)
        self.amplitude_plot = pg.PlotWidget(title="Amplitude vs Frequency")
        self.amplitude_plot.setBackground('w')
        self.amplitude_plot.setLabel('left', "Amplitude", units='dB')
        self.amplitude_plot.setLabel('bottom', "Frequency", units='GHz')
        self.amplitude_plot.getAxis('left').setPen(pg.mkPen('k'))
        self.amplitude_plot.getAxis('bottom').setPen(pg.mkPen('k'))
        self.amplitude_plot.showGrid(x=True, y=True)
        layout.addWidget(self.amplitude_plot)
        
        # Plot curves
        self.amplitude_curve = self.amplitude_plot.plot(pen=pg.mkPen('b', width=2))
        self.peak_curve = self.amplitude_plot.plot(pen=pg.mkPen('r', width=2, style=Qt.PenStyle.DashLine))
        
        # Crosshair
        self.vLine_amp = pg.InfiniteLine(angle=90, movable=False)
        self.hLine_amp = pg.InfiniteLine(angle=0, movable=False)
        self.amplitude_plot.addItem(self.vLine_amp, ignoreBounds=True)
        self.amplitude_plot.addItem(self.hLine_amp, ignoreBounds=True)
        
        # Connect mouse events
        self.amplitude_plot.scene().sigMouseMoved.connect(self.mouse_moved_amp)
        self.amplitude_plot.plotItem.scene().sigMouseClicked.connect(self.mouse_clicked_amp)

    def init_device_tab(self):
        """Initialize the device management tab"""
        layout = QVBoxLayout(self.device_tab)

        # Device discovery and connection
        discovery_group = QGroupBox("Device Discovery & Connection")
        discovery_layout = QGridLayout(discovery_group)

        # Device selection
        discovery_layout.addWidget(QLabel("Device URI:"), 0, 0)
        self.device_uri_combo = QComboBox()
        self.device_uri_combo.setEditable(True)
        discovery_layout.addWidget(self.device_uri_combo, 0, 1, 1, 2)

        self.discover_button = QPushButton("Discover Devices")
        self.discover_button.clicked.connect(self.discover_devices)
        discovery_layout.addWidget(self.discover_button, 0, 3)

        # Connection controls
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_device)
        discovery_layout.addWidget(self.connect_button, 1, 0)

        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self.disconnect_device)
        discovery_layout.addWidget(self.disconnect_button, 1, 1)

        # Device info display
        self.device_info_text = QTextEdit()
        self.device_info_text.setMaximumHeight(100)
        self.device_info_text.setReadOnly(True)
        discovery_layout.addWidget(self.device_info_text, 2, 0, 1, 4)

        layout.addWidget(discovery_group)

        # Configuration management
        config_group = QGroupBox("Configuration Management")
        config_layout = QGridLayout(config_group)

        config_layout.addWidget(QLabel("Profile Name:"), 0, 0)
        self.profile_name_edit = QLineEdit()
        config_layout.addWidget(self.profile_name_edit, 0, 1)

        self.save_config_button = QPushButton("Save Config")
        self.save_config_button.clicked.connect(self.save_configuration)
        config_layout.addWidget(self.save_config_button, 0, 2)

        config_layout.addWidget(QLabel("Load Profile:"), 1, 0)
        self.profile_combo = QComboBox()
        config_layout.addWidget(self.profile_combo, 1, 1)

        self.load_config_button = QPushButton("Load Config")
        self.load_config_button.clicked.connect(self.load_configuration)
        config_layout.addWidget(self.load_config_button, 1, 2)

        layout.addWidget(config_group)

        # Temperature monitoring
        temp_group = QGroupBox("Temperature Monitoring")
        temp_layout = QVBoxLayout(temp_group)

        self.temp_display = QTextEdit()
        self.temp_display.setMaximumHeight(80)
        self.temp_display.setReadOnly(True)
        temp_layout.addWidget(self.temp_display)

        temp_controls = QHBoxLayout()
        self.temp_monitor_button = QPushButton("Start Monitoring")
        self.temp_monitor_button.clicked.connect(self.toggle_temp_monitoring)
        temp_controls.addWidget(self.temp_monitor_button)

        temp_controls.addWidget(QLabel("Duration (s):"))
        self.temp_duration_spin = QSpinBox()
        self.temp_duration_spin.setRange(10, 3600)
        self.temp_duration_spin.setValue(60)
        temp_controls.addWidget(self.temp_duration_spin)

        temp_layout.addLayout(temp_controls)
        layout.addWidget(temp_group)

        layout.addStretch()

    def init_generator_tab(self):
        """Initialize the signal generator tab"""
        layout = QVBoxLayout(self.generator_tab)

        # Waveform generation
        waveform_group = QGroupBox("Waveform Generation")
        waveform_layout = QGridLayout(waveform_group)

        # Waveform type
        waveform_layout.addWidget(QLabel("Waveform Type:"), 0, 0)
        self.waveform_combo = QComboBox()
        self.waveform_combo.addItems(["Sine Wave", "Triangle Wave", "Chirp", "DDS Tone"])
        waveform_layout.addWidget(self.waveform_combo, 0, 1)

        # Frequency
        waveform_layout.addWidget(QLabel("Frequency (Hz):"), 1, 0)
        self.gen_freq_edit = QLineEdit("100000")
        waveform_layout.addWidget(self.gen_freq_edit, 1, 1)

        # Amplitude
        waveform_layout.addWidget(QLabel("Amplitude (0-1):"), 1, 2)
        self.gen_amp_spin = QDoubleSpinBox()
        self.gen_amp_spin.setRange(0.0, 1.0)
        self.gen_amp_spin.setValue(0.5)
        self.gen_amp_spin.setSingleStep(0.1)
        waveform_layout.addWidget(self.gen_amp_spin, 1, 3)

        # Duration
        waveform_layout.addWidget(QLabel("Duration (s):"), 2, 0)
        self.gen_duration_spin = QDoubleSpinBox()
        self.gen_duration_spin.setRange(0.1, 10.0)
        self.gen_duration_spin.setValue(1.0)
        self.gen_duration_spin.setSingleStep(0.1)
        waveform_layout.addWidget(self.gen_duration_spin, 2, 1)

        # Cyclic transmission
        self.cyclic_checkbox = QCheckBox("Cyclic Transmission")
        self.cyclic_checkbox.setChecked(True)
        waveform_layout.addWidget(self.cyclic_checkbox, 2, 2)

        # Generation controls
        gen_controls = QHBoxLayout()
        self.generate_button = QPushButton("Generate & Transmit")
        self.generate_button.clicked.connect(self.generate_signal)
        gen_controls.addWidget(self.generate_button)

        self.stop_gen_button = QPushButton("Stop Transmission")
        self.stop_gen_button.clicked.connect(self.stop_signal_generation)
        gen_controls.addWidget(self.stop_gen_button)

        waveform_layout.addLayout(gen_controls, 3, 0, 1, 4)
        layout.addWidget(waveform_group)

        # Loopback testing
        loopback_group = QGroupBox("Loopback Testing")
        loopback_layout = QVBoxLayout(loopback_group)

        loopback_controls = QHBoxLayout()
        self.loopback_checkbox = QCheckBox("Enable Digital Loopback")
        loopback_controls.addWidget(self.loopback_checkbox)

        self.test_loopback_button = QPushButton("Test Loopback")
        self.test_loopback_button.clicked.connect(self.test_loopback)
        loopback_controls.addWidget(self.test_loopback_button)

        loopback_layout.addLayout(loopback_controls)

        self.loopback_result_text = QTextEdit()
        self.loopback_result_text.setMaximumHeight(100)
        self.loopback_result_text.setReadOnly(True)
        loopback_layout.addWidget(self.loopback_result_text)

        layout.addWidget(loopback_group)
        layout.addStretch()

    def init_calibration_tab(self):
        """Initialize the calibration and diagnostics tab"""
        layout = QVBoxLayout(self.calibration_tab)

        # Calibration controls
        cal_group = QGroupBox("Calibration")
        cal_layout = QGridLayout(cal_group)

        # Calibration parameters
        cal_layout.addWidget(QLabel("RX LO (Hz):"), 0, 0)
        self.cal_rx_lo_edit = QLineEdit("2400000000")
        cal_layout.addWidget(self.cal_rx_lo_edit, 0, 1)

        cal_layout.addWidget(QLabel("TX LO (Hz):"), 0, 2)
        self.cal_tx_lo_edit = QLineEdit("2400000000")
        cal_layout.addWidget(self.cal_tx_lo_edit, 0, 3)

        cal_layout.addWidget(QLabel("Sample Rate (Hz):"), 1, 0)
        self.cal_sr_edit = QLineEdit("3000000")
        cal_layout.addWidget(self.cal_sr_edit, 1, 1)

        # Calibration controls
        self.calibrate_button = QPushButton("Run Calibration")
        self.calibrate_button.clicked.connect(self.run_calibration)
        cal_layout.addWidget(self.calibrate_button, 1, 2)

        self.cal_progress = QProgressBar()
        cal_layout.addWidget(self.cal_progress, 1, 3)

        # Calibration results
        self.cal_results_text = QTextEdit()
        self.cal_results_text.setMaximumHeight(150)
        self.cal_results_text.setReadOnly(True)
        cal_layout.addWidget(self.cal_results_text, 2, 0, 1, 4)

        layout.addWidget(cal_group)

        # Diagnostics
        diag_group = QGroupBox("Diagnostics")
        diag_layout = QVBoxLayout(diag_group)

        diag_controls = QHBoxLayout()
        self.run_diagnostics_button = QPushButton("Run Diagnostics")
        self.run_diagnostics_button.clicked.connect(self.run_diagnostics)
        diag_controls.addWidget(self.run_diagnostics_button)

        self.diag_progress = QProgressBar()
        diag_controls.addWidget(self.diag_progress)

        diag_layout.addLayout(diag_controls)

        self.diag_results_text = QTextEdit()
        self.diag_results_text.setReadOnly(True)
        diag_layout.addWidget(self.diag_results_text)

        layout.addWidget(diag_group)
        layout.addStretch()

    def init_waterfall_tab(self):
        """Initialize the waterfall display tab"""
        layout = QVBoxLayout(self.waterfall_tab)

        # Create waterfall configuration
        waterfall_config = WaterfallConfig(
            fft_size=1024,
            history_size=800,
            update_rate_ms=50,
            center_frequency=100e6,
            sample_rate=20e6,
            gain=60.0,
            colormap=ColorMap.VIRIDIS,
            intensity_min=-80.0,
            intensity_max=-20.0
        )

        # Create waterfall display widget
        self.waterfall_display = WaterfallDisplay(self.pluto_manager, waterfall_config)
        layout.addWidget(self.waterfall_display)

        # Connect waterfall signals to main window
        self.waterfall_display.frequency_changed.connect(self.on_waterfall_frequency_changed)
        self.waterfall_display.sample_rate_changed.connect(self.on_waterfall_sample_rate_changed)
        self.waterfall_display.peak_detected.connect(self.on_waterfall_peak_detected)

    def init_device_connection(self):
        """Initialize device connection using enhanced manager"""
        try:
            self.pluto_manager = PlutoSDRManager(auto_discover=True)

            if self.pluto_manager.is_connected:
                self.signal_generator = SignalGenerator(self.pluto_manager)
                self.calibration_manager = CalibrationManager(self.pluto_manager)
                self.config_manager = ConfigurationManager(self.pluto_manager)

                self.update_device_info_display()
                self.update_connection_status(True)
                self.update_waterfall_connection()
                self.status.showMessage("Connected to PlutoSDR", 3000)
            else:
                self.update_connection_status(False)
                self.status.showMessage("No PlutoSDR device found", 3000)

        except Exception as e:
            self.status.showMessage(f"Connection error: {e}", 5000)
            self.update_connection_status(False)

    def start_device_monitoring(self):
        """Start background device monitoring"""
        if self.pluto_manager and self.pluto_manager.is_connected:
            self.device_monitor = DeviceMonitorThread(self.pluto_manager)
            self.device_monitor.temperature_update.connect(self.update_temperature_display)
            self.device_monitor.connection_status.connect(self.update_connection_status)
            self.device_monitor.start()

    def update_connection_status(self, connected: bool):
        """Update connection status display"""
        if connected:
            self.connection_label.setText("🟢 Connected")
            self.connection_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.connection_label.setText("🔴 Disconnected")
            self.connection_label.setStyleSheet("color: red; font-weight: bold;")

    def update_temperature_display(self, temps: dict):
        """Update temperature display"""
        ad9361_temp = temps.get('ad9361', 'N/A')
        zynq_temp = temps.get('zynq', 'N/A')

        if isinstance(ad9361_temp, (int, float)):
            ad9361_str = f"{ad9361_temp:.1f}°C"
        else:
            ad9361_str = str(ad9361_temp)

        if isinstance(zynq_temp, (int, float)):
            zynq_str = f"{zynq_temp:.1f}°C"
        else:
            zynq_str = str(zynq_temp)

        self.temp_label.setText(f"AD9361: {ad9361_str}, Zynq: {zynq_str}")

        # Update device tab temperature display
        temp_text = f"AD9361 Temperature: {ad9361_str}\nZynq Temperature: {zynq_str}"
        self.temp_display.setText(temp_text)

    def discover_devices(self):
        """Discover available PlutoSDR devices"""
        if not self.pluto_manager:
            self.pluto_manager = PlutoSDRManager(auto_discover=False)

        devices = self.pluto_manager.discover_devices()

        self.device_uri_combo.clear()
        for device in devices:
            self.device_uri_combo.addItem(device.uri)

        if devices:
            self.status.showMessage(f"Found {len(devices)} device(s)", 3000)
        else:
            self.status.showMessage("No devices found", 3000)

    def connect_device(self):
        """Connect to selected device"""
        uri = self.device_uri_combo.currentText()
        if not uri:
            self.status.showMessage("No device URI specified", 3000)
            return

        try:
            if self.pluto_manager:
                self.pluto_manager.disconnect()

            self.pluto_manager = PlutoSDRManager(uri=uri, auto_discover=False)

            if self.pluto_manager.is_connected:
                self.signal_generator = SignalGenerator(self.pluto_manager)
                self.calibration_manager = CalibrationManager(self.pluto_manager)
                self.config_manager = ConfigurationManager(self.pluto_manager)

                self.update_device_info_display()
                self.update_connection_status(True)
                self.update_waterfall_connection()
                self.status.showMessage(f"Connected to {uri}", 3000)

                # Restart monitoring
                if self.device_monitor:
                    self.device_monitor.stop()
                self.start_device_monitoring()
            else:
                self.update_connection_status(False)
                self.status.showMessage(f"Failed to connect to {uri}", 3000)

        except Exception as e:
            self.status.showMessage(f"Connection error: {e}", 5000)
            self.update_connection_status(False)

    def disconnect_device(self):
        """Disconnect from current device"""
        if self.device_monitor:
            self.device_monitor.stop()
            self.device_monitor = None

        if self.pluto_manager:
            self.pluto_manager.disconnect()
            self.pluto_manager = None

        self.signal_generator = None
        self.calibration_manager = None
        self.config_manager = None

        self.update_connection_status(False)
        self.update_waterfall_connection()
        self.device_info_text.clear()
        self.status.showMessage("Disconnected", 3000)

    def update_waterfall_connection(self):
        """Update waterfall display with current PlutoSDR connection"""
        if hasattr(self, 'waterfall_display'):
            self.waterfall_display.pluto_manager = self.pluto_manager

    def update_device_info_display(self):
        """Update device information display"""
        if not self.pluto_manager or not self.pluto_manager.device_info:
            return

        info = self.pluto_manager.device_info
        info_text = f"URI: {info.uri}\n"
        info_text += f"Connection Type: {info.connection_type.value}\n"

        if info.ip_address:
            info_text += f"IP Address: {info.ip_address}\n"
        if info.serial_number:
            info_text += f"Serial Number: {info.serial_number}\n"
        if info.firmware_version:
            info_text += f"Firmware Version: {info.firmware_version}\n"

        self.device_info_text.setText(info_text)

    def save_configuration(self):
        """Save current configuration as profile"""
        if not self.config_manager:
            self.status.showMessage("No device connected", 3000)
            return

        profile_name = self.profile_name_edit.text().strip()
        if not profile_name:
            self.status.showMessage("Please enter a profile name", 3000)
            return

        if self.config_manager.save_current_config(profile_name):
            self.status.showMessage(f"Configuration saved as '{profile_name}'", 3000)
            self.update_profile_list()
        else:
            self.status.showMessage("Failed to save configuration", 3000)

    def load_configuration(self):
        """Load selected configuration profile"""
        if not self.config_manager:
            self.status.showMessage("No device connected", 3000)
            return

        profile_name = self.profile_combo.currentText()
        if not profile_name:
            self.status.showMessage("No profile selected", 3000)
            return

        if self.config_manager.load_config_profile(profile_name):
            self.status.showMessage(f"Configuration '{profile_name}' loaded", 3000)
        else:
            self.status.showMessage("Failed to load configuration", 3000)

    def update_profile_list(self):
        """Update the profile selection combo box"""
        if not self.config_manager:
            return

        current_text = self.profile_combo.currentText()
        self.profile_combo.clear()

        profiles = self.config_manager.get_profile_list()
        self.profile_combo.addItems(profiles)

        # Restore selection if it still exists
        index = self.profile_combo.findText(current_text)
        if index >= 0:
            self.profile_combo.setCurrentIndex(index)

    def generate_signal(self):
        """Generate and transmit selected waveform"""
        if not self.signal_generator:
            self.status.showMessage("No device connected", 3000)
            return

        try:
            waveform_type = self.waveform_combo.currentText()
            frequency = float(self.gen_freq_edit.text())
            amplitude = self.gen_amp_spin.value()
            duration = self.gen_duration_spin.value()
            cyclic = self.cyclic_checkbox.isChecked()

            # Generate waveform based on type
            if waveform_type == "Sine Wave":
                samples = self.signal_generator.generate_sine_wave(
                    frequency, amplitude, int(self.sample_rate), duration
                )
            elif waveform_type == "Triangle Wave":
                samples = self.signal_generator.generate_triangle_wave(
                    int(self.sample_rate), int(self.sample_rate * duration)
                )
            elif waveform_type == "Chirp":
                # For chirp, use frequency as start and 2*frequency as end
                samples = self.signal_generator.generate_chirp(
                    frequency, frequency * 2, duration, int(self.sample_rate), amplitude
                )
            elif waveform_type == "DDS Tone":
                # Configure DDS instead of generating samples
                if self.signal_generator.configure_dds_tone(frequency, amplitude):
                    self.status.showMessage(f"DDS tone configured: {format_frequency(frequency)}", 3000)
                else:
                    self.status.showMessage("Failed to configure DDS tone", 3000)
                return
            else:
                self.status.showMessage("Unknown waveform type", 3000)
                return

            # Transmit the generated samples
            if self.signal_generator.transmit_signal(samples, cyclic):
                self.status.showMessage(f"Transmitting {waveform_type}: {format_frequency(frequency)}", 3000)
            else:
                self.status.showMessage("Failed to start transmission", 3000)

        except ValueError as e:
            self.status.showMessage(f"Invalid parameter: {e}", 3000)
        except Exception as e:
            self.status.showMessage(f"Signal generation error: {e}", 3000)

    def stop_signal_generation(self):
        """Stop signal transmission"""
        if self.signal_generator:
            self.signal_generator.stop_transmission()
            self.status.showMessage("Transmission stopped", 3000)

    def test_loopback(self):
        """Test loopback functionality"""
        if not self.pluto_manager:
            self.status.showMessage("No device connected", 3000)
            return

        try:
            # Enable/disable loopback based on checkbox
            loopback_enabled = self.loopback_checkbox.isChecked()
            if self.pluto_manager.set_loopback_mode(loopback_enabled):
                if loopback_enabled:
                    # Run a simple loopback test
                    if self.calibration_manager:
                        result = self.calibration_manager._test_loopback()
                        if result:
                            self.loopback_result_text.setText("✅ Loopback test PASSED\nDigital loopback is working correctly.")
                        else:
                            self.loopback_result_text.setText("❌ Loopback test FAILED\nCheck connections and settings.")
                    else:
                        self.loopback_result_text.setText("Loopback enabled (test requires calibration manager)")
                else:
                    self.loopback_result_text.setText("Loopback disabled")
            else:
                self.loopback_result_text.setText("Failed to set loopback mode")

        except Exception as e:
            self.loopback_result_text.setText(f"Loopback test error: {e}")

    def run_calibration(self):
        """Run device calibration"""
        if not self.calibration_manager:
            self.status.showMessage("No device connected", 3000)
            return

        try:
            rx_lo = float(self.cal_rx_lo_edit.text())
            tx_lo = float(self.cal_tx_lo_edit.text())
            sample_rate = int(self.cal_sr_edit.text())

            self.cal_progress.setValue(0)
            self.calibrate_button.setEnabled(False)

            # Run calibration
            result = self.calibration_manager.perform_basic_calibration(rx_lo, tx_lo, sample_rate)

            # Display results
            if result.success:
                results_text = "✅ Calibration SUCCESSFUL\n\n"
                results_text += f"RX LO: {format_frequency(result.rx_lo_freq)}\n"
                results_text += f"TX LO: {format_frequency(result.tx_lo_freq)}\n"
                results_text += f"Sample Rate: {format_frequency(result.sample_rate)}\n"
                results_text += f"RX Gain: {result.rx_gain} dB\n"
                results_text += f"TX Gain: {result.tx_gain} dB\n"
                results_text += f"DC Offset I: {result.dc_offset_i:.6f}\n"
                results_text += f"DC Offset Q: {result.dc_offset_q:.6f}\n"
                results_text += f"IQ Imbalance: {result.iq_imbalance:.3f} dB\n"
                results_text += f"Phase Correction: {result.phase_correction:.3f}°\n"

                self.status.showMessage("Calibration completed successfully", 3000)
            else:
                results_text = "❌ Calibration FAILED\n\nCheck device connection and settings."
                self.status.showMessage("Calibration failed", 3000)

            self.cal_results_text.setText(results_text)
            self.cal_progress.setValue(100)

        except ValueError as e:
            self.cal_results_text.setText(f"Invalid calibration parameter: {e}")
        except Exception as e:
            self.cal_results_text.setText(f"Calibration error: {e}")
        finally:
            self.calibrate_button.setEnabled(True)

    def run_diagnostics(self):
        """Run comprehensive diagnostics"""
        if not self.calibration_manager:
            self.status.showMessage("No device connected", 3000)
            return

        try:
            self.diag_progress.setValue(0)
            self.run_diagnostics_button.setEnabled(False)

            # Run diagnostic tests
            results = self.calibration_manager.run_diagnostic_tests()

            # Format results for display
            diag_text = "🔍 DIAGNOSTIC RESULTS\n"
            diag_text += "=" * 40 + "\n\n"

            # Connection status
            if results['device_connected']:
                diag_text += "✅ Device Connection: OK\n"
            else:
                diag_text += "❌ Device Connection: FAILED\n"

            # Temperature status
            temps = results.get('temperatures')
            if temps:
                ad9361_temp = temps.get('ad9361', 'N/A')
                zynq_temp = temps.get('zynq', 'N/A')
                diag_text += f"🌡️  AD9361 Temperature: {ad9361_temp:.1f}°C\n"
                diag_text += f"🌡️  Zynq Temperature: {zynq_temp:.1f}°C\n"

                # Temperature warnings
                if isinstance(ad9361_temp, (int, float)) and ad9361_temp > 80:
                    diag_text += "⚠️  WARNING: AD9361 temperature high!\n"
                if isinstance(zynq_temp, (int, float)) and zynq_temp > 85:
                    diag_text += "⚠️  WARNING: Zynq temperature high!\n"
            else:
                diag_text += "❌ Temperature Reading: FAILED\n"

            # Loopback test
            if results['loopback_test']:
                diag_text += "✅ Loopback Test: PASSED\n"
            else:
                diag_text += "❌ Loopback Test: FAILED\n"

            # Noise floor
            noise_floor = results.get('noise_floor')
            if noise_floor is not None:
                diag_text += f"📊 Noise Floor: {noise_floor:.1f} dB\n"
            else:
                diag_text += "❌ Noise Floor Measurement: FAILED\n"

            # Additional tests (placeholders for future implementation)
            freq_acc = results.get('frequency_accuracy')
            if freq_acc is not None:
                diag_text += f"📡 Frequency Accuracy: {freq_acc:.3f} ppm\n"
            else:
                diag_text += "⚠️  Frequency Accuracy: Not tested\n"

            gain_lin = results.get('gain_linearity')
            if gain_lin is not None:
                diag_text += f"📈 Gain Linearity: OK\n"
            else:
                diag_text += "⚠️  Gain Linearity: Not tested\n"

            self.diag_results_text.setText(diag_text)
            self.diag_progress.setValue(100)
            self.status.showMessage("Diagnostics completed", 3000)

        except Exception as e:
            self.diag_results_text.setText(f"Diagnostics error: {e}")
        finally:
            self.run_diagnostics_button.setEnabled(True)

    # Waterfall display event handlers
    def on_waterfall_frequency_changed(self, frequency: float):
        """Handle frequency change from waterfall display"""
        self.status.showMessage(f"Waterfall center frequency: {format_frequency(frequency)}", 3000)

        # Optionally sync with spectrum analyzer
        if hasattr(self, 'sweep_start_edit') and hasattr(self, 'sweep_stop_edit'):
            # Update spectrum analyzer frequency range around waterfall center
            bandwidth = float(self.sr_edit.text()) if hasattr(self, 'sr_edit') else 20e6
            new_start = frequency - bandwidth
            new_stop = frequency + bandwidth

            self.sweep_start_edit.setText(str(int(new_start)))
            self.sweep_stop_edit.setText(str(int(new_stop)))

    def on_waterfall_sample_rate_changed(self, sample_rate: float):
        """Handle sample rate change from waterfall display"""
        self.status.showMessage(f"Waterfall sample rate: {format_frequency(sample_rate)}", 3000)

        # Optionally sync with spectrum analyzer
        if hasattr(self, 'sr_edit'):
            self.sr_edit.setText(str(int(sample_rate)))

    def on_waterfall_peak_detected(self, frequency: float, amplitude: float):
        """Handle peak detection from waterfall display"""
        self.status.showMessage(
            f"Waterfall peak: {format_frequency(frequency)}, {amplitude:.1f} dB",
            2000
        )

    # Original spectrum analyzer methods (adapted for enhanced version)
    def toggle_pause(self):
        """Toggle pause/resume for spectrum sweep"""
        self.is_paused = not self.is_paused
        self.pause_button.setText("Resume" if self.is_paused else "Pause")

    def clear_all_markers(self):
        """Clear all amplitude markers"""
        for scatter, label in self.amplitude_markers:
            self.amplitude_plot.removeItem(scatter)
            if label is not None:
                self.amplitude_plot.removeItem(label)
        self.amplitude_markers.clear()
        self.status.showMessage("All markers cleared", 2000)

    def save_data(self):
        """Save spectrum data to CSV file"""
        if not self.freq_list or not self.amp_list:
            self.status.showMessage("No data to save", 3000)
            return

        filename, _ = QFileDialog.getSaveFileName(self, "Save Data", "", "CSV Files (*.csv)")
        if filename:
            data = np.column_stack((self.freq_list, self.amp_list))
            header = "Frequency_GHz,Amplitude_dB"
            np.savetxt(filename, data, delimiter=",", header=header, comments='')
            self.status.showMessage(f"Data saved to {filename}", 3000)

    def reset_peak_hold(self):
        """Reset peak hold data"""
        self.peak_hold_data.clear()
        self.peak_curve.setData([], [])
        self.status.showMessage("Peak hold data reset", 2000)

    def apply_sdr_settings(self):
        """Apply SDR settings from UI controls"""
        if not self.pluto_manager or not self.pluto_manager.is_connected:
            self.status.showMessage("No device connected", 3000)
            return

        try:
            # Parse parameters
            sr_val = float(self.sr_edit.text())
            cutoff_val = float(self.cutoff_edit.text())
            sweep_start_val = float(self.sweep_start_edit.text())
            sweep_stop_val = float(self.sweep_stop_edit.text())
            sweep_steps_val = int(self.sweep_steps_edit.text())

            # Update internal parameters
            self.sample_rate = sr_val
            self.rf_bw = sr_val
            self.cutoff_hz = cutoff_val
            self.sweep_start = sweep_start_val
            self.sweep_stop = sweep_stop_val
            self.sweep_steps = sweep_steps_val

            # Configure device
            success = self.pluto_manager.configure_basic_settings(
                sample_rate=int(sr_val),
                rx_bandwidth=int(sr_val),
                tx_bandwidth=int(sr_val)
            )

            if success:
                # Update sweep frequencies
                self.frequencies = np.linspace(self.sweep_start, self.sweep_stop, self.sweep_steps)

                # Reset data
                self.freq_list.clear()
                self.amp_list.clear()
                self.peak_hold_data.clear()
                self.amplitude_curve.setData([], [])
                self.peak_curve.setData([], [])
                self.sweep_index = 0
                self.sweep_complete = False

                # Clear markers
                self.clear_all_markers()

                # Update plot range
                sweep_min_ghz = self.sweep_start / 1e9
                sweep_max_ghz = self.sweep_stop / 1e9
                self.amplitude_plot.setXRange(sweep_min_ghz, sweep_max_ghz)

                self.status.showMessage("Settings applied successfully", 3000)
            else:
                self.status.showMessage("Failed to apply settings", 3000)

        except ValueError as e:
            self.status.showMessage(f"Invalid parameter: {e}", 3000)
        except Exception as e:
            self.status.showMessage(f"Error applying settings: {e}", 3000)

    def mouse_moved_amp(self, pos):
        """Handle mouse movement over amplitude plot"""
        if self.amplitude_plot.sceneBoundingRect().contains(pos):
            mouse_point = self.amplitude_plot.plotItem.vb.mapSceneToView(pos)
            self.vLine_amp.setPos(mouse_point.x())
            self.hLine_amp.setPos(mouse_point.y())
            self.status.showMessage(
                f"Frequency: {mouse_point.x():.2f} GHz, Amplitude: {mouse_point.y():.1f} dB"
            )

    def mouse_clicked_amp(self, event):
        """Handle mouse clicks on amplitude plot to add markers"""
        if event.button() == Qt.MouseButton.LeftButton and self.freq_list:
            pos = event.scenePos()
            view = self.amplitude_plot.plotItem.vb
            mouse_point = view.mapSceneToView(pos)

            # Find nearest data point
            nearest_x, nearest_y = self.find_nearest_point(
                mouse_point.x(), mouse_point.y(),
                self.freq_list, self.amp_list
            )

            if nearest_x is not None:
                # Add marker
                scatter = pg.ScatterPlotItem(
                    pos=[(nearest_x, nearest_y)],
                    symbol='o',
                    brush=pg.mkBrush(255, 165, 0, 255),
                    size=10,
                    pen=pg.mkPen(None)
                )

                label = DraggableTextItem(
                    text=f'({nearest_x:.6f} GHz,\n {nearest_y:.1f} dB)',
                    color=(0, 0, 0),
                    anchor=(0, -1),
                    border=pg.mkPen(color=(200, 200, 200)),
                    fill=pg.mkBrush('white')
                )
                label.setPos(nearest_x, nearest_y)

                self.amplitude_plot.addItem(scatter)
                self.amplitude_plot.addItem(label)
                self.amplitude_markers.append((scatter, label))

    def find_nearest_point(self, x, y, data_x, data_y):
        """Find nearest data point to mouse click"""
        if not data_x or not data_y:
            return None, None
        distances = np.sqrt((np.array(data_x) - x)**2 + (np.array(data_y) - y)**2)
        nearest_idx = np.argmin(distances)
        return data_x[nearest_idx], data_y[nearest_idx]

    def update_plot(self):
        """Main update loop for spectrum analysis (simplified version)"""
        if self.is_paused or not self.pluto_manager or not self.pluto_manager.is_connected:
            return

        # This is a simplified version - in a full implementation,
        # you would integrate the original spectrum analyzer sweep logic here
        # For now, we'll just update the frequency label
        if hasattr(self, 'frequencies') and len(self.frequencies) > 0:
            if self.sweep_index < len(self.frequencies):
                freq = self.frequencies[self.sweep_index]
                self.freq_label.setText(f"Current Frequency: {freq/1e9:.2f} GHz")

    def closeEvent(self, event):
        """Handle application close event"""
        # Stop monitoring thread
        if self.device_monitor:
            self.device_monitor.stop()

        # Stop any signal generation
        if self.signal_generator:
            self.signal_generator.stop_transmission()

        # Disconnect device
        if self.pluto_manager:
            self.pluto_manager.disconnect()

        event.accept()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("Enhanced ADALM-Pluto Spectrum Analyzer")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Enhanced SDR Tools")

    # Create and show main window
    main_window = EnhancedMainWindow()
    main_window.show()

    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        main_window.close()


if __name__ == '__main__':
    main()
