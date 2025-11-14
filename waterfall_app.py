#!/usr/bin/env python3
"""
Standalone Waterfall Spectrum Analyzer Application

A standalone application featuring the waterfall display for ADALM-Pluto SDR,
inspired by the Stvff/waterfall repository but implemented in Python.

Features:
- Real-time waterfall spectrum display
- Interactive frequency and bandwidth control
- Keyboard shortcuts for quick adjustments
- Peak detection and marking
- Configurable display parameters
- Integration with PlutoSDR utilities

Usage:
    python waterfall_app.py [--center-freq FREQ] [--sample-rate SR] [--fft-size SIZE]

Author: Enhanced integration inspired by Stvff/waterfall
License: GPL-2 (compatible with original projects)
"""

import sys
import argparse
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QStatusBar
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut

from waterfall_display import WaterfallDisplay, WaterfallConfig, ColorMap
from pluto_utils import PlutoSDRManager


class WaterfallMainWindow(QMainWindow):
    """Main window for standalone waterfall application"""
    
    def __init__(self, config: WaterfallConfig):
        super().__init__()
        
        self.setWindowTitle("ADALM-Pluto Waterfall Spectrum Analyzer")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize PlutoSDR manager
        self.pluto_manager = PlutoSDRManager(auto_discover=True)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create waterfall display
        self.waterfall_display = WaterfallDisplay(self.pluto_manager, config)
        layout.addWidget(self.waterfall_display)
        
        # Connect signals
        self.waterfall_display.frequency_changed.connect(self.on_frequency_changed)
        self.waterfall_display.sample_rate_changed.connect(self.on_sample_rate_changed)
        self.waterfall_display.peak_detected.connect(self.on_peak_detected)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Update status
        self.update_connection_status()
        
        # Set up keyboard shortcuts
        self.setup_shortcuts()
        
        # Set focus to waterfall display for keyboard control
        self.waterfall_display.setFocus()
    
    def setup_shortcuts(self):
        """Set up keyboard shortcuts"""
        # Global shortcuts
        quit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        quit_shortcut.activated.connect(self.close)
        
        help_shortcut = QShortcut(QKeySequence("F1"), self)
        help_shortcut.activated.connect(self.show_help)
        
        fullscreen_shortcut = QShortcut(QKeySequence("F11"), self)
        fullscreen_shortcut.activated.connect(self.toggle_fullscreen)
    
    def update_connection_status(self):
        """Update connection status in status bar"""
        if self.pluto_manager and self.pluto_manager.is_connected:
            device_info = self.pluto_manager.device_info
            status_text = f"Connected: {device_info.uri if device_info else 'PlutoSDR'}"
            
            # Add temperature info if available
            temps = self.pluto_manager.get_temperatures()
            if temps:
                temp_info = []
                if 'ad9361' in temps:
                    temp_info.append(f"AD9361: {temps['ad9361']:.1f}°C")
                if 'zynq' in temps:
                    temp_info.append(f"Zynq: {temps['zynq']:.1f}°C")
                if temp_info:
                    status_text += f" | {', '.join(temp_info)}"
        else:
            status_text = "No PlutoSDR connected"
        
        self.status_bar.showMessage(status_text)
    
    def on_frequency_changed(self, frequency: float):
        """Handle frequency change from waterfall display"""
        self.status_bar.showMessage(f"Center frequency: {frequency/1e6:.3f} MHz", 2000)
    
    def on_sample_rate_changed(self, sample_rate: float):
        """Handle sample rate change from waterfall display"""
        self.status_bar.showMessage(f"Sample rate: {sample_rate/1e6:.1f} MHz", 2000)
    
    def on_peak_detected(self, frequency: float, amplitude: float):
        """Handle peak detection from waterfall display"""
        self.status_bar.showMessage(f"Peak: {frequency/1e6:.3f} MHz, {amplitude:.1f} dB", 1000)
    
    def show_help(self):
        """Show help information"""
        help_text = """
Waterfall Spectrum Analyzer - Keyboard Shortcuts:

Frequency Control:
  ↑/↓ Arrow Keys    - Change center frequency (±100 MHz)
  Shift+↑/↓         - Fine frequency adjustment (±10 MHz)
  
Bandwidth Control:
  ←/→ Arrow Keys    - Change sample rate (±10 MHz)
  Shift+←/→         - Fine sample rate adjustment (±1 MHz)
  
Display Control:
  Space             - Pause/Resume acquisition
  C                 - Clear display and peak hold
  M                 - Mark highest peak
  
Application:
  F1                - Show this help
  F11               - Toggle fullscreen
  Ctrl+Q            - Quit application
  
Mouse:
  Click on spectrum - Show frequency at cursor
  
The waterfall display shows spectrum intensity over time, with:
- Frequency on horizontal axis
- Time on vertical axis (newest at top)
- Color intensity representing signal strength
        """
        
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Help - Waterfall Spectrum Analyzer", help_text)
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def closeEvent(self, event):
        """Handle application close"""
        # Stop waterfall acquisition
        if hasattr(self, 'waterfall_display'):
            self.waterfall_display.stop_acquisition()
        
        # Disconnect PlutoSDR
        if self.pluto_manager:
            self.pluto_manager.disconnect()
        
        event.accept()


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Waterfall Spectrum Analyzer for ADALM-Pluto SDR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python waterfall_app.py
  python waterfall_app.py --center-freq 2.4e9 --sample-rate 20e6
  python waterfall_app.py --fft-size 2048 --history-size 1000
  
