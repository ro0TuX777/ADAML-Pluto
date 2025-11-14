#!/usr/bin/env python3
"""
Enhanced PlutoSDR Utility Library

This module provides comprehensive utilities for ADALM-Pluto SDR operations,
integrating features from the official plutosdr_scripts and plutosdr-fw repositories.

Features:
- Device discovery and connection management
- Temperature monitoring and diagnostics
- Calibration routines
- Signal generation and analysis
- Configuration management
- Power measurement utilities

Author: Enhanced integration from multiple ADI sources
License: GPL-2 (compatible with original ADI scripts)
"""

import sys
import time
import subprocess
import numpy as np
import logging
from typing import Optional, Dict, List, Tuple, Union
from dataclasses import dataclass
from enum import Enum

try:
    import iio
except ImportError:
    # Fallback path for iio python bindings
    sys.path.append('/usr/lib/python2.7/site-packages/')
    try:
        import iio
    except ImportError:
        print("Warning: libiio python bindings not found. Some features may not work.")
        iio = None

try:
    import adi
except ImportError:
    print("Warning: pyadi-iio not found. Install with: pip install pyadi-iio")
    adi = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConnectionType(Enum):
    """Supported connection types for PlutoSDR"""
    USB = "usb"
    IP = "ip"
    ZEROCONF = "zeroconf"
    AUTO = "auto"


@dataclass
class PlutoDeviceInfo:
    """Information about a discovered PlutoSDR device"""
    uri: str
    connection_type: ConnectionType
    ip_address: Optional[str] = None
    serial_number: Optional[str] = None
    firmware_version: Optional[str] = None
    temperature_ad9361: Optional[float] = None
    temperature_zynq: Optional[float] = None


@dataclass
class CalibrationResult:
    """Results from AD9361 calibration"""
    success: bool
    rx_lo_freq: float
    tx_lo_freq: float
    sample_rate: float
    rx_gain: float
    tx_gain: float
    dc_offset_i: float
    dc_offset_q: float
    iq_imbalance: float
    phase_correction: float
    timestamp: float


