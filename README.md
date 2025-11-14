
# ADALM-Pluto Spectrum Analyzer

**Professional spectrum analysis and RF monitoring toolkit for ADALM-Pluto SDR**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-GPL--2-green.svg)](LICENSE)
[![SDR](https://img.shields.io/badge/SDR-ADALM--Pluto-orange.svg)](https://www.analog.com/en/design-center/evaluation-hardware-and-software/evaluation-boards-kits/adalm-pluto.html)

## 🚀 Features

- **Real-time Spectrum Analysis** - Professional frequency domain visualization
- **Waterfall Display** - Time-frequency analysis with configurable parameters
- **Signal Monitoring** - Continuous RF environment monitoring and logging
- **Interactive Menu System** - Terminal-based interface for all tools
- **Device Management** - Comprehensive ADALM-Pluto configuration and control
- **Data Export** - Multiple formats for external analysis
- **Desktop Integration** - Native desktop launcher with icon
- **Calibration Tools** - Built-in calibration and diagnostics

## 📋 Quick Start

### Prerequisites
- Python 3.8 or higher
- ADALM-Pluto SDR device
- Linux/Windows/macOS compatible

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ro0TuX777/ADAML-Pluto.git
   cd ADAML-Pluto
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements_enhanced.txt
   ```

3. **Connect your ADALM-Pluto SDR:**
   - USB connection (default IP: 192.168.2.1)
   - Network connection (configure IP as needed)

4. **Launch the application:**
   ```bash
   python pluto_menu.py
   ```

### Desktop Integration

Create a desktop icon for easy access:
```bash
./create-desktop-icon.sh
```

## 🔧 Core Applications

### Spectrum Analyzer (`enhanced_spectrum_analyzer.py`)
Professional frequency domain analysis with advanced features:
- Real-time spectrum sweeping across configurable frequency ranges
- Peak detection and tracking with automatic signal identification
- Threshold-based alerting for signal monitoring applications
- Draggable markers for precise frequency measurement
- Band highlighting for Wi-Fi, LTE, GSM, Bluetooth identification
- Export capabilities for data analysis and reporting

### Waterfall Display (`waterfall_display.py`)
Time-frequency visualization for signal pattern analysis:
- Continuous time-frequency mapping showing signal evolution
- Color-coded power levels for easy signal identification
- Configurable time windows from seconds to hours
- Real-time updates with smooth scrolling display
- Signal persistence tracking for intermittent signal detection

### Real-Time Visualizer (`realtime_visualizer.py`)
Dynamic signal monitoring with live updates:
- Continuous spectrum updates with sub-second refresh rates
- Multi-panel display showing spectrum, time domain, and constellation
- Automatic scaling for optimal signal visualization
- Signal quality metrics including SNR and RMS calculations
- Terminal-based operation for SSH and headless systems

### Interactive Menu (`pluto_menu.py`)
Unified control interface for all applications:
- Application launcher with guided setup
- Device configuration with automatic PlutoSDR detection
- Settings management for frequency, gain, and sample rate
- Session management with automatic logging and recovery

## 🔧 Configuration

### Device Connection
The application automatically detects ADALM-Pluto SDR at:
- **USB Mode**: `192.168.2.1` (default)
- **Network Mode**: Configure IP address in settings

### Frequency Ranges
- **70 MHz - 6 GHz**: Full PlutoSDR range
- **Common Bands**: Wi-Fi (2.4/5 GHz), LTE, GSM, ISM
- **Custom Ranges**: User-configurable start/stop frequencies

### Sample Rates
- **61.44 kSPS - 61.44 MSPS**: Hardware-supported range
- **Automatic Optimization**: Based on frequency span and resolution requirements

## 📖 Documentation

- **Desktop Integration**: [Desktop Icon Guide](DESKTOP_ICON_CREATION_GUIDE.md)
- **Quick Reference**: [Desktop Icon Quick Reference](DESKTOP_ICON_QUICK_REFERENCE.md)
- **Implementation Details**: [Desktop Icon Implementation](DESKTOP_ICON_IMPLEMENTATION_SUMMARY.md)

## 🎯 Use Cases

### RF Environment Analysis
- Wi-Fi network planning and interference detection
- Cellular signal mapping and coverage analysis
- Spectrum occupancy studies for regulatory compliance
- EMI/EMC testing and troubleshooting

### Signal Intelligence
- Unknown signal detection and characterization
- Protocol analysis and reverse engineering
- Security monitoring for unauthorized transmissions
- Research and development support

### Educational Applications
- RF engineering education with hands-on learning
- Signal processing demonstrations with real data
- Wireless communication principles visualization
- Laboratory exercises and student projects

## 📋 Technical Specifications

### Hardware Requirements
- **ADALM-Pluto SDR**: USB or Ethernet connectivity
- **Frequency Range**: 70 MHz to 6 GHz
- **Sample Rate**: 61.44 kSPS to 61.44 MSPS
- **Resolution**: 12-bit ADC

### Software Requirements
- **Python**: 3.8 or higher
- **Operating System**: Linux, Windows, macOS
- **Memory**: Minimum 4GB RAM recommended
- **Dependencies**: See `requirements_enhanced.txt`

## 🤝 Contributing

Contributions and improvements are welcome! Please feel free to:
- Report bugs and issues
- Suggest new features
- Submit pull requests
- Improve documentation

## 📄 License

This project is licensed under the GPL-2 License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Analog Devices**: For the ADALM-Pluto SDR platform
- **PyADI-IIO**: Python bindings for ADI hardware
- **Open Source Community**: For the excellent Python ecosystem

## 📞 Support

For questions, issues, or contributions:
- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Documentation**: Check the included guides and documentation files
- **Community**: Join the SDR and RF engineering communities

---

**Professional SDR Analysis Tools - Ready for Research, Education, and Development**