Keyboard Controls:
  Arrow keys: Adjust frequency (↑/↓) and sample rate (←/→)
  Shift + arrows: Fine adjustments
  Space: Pause/Resume
  C: Clear display
  M: Mark peak
  F1: Help
  F11: Fullscreen
  Ctrl+Q: Quit
        """
    )
    
    parser.add_argument(
        "--center-freq", type=float, default=100e6,
        help="Initial center frequency in Hz (default: 100 MHz)"
    )
    parser.add_argument(
        "--sample-rate", type=float, default=20e6,
        help="Initial sample rate in Hz (default: 20 MHz)"
    )
    parser.add_argument(
        "--fft-size", type=int, default=1024, choices=[256, 512, 1024, 2048, 4096],
        help="FFT size (default: 1024)"
    )
    parser.add_argument(
        "--history-size", type=int, default=800,
        help="Waterfall history size in lines (default: 800)"
    )
    parser.add_argument(
        "--colormap", type=str, default="viridis",
        choices=[cm.value for cm in ColorMap],
        help="Colormap for waterfall display (default: viridis)"
    )
    parser.add_argument(
        "--gain", type=float, default=60.0,
        help="RX gain in dB (default: 60)"
    )
    parser.add_argument(
        "--update-rate", type=int, default=50,
        help="Display update rate in ms (default: 50)"
    )
    parser.add_argument(
        "--intensity-min", type=float, default=-80.0,
        help="Minimum intensity for display in dB (default: -80)"
    )
    parser.add_argument(
        "--intensity-max", type=float, default=-20.0,
        help="Maximum intensity for display in dB (default: -20)"
    )
    
    return parser.parse_args()


def main():
    """Main entry point"""
    # Parse command line arguments
    args = parse_arguments()
    
    # Create configuration
    config = WaterfallConfig(
        fft_size=args.fft_size,
        history_size=args.history_size,
        update_rate_ms=args.update_rate,
        center_frequency=args.center_freq,
        sample_rate=args.sample_rate,
        gain=args.gain,
        colormap=ColorMap(args.colormap),
        intensity_min=args.intensity_min,
        intensity_max=args.intensity_max
    )
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Waterfall Spectrum Analyzer")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Enhanced SDR Tools")
    
    # Create and show main window
    main_window = WaterfallMainWindow(config)
    main_window.show()
    
    # Print startup information
    print("🌊 Waterfall Spectrum Analyzer for ADALM-Pluto SDR")
    print("=" * 50)
    print(f"Center Frequency: {config.center_frequency/1e6:.1f} MHz")
    print(f"Sample Rate: {config.sample_rate/1e6:.1f} MHz")
    print(f"FFT Size: {config.fft_size}")
    print(f"History Size: {config.history_size}")
    print(f"Colormap: {config.colormap.value}")
    print("\nKeyboard shortcuts:")
    print("  ↑/↓: Frequency, ←/→: Sample rate")
    print("  Space: Pause, C: Clear, M: Mark peak")
    print("  F1: Help, F11: Fullscreen, Ctrl+Q: Quit")
    print("\nClick 'Start' to begin acquisition...")
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        main_window.close()


if __name__ == "__main__":
    main()
