#!/usr/bin/env python3
"""
Enhanced ADALM-Pluto SDR Terminal Menu System

A comprehensive terminal-based interface for accessing all integrated tools,
features, and functions from the enhanced spectrum analyzer project.

Features:
- Interactive menu navigation
- Device discovery and management
- Spectrum analysis tools
- Signal generation utilities
- Calibration and diagnostics
- Waterfall display options
- Configuration management
- Help and documentation

Usage:
    python pluto_menu.py

Author: Enhanced SDR Tools
License: GPL-2 (compatible with all integrated projects)
"""

import sys
import os
import time
import subprocess
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass

# Import our enhanced utilities
try:
    from pluto_utils import (
        PlutoSDRManager, SignalGenerator, CalibrationManager,
        ConfigurationManager, format_frequency
    )
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False

# Terminal colors and formatting
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


@dataclass
class MenuOption:
    """Menu option definition"""
    key: str
    title: str
    description: str
    action: Callable
    requires_device: bool = False


class PlutoMenuSystem:
    """
    Terminal-based menu system for Enhanced ADALM-Pluto SDR tools
    """
    
    def __init__(self):
        self.pluto_manager: Optional[PlutoSDRManager] = None
        self.running = True
        self.current_menu = "main"
        
        # Initialize menu structure
        self.menus = self._build_menu_structure()
        
        # Check system requirements
        self.check_requirements()
    
    def check_requirements(self):
        """Check system requirements and available tools"""
        print(f"{Colors.HEADER}🔍 Checking System Requirements...{Colors.ENDC}")
        
        # Check Python modules
        modules = {
            "numpy": "NumPy (numerical computing)",
            "scipy": "SciPy (scientific computing)", 
            "pyqtgraph": "PyQtGraph (plotting)",
            "PyQt6": "PyQt6 (GUI framework)"
        }
        
        missing_modules = []
        for module, description in modules.items():
            try:
                __import__(module)
                print(f"  ✅ {description}")
            except ImportError:
                print(f"  ❌ {description} - Not available")
                missing_modules.append(module)
        
        # Check our utilities
        if UTILS_AVAILABLE:
            print(f"  ✅ Enhanced PlutoSDR utilities")
        else:
            print(f"  ❌ Enhanced PlutoSDR utilities - Not available")
        
        # Check system tools
        system_tools = {
            "iio_info": "libiio tools",
            "avahi-resolve": "Avahi/Zeroconf tools"
        }
        
        for tool, description in system_tools.items():
            try:
                result = subprocess.run([tool, "--help"], 
                                      capture_output=True, timeout=2)
                print(f"  ✅ {description}")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                print(f"  ⚠️  {description} - Optional")
        
        if missing_modules:
            print(f"\n{Colors.WARNING}⚠️  Some modules are missing. Install with:{Colors.ENDC}")
            print(f"   pip install {' '.join(missing_modules)}")
        
        print()
    
    def _build_menu_structure(self) -> Dict[str, List[MenuOption]]:
        """Build the complete menu structure"""
        return {
            "main": [
                MenuOption("1", "🔌 Device Management", "Connect, discover, and manage PlutoSDR devices", self.device_menu),
                MenuOption("2", "📊 Spectrum Analysis", "Run spectrum analyzer tools", self.spectrum_menu),
                MenuOption("3", "🎵 Signal Generation", "Generate and transmit signals", self.signal_menu, True),
                MenuOption("4", "🔧 Calibration & Diagnostics", "Device calibration and health checks", self.calibration_menu, True),
                MenuOption("5", "🌊 Waterfall Display", "Real-time waterfall spectrum visualization", self.waterfall_menu),
                MenuOption("6", "⚙️  Configuration", "Manage device configurations and profiles", self.config_menu, True),
                MenuOption("7", "🧪 Testing & Validation", "Run integration tests and demos", self.testing_menu),
                MenuOption("8", "📚 Help & Documentation", "View help, guides, and examples", self.help_menu),
                MenuOption("q", "🚪 Quit", "Exit the menu system", self.quit_application),
            ],
            "device": [
                MenuOption("1", "🔍 Discover Devices", "Scan for available PlutoSDR devices", self.discover_devices),
                MenuOption("2", "🔌 Connect to Device", "Connect to a specific device", self.connect_device),
                MenuOption("3", "📋 Device Information", "Show connected device details", self.show_device_info, True),
                MenuOption("4", "🌡️  Temperature Monitor", "Monitor device temperatures", self.monitor_temperature, True),
                MenuOption("5", "🔌 Disconnect Device", "Disconnect current device", self.disconnect_device, True),
                MenuOption("b", "⬅️  Back to Main Menu", "Return to main menu", self.back_to_main),
            ],
            "spectrum": [
                MenuOption("1", "🖥️  GUI Spectrum Analyzer", "Launch enhanced GUI spectrum analyzer", self.launch_gui_spectrum),
                MenuOption("2", "📈 Quick Spectrum Scan", "Perform a quick spectrum scan", self.quick_spectrum_scan, True),
                MenuOption("3", "📊 Band Analysis", "Analyze specific frequency bands", self.band_analysis, True),
                MenuOption("4", "🎯 Peak Detection", "Find and analyze spectral peaks", self.peak_detection, True),
                MenuOption("b", "⬅️  Back to Main Menu", "Return to main menu", self.back_to_main),
            ],
            "signal": [
                MenuOption("1", "🎵 Generate Sine Wave", "Generate and transmit sine wave", self.generate_sine, True),
                MenuOption("2", "📐 Generate Triangle Wave", "Generate triangle test signal", self.generate_triangle, True),
                MenuOption("3", "🌊 Generate Frequency Chirp", "Generate swept frequency signal", self.generate_chirp, True),
                MenuOption("4", "🎛️  Configure DDS Tone", "Set up hardware DDS tone", self.configure_dds, True),
                MenuOption("5", "🔄 Loopback Test", "Test TX/RX with loopback", self.loopback_test, True),
                MenuOption("6", "⏹️  Stop Transmission", "Stop all signal transmission", self.stop_transmission, True),
                MenuOption("b", "⬅️  Back to Main Menu", "Return to main menu", self.back_to_main),
            ],
            "calibration": [
                MenuOption("1", "🔧 Run Full Calibration", "Perform comprehensive device calibration", self.run_calibration, True),
                MenuOption("2", "🩺 Device Diagnostics", "Run complete diagnostic tests", self.run_diagnostics, True),
                MenuOption("3", "📊 Noise Floor Measurement", "Measure device noise floor", self.measure_noise_floor, True),
                MenuOption("4", "🔄 Loopback Validation", "Validate TX/RX paths", self.validate_loopback, True),
                MenuOption("5", "📈 Performance Report", "Generate performance report", self.performance_report, True),
                MenuOption("b", "⬅️  Back to Main Menu", "Return to main menu", self.back_to_main),
            ],
            "waterfall": [
                MenuOption("1", "🖥️  GUI Waterfall Display", "Launch GUI waterfall application", self.launch_gui_waterfall),
                MenuOption("2", "🌊 Standalone Waterfall", "Run standalone waterfall app", self.launch_standalone_waterfall),
                MenuOption("3", "⚙️  Waterfall Configuration", "Configure waterfall parameters", self.configure_waterfall),
                MenuOption("4", "📊 Waterfall Demo", "Run waterfall demonstration", self.waterfall_demo),
                MenuOption("b", "⬅️  Back to Main Menu", "Return to main menu", self.back_to_main),
            ],
            "config": [
                MenuOption("1", "💾 Save Configuration", "Save current device settings", self.save_config, True),
                MenuOption("2", "📂 Load Configuration", "Load saved configuration profile", self.load_config, True),
                MenuOption("3", "📋 List Profiles", "Show available configuration profiles", self.list_profiles, True),
                MenuOption("4", "🗑️  Delete Profile", "Remove a configuration profile", self.delete_profile, True),
                MenuOption("5", "⚙️  Device Settings", "Configure basic device parameters", self.device_settings, True),
                MenuOption("b", "⬅️  Back to Main Menu", "Return to main menu", self.back_to_main),
            ],
            "testing": [
                MenuOption("1", "🧪 Integration Tests", "Run comprehensive integration tests", self.run_integration_tests),
                MenuOption("2", "🎭 Feature Demo", "Demonstrate all features", self.run_feature_demo),
                MenuOption("3", "🔍 System Check", "Check system requirements", self.system_check),
                MenuOption("4", "📊 Performance Benchmark", "Benchmark system performance", self.performance_benchmark),
                MenuOption("b", "⬅️  Back to Main Menu", "Return to main menu", self.back_to_main),
            ],
            "help": [
                MenuOption("1", "📖 User Guide", "View comprehensive user guide", self.show_user_guide),
                MenuOption("2", "🚀 Quick Start", "Quick start tutorial", self.show_quick_start),
                MenuOption("3", "⌨️  Keyboard Shortcuts", "View keyboard shortcuts", self.show_shortcuts),
                MenuOption("4", "🔗 Related Projects", "Information about integrated projects", self.show_projects),
                MenuOption("5", "❓ FAQ", "Frequently asked questions", self.show_faq),
                MenuOption("6", "🐛 Troubleshooting", "Common issues and solutions", self.show_troubleshooting),
                MenuOption("b", "⬅️  Back to Main Menu", "Return to main menu", self.back_to_main),
            ]
        }
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_banner(self):
        """Print application banner"""
        banner = f"""
{Colors.HEADER}╔══════════════════════════════════════════════════════════════════════════════╗
║                    Enhanced ADALM-Pluto SDR Terminal Menu                   ║
║                                                                              ║
║  🚀 Comprehensive SDR toolkit integrating features from:                    ║
║     📡 ADALM-Pluto-Spectrum-Analyzer (original)                            ║
║     🔧 plutosdr_scripts (Analog Devices)                                   ║
║     💾 plutosdr-fw (Analog Devices)                                        ║
║     🌊 waterfall display (inspired by Stvff/waterfall)                     ║
╚══════════════════════════════════════════════════════════════════════════════╝{Colors.ENDC}
"""
        print(banner)
    
    def print_status(self):
        """Print current system status"""
        status = f"\n{Colors.OKBLUE}📊 System Status:{Colors.ENDC}\n"
        
        if self.pluto_manager and self.pluto_manager.is_connected:
            device_info = self.pluto_manager.device_info
            status += f"  🟢 Device: Connected ({device_info.uri if device_info else 'Unknown'})\n"
            
            # Show temperatures if available
            temps = self.pluto_manager.get_temperatures()
            if temps:
                temp_strs = []
                for sensor, temp in temps.items():
                    if isinstance(temp, (int, float)):
                        temp_strs.append(f"{sensor}: {temp:.1f}°C")
                if temp_strs:
                    status += f"  🌡️  Temperature: {', '.join(temp_strs)}\n"
        else:
            status += f"  🔴 Device: Not connected\n"
        
        status += f"  🛠️  Utils: {'Available' if UTILS_AVAILABLE else 'Not available'}\n"
        
        print(status)
    
    def display_menu(self, menu_name: str):
        """Display a specific menu"""
        self.clear_screen()
        self.print_banner()
        self.print_status()
        
        menu_options = self.menus.get(menu_name, [])
        menu_title = {
            "main": "Main Menu",
            "device": "Device Management",
            "spectrum": "Spectrum Analysis",
            "signal": "Signal Generation", 
            "calibration": "Calibration & Diagnostics",
            "waterfall": "Waterfall Display",
            "config": "Configuration Management",
            "testing": "Testing & Validation",
            "help": "Help & Documentation"
        }.get(menu_name, "Menu")
        
        print(f"{Colors.BOLD}📋 {menu_title}:{Colors.ENDC}\n")
        
        for option in menu_options:
            # Check if option requires device and show status
            status_indicator = ""
            if option.requires_device:
                if not self.pluto_manager or not self.pluto_manager.is_connected:
                    status_indicator = f" {Colors.WARNING}(requires device){Colors.ENDC}"
                else:
                    status_indicator = f" {Colors.OKGREEN}(device ready){Colors.ENDC}"
            
            print(f"  {Colors.OKCYAN}{option.key}{Colors.ENDC}. {option.title}{status_indicator}")
            print(f"     {Colors.OKBLUE}{option.description}{Colors.ENDC}")
            print()
        
        print(f"{Colors.WARNING}Enter your choice:{Colors.ENDC} ", end="")
    
    def get_user_input(self, prompt: str = "") -> str:
        """Get user input with optional prompt"""
        if prompt:
            print(f"{Colors.WARNING}{prompt}{Colors.ENDC} ", end="")
        return input().strip().lower()
    
    def wait_for_enter(self, message: str = "Press Enter to continue..."):
        """Wait for user to press Enter"""
        print(f"\n{Colors.OKCYAN}{message}{Colors.ENDC}")
        input()
    
    def run(self):
        """Main menu loop"""
        while self.running:
            self.display_menu(self.current_menu)
            choice = input().strip().lower()
            
            # Find and execute the selected option
            menu_options = self.menus.get(self.current_menu, [])
            option_found = False
            
            for option in menu_options:
                if option.key.lower() == choice:
                    option_found = True
                    
                    # Check device requirement
                    if option.requires_device and (not self.pluto_manager or not self.pluto_manager.is_connected):
                        print(f"\n{Colors.FAIL}❌ This option requires a connected PlutoSDR device.{Colors.ENDC}")
                        print(f"Please connect a device first (Device Management → Connect to Device)")
                        self.wait_for_enter()
                        break
                    
                    # Execute the option
                    try:
                        option.action()
                    except KeyboardInterrupt:
                        print(f"\n{Colors.WARNING}Operation cancelled by user.{Colors.ENDC}")
                        self.wait_for_enter()
                    except Exception as e:
                        print(f"\n{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
                        self.wait_for_enter()
                    break
            
            if not option_found:
                print(f"\n{Colors.FAIL}❌ Invalid choice: {choice}{Colors.ENDC}")
                self.wait_for_enter()
    
    # Menu navigation methods
    def device_menu(self):
        """Switch to device management menu"""
        self.current_menu = "device"
    
    def spectrum_menu(self):
        """Switch to spectrum analysis menu"""
        self.current_menu = "spectrum"
    
    def signal_menu(self):
        """Switch to signal generation menu"""
        self.current_menu = "signal"
    
    def calibration_menu(self):
        """Switch to calibration menu"""
        self.current_menu = "calibration"
    
    def waterfall_menu(self):
        """Switch to waterfall menu"""
        self.current_menu = "waterfall"
    
    def config_menu(self):
        """Switch to configuration menu"""
        self.current_menu = "config"
    
    def testing_menu(self):
        """Switch to testing menu"""
        self.current_menu = "testing"
    
    def help_menu(self):
        """Switch to help menu"""
        self.current_menu = "help"
    
    def back_to_main(self):
        """Return to main menu"""
        self.current_menu = "main"
    
    def quit_application(self):
        """Quit the application"""
        print(f"\n{Colors.OKGREEN}👋 Thank you for using Enhanced ADALM-Pluto SDR Tools!{Colors.ENDC}")
        if self.pluto_manager and self.pluto_manager.is_connected:
            print("🔌 Disconnecting from PlutoSDR...")
            self.pluto_manager.disconnect()
        self.running = False

    # Device Management Methods
    def discover_devices(self):
        """Discover available PlutoSDR devices"""
        print(f"\n{Colors.HEADER}🔍 Discovering PlutoSDR Devices...{Colors.ENDC}")

        if not UTILS_AVAILABLE:
            print(f"{Colors.FAIL}❌ PlutoSDR utilities not available{Colors.ENDC}")
            self.wait_for_enter()
            return

        try:
            manager = PlutoSDRManager(auto_discover=False)
            devices = manager.discover_devices()

            if devices:
                print(f"\n{Colors.OKGREEN}✅ Found {len(devices)} device(s):{Colors.ENDC}")
                for i, device in enumerate(devices, 1):
                    print(f"  {i}. URI: {device.uri}")
                    print(f"     Type: {device.connection_type.value}")
                    if device.ip_address:
                        print(f"     IP: {device.ip_address}")
                    print()
            else:
                print(f"\n{Colors.WARNING}⚠️  No PlutoSDR devices found{Colors.ENDC}")
                print("Make sure your device is:")
                print("  • Connected via USB or network")
                print("  • Powered on and recognized by the system")
                print("  • Not in use by another application")

        except Exception as e:
            print(f"\n{Colors.FAIL}❌ Discovery failed: {e}{Colors.ENDC}")

        self.wait_for_enter()

    def connect_device(self):
        """Connect to a PlutoSDR device"""
        print(f"\n{Colors.HEADER}🔌 Connect to PlutoSDR Device{Colors.ENDC}")

        if not UTILS_AVAILABLE:
            print(f"{Colors.FAIL}❌ PlutoSDR utilities not available{Colors.ENDC}")
            self.wait_for_enter()
            return

        print("\nConnection options:")
        print("1. Auto-discover and connect")
        print("2. Connect to specific URI")
        print("3. Connect to IP address")

        choice = self.get_user_input("Enter choice (1-3):")

        try:
            if choice == "1":
                print("🔍 Auto-discovering devices...")
                self.pluto_manager = PlutoSDRManager(auto_discover=True)

            elif choice == "2":
                uri = self.get_user_input("Enter device URI (e.g., usb:1.2.5):")
                if uri:
                    self.pluto_manager = PlutoSDRManager(uri=uri, auto_discover=False)
                else:
                    print(f"{Colors.FAIL}❌ No URI provided{Colors.ENDC}")
                    self.wait_for_enter()
                    return

            elif choice == "3":
                ip = self.get_user_input("Enter IP address (e.g., 192.168.2.1):")
                if ip:
                    uri = f"ip:{ip}"
                    self.pluto_manager = PlutoSDRManager(uri=uri, auto_discover=False)
                else:
                    print(f"{Colors.FAIL}❌ No IP address provided{Colors.ENDC}")
                    self.wait_for_enter()
                    return
            else:
                print(f"{Colors.FAIL}❌ Invalid choice{Colors.ENDC}")
                self.wait_for_enter()
                return

            if self.pluto_manager and self.pluto_manager.is_connected:
                print(f"\n{Colors.OKGREEN}✅ Successfully connected to PlutoSDR!{Colors.ENDC}")
                if self.pluto_manager.device_info:
                    info = self.pluto_manager.device_info
                    print(f"   URI: {info.uri}")
                    print(f"   Connection: {info.connection_type.value}")
            else:
                print(f"\n{Colors.FAIL}❌ Failed to connect to PlutoSDR{Colors.ENDC}")
                self.pluto_manager = None

        except Exception as e:
            print(f"\n{Colors.FAIL}❌ Connection error: {e}{Colors.ENDC}")
            self.pluto_manager = None

        self.wait_for_enter()

    def show_device_info(self):
        """Show detailed device information"""
        print(f"\n{Colors.HEADER}📋 Device Information{Colors.ENDC}")

        if not self.pluto_manager or not self.pluto_manager.is_connected:
            print(f"{Colors.FAIL}❌ No device connected{Colors.ENDC}")
            self.wait_for_enter()
            return

        try:
            info = self.pluto_manager.device_info
            if info:
                print(f"\n{Colors.OKGREEN}Device Details:{Colors.ENDC}")
                print(f"  URI: {info.uri}")
                print(f"  Connection Type: {info.connection_type.value}")
                if info.ip_address:
                    print(f"  IP Address: {info.ip_address}")
                if info.serial_number:
                    print(f"  Serial Number: {info.serial_number}")
                if info.firmware_version:
                    print(f"  Firmware Version: {info.firmware_version}")

            # Show temperatures
            temps = self.pluto_manager.get_temperatures()
            if temps:
                print(f"\n{Colors.OKGREEN}Temperature Readings:{Colors.ENDC}")
                for sensor, temp in temps.items():
                    if isinstance(temp, (int, float)):
                        status = ""
                        if temp > 80:
                            status = f" {Colors.FAIL}(HIGH!){Colors.ENDC}"
                        elif temp > 70:
                            status = f" {Colors.WARNING}(Elevated){Colors.ENDC}"
                        else:
                            status = f" {Colors.OKGREEN}(Normal){Colors.ENDC}"
                        print(f"  {sensor.upper()}: {temp:.1f}°C{status}")

            # Show current configuration if available
            if hasattr(self.pluto_manager, 'sdr') and self.pluto_manager.sdr:
                print(f"\n{Colors.OKGREEN}Current Configuration:{Colors.ENDC}")
                try:
                    print(f"  RX LO: {format_frequency(self.pluto_manager.sdr.rx_lo)}")
                    print(f"  TX LO: {format_frequency(self.pluto_manager.sdr.tx_lo)}")
                    print(f"  Sample Rate: {format_frequency(self.pluto_manager.sdr.sample_rate)}")
                    print(f"  RX Gain: {self.pluto_manager.sdr.rx_hardwaregain_chan0} dB")
                    print(f"  TX Gain: {self.pluto_manager.sdr.tx_hardwaregain_chan0} dB")
                except:
                    print("  Configuration details not available")

        except Exception as e:
            print(f"\n{Colors.FAIL}❌ Error reading device info: {e}{Colors.ENDC}")

        self.wait_for_enter()

    def monitor_temperature(self):
        """Monitor device temperatures in real-time"""
        print(f"\n{Colors.HEADER}🌡️  Temperature Monitor{Colors.ENDC}")
        print("Press Ctrl+C to stop monitoring\n")

        try:
            while True:
                temps = self.pluto_manager.get_temperatures()
                if temps:
                    temp_display = []
                    for sensor, temp in temps.items():
                        if isinstance(temp, (int, float)):
                            color = Colors.OKGREEN
                            if temp > 80:
                                color = Colors.FAIL
                            elif temp > 70:
                                color = Colors.WARNING
                            temp_display.append(f"{color}{sensor.upper()}: {temp:.1f}°C{Colors.ENDC}")

                    # Clear line and print temperatures
                    print(f"\r{' | '.join(temp_display)}", end="", flush=True)
                else:
                    print(f"\r{Colors.FAIL}Temperature reading failed{Colors.ENDC}", end="", flush=True)

                time.sleep(1)

        except KeyboardInterrupt:
            print(f"\n\n{Colors.OKGREEN}Temperature monitoring stopped{Colors.ENDC}")

        self.wait_for_enter()

    def disconnect_device(self):
        """Disconnect from current device"""
        print(f"\n{Colors.HEADER}🔌 Disconnect Device{Colors.ENDC}")

        if self.pluto_manager and self.pluto_manager.is_connected:
            self.pluto_manager.disconnect()
            self.pluto_manager = None
            print(f"\n{Colors.OKGREEN}✅ Device disconnected successfully{Colors.ENDC}")
        else:
            print(f"\n{Colors.WARNING}⚠️  No device was connected{Colors.ENDC}")

        self.wait_for_enter()

    # Spectrum Analysis Methods
    def launch_gui_spectrum(self):
        """Launch the GUI spectrum analyzer"""
        print(f"\n{Colors.HEADER}🖥️  Launching Enhanced Spectrum Analyzer...{Colors.ENDC}")

        try:
            subprocess.Popen([sys.executable, "enhanced_spectrum_analyzer.py"])
            print(f"{Colors.OKGREEN}✅ GUI application launched{Colors.ENDC}")
            print("The enhanced spectrum analyzer window should open shortly.")
        except Exception as e:
            print(f"{Colors.FAIL}❌ Failed to launch GUI: {e}{Colors.ENDC}")

        self.wait_for_enter()

    def quick_spectrum_scan(self):
        """Perform a quick spectrum scan"""
        print(f"\n{Colors.HEADER}📈 Quick Spectrum Scan{Colors.ENDC}")

        # Get scan parameters
        center_freq = self.get_user_input("Center frequency (MHz, default 100):")
        if not center_freq:
            center_freq = "100"

        sample_rate = self.get_user_input("Sample rate (MHz, default 20):")
        if not sample_rate:
            sample_rate = "20"

        try:
            center_hz = float(center_freq) * 1e6
            sr_hz = float(sample_rate) * 1e6

            print(f"\n🔍 Scanning {format_frequency(center_hz)} ± {format_frequency(sr_hz/2)}...")

            # Configure device
            self.pluto_manager.configure_basic_settings(
                rx_lo=int(center_hz),
                sample_rate=int(sr_hz),
                rx_bandwidth=int(sr_hz),
                rx_gain=60
            )

            # Collect samples
            samples = self.pluto_manager.sdr.rx()

            # Compute spectrum
            from pluto_utils import calculate_fft_spectrum
            freqs, spectrum = calculate_fft_spectrum(samples, sr_hz)

            # Find peaks
            import numpy as np
            peak_threshold = np.max(spectrum) - 20  # 20 dB below max
            peaks = []
            for i in range(1, len(spectrum)-1):
                if (spectrum[i] > peak_threshold and
                    spectrum[i] > spectrum[i-1] and
                    spectrum[i] > spectrum[i+1]):
                    freq_mhz = (center_hz + freqs[i]) / 1e6
                    peaks.append((freq_mhz, spectrum[i]))

            # Display results
            print(f"\n{Colors.OKGREEN}📊 Scan Results:{Colors.ENDC}")
            print(f"  Center: {center_freq} MHz")
            print(f"  Bandwidth: {sample_rate} MHz")
            print(f"  Samples: {len(samples)}")
            print(f"  Max Signal: {np.max(spectrum):.1f} dB")
            print(f"  Min Signal: {np.min(spectrum):.1f} dB")

            if peaks:
                print(f"\n{Colors.OKGREEN}🎯 Detected Peaks:{Colors.ENDC}")
                for freq, amp in sorted(peaks, key=lambda x: x[1], reverse=True)[:5]:
                    print(f"  {freq:.3f} MHz: {amp:.1f} dB")
            else:
                print(f"\n{Colors.WARNING}No significant peaks detected{Colors.ENDC}")

        except ValueError:
            print(f"{Colors.FAIL}❌ Invalid frequency or sample rate{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}❌ Scan failed: {e}{Colors.ENDC}")

        self.wait_for_enter()

    def band_analysis(self):
        """Analyze specific frequency bands"""
        print(f"\n{Colors.HEADER}📊 Frequency Band Analysis{Colors.ENDC}")

        bands = {
            "1": ("FM Radio", 88e6, 108e6),
            "2": ("GSM 900", 880e6, 960e6),
            "3": ("GPS L1", 1575e6, 1576e6),
            "4": ("GSM 1800", 1710e6, 1880e6),
            "5": ("WiFi 2.4G", 2400e6, 2500e6),
            "6": ("WiFi 5G", 5150e6, 5850e6),
            "7": ("Custom", None, None)
        }

        print("\nAvailable bands:")
        for key, (name, start, stop) in bands.items():
            if start and stop:
                print(f"  {key}. {name} ({start/1e6:.0f}-{stop/1e6:.0f} MHz)")
            else:
                print(f"  {key}. {name} (specify frequencies)")

        choice = self.get_user_input("Select band (1-7):")

        if choice in bands:
            name, start_freq, stop_freq = bands[choice]

            if choice == "7":  # Custom
                start_input = self.get_user_input("Start frequency (MHz):")
                stop_input = self.get_user_input("Stop frequency (MHz):")
                try:
                    start_freq = float(start_input) * 1e6
                    stop_freq = float(stop_input) * 1e6
                    name = f"Custom ({start_input}-{stop_input} MHz)"
                except ValueError:
                    print(f"{Colors.FAIL}❌ Invalid frequencies{Colors.ENDC}")
                    self.wait_for_enter()
                    return

            print(f"\n🔍 Analyzing {name}...")

            try:
                center_freq = (start_freq + stop_freq) / 2
                bandwidth = stop_freq - start_freq
                sample_rate = min(bandwidth * 1.2, 61e6)  # Add 20% margin, max 61 MHz

                # Configure and scan
                self.pluto_manager.configure_basic_settings(
                    rx_lo=int(center_freq),
                    sample_rate=int(sample_rate),
                    rx_bandwidth=int(sample_rate),
                    rx_gain=60
                )

                samples = self.pluto_manager.sdr.rx()

                from pluto_utils import calculate_fft_spectrum, estimate_snr
                freqs, spectrum = calculate_fft_spectrum(samples, sample_rate)

                # Convert to absolute frequencies
                abs_freqs = center_freq + freqs

                # Find signals in band
                band_mask = (abs_freqs >= start_freq) & (abs_freqs <= stop_freq)
                band_spectrum = spectrum[band_mask]
                band_freqs = abs_freqs[band_mask]

                if len(band_spectrum) > 0:
                    max_signal = np.max(band_spectrum)
                    max_idx = np.argmax(band_spectrum)
                    max_freq = band_freqs[max_idx]

                    print(f"\n{Colors.OKGREEN}📊 {name} Analysis:{Colors.ENDC}")
                    print(f"  Frequency Range: {start_freq/1e6:.1f} - {stop_freq/1e6:.1f} MHz")
                    print(f"  Sample Rate: {sample_rate/1e6:.1f} MHz")
                    print(f"  Peak Signal: {max_signal:.1f} dB at {max_freq/1e6:.3f} MHz")
                    print(f"  Average Level: {np.mean(band_spectrum):.1f} dB")
                    print(f"  Dynamic Range: {max_signal - np.min(band_spectrum):.1f} dB")
                else:
                    print(f"{Colors.WARNING}⚠️  No data in specified band{Colors.ENDC}")

            except Exception as e:
                print(f"{Colors.FAIL}❌ Analysis failed: {e}{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}❌ Invalid band selection{Colors.ENDC}")

        self.wait_for_enter()

    def peak_detection(self):
        """Find and analyze spectral peaks"""
        print(f"\n{Colors.HEADER}🎯 Peak Detection Analysis{Colors.ENDC}")

        center_freq = self.get_user_input("Center frequency (MHz, default 100):")
        if not center_freq:
            center_freq = "100"

        try:
            center_hz = float(center_freq) * 1e6
            sample_rate = 20e6  # 20 MHz bandwidth

            print(f"\n🔍 Scanning for peaks around {center_freq} MHz...")

            # Configure device
            self.pluto_manager.configure_basic_settings(
                rx_lo=int(center_hz),
                sample_rate=int(sample_rate),
                rx_bandwidth=int(sample_rate),
                rx_gain=60
            )

            # Collect multiple samples for averaging
            print("📊 Collecting samples...")
            spectrums = []
            for i in range(5):
                samples = self.pluto_manager.sdr.rx()
                from pluto_utils import calculate_fft_spectrum
                freqs, spectrum = calculate_fft_spectrum(samples, sample_rate)
                spectrums.append(spectrum)
                print(f"  Sample {i+1}/5 collected")

            # Average spectrums
            import numpy as np
            avg_spectrum = np.mean(spectrums, axis=0)
            abs_freqs = center_hz + freqs

            # Advanced peak detection
            from scipy.signal import find_peaks

            # Find peaks with minimum height and prominence
            peak_height = np.max(avg_spectrum) - 30  # 30 dB below max
            peaks, properties = find_peaks(avg_spectrum,
                                         height=peak_height,
                                         prominence=5,  # 5 dB prominence
                                         distance=10)   # Minimum 10 bins apart

            print(f"\n{Colors.OKGREEN}🎯 Peak Detection Results:{Colors.ENDC}")
            print(f"  Center: {center_freq} MHz")
            print(f"  Bandwidth: {sample_rate/1e6:.1f} MHz")
            print(f"  Threshold: {peak_height:.1f} dB")
            print(f"  Peaks Found: {len(peaks)}")

            if len(peaks) > 0:
                print(f"\n{Colors.OKGREEN}📊 Detected Peaks:{Colors.ENDC}")
                peak_data = []
                for i, peak_idx in enumerate(peaks):
                    freq_mhz = abs_freqs[peak_idx] / 1e6
                    amplitude = avg_spectrum[peak_idx]
                    prominence = properties['prominences'][i]
                    peak_data.append((freq_mhz, amplitude, prominence))

                # Sort by amplitude
                peak_data.sort(key=lambda x: x[1], reverse=True)

                for i, (freq, amp, prom) in enumerate(peak_data[:10]):  # Top 10 peaks
                    print(f"  {i+1:2d}. {freq:8.3f} MHz: {amp:6.1f} dB (prominence: {prom:.1f} dB)")
            else:
                print(f"\n{Colors.WARNING}⚠️  No significant peaks detected{Colors.ENDC}")
                print("Try adjusting the center frequency or increasing gain")

        except ValueError:
            print(f"{Colors.FAIL}❌ Invalid frequency{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}❌ Peak detection failed: {e}{Colors.ENDC}")

        self.wait_for_enter()

    # Signal Generation Methods
    def generate_sine(self):
        """Generate and transmit sine wave"""
        print(f"\n{Colors.HEADER}🎵 Generate Sine Wave{Colors.ENDC}")

        frequency = self.get_user_input("Frequency (kHz, default 100):")
        if not frequency:
            frequency = "100"

        amplitude = self.get_user_input("Amplitude (0.0-1.0, default 0.5):")
        if not amplitude:
            amplitude = "0.5"

        duration = self.get_user_input("Duration (seconds, default 1.0):")
        if not duration:
            duration = "1.0"

        try:
            freq_hz = float(frequency) * 1000
            amp_val = float(amplitude)
            dur_val = float(duration)

            if not (0.0 <= amp_val <= 1.0):
                print(f"{Colors.FAIL}❌ Amplitude must be between 0.0 and 1.0{Colors.ENDC}")
                self.wait_for_enter()
                return

            print(f"\n🎵 Generating sine wave: {freq_hz/1000:.1f} kHz, amplitude {amp_val:.2f}")

            from pluto_utils import SignalGenerator
            sig_gen = SignalGenerator(self.pluto_manager)

            # Generate signal
            samples = sig_gen.generate_sine_wave(freq_hz, amp_val, 3000000, dur_val)

            print(f"✅ Generated {len(samples)} samples")

            # Ask if user wants to transmit
            transmit = self.get_user_input("Transmit signal? (y/n, default n):")
            if transmit.lower() in ['y', 'yes']:
                cyclic = self.get_user_input("Cyclic transmission? (y/n, default y):")
                cyclic_mode = cyclic.lower() not in ['n', 'no']

                if sig_gen.transmit_signal(samples, cyclic_mode):
                    print(f"{Colors.OKGREEN}✅ Signal transmission started{Colors.ENDC}")
                    if cyclic_mode:
                        print("Signal will transmit continuously until stopped")
                else:
                    print(f"{Colors.FAIL}❌ Failed to start transmission{Colors.ENDC}")

        except ValueError:
            print(f"{Colors.FAIL}❌ Invalid parameters{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}❌ Signal generation failed: {e}{Colors.ENDC}")

        self.wait_for_enter()

    def generate_triangle(self):
        """Generate triangle test signal"""
        print(f"\n{Colors.HEADER}📐 Generate Triangle Wave{Colors.ENDC}")

        sample_rate = self.get_user_input("Sample rate (MHz, default 3):")
        if not sample_rate:
            sample_rate = "3"

        num_samples = self.get_user_input("Number of samples (default 2048):")
        if not num_samples:
            num_samples = "2048"

        try:
            sr_hz = float(sample_rate) * 1e6
            n_samples = int(num_samples)

            print(f"\n📐 Generating triangle wave: {sr_hz/1e6:.1f} MHz sample rate, {n_samples} samples")

            from pluto_utils import SignalGenerator
            sig_gen = SignalGenerator(self.pluto_manager)

            # Generate signal
            samples = sig_gen.generate_triangle_wave(int(sr_hz), n_samples)

            print(f"✅ Generated {len(samples)} samples")

            # Ask if user wants to transmit
            transmit = self.get_user_input("Transmit signal? (y/n, default n):")
            if transmit.lower() in ['y', 'yes']:
                if sig_gen.transmit_signal(samples, True):  # Always cyclic for triangle
                    print(f"{Colors.OKGREEN}✅ Triangle wave transmission started{Colors.ENDC}")
                else:
                    print(f"{Colors.FAIL}❌ Failed to start transmission{Colors.ENDC}")

        except ValueError:
            print(f"{Colors.FAIL}❌ Invalid parameters{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}❌ Triangle generation failed: {e}{Colors.ENDC}")

        self.wait_for_enter()

    def generate_chirp(self):
        """Generate frequency chirp signal"""
        print(f"\n{Colors.HEADER}🌊 Generate Frequency Chirp{Colors.ENDC}")

        start_freq = self.get_user_input("Start frequency (kHz, default 50):")
        if not start_freq:
            start_freq = "50"

        end_freq = self.get_user_input("End frequency (kHz, default 150):")
        if not end_freq:
            end_freq = "150"

        duration = self.get_user_input("Duration (seconds, default 1.0):")
        if not duration:
            duration = "1.0"

        amplitude = self.get_user_input("Amplitude (0.0-1.0, default 0.5):")
        if not amplitude:
            amplitude = "0.5"

        try:
            start_hz = float(start_freq) * 1000
            end_hz = float(end_freq) * 1000
            dur_val = float(duration)
            amp_val = float(amplitude)

            if not (0.0 <= amp_val <= 1.0):
                print(f"{Colors.FAIL}❌ Amplitude must be between 0.0 and 1.0{Colors.ENDC}")
                self.wait_for_enter()
                return

            print(f"\n🌊 Generating chirp: {start_hz/1000:.1f} → {end_hz/1000:.1f} kHz over {dur_val:.1f}s")

            from pluto_utils import SignalGenerator
            sig_gen = SignalGenerator(self.pluto_manager)

            # Generate signal
            samples = sig_gen.generate_chirp(start_hz, end_hz, dur_val, 3000000, amp_val)

            print(f"✅ Generated {len(samples)} samples")

            # Ask if user wants to transmit
            transmit = self.get_user_input("Transmit signal? (y/n, default n):")
            if transmit.lower() in ['y', 'yes']:
                cyclic = self.get_user_input("Cyclic transmission? (y/n, default n):")
                cyclic_mode = cyclic.lower() in ['y', 'yes']

                if sig_gen.transmit_signal(samples, cyclic_mode):
                    print(f"{Colors.OKGREEN}✅ Chirp transmission started{Colors.ENDC}")
                else:
                    print(f"{Colors.FAIL}❌ Failed to start transmission{Colors.ENDC}")

        except ValueError:
            print(f"{Colors.FAIL}❌ Invalid parameters{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}❌ Chirp generation failed: {e}{Colors.ENDC}")

        self.wait_for_enter()

    def configure_dds(self):
        """Configure DDS tone generation"""
        print(f"\n{Colors.HEADER}🎛️  Configure DDS Tone{Colors.ENDC}")

        frequency = self.get_user_input("Frequency (kHz, default 100):")
        if not frequency:
            frequency = "100"

        amplitude = self.get_user_input("Amplitude (0.0-1.0, default 0.8):")
        if not amplitude:
            amplitude = "0.8"

        phase = self.get_user_input("Phase (degrees, default 0):")
        if not phase:
            phase = "0"

        try:
            freq_hz = float(frequency) * 1000
            amp_val = float(amplitude)
            phase_val = float(phase)

            if not (0.0 <= amp_val <= 1.0):
                print(f"{Colors.FAIL}❌ Amplitude must be between 0.0 and 1.0{Colors.ENDC}")
                self.wait_for_enter()
                return

            print(f"\n🎛️  Configuring DDS: {freq_hz/1000:.1f} kHz, amplitude {amp_val:.2f}, phase {phase_val:.1f}°")

            from pluto_utils import SignalGenerator
            sig_gen = SignalGenerator(self.pluto_manager)

            if sig_gen.configure_dds_tone(freq_hz, amp_val, phase_val):
                print(f"{Colors.OKGREEN}✅ DDS tone configured and active{Colors.ENDC}")
                print("The tone is now being generated by the hardware DDS")
            else:
                print(f"{Colors.FAIL}❌ Failed to configure DDS tone{Colors.ENDC}")

        except ValueError:
            print(f"{Colors.FAIL}❌ Invalid parameters{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}❌ DDS configuration failed: {e}{Colors.ENDC}")

        self.wait_for_enter()

    def loopback_test(self):
        """Test TX/RX with loopback"""
        print(f"\n{Colors.HEADER}🔄 Loopback Test{Colors.ENDC}")

        print("This test will:")
        print("1. Enable digital loopback mode")
        print("2. Generate a test signal")
        print("3. Transmit and receive the signal")
        print("4. Verify signal integrity")
        print("5. Disable loopback mode")

        proceed = self.get_user_input("\nProceed with loopback test? (y/n):")
        if proceed.lower() not in ['y', 'yes']:
            return

        try:
            print(f"\n🔄 Running loopback test...")

            from pluto_utils import CalibrationManager
            cal_mgr = CalibrationManager(self.pluto_manager)

            # Run the loopback test
            result = cal_mgr._test_loopback()

            if result:
                print(f"{Colors.OKGREEN}✅ Loopback test PASSED{Colors.ENDC}")
                print("TX and RX paths are working correctly")
            else:
                print(f"{Colors.FAIL}❌ Loopback test FAILED{Colors.ENDC}")
                print("There may be an issue with TX or RX paths")

        except Exception as e:
            print(f"{Colors.FAIL}❌ Loopback test error: {e}{Colors.ENDC}")

        self.wait_for_enter()

    def stop_transmission(self):
        """Stop all signal transmission"""
        print(f"\n{Colors.HEADER}⏹️  Stop Signal Transmission{Colors.ENDC}")

        try:
            from pluto_utils import SignalGenerator
            sig_gen = SignalGenerator(self.pluto_manager)
            sig_gen.stop_transmission()

            print(f"{Colors.OKGREEN}✅ All signal transmission stopped{Colors.ENDC}")

        except Exception as e:
            print(f"{Colors.FAIL}❌ Error stopping transmission: {e}{Colors.ENDC}")

        self.wait_for_enter()

    # Calibration Methods (placeholder implementations)
    def run_calibration(self):
        """Run full device calibration"""
        print(f"\n{Colors.HEADER}🔧 Device Calibration{Colors.ENDC}")
        print("Running comprehensive device calibration...")

        try:
            from pluto_utils import CalibrationManager
            cal_mgr = CalibrationManager(self.pluto_manager)
            result = cal_mgr.perform_basic_calibration()

            if result.success:
                print(f"\n{Colors.OKGREEN}✅ Calibration completed successfully{Colors.ENDC}")
                print(f"DC Offset I: {result.dc_offset_i:.6f}")
                print(f"DC Offset Q: {result.dc_offset_q:.6f}")
                print(f"IQ Imbalance: {result.iq_imbalance:.3f} dB")
            else:
                print(f"{Colors.FAIL}❌ Calibration failed{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}❌ Calibration error: {e}{Colors.ENDC}")

        self.wait_for_enter()

    def run_diagnostics(self):
        """Run device diagnostics"""
        print(f"\n{Colors.HEADER}🩺 Device Diagnostics{Colors.ENDC}")
        print("Running comprehensive diagnostic tests...")

        try:
            from pluto_utils import CalibrationManager
            cal_mgr = CalibrationManager(self.pluto_manager)
            results = cal_mgr.run_diagnostic_tests()

            print(f"\n{Colors.OKGREEN}📊 Diagnostic Results:{Colors.ENDC}")
            print(f"Device Connected: {'✅' if results['device_connected'] else '❌'}")
            print(f"Loopback Test: {'✅' if results['loopback_test'] else '❌'}")

            if results['temperatures']:
                print(f"Temperature Check: ✅")

            if results['noise_floor'] is not None:
                print(f"Noise Floor: {results['noise_floor']:.1f} dB")

        except Exception as e:
            print(f"{Colors.FAIL}❌ Diagnostics error: {e}{Colors.ENDC}")

        self.wait_for_enter()

    def measure_noise_floor(self):
        """Measure device noise floor"""
        print(f"\n{Colors.HEADER}📊 Noise Floor Measurement{Colors.ENDC}")

        try:
            from pluto_utils import CalibrationManager
            cal_mgr = CalibrationManager(self.pluto_manager)
            noise_floor = cal_mgr._measure_noise_floor()

            if noise_floor is not None:
                print(f"\n{Colors.OKGREEN}📊 Noise Floor: {noise_floor:.1f} dB{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}❌ Noise floor measurement failed{Colors.ENDC}")

        except Exception as e:
            print(f"{Colors.FAIL}❌ Measurement error: {e}{Colors.ENDC}")

        self.wait_for_enter()

    def validate_loopback(self):
        """Validate TX/RX paths"""
        print(f"\n{Colors.HEADER}🔄 Loopback Validation{Colors.ENDC}")
        self.loopback_test()  # Reuse the loopback test

    def performance_report(self):
        """Generate performance report"""
        print(f"\n{Colors.HEADER}📈 Performance Report{Colors.ENDC}")
        print("Generating comprehensive performance report...")

        try:
            # Run multiple tests and compile report
            from pluto_utils import CalibrationManager
            cal_mgr = CalibrationManager(self.pluto_manager)

            print("\n📊 Performance Summary:")
            print("=" * 40)

            # Temperature
            temps = self.pluto_manager.get_temperatures()
            if temps:
                for sensor, temp in temps.items():
                    print(f"{sensor.upper()} Temperature: {temp:.1f}°C")

            # Calibration
            cal_result = cal_mgr.perform_basic_calibration()
            if cal_result.success:
                print(f"DC Offset: I={cal_result.dc_offset_i:.6f}, Q={cal_result.dc_offset_q:.6f}")
                print(f"IQ Imbalance: {cal_result.iq_imbalance:.3f} dB")

            # Diagnostics
            diag_results = cal_mgr.run_diagnostic_tests()
            print(f"Loopback Test: {'PASS' if diag_results['loopback_test'] else 'FAIL'}")

            if diag_results['noise_floor'] is not None:
                print(f"Noise Floor: {diag_results['noise_floor']:.1f} dB")

            print("=" * 40)
            print(f"{Colors.OKGREEN}✅ Performance report completed{Colors.ENDC}")

        except Exception as e:
            print(f"{Colors.FAIL}❌ Report generation error: {e}{Colors.ENDC}")

        self.wait_for_enter()

    # Waterfall Methods
    def launch_gui_waterfall(self):
        """Launch GUI waterfall in enhanced spectrum analyzer"""
        print(f"\n{Colors.HEADER}🖥️  Launching Enhanced Spectrum Analyzer (Waterfall Tab)...{Colors.ENDC}")

        try:
            subprocess.Popen([sys.executable, "enhanced_spectrum_analyzer.py"])
            print(f"{Colors.OKGREEN}✅ GUI application launched{Colors.ENDC}")
            print("Click the 'Waterfall Display' tab to access the waterfall view.")
        except Exception as e:
            print(f"{Colors.FAIL}❌ Failed to launch GUI: {e}{Colors.ENDC}")

        self.wait_for_enter()

    def launch_standalone_waterfall(self):
        """Launch standalone waterfall application"""
        print(f"\n{Colors.HEADER}🌊 Launching Standalone Waterfall...{Colors.ENDC}")

        center_freq = self.get_user_input("Center frequency (MHz, default 100):")
        if not center_freq:
            center_freq = "100"

        sample_rate = self.get_user_input("Sample rate (MHz, default 20):")
        if not sample_rate:
            sample_rate = "20"

        try:
            cmd = [
                sys.executable, "waterfall_app.py",
                "--center-freq", str(float(center_freq) * 1e6),
                "--sample-rate", str(float(sample_rate) * 1e6)
            ]
            subprocess.Popen(cmd)
            print(f"{Colors.OKGREEN}✅ Standalone waterfall launched{Colors.ENDC}")
            print(f"Center: {center_freq} MHz, Sample Rate: {sample_rate} MHz")
        except Exception as e:
            print(f"{Colors.FAIL}❌ Failed to launch waterfall: {e}{Colors.ENDC}")

        self.wait_for_enter()

    def configure_waterfall(self):
        """Configure waterfall parameters"""
        print(f"\n{Colors.HEADER}⚙️  Waterfall Configuration{Colors.ENDC}")

        print("Available colormaps:")
        colormaps = ["viridis", "plasma", "inferno", "magma", "jet", "hot", "cool", "gray"]
        for i, cm in enumerate(colormaps, 1):
            print(f"  {i}. {cm}")

        colormap_choice = self.get_user_input("Select colormap (1-8, default 1):")
        if not colormap_choice:
            colormap_choice = "1"

        fft_size = self.get_user_input("FFT size (256/512/1024/2048/4096, default 1024):")
        if not fft_size:
            fft_size = "1024"

        try:
            cm_idx = int(colormap_choice) - 1
            if 0 <= cm_idx < len(colormaps):
                selected_colormap = colormaps[cm_idx]
            else:
                selected_colormap = "viridis"

            print(f"\n⚙️  Waterfall Configuration:")
            print(f"  Colormap: {selected_colormap}")
            print(f"  FFT Size: {fft_size}")
            print(f"  Use these settings when launching the waterfall display")

        except ValueError:
            print(f"{Colors.FAIL}❌ Invalid configuration{Colors.ENDC}")

        self.wait_for_enter()

    def waterfall_demo(self):
        """Run waterfall demonstration"""
        print(f"\n{Colors.HEADER}📊 Waterfall Demo{Colors.ENDC}")

        try:
            subprocess.Popen([sys.executable, "demo_all_features.py"])
            print(f"{Colors.OKGREEN}✅ Demo launched{Colors.ENDC}")
            print("The demo will show all integrated features including waterfall display.")
        except Exception as e:
            print(f"{Colors.FAIL}❌ Failed to launch demo: {e}{Colors.ENDC}")

        self.wait_for_enter()

    # Configuration Methods
    def save_config(self):
        """Save current configuration"""
        print(f"\n{Colors.HEADER}💾 Save Configuration{Colors.ENDC}")

        profile_name = self.get_user_input("Profile name:")
        if not profile_name:
            print(f"{Colors.FAIL}❌ Profile name required{Colors.ENDC}")
            self.wait_for_enter()
            return

        try:
            from pluto_utils import ConfigurationManager
            config_mgr = ConfigurationManager(self.pluto_manager)

            if config_mgr.save_current_config(profile_name):
                print(f"{Colors.OKGREEN}✅ Configuration saved as '{profile_name}'{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}❌ Failed to save configuration{Colors.ENDC}")

        except Exception as e:
            print(f"{Colors.FAIL}❌ Save error: {e}{Colors.ENDC}")

        self.wait_for_enter()

    def load_config(self):
        """Load configuration profile"""
        print(f"\n{Colors.HEADER}📂 Load Configuration{Colors.ENDC}")

        try:
            from pluto_utils import ConfigurationManager
            config_mgr = ConfigurationManager(self.pluto_manager)
            profiles = config_mgr.get_profile_list()

            if not profiles:
                print(f"{Colors.WARNING}⚠️  No saved profiles found{Colors.ENDC}")
                self.wait_for_enter()
                return

            print("\nAvailable profiles:")
            for i, profile in enumerate(profiles, 1):
                print(f"  {i}. {profile}")

            choice = self.get_user_input("Select profile number:")
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(profiles):
                    profile_name = profiles[idx]
                    if config_mgr.load_config_profile(profile_name):
                        print(f"{Colors.OKGREEN}✅ Configuration '{profile_name}' loaded{Colors.ENDC}")
                    else:
                        print(f"{Colors.FAIL}❌ Failed to load configuration{Colors.ENDC}")
                else:
                    print(f"{Colors.FAIL}❌ Invalid selection{Colors.ENDC}")
            except ValueError:
                print(f"{Colors.FAIL}❌ Invalid selection{Colors.ENDC}")

        except Exception as e:
            print(f"{Colors.FAIL}❌ Load error: {e}{Colors.ENDC}")

        self.wait_for_enter()

    def list_profiles(self):
        """List configuration profiles"""
        print(f"\n{Colors.HEADER}📋 Configuration Profiles{Colors.ENDC}")

        try:
            from pluto_utils import ConfigurationManager
            config_mgr = ConfigurationManager(self.pluto_manager)
            profiles = config_mgr.get_profile_list()

            if profiles:
                print(f"\n{Colors.OKGREEN}Available profiles:{Colors.ENDC}")
                for i, profile in enumerate(profiles, 1):
                    print(f"  {i}. {profile}")
            else:
                print(f"\n{Colors.WARNING}⚠️  No saved profiles found{Colors.ENDC}")

        except Exception as e:
            print(f"{Colors.FAIL}❌ Error listing profiles: {e}{Colors.ENDC}")

        self.wait_for_enter()

    def delete_profile(self):
        """Delete configuration profile"""
        print(f"\n{Colors.HEADER}🗑️  Delete Configuration Profile{Colors.ENDC}")

        try:
            from pluto_utils import ConfigurationManager
            config_mgr = ConfigurationManager(self.pluto_manager)
            profiles = config_mgr.get_profile_list()

            if not profiles:
                print(f"{Colors.WARNING}⚠️  No saved profiles found{Colors.ENDC}")
                self.wait_for_enter()
                return

            print("\nAvailable profiles:")
            for i, profile in enumerate(profiles, 1):
                print(f"  {i}. {profile}")

            choice = self.get_user_input("Select profile to delete:")
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(profiles):
                    profile_name = profiles[idx]
                    confirm = self.get_user_input(f"Delete '{profile_name}'? (y/n):")
                    if confirm.lower() in ['y', 'yes']:
                        if config_mgr.delete_profile(profile_name):
                            print(f"{Colors.OKGREEN}✅ Profile '{profile_name}' deleted{Colors.ENDC}")
                        else:
                            print(f"{Colors.FAIL}❌ Failed to delete profile{Colors.ENDC}")
                else:
                    print(f"{Colors.FAIL}❌ Invalid selection{Colors.ENDC}")
            except ValueError:
                print(f"{Colors.FAIL}❌ Invalid selection{Colors.ENDC}")

        except Exception as e:
            print(f"{Colors.FAIL}❌ Delete error: {e}{Colors.ENDC}")

        self.wait_for_enter()

    def device_settings(self):
        """Configure basic device parameters"""
        print(f"\n{Colors.HEADER}⚙️  Device Settings{Colors.ENDC}")

        print("Current settings:")
        try:
            if hasattr(self.pluto_manager, 'sdr') and self.pluto_manager.sdr:
                print(f"  RX LO: {format_frequency(self.pluto_manager.sdr.rx_lo)}")
                print(f"  TX LO: {format_frequency(self.pluto_manager.sdr.tx_lo)}")
                print(f"  Sample Rate: {format_frequency(self.pluto_manager.sdr.sample_rate)}")
                print(f"  RX Gain: {self.pluto_manager.sdr.rx_hardwaregain_chan0} dB")
                print(f"  TX Gain: {self.pluto_manager.sdr.tx_hardwaregain_chan0} dB")
        except:
            print("  Settings not available")

        print("\nEnter new settings (press Enter to keep current):")

        rx_lo = self.get_user_input("RX LO frequency (MHz):")
        tx_lo = self.get_user_input("TX LO frequency (MHz):")
        sample_rate = self.get_user_input("Sample rate (MHz):")
        rx_gain = self.get_user_input("RX gain (dB):")
        tx_gain = self.get_user_input("TX gain (dB):")

        try:
            kwargs = {}
            if rx_lo:
                kwargs['rx_lo'] = int(float(rx_lo) * 1e6)
            if tx_lo:
                kwargs['tx_lo'] = int(float(tx_lo) * 1e6)
            if sample_rate:
                kwargs['sample_rate'] = int(float(sample_rate) * 1e6)
                kwargs['rx_bandwidth'] = kwargs['sample_rate']
                kwargs['tx_bandwidth'] = kwargs['sample_rate']
            if rx_gain:
                kwargs['rx_gain'] = int(float(rx_gain))
            if tx_gain:
                kwargs['tx_gain'] = int(float(tx_gain))

            if kwargs:
                if self.pluto_manager.configure_basic_settings(**kwargs):
                    print(f"{Colors.OKGREEN}✅ Settings updated successfully{Colors.ENDC}")
                else:
                    print(f"{Colors.FAIL}❌ Failed to update settings{Colors.ENDC}")
            else:
                print(f"{Colors.WARNING}⚠️  No changes made{Colors.ENDC}")

        except ValueError:
            print(f"{Colors.FAIL}❌ Invalid parameter values{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}❌ Settings error: {e}{Colors.ENDC}")

        self.wait_for_enter()

    # Testing Methods
    def run_integration_tests(self):
        """Run integration tests"""
        print(f"\n{Colors.HEADER}🧪 Integration Tests{Colors.ENDC}")

        test_mode = self.get_user_input("Test mode - with device (y) or without (n, default):")

        try:
            if test_mode.lower() in ['y', 'yes']:
                subprocess.run([sys.executable, "test_integration.py", "--verbose"])
            else:
                subprocess.run([sys.executable, "test_integration.py", "--no-device", "--verbose"])

            print(f"{Colors.OKGREEN}✅ Integration tests completed{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}❌ Test execution error: {e}{Colors.ENDC}")

        self.wait_for_enter()

    def run_feature_demo(self):
        """Run feature demonstration"""
        print(f"\n{Colors.HEADER}🎭 Feature Demo{Colors.ENDC}")

        demo_mode = self.get_user_input("Demo mode - interactive (i) or automatic (a, default):")

        try:
            if demo_mode.lower() in ['i', 'interactive']:
                subprocess.run([sys.executable, "demo_all_features.py", "--interactive"])
            else:
                subprocess.run([sys.executable, "demo_all_features.py"])

            print(f"{Colors.OKGREEN}✅ Feature demo completed{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}❌ Demo execution error: {e}{Colors.ENDC}")

        self.wait_for_enter()

    def system_check(self):
        """Check system requirements"""
        print(f"\n{Colors.HEADER}🔍 System Check{Colors.ENDC}")
        self.check_requirements()
        self.wait_for_enter()

    def performance_benchmark(self):
        """Benchmark system performance"""
        print(f"\n{Colors.HEADER}📊 Performance Benchmark{Colors.ENDC}")

        if not self.pluto_manager or not self.pluto_manager.is_connected:
            print(f"{Colors.WARNING}⚠️  Device required for performance benchmark{Colors.ENDC}")
            self.wait_for_enter()
            return

        print("Running performance benchmark...")

        try:
            import time
            import numpy as np

            # Test sample acquisition speed
            print("📊 Testing sample acquisition...")
            start_time = time.time()
            for i in range(10):
                samples = self.pluto_manager.sdr.rx()
                print(f"  Sample {i+1}/10: {len(samples)} samples")
            acquisition_time = time.time() - start_time

            # Test FFT performance
            print("📊 Testing FFT performance...")
            start_time = time.time()
            for i in range(10):
                from pluto_utils import calculate_fft_spectrum
                freqs, spectrum = calculate_fft_spectrum(samples, 3000000)
            fft_time = time.time() - start_time

            print(f"\n{Colors.OKGREEN}📊 Benchmark Results:{Colors.ENDC}")
            print(f"  Sample Acquisition: {acquisition_time:.2f}s for 10 acquisitions")
            print(f"  FFT Processing: {fft_time:.2f}s for 10 FFTs")
            print(f"  Samples per second: {len(samples) * 10 / acquisition_time:.0f}")
            print(f"  FFTs per second: {10 / fft_time:.1f}")

        except Exception as e:
            print(f"{Colors.FAIL}❌ Benchmark error: {e}{Colors.ENDC}")

        self.wait_for_enter()

    # Help Methods
    def show_user_guide(self):
        """Show comprehensive user guide"""
        print(f"\n{Colors.HEADER}📖 Enhanced ADALM-Pluto SDR User Guide{Colors.ENDC}")

        guide = f"""
{Colors.BOLD}OVERVIEW{Colors.ENDC}
This enhanced toolkit integrates features from multiple repositories:
• ADALM-Pluto-Spectrum-Analyzer (original spectrum analysis)
• plutosdr_scripts (ADI device utilities and calibration)
• plutosdr-fw (ADI firmware integration and configuration)
• waterfall display (inspired by Stvff/waterfall)

{Colors.BOLD}GETTING STARTED{Colors.ENDC}
1. Connect your PlutoSDR via USB or network
2. Use Device Management → Discover Devices to find your device
3. Connect to the device using Device Management → Connect to Device
4. Explore the various tools and features available

{Colors.BOLD}MAIN FEATURES{Colors.ENDC}
• Device Management: Discovery, connection, monitoring
• Spectrum Analysis: GUI and command-line spectrum analysis
• Signal Generation: Sine waves, chirps, DDS tones
• Calibration: Device calibration and diagnostics
• Waterfall Display: Real-time spectrum visualization
• Configuration: Save/load device settings

{Colors.BOLD}APPLICATIONS{Colors.ENDC}
• GUI Applications: enhanced_spectrum_analyzer.py, waterfall_app.py
• Command Line: This menu system (pluto_menu.py)
• Testing: test_integration.py, demo_all_features.py

{Colors.BOLD}KEYBOARD SHORTCUTS (GUI){Colors.ENDC}
• Arrow keys: Frequency/bandwidth control in waterfall
• Space: Pause/resume acquisition
• C: Clear display
• M: Mark peaks

{Colors.BOLD}TROUBLESHOOTING{Colors.ENDC}
• Device not found: Check USB connection, try different ports
• Permission issues: Add user to plugdev group (Linux)
• GUI issues: Install PyQt6 and pyqtgraph
• Performance: Close other applications using the device
        """

        print(guide)
        self.wait_for_enter()

    def show_quick_start(self):
        """Show quick start tutorial"""
        print(f"\n{Colors.HEADER}🚀 Quick Start Tutorial{Colors.ENDC}")

        tutorial = f"""
{Colors.BOLD}QUICK START - 5 MINUTES TO SUCCESS{Colors.ENDC}

{Colors.OKGREEN}Step 1: Connect Your PlutoSDR{Colors.ENDC}
• Connect via USB cable or network
• Power on the device
• Wait for system recognition

{Colors.OKGREEN}Step 2: Discover and Connect{Colors.ENDC}
• From main menu: 1 → 1 (Device Management → Discover Devices)
• From main menu: 1 → 2 (Device Management → Connect to Device)
• Choose option 1 for auto-discovery

{Colors.OKGREEN}Step 3: Verify Connection{Colors.ENDC}
• From main menu: 1 → 3 (Device Management → Device Information)
• Check temperatures and device details

{Colors.OKGREEN}Step 4: Try Spectrum Analysis{Colors.ENDC}
• From main menu: 2 → 1 (Launch GUI Spectrum Analyzer)
• Or try: 2 → 2 (Quick Spectrum Scan)

{Colors.OKGREEN}Step 5: Explore Waterfall Display{Colors.ENDC}
• From main menu: 5 → 2 (Standalone Waterfall)
• Use arrow keys to change frequency/bandwidth

{Colors.BOLD}NEXT STEPS{Colors.ENDC}
• Try signal generation (menu 3)
• Run calibration (menu 4)
• Save your configuration (menu 6)
• Explore help and documentation (menu 8)
        """

        print(tutorial)
        self.wait_for_enter()

    def show_shortcuts(self):
        """Show keyboard shortcuts"""
        print(f"\n{Colors.HEADER}⌨️  Keyboard Shortcuts{Colors.ENDC}")

        shortcuts = f"""
{Colors.BOLD}TERMINAL MENU SHORTCUTS{Colors.ENDC}
• Numbers 1-8: Navigate to main menu sections
• 'b': Back to main menu (from submenus)
• 'q': Quit application
• Ctrl+C: Cancel current operation

{Colors.BOLD}GUI SPECTRUM ANALYZER{Colors.ENDC}
• Mouse click: Add frequency markers
• Drag markers: Move measurement points
• Pause button: Stop/resume sweep
• Clear button: Remove all markers

{Colors.BOLD}WATERFALL DISPLAY{Colors.ENDC}
• ↑/↓ Arrow Keys: Frequency ±100 MHz (Shift: ±10 MHz)
• ←/→ Arrow Keys: Sample rate ±10 MHz (Shift: ±1 MHz)
• Space: Pause/Resume acquisition
• C: Clear display and peak hold
• M: Mark highest peak
• F1: Help (standalone app)
• F11: Fullscreen toggle
• Ctrl+Q: Quit application

{Colors.BOLD}SIGNAL GENERATION{Colors.ENDC}
• Configure parameters via menu prompts
• Use loopback mode for testing
• Stop transmission when done

{Colors.BOLD}DEVICE MANAGEMENT{Colors.ENDC}
• Auto-discovery finds devices automatically
• Manual connection for specific URIs
• Temperature monitoring with Ctrl+C to stop
        """

        print(shortcuts)
        self.wait_for_enter()

    def show_projects(self):
        """Show information about integrated projects"""
        print(f"\n{Colors.HEADER}🔗 Integrated Projects{Colors.ENDC}")

        projects = f"""
{Colors.BOLD}INTEGRATED REPOSITORIES{Colors.ENDC}

{Colors.OKGREEN}1. ADALM-Pluto-Spectrum-Analyzer (Original){Colors.ENDC}
• Repository: github.com/fromconcepttocircuit/ADALM-Pluto-Spectrum-Analyzer
• Features: Basic spectrum analysis, GUI interface
• Integration: Base platform and spectrum analysis core

{Colors.OKGREEN}2. plutosdr_scripts (Analog Devices){Colors.ENDC}
• Repository: github.com/analogdevicesinc/plutosdr_scripts
• Features: Device utilities, calibration, signal generation
• Integration: Device management, temperature monitoring, calibration

{Colors.OKGREEN}3. plutosdr-fw (Analog Devices){Colors.ENDC}
• Repository: github.com/analogdevicesinc/plutosdr-fw
• Features: Firmware tools, configuration management
• Integration: Device discovery, configuration profiles

{Colors.OKGREEN}4. waterfall (Stvff - Inspired){Colors.ENDC}
• Repository: github.com/Stvff/waterfall
• Features: Real-time waterfall spectrum display
• Integration: Python implementation with PyQt6/PyQtGraph

{Colors.BOLD}ADDITIONAL DEPENDENCIES{Colors.ENDC}
• pyadi-iio: Python interface for PlutoSDR
• PyQt6: GUI framework
• PyQtGraph: Real-time plotting
• NumPy/SciPy: Scientific computing
• libiio: Industrial I/O library

{Colors.BOLD}LICENSE COMPATIBILITY{Colors.ENDC}
• Enhanced version: GPL-2 (compatible with all sources)
• Original components maintain their respective licenses
• Open source and freely redistributable
        """

        print(projects)
        self.wait_for_enter()

    def show_faq(self):
        """Show frequently asked questions"""
        print(f"\n{Colors.HEADER}❓ Frequently Asked Questions{Colors.ENDC}")

        faq = f"""
{Colors.BOLD}FREQUENTLY ASKED QUESTIONS{Colors.ENDC}

{Colors.OKGREEN}Q: My PlutoSDR is not detected. What should I do?{Colors.ENDC}
A: 1. Check USB cable and connection
   2. Try different USB ports
   3. Ensure device is powered on
   4. Check if another application is using the device
   5. Try IP connection if USB fails

{Colors.OKGREEN}Q: I get permission errors on Linux. How to fix?{Colors.ENDC}
A: 1. Add your user to the plugdev group:
      sudo usermod -a -G plugdev $USER
   2. Install udev rules for PlutoSDR
   3. Log out and log back in

{Colors.OKGREEN}Q: The GUI applications don't start. What's wrong?{Colors.ENDC}
A: 1. Install required packages: pip install PyQt6 pyqtgraph
   2. Check if X11 forwarding is enabled (SSH)
   3. Try running from terminal to see error messages

{Colors.OKGREEN}Q: Waterfall display is slow or choppy. How to improve?{Colors.ENDC}
A: 1. Reduce FFT size (512 or 256)
   2. Increase update interval (100ms)
   3. Close other applications
   4. Use lower sample rates

{Colors.OKGREEN}Q: Signal generation doesn't work. What to check?{Colors.ENDC}
A: 1. Ensure device is properly connected
   2. Check TX gain settings (not too low)
   3. Verify antenna connections
   4. Try loopback mode for testing

{Colors.OKGREEN}Q: Calibration fails. What could be wrong?{Colors.ENDC}
A: 1. Ensure stable temperature
   2. Check for interference
   3. Try different sample rates
   4. Restart the device

{Colors.OKGREEN}Q: How do I update the enhanced toolkit?{Colors.ENDC}
A: 1. Download latest version from repository
   2. Backup your configuration profiles
   3. Replace files and reinstall dependencies
   4. Restore configuration profiles
        """

        print(faq)
        self.wait_for_enter()

    def show_troubleshooting(self):
        """Show troubleshooting guide"""
        print(f"\n{Colors.HEADER}🐛 Troubleshooting Guide{Colors.ENDC}")

        troubleshooting = f"""
{Colors.BOLD}TROUBLESHOOTING GUIDE{Colors.ENDC}

{Colors.FAIL}PROBLEM: Device not found{Colors.ENDC}
{Colors.OKGREEN}SOLUTIONS:{Colors.ENDC}
• Check physical connections (USB cable, power)
• Try different USB ports or cables
• Restart the PlutoSDR device
• Check if device appears in system (lsusb on Linux)
• Try IP connection: ping 192.168.2.1

{Colors.FAIL}PROBLEM: Connection timeout{Colors.ENDC}
{Colors.OKGREEN}SOLUTIONS:{Colors.ENDC}
• Close other applications using the device
• Restart the device and try again
• Check network settings for IP connections
• Try USB connection instead of network

{Colors.FAIL}PROBLEM: Poor performance{Colors.ENDC}
{Colors.OKGREEN}SOLUTIONS:{Colors.ENDC}
• Close unnecessary applications
• Reduce sample rates and FFT sizes
• Check system resources (CPU, memory)
• Use wired connection instead of WiFi

{Colors.FAIL}PROBLEM: GUI crashes{Colors.ENDC}
{Colors.OKGREEN}SOLUTIONS:{Colors.ENDC}
• Update PyQt6 and pyqtgraph
• Check graphics drivers
• Run from terminal to see error messages
• Try different display settings

{Colors.FAIL}PROBLEM: Inaccurate measurements{Colors.ENDC}
{Colors.OKGREEN}SOLUTIONS:{Colors.ENDC}
• Run device calibration
• Check antenna connections
• Verify frequency settings
• Allow device to warm up
• Check for interference

{Colors.FAIL}PROBLEM: High temperatures{Colors.ENDC}
{Colors.OKGREEN}SOLUTIONS:{Colors.ENDC}
• Improve ventilation around device
• Reduce TX power
• Take breaks between measurements
• Check ambient temperature

{Colors.BOLD}GETTING HELP{Colors.ENDC}
• Check documentation and examples
• Run integration tests for diagnostics
• Report issues with detailed error messages
• Include system information and device details
        """

        print(troubleshooting)
        self.wait_for_enter()


def main():
    """Main entry point for the terminal menu system"""
    try:
        menu_system = PlutoMenuSystem()
        menu_system.run()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Menu system interrupted by user.{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ Menu system error: {e}{Colors.ENDC}")
    finally:
        print(f"{Colors.OKGREEN}Goodbye!{Colors.ENDC}")


if __name__ == "__main__":
    main()