class PlutoSDRManager:
    """
    Comprehensive PlutoSDR device manager with enhanced capabilities
    """
    
    def __init__(self, uri: Optional[str] = None, auto_discover: bool = True):
        """
        Initialize PlutoSDR manager
        
        Args:
            uri: Specific URI to connect to, or None for auto-discovery
            auto_discover: Whether to attempt automatic device discovery
        """
        self.uri = uri
        self.ctx = None
        self.ctrl_device = None
        self.tx_device = None
        self.rx_device = None
        self.sdr = None
        self.device_info = None
        self.is_connected = False
        
        if auto_discover and not uri:
            discovered = self.discover_devices()
            if discovered:
                self.uri = discovered[0].uri
                self.device_info = discovered[0]
        
        if self.uri:
            self.connect()
    
    def discover_devices(self) -> List[PlutoDeviceInfo]:
        """
        Discover available PlutoSDR devices using multiple methods
        
        Returns:
            List of discovered PlutoDeviceInfo objects
        """
        devices = []
        
        # Method 1: Try USB discovery
        try:
            result = subprocess.run(['iio_info', '-s'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'PLUTO' in line and 'usb:' in line:
                        # Extract USB URI
                        parts = line.split()
                        for part in parts:
                            if part.startswith('[usb:') and part.endswith(']'):
                                usb_uri = part[1:-1]  # Remove brackets
                                devices.append(PlutoDeviceInfo(
                                    uri=usb_uri,
                                    connection_type=ConnectionType.USB
                                ))
                                logger.info(f"Found USB PlutoSDR: {usb_uri}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.debug("USB discovery failed or iio_info not available")
        
        # Method 2: Try default IP
        default_ips = ['192.168.2.1', '192.168.1.10']
        for ip in default_ips:
            try:
                test_uri = f'ip:{ip}'
                if iio:
                    test_ctx = iio.Context(test_uri)
                    if test_ctx:
                        devices.append(PlutoDeviceInfo(
                            uri=test_uri,
                            connection_type=ConnectionType.IP,
                            ip_address=ip
                        ))
                        logger.info(f"Found IP PlutoSDR: {test_uri}")
                        test_ctx = None  # Clean up
                        break
            except:
                continue
        
        # Method 3: Try zeroconf/avahi discovery
        try:
            result = subprocess.run(['avahi-resolve', '--name', 'pluto.local'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                ip = result.stdout.split()[-1].strip()
                zeroconf_uri = f'ip:{ip}'
                devices.append(PlutoDeviceInfo(
                    uri=zeroconf_uri,
                    connection_type=ConnectionType.ZEROCONF,
                    ip_address=ip
                ))
                logger.info(f"Found Zeroconf PlutoSDR: {zeroconf_uri}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.debug("Zeroconf discovery failed or avahi-resolve not available")
        
        return devices
    
    def connect(self) -> bool:
        """
        Connect to PlutoSDR device
        
        Returns:
            True if connection successful, False otherwise
        """
        if not self.uri:
            logger.error("No URI specified for connection")
            return False
        
        try:
            # Connect using libiio
            if iio:
                self.ctx = iio.Context(self.uri)
                self.ctrl_device = self.ctx.find_device("ad9361-phy")
                self.tx_device = self.ctx.find_device("cf-ad9361-dds-core-lpc")
                self.rx_device = self.ctx.find_device("cf-ad9361-lpc")
            
            # Connect using pyadi-iio
            if adi:
                self.sdr = adi.ad9361(uri=self.uri)
            
            self.is_connected = True
            logger.info(f"Successfully connected to PlutoSDR at {self.uri}")
            
            # Get device information
            self._update_device_info()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to PlutoSDR at {self.uri}: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Disconnect from PlutoSDR device"""
        try:
            if self.sdr and hasattr(self.sdr, 'rx_destroy_buffer'):
                self.sdr.rx_destroy_buffer()
        except:
            pass
        
        self.ctx = None
        self.ctrl_device = None
        self.tx_device = None
        self.rx_device = None
        self.sdr = None
        self.is_connected = False
        logger.info("Disconnected from PlutoSDR")

    def _update_device_info(self):
        """Update device information from connected device"""
        if not self.is_connected:
            return

        try:
            if not self.device_info:
                self.device_info = PlutoDeviceInfo(
                    uri=self.uri,
                    connection_type=ConnectionType.AUTO
                )

            # Get temperatures
            temps = self.get_temperatures()
            if temps:
                self.device_info.temperature_ad9361 = temps.get('ad9361')
                self.device_info.temperature_zynq = temps.get('zynq')

            # Get firmware version and other info if available
            if self.ctx:
                try:
                    # Try to get device attributes
                    attrs = self.ctx.attrs
                    for attr_name in attrs:
                        if 'fw_version' in attr_name.lower():
                            self.device_info.firmware_version = attrs[attr_name].value
                        elif 'serial' in attr_name.lower():
                            self.device_info.serial_number = attrs[attr_name].value
                except:
                    pass

        except Exception as e:
            logger.debug(f"Could not update device info: {e}")

    def get_temperatures(self) -> Optional[Dict[str, float]]:
        """
        Get device temperatures (AD9361 and Zynq)

        Returns:
            Dictionary with temperature readings in Celsius, or None if failed
        """
        if not self.is_connected or not self.ctx:
            return None

        temps = {}

        try:
            # AD9361 temperature
            if self.ctrl_device:
                temp_channel = self.ctrl_device.find_channel("temp0", False)
                if temp_channel:
                    temp_raw = int(temp_channel.attrs["input"].value)
                    temps['ad9361'] = temp_raw / 1000.0  # Convert milli-Celsius to Celsius
        except Exception as e:
            logger.debug(f"Could not read AD9361 temperature: {e}")

        try:
            # Zynq temperature via XADC
            xadc_device = self.ctx.find_device("xadc")
            if xadc_device:
                temp_channel = xadc_device.find_channel("temp0", False)
                if temp_channel:
                    raw = int(temp_channel.attrs["raw"].value)
                    offset = int(temp_channel.attrs["offset"].value)
                    scale = float(temp_channel.attrs["scale"].value)
                    temps['zynq'] = (raw + offset) * scale / 1000.0
        except Exception as e:
            logger.debug(f"Could not read Zynq temperature: {e}")

        return temps if temps else None

    def monitor_temperatures(self, duration: int = 60, interval: int = 1) -> List[Dict]:
        """
        Monitor temperatures over time

        Args:
            duration: Total monitoring duration in seconds
            interval: Measurement interval in seconds

        Returns:
            List of temperature readings with timestamps
        """
        readings = []
        start_time = time.time()

        while time.time() - start_time < duration:
            temps = self.get_temperatures()
            if temps:
                reading = {
                    'timestamp': time.time(),
                    'elapsed': time.time() - start_time,
                    **temps
                }
                readings.append(reading)
                logger.info(f"Temps - AD9361: {temps.get('ad9361', 'N/A'):.1f}°C, "
                           f"Zynq: {temps.get('zynq', 'N/A'):.1f}°C")

            time.sleep(interval)

        return readings

    def set_loopback_mode(self, enable: bool = True) -> bool:
        """
        Enable or disable digital loopback mode

        Args:
            enable: True to enable loopback, False to disable

        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected or not self.ctrl_device:
            return False

        try:
            loopback_attr = self.ctrl_device.debug_attrs.get('loopback')
            if loopback_attr:
                loopback_attr.value = '1' if enable else '0'
                logger.info(f"Digital loopback {'enabled' if enable else 'disabled'}")
                return True
        except Exception as e:
            logger.error(f"Failed to set loopback mode: {e}")

        return False

    def configure_basic_settings(self,
                                rx_lo: int = 2400000000,
                                tx_lo: int = 2400000000,
                                sample_rate: int = 3000000,
                                rx_bandwidth: int = 5000000,
                                tx_bandwidth: int = 5000000,
                                rx_gain: int = 60,
                                tx_gain: int = -30) -> bool:
        """
        Configure basic SDR settings

        Args:
            rx_lo: RX LO frequency in Hz
            tx_lo: TX LO frequency in Hz
            sample_rate: Sample rate in Hz
            rx_bandwidth: RX RF bandwidth in Hz
            tx_bandwidth: TX RF bandwidth in Hz
            rx_gain: RX hardware gain in dB
            tx_gain: TX hardware gain in dB

        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected:
            return False

        try:
            # Configure using pyadi-iio if available
            if self.sdr:
                self.sdr.rx_lo = rx_lo
                self.sdr.tx_lo = tx_lo
                self.sdr.sample_rate = sample_rate
                self.sdr.rx_rf_bandwidth = rx_bandwidth
                self.sdr.tx_rf_bandwidth = tx_bandwidth
                self.sdr.rx_hardwaregain_chan0 = rx_gain
                self.sdr.tx_hardwaregain_chan0 = tx_gain

                logger.info(f"Configured SDR: RX_LO={rx_lo/1e6:.1f}MHz, "
                           f"TX_LO={tx_lo/1e6:.1f}MHz, SR={sample_rate/1e6:.1f}MHz")
                return True

            # Fallback to libiio configuration
            elif self.ctrl_device:
                # Set LO frequencies
                rx_lo_ch = self.ctrl_device.find_channel("altvoltage0", True)
                tx_lo_ch = self.ctrl_device.find_channel("altvoltage1", True)
                if rx_lo_ch:
                    rx_lo_ch.attrs["frequency"].value = str(rx_lo)
                if tx_lo_ch:
                    tx_lo_ch.attrs["frequency"].value = str(tx_lo)

                # Set other parameters
                rx_ch = self.ctrl_device.find_channel("voltage0", False)
                tx_ch = self.ctrl_device.find_channel("voltage0", True)

                if rx_ch:
                    rx_ch.attrs["rf_bandwidth"].value = str(rx_bandwidth)
                    rx_ch.attrs["sampling_frequency"].value = str(sample_rate)
                    rx_ch.attrs["hardwaregain"].value = str(rx_gain)

                if tx_ch:
                    tx_ch.attrs["rf_bandwidth"].value = str(tx_bandwidth)
                    tx_ch.attrs["sampling_frequency"].value = str(sample_rate)
                    tx_ch.attrs["hardwaregain"].value = str(tx_gain)

                logger.info("Configured SDR using libiio")
                return True

        except Exception as e:
            logger.error(f"Failed to configure SDR settings: {e}")

        return False


class SignalGenerator:
    """
    Signal generation utilities for PlutoSDR
    """

    def __init__(self, pluto_manager: PlutoSDRManager):
        """
        Initialize signal generator

        Args:
            pluto_manager: Connected PlutoSDRManager instance
        """
        self.pluto = pluto_manager
        self.tx_buffer = None
        self.is_transmitting = False

    def generate_sine_wave(self,
                          frequency: float,
                          amplitude: float = 0.9,
                          sample_rate: int = 3000000,
                          duration: float = 1.0) -> np.ndarray:
        """
        Generate a sine wave signal

        Args:
            frequency: Signal frequency in Hz
            amplitude: Signal amplitude (0.0 to 1.0)
            sample_rate: Sample rate in Hz
            duration: Signal duration in seconds

        Returns:
            Complex IQ samples
        """
        num_samples = int(sample_rate * duration)
        t = np.arange(num_samples) / sample_rate

        # Generate complex sine wave
        i_signal = amplitude * np.sin(2 * np.pi * frequency * t)
        q_signal = amplitude * np.cos(2 * np.pi * frequency * t)

        # Convert to complex samples
        iq_samples = i_signal + 1j * q_signal

        return iq_samples

    def generate_triangle_wave(self,
                              sample_rate: int = 3000000,
                              num_samples: int = 2048) -> np.ndarray:
        """
        Generate a triangle wave (useful for testing)

        Args:
            sample_rate: Sample rate in Hz
            num_samples: Number of samples to generate

        Returns:
            Complex IQ samples
        """
        # Create triangle wave
        half_samples = num_samples // 2
        ramp_up = np.arange(half_samples, dtype=np.int16)
        ramp_down = ramp_up[::-1]
        triangle = np.concatenate((ramp_up, ramp_down))

        # Scale and shift to prevent clipping
        triangle = triangle << 4

        # Create complex samples (I and Q identical for simplicity)
        iq_samples = triangle + 1j * triangle

        return iq_samples.astype(np.complex64)

    def generate_chirp(self,
                      start_freq: float,
                      end_freq: float,
                      duration: float = 1.0,
                      sample_rate: int = 3000000,
                      amplitude: float = 0.9) -> np.ndarray:
        """
        Generate a frequency chirp signal

        Args:
            start_freq: Starting frequency in Hz
            end_freq: Ending frequency in Hz
            duration: Signal duration in seconds
            sample_rate: Sample rate in Hz
            amplitude: Signal amplitude (0.0 to 1.0)

        Returns:
            Complex IQ samples
        """
        num_samples = int(sample_rate * duration)
        t = np.arange(num_samples) / sample_rate

        # Linear frequency sweep
        freq_sweep = start_freq + (end_freq - start_freq) * t / duration
        phase = 2 * np.pi * np.cumsum(freq_sweep) / sample_rate

        # Generate complex chirp
        i_signal = amplitude * np.cos(phase)
        q_signal = amplitude * np.sin(phase)

        iq_samples = i_signal + 1j * q_signal

        return iq_samples.astype(np.complex64)

    def transmit_signal(self, iq_samples: np.ndarray, cyclic: bool = True) -> bool:
        """
        Transmit IQ samples

        Args:
            iq_samples: Complex IQ samples to transmit
            cyclic: Whether to transmit cyclically

        Returns:
            True if successful, False otherwise
        """
        if not self.pluto.is_connected or not self.pluto.tx_device:
            logger.error("PlutoSDR not connected or TX device not available")
            return False

        try:
            # Enable TX channels
            tx_i = self.pluto.tx_device.find_channel("voltage0", True)
            tx_q = self.pluto.tx_device.find_channel("voltage1", True)

            if tx_i and tx_q:
                tx_i.enabled = True
                tx_q.enabled = True

            # Disable DDS to use DMA
            if self.pluto.tx_device:
                dds_channels = ['TX1_I_F1', 'TX1_Q_F1', 'TX1_I_F2', 'TX1_Q_F2']
                for ch_name in dds_channels:
                    try:
                        ch = self.pluto.tx_device.find_channel(ch_name, True)
                        if ch:
                            ch.attrs['raw'].value = '0'
                    except:
                        pass

            # Convert complex samples to interleaved I/Q
            samples_per_channel = len(iq_samples)
            iq_interleaved = np.empty(samples_per_channel * 2, dtype=np.int16)

            # Scale to 16-bit range
            scale_factor = 2**14  # Leave some headroom
            i_scaled = (np.real(iq_samples) * scale_factor).astype(np.int16)
            q_scaled = (np.imag(iq_samples) * scale_factor).astype(np.int16)

            iq_interleaved[0::2] = i_scaled
            iq_interleaved[1::2] = q_scaled

            # Create TX buffer
            if iio:
                self.tx_buffer = iio.Buffer(self.pluto.tx_device, samples_per_channel, cyclic)
                self.tx_buffer.write(bytearray(iq_interleaved))
                self.tx_buffer.push()

                self.is_transmitting = True
                logger.info(f"Started transmitting {samples_per_channel} samples")
                return True

        except Exception as e:
            logger.error(f"Failed to transmit signal: {e}")

        return False

    def stop_transmission(self):
        """Stop signal transmission"""
        try:
            if self.tx_buffer:
                self.tx_buffer.cancel()
                self.tx_buffer = None
            self.is_transmitting = False
            logger.info("Stopped transmission")
        except Exception as e:
            logger.error(f"Error stopping transmission: {e}")

    def configure_dds_tone(self,
                          frequency: float = 100000,
                          amplitude: float = 0.9,
                          phase: float = 0) -> bool:
        """
        Configure DDS to generate a single tone

        Args:
            frequency: Tone frequency in Hz
            amplitude: Tone amplitude (0.0 to 1.0)
            phase: Phase in degrees

        Returns:
            True if successful, False otherwise
        """
        if not self.pluto.is_connected or not self.pluto.tx_device:
            return False

        try:
            # Configure DDS channels
            dds0 = self.pluto.tx_device.find_channel('altvoltage0', True)  # I channel
            dds2 = self.pluto.tx_device.find_channel('altvoltage2', True)  # Q channel

            if dds0 and dds2:
                # I channel (with phase offset)
                dds0.attrs['raw'].value = '1'  # Enable
                dds0.attrs['frequency'].value = str(int(frequency))
                dds0.attrs['scale'].value = str(amplitude)
                dds0.attrs['phase'].value = str(int(phase * 1000))  # Phase in milli-degrees

                # Q channel (90 degree phase shift for complex signal)
                dds2.attrs['raw'].value = '1'  # Enable
                dds2.attrs['frequency'].value = str(int(frequency))
                dds2.attrs['scale'].value = str(amplitude)
                dds2.attrs['phase'].value = str(int((phase + 90) * 1000))

                logger.info(f"Configured DDS tone: {frequency/1000:.1f} kHz, "
                           f"amplitude: {amplitude:.2f}, phase: {phase:.1f}°")
                return True

        except Exception as e:
            logger.error(f"Failed to configure DDS tone: {e}")

        return False


class CalibrationManager:
    """
    Calibration and diagnostic utilities for PlutoSDR
    """

    def __init__(self, pluto_manager: PlutoSDRManager):
        """
        Initialize calibration manager

        Args:
            pluto_manager: Connected PlutoSDRManager instance
        """
        self.pluto = pluto_manager
        self.calibration_history = []

    def perform_basic_calibration(self,
                                 rx_lo: float = 2400000000,
                                 tx_lo: float = 2400000000,
                                 sample_rate: int = 3000000) -> CalibrationResult:
        """
        Perform basic AD9361 calibration

        Args:
            rx_lo: RX LO frequency for calibration
            tx_lo: TX LO frequency for calibration
            sample_rate: Sample rate for calibration

        Returns:
            CalibrationResult object
        """
        start_time = time.time()

        try:
            # Configure basic settings
            success = self.pluto.configure_basic_settings(
                rx_lo=int(rx_lo),
                tx_lo=int(tx_lo),
                sample_rate=sample_rate
            )

            if not success:
                return CalibrationResult(
                    success=False,
                    rx_lo_freq=rx_lo,
                    tx_lo_freq=tx_lo,
                    sample_rate=sample_rate,
                    rx_gain=0, tx_gain=0,
                    dc_offset_i=0, dc_offset_q=0,
                    iq_imbalance=0, phase_correction=0,
                    timestamp=start_time
                )

            # Enable loopback for calibration
            self.pluto.set_loopback_mode(True)

            # Collect calibration data
            dc_offset_i, dc_offset_q = self._measure_dc_offset()
            iq_imbalance = self._measure_iq_imbalance()
            phase_correction = self._measure_phase_error()

            # Get current gain settings
            rx_gain = 60  # Default
            tx_gain = -30  # Default

            if self.pluto.sdr:
                try:
                    rx_gain = self.pluto.sdr.rx_hardwaregain_chan0
                    tx_gain = self.pluto.sdr.tx_hardwaregain_chan0
                except:
                    pass

            # Disable loopback
            self.pluto.set_loopback_mode(False)

            result = CalibrationResult(
                success=True,
                rx_lo_freq=rx_lo,
                tx_lo_freq=tx_lo,
                sample_rate=sample_rate,
                rx_gain=rx_gain,
                tx_gain=tx_gain,
                dc_offset_i=dc_offset_i,
                dc_offset_q=dc_offset_q,
                iq_imbalance=iq_imbalance,
                phase_correction=phase_correction,
                timestamp=start_time
            )

            self.calibration_history.append(result)
            logger.info(f"Calibration completed successfully in {time.time() - start_time:.2f}s")

            return result

        except Exception as e:
            logger.error(f"Calibration failed: {e}")
            return CalibrationResult(
                success=False,
                rx_lo_freq=rx_lo,
                tx_lo_freq=tx_lo,
                sample_rate=sample_rate,
                rx_gain=0, tx_gain=0,
                dc_offset_i=0, dc_offset_q=0,
                iq_imbalance=0, phase_correction=0,
                timestamp=start_time
            )

    def _measure_dc_offset(self) -> Tuple[float, float]:
        """
        Measure DC offset in I and Q channels

        Returns:
            Tuple of (I_offset, Q_offset)
        """
        try:
            if not self.pluto.sdr:
                return 0.0, 0.0

            # Collect samples with no signal
            samples = self.pluto.sdr.rx()

            # Calculate DC offset
            i_offset = np.mean(np.real(samples))
            q_offset = np.mean(np.imag(samples))

            return float(i_offset), float(q_offset)

        except Exception as e:
            logger.debug(f"DC offset measurement failed: {e}")
            return 0.0, 0.0

    def _measure_iq_imbalance(self) -> float:
        """
        Measure IQ imbalance

        Returns:
            IQ imbalance in dB
        """
        try:
            if not self.pluto.sdr:
                return 0.0

            # Generate test tone and measure response
            samples = self.pluto.sdr.rx()

            # Calculate power in I and Q channels
            i_power = np.mean(np.abs(np.real(samples))**2)
            q_power = np.mean(np.abs(np.imag(samples))**2)

            if q_power > 0:
                imbalance_db = 10 * np.log10(i_power / q_power)
                return float(imbalance_db)

        except Exception as e:
            logger.debug(f"IQ imbalance measurement failed: {e}")

        return 0.0

    def _measure_phase_error(self) -> float:
        """
        Measure phase error between I and Q channels

        Returns:
            Phase error in degrees
        """
        try:
            if not self.pluto.sdr:
                return 0.0

            # Collect samples
            samples = self.pluto.sdr.rx()

            # Calculate phase difference
            phase_diff = np.angle(samples)
            mean_phase = np.mean(phase_diff)

            # Convert to degrees
            phase_error_deg = np.degrees(mean_phase - np.pi/2)  # Expect 90° between I and Q

            return float(phase_error_deg)

        except Exception as e:
            logger.debug(f"Phase error measurement failed: {e}")

        return 0.0

    def run_diagnostic_tests(self) -> Dict[str, any]:
        """
        Run comprehensive diagnostic tests

        Returns:
            Dictionary with test results
        """
        results = {
            'timestamp': time.time(),
            'device_connected': self.pluto.is_connected,
            'temperatures': None,
            'loopback_test': False,
            'frequency_accuracy': None,
            'gain_linearity': None,
            'noise_floor': None
        }

        if not self.pluto.is_connected:
            return results

        # Temperature check
        results['temperatures'] = self.pluto.get_temperatures()

        # Loopback test
        results['loopback_test'] = self._test_loopback()

        # Frequency accuracy test
        results['frequency_accuracy'] = self._test_frequency_accuracy()

        # Gain linearity test
        results['gain_linearity'] = self._test_gain_linearity()

        # Noise floor measurement
        results['noise_floor'] = self._measure_noise_floor()

        return results

    def _test_loopback(self) -> bool:
        """Test digital loopback functionality"""
        try:
            # Enable loopback
            if not self.pluto.set_loopback_mode(True):
                return False

            # Generate test signal and verify reception
            sig_gen = SignalGenerator(self.pluto)
            test_signal = sig_gen.generate_sine_wave(100000, 0.5, 3000000, 0.1)

            if sig_gen.transmit_signal(test_signal, cyclic=True):
                time.sleep(0.1)  # Allow signal to stabilize

                # Receive and check signal
                if self.pluto.sdr:
                    rx_samples = self.pluto.sdr.rx()

                    # Simple correlation check
                    correlation = np.abs(np.corrcoef(np.real(test_signal[:len(rx_samples)]),
                                                   np.real(rx_samples))[0,1])

                    sig_gen.stop_transmission()
                    self.pluto.set_loopback_mode(False)

                    return correlation > 0.5  # Threshold for successful loopback

            self.pluto.set_loopback_mode(False)

        except Exception as e:
            logger.debug(f"Loopback test failed: {e}")

        return False

    def _test_frequency_accuracy(self) -> Optional[float]:
        """Test frequency accuracy"""
        # This would require a known reference signal
        # For now, return None (not implemented)
        return None

    def _test_gain_linearity(self) -> Optional[Dict]:
        """Test gain linearity across range"""
        # This would test gain settings across the range
        # For now, return None (not implemented)
        return None

    def _measure_noise_floor(self) -> Optional[float]:
        """Measure noise floor"""
        try:
            if not self.pluto.sdr:
                return None

            # Set low gain and measure noise
            original_gain = self.pluto.sdr.rx_hardwaregain_chan0
            self.pluto.sdr.rx_hardwaregain_chan0 = 0  # Minimum gain

            time.sleep(0.1)  # Allow settling

            # Collect samples
            samples = self.pluto.sdr.rx()

            # Calculate noise power
            noise_power = np.mean(np.abs(samples)**2)
            noise_floor_db = 10 * np.log10(noise_power)

            # Restore original gain
            self.pluto.sdr.rx_hardwaregain_chan0 = original_gain

            return float(noise_floor_db)

        except Exception as e:
            logger.debug(f"Noise floor measurement failed: {e}")

        return None


class ConfigurationManager:
    """
    Configuration management for PlutoSDR settings
    """

    def __init__(self, pluto_manager: PlutoSDRManager):
        """
        Initialize configuration manager

        Args:
            pluto_manager: Connected PlutoSDRManager instance
        """
        self.pluto = pluto_manager
        self.config_profiles = {}

    def save_current_config(self, profile_name: str) -> bool:
        """
        Save current device configuration as a profile

        Args:
            profile_name: Name for the configuration profile

        Returns:
            True if successful, False otherwise
        """
        if not self.pluto.is_connected or not self.pluto.sdr:
            return False

        try:
            config = {
                'timestamp': time.time(),
                'rx_lo': self.pluto.sdr.rx_lo,
                'tx_lo': self.pluto.sdr.tx_lo,
                'sample_rate': self.pluto.sdr.sample_rate,
                'rx_rf_bandwidth': self.pluto.sdr.rx_rf_bandwidth,
                'tx_rf_bandwidth': self.pluto.sdr.tx_rf_bandwidth,
                'rx_hardwaregain_chan0': self.pluto.sdr.rx_hardwaregain_chan0,
                'tx_hardwaregain_chan0': self.pluto.sdr.tx_hardwaregain_chan0,
                'rx_buffer_size': self.pluto.sdr.rx_buffer_size,
            }

            # Add gain control mode if available
            try:
                config['gain_control_mode_chan0'] = self.pluto.sdr.gain_control_mode_chan0
            except:
                pass

            self.config_profiles[profile_name] = config
            logger.info(f"Saved configuration profile: {profile_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False

    def load_config_profile(self, profile_name: str) -> bool:
        """
        Load a configuration profile

        Args:
            profile_name: Name of the profile to load

        Returns:
            True if successful, False otherwise
        """
        if profile_name not in self.config_profiles:
            logger.error(f"Configuration profile '{profile_name}' not found")
            return False

        if not self.pluto.is_connected or not self.pluto.sdr:
            logger.error("PlutoSDR not connected")
            return False

        try:
            config = self.config_profiles[profile_name]

            # Apply configuration
            self.pluto.sdr.rx_lo = config['rx_lo']
            self.pluto.sdr.tx_lo = config['tx_lo']
            self.pluto.sdr.sample_rate = config['sample_rate']
            self.pluto.sdr.rx_rf_bandwidth = config['rx_rf_bandwidth']
            self.pluto.sdr.tx_rf_bandwidth = config['tx_rf_bandwidth']
            self.pluto.sdr.rx_hardwaregain_chan0 = config['rx_hardwaregain_chan0']
            self.pluto.sdr.tx_hardwaregain_chan0 = config['tx_hardwaregain_chan0']
            self.pluto.sdr.rx_buffer_size = config['rx_buffer_size']

            if 'gain_control_mode_chan0' in config:
                try:
                    self.pluto.sdr.gain_control_mode_chan0 = config['gain_control_mode_chan0']
                except:
                    pass

            logger.info(f"Loaded configuration profile: {profile_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return False

    def get_profile_list(self) -> List[str]:
        """Get list of available configuration profiles"""
        return list(self.config_profiles.keys())

    def delete_profile(self, profile_name: str) -> bool:
        """Delete a configuration profile"""
        if profile_name in self.config_profiles:
            del self.config_profiles[profile_name]
            logger.info(f"Deleted configuration profile: {profile_name}")
            return True
        return False


# Utility functions
def format_frequency(freq_hz: float) -> str:
    """
    Format frequency for display

    Args:
        freq_hz: Frequency in Hz

    Returns:
        Formatted frequency string
    """
    if freq_hz >= 1e9:
        return f"{freq_hz/1e9:.3f} GHz"
    elif freq_hz >= 1e6:
        return f"{freq_hz/1e6:.3f} MHz"
    elif freq_hz >= 1e3:
        return f"{freq_hz/1e3:.3f} kHz"
    else:
        return f"{freq_hz:.1f} Hz"


def parse_frequency(freq_str: str) -> float:
    """
    Parse frequency string to Hz

    Args:
        freq_str: Frequency string (e.g., "2.4 GHz", "100 MHz")

    Returns:
        Frequency in Hz
    """
    freq_str = freq_str.strip().upper()

    # Extract number and unit
    parts = freq_str.split()
    if len(parts) == 1:
        # No unit, assume Hz
        return float(parts[0])
    elif len(parts) == 2:
        value = float(parts[0])
        unit = parts[1]

        if unit in ['GHZ', 'G']:
            return value * 1e9
        elif unit in ['MHZ', 'M']:
            return value * 1e6
        elif unit in ['KHZ', 'K']:
            return value * 1e3
        else:
            return value

    return float(freq_str)


def calculate_fft_spectrum(samples: np.ndarray,
                          sample_rate: float,
                          window: str = 'hann') -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate FFT spectrum from IQ samples

    Args:
        samples: Complex IQ samples
        sample_rate: Sample rate in Hz
        window: Window function to apply

    Returns:
        Tuple of (frequencies, magnitude_db)
    """
    # Apply window
    if window == 'hann':
        windowed = samples * np.hanning(len(samples))
    elif window == 'hamming':
        windowed = samples * np.hamming(len(samples))
    elif window == 'blackman':
        windowed = samples * np.blackman(len(samples))
    else:
        windowed = samples

    # Calculate FFT
    fft_result = np.fft.fftshift(np.fft.fft(windowed))

    # Calculate frequencies
    freqs = np.fft.fftshift(np.fft.fftfreq(len(samples), 1/sample_rate))

    # Calculate magnitude in dB
    magnitude_db = 20 * np.log10(np.abs(fft_result) + 1e-12)  # Add small value to avoid log(0)

    return freqs, magnitude_db


def estimate_snr(samples: np.ndarray, signal_bw: float, sample_rate: float) -> float:
    """
    Estimate Signal-to-Noise Ratio

    Args:
        samples: Complex IQ samples
        signal_bw: Signal bandwidth in Hz
        sample_rate: Sample rate in Hz

    Returns:
        SNR estimate in dB
    """
    # Calculate spectrum
    freqs, spectrum_db = calculate_fft_spectrum(samples, sample_rate)

    # Find signal region (center portion)
    center_idx = len(spectrum_db) // 2
    signal_bins = int(signal_bw / sample_rate * len(spectrum_db))
    signal_start = center_idx - signal_bins // 2
    signal_end = center_idx + signal_bins // 2

    # Calculate signal power (peak in signal region)
    signal_power_db = np.max(spectrum_db[signal_start:signal_end])

    # Calculate noise power (average outside signal region)
    noise_spectrum = np.concatenate([
        spectrum_db[:signal_start],
        spectrum_db[signal_end:]
    ])
    noise_power_db = np.mean(noise_spectrum)

    snr_db = signal_power_db - noise_power_db

    return snr_db


# Example usage and testing functions
def run_basic_test():
    """Run basic functionality test"""
    print("PlutoSDR Enhanced Utility Library Test")
    print("=" * 40)

    # Initialize manager
    manager = PlutoSDRManager(auto_discover=True)

    if not manager.is_connected:
        print("❌ No PlutoSDR device found")
        return False

    print(f"✅ Connected to PlutoSDR at {manager.uri}")

    # Test temperature monitoring
    temps = manager.get_temperatures()
    if temps:
        print(f"🌡️  Temperatures: AD9361={temps.get('ad9361', 'N/A'):.1f}°C, "
              f"Zynq={temps.get('zynq', 'N/A'):.1f}°C")

    # Test configuration
    config_mgr = ConfigurationManager(manager)
    config_mgr.save_current_config("test_profile")
    print("💾 Saved test configuration profile")

    # Test signal generation
    sig_gen = SignalGenerator(manager)
    test_signal = sig_gen.generate_sine_wave(100000, 0.5, 3000000, 0.1)
    print(f"🎵 Generated test signal: {len(test_signal)} samples")

    # Test calibration
    cal_mgr = CalibrationManager(manager)
    cal_result = cal_mgr.perform_basic_calibration()
    print(f"🔧 Calibration: {'✅ Success' if cal_result.success else '❌ Failed'}")

    # Cleanup
    manager.disconnect()
    print("🔌 Disconnected")

    return True


if __name__ == "__main__":
    run_basic_test()
