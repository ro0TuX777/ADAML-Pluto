#!/usr/bin/env python3
"""
Device Manager for Enhanced ADALM-Pluto SDR Toolkit

This module provides device discovery, connection management, and basic
device operations for PlutoSDR devices with improved error handling
and separation of concerns.

Author: Enhanced SDR Tools - Refactored
License: GPL-2 (compatible with original ADI scripts)
"""

import logging
import subprocess
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

from .constants import (
    ConnectionType, DeviceDiscovery, FrequencyLimits, GainLimits,
    NetworkConstants, TemperatureThresholds
)
from .exceptions import (
    DeviceNotFoundError, DeviceConnectionError, DeviceNotConnectedError,
    DeviceTimeoutError, OvertemperatureError, TemperatureReadError,
    handle_device_error, validate_frequency, validate_sample_rate, validate_gain
)
from .utils import retry_on_failure, timeout_after, PerformanceTimer

# Configure logging
logger = logging.getLogger(__name__)

# Optional imports with fallback
try:
    import adi
    ADI_AVAILABLE = True
except ImportError:
    ADI_AVAILABLE = False
    logger.warning("PyADI-IIO not available - device functionality limited")

try:
    import iio
    IIO_AVAILABLE = True
except ImportError:
    IIO_AVAILABLE = False
    logger.warning("libiio Python bindings not available")


@dataclass
class DeviceInfo:
    """Information about a discovered PlutoSDR device"""
    uri: str
    connection_type: ConnectionType
    ip_address: Optional[str] = None
    serial_number: Optional[str] = None
    firmware_version: Optional[str] = None
    hardware_revision: Optional[str] = None


@dataclass
class TemperatureReading:
    """Temperature reading from device sensors"""
    ad9361: Optional[float] = None
    zynq: Optional[float] = None
    timestamp: Optional[float] = None
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary format"""
        result = {}
        if self.ad9361 is not None:
            result['ad9361'] = self.ad9361
        if self.zynq is not None:
            result['zynq'] = self.zynq
        return result
    
    def check_warnings(self) -> List[str]:
        """Check for temperature warnings"""
        warnings = []
        
        if self.ad9361 is not None:
            if self.ad9361 > TemperatureThresholds.AD9361_CRITICAL:
                warnings.append(f"AD9361 temperature critical: {self.ad9361:.1f}°C")
            elif self.ad9361 > TemperatureThresholds.AD9361_WARNING:
                warnings.append(f"AD9361 temperature high: {self.ad9361:.1f}°C")
        
        if self.zynq is not None:
            if self.zynq > TemperatureThresholds.ZYNQ_CRITICAL:
                warnings.append(f"Zynq temperature critical: {self.zynq:.1f}°C")
            elif self.zynq > TemperatureThresholds.ZYNQ_WARNING:
                warnings.append(f"Zynq temperature high: {self.zynq:.1f}°C")
        
        return warnings


class DeviceDiscoverer(ABC):
    """Abstract base class for device discovery methods"""
    
    @abstractmethod
    def discover(self) -> List[DeviceInfo]:
        """Discover devices using this method"""
        pass


class USBDiscoverer(DeviceDiscoverer):
    """USB device discovery"""
    
    @retry_on_failure(max_attempts=2, delay=1.0)
    def discover(self) -> List[DeviceInfo]:
        """Discover USB-connected PlutoSDR devices"""
        devices = []
        
        if not IIO_AVAILABLE:
            logger.debug("libiio not available for USB discovery")
            return devices
        
        try:
            # Use iio_info to scan for USB devices
            result = subprocess.run(
                ['iio_info', '-s'],
                capture_output=True,
                text=True,
                timeout=DeviceDiscovery.DISCOVERY_TIMEOUT
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if DeviceDiscovery.USB_DEVICE_NAME.lower() in line.lower():
                        # Extract URI from iio_info output
                        parts = line.split()
                        for part in parts:
                            if part.startswith('usb:'):
                                devices.append(DeviceInfo(
                                    uri=part.rstrip(','),
                                    connection_type=ConnectionType.USB
                                ))
                                break
            
            logger.debug(f"USB discovery found {len(devices)} device(s)")
            
        except subprocess.TimeoutExpired:
            logger.warning("USB discovery timed out")
        except FileNotFoundError:
            logger.debug("iio_info not found - USB discovery unavailable")
        except Exception as e:
            logger.debug(f"USB discovery error: {e}")
        
        return devices


class IPDiscoverer(DeviceDiscoverer):
    """IP-based device discovery"""
    
    def discover(self) -> List[DeviceInfo]:
        """Discover IP-connected PlutoSDR devices"""
        devices = []
        
        for ip in DeviceDiscovery.DEFAULT_IPS:
            try:
                # Test connection to IP
                if self._test_ip_connection(ip):
                    devices.append(DeviceInfo(
                        uri=f"ip:{ip}",
                        connection_type=ConnectionType.IP,
                        ip_address=ip
                    ))
                    logger.debug(f"Found device at IP: {ip}")
            
            except Exception as e:
                logger.debug(f"IP discovery error for {ip}: {e}")
        
        logger.debug(f"IP discovery found {len(devices)} device(s)")
        return devices
    
    @timeout_after(NetworkConstants.CONNECTION_TIMEOUT)
    def _test_ip_connection(self, ip: str) -> bool:
        """Test if PlutoSDR is accessible at IP address"""
        try:
            # Try to ping the IP first
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '2', ip],
                capture_output=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # If ping succeeds, try to connect with iio
                if IIO_AVAILABLE:
                    try:
                        ctx = iio.Context(f"ip:{ip}")
                        devices = ctx.devices
                        # Look for AD9361 device
                        for device in devices:
                            if 'ad9361' in device.name.lower():
                                return True
                    except:
                        pass
                else:
                    # Fallback: assume ping success means device is there
                    return True
            
            return False
            
        except Exception:
            return False


class ZeroconfDiscoverer(DeviceDiscoverer):
    """Zeroconf/mDNS device discovery"""
    
    def discover(self) -> List[DeviceInfo]:
        """Discover devices using Zeroconf/mDNS"""
        devices = []
        
        try:
            # Try to resolve pluto.local
            result = subprocess.run(
                ['avahi-resolve', '--name', DeviceDiscovery.ZEROCONF_HOSTNAME],
                capture_output=True,
                text=True,
                timeout=DeviceDiscovery.DISCOVERY_TIMEOUT
            )
            
            if result.returncode == 0:
                # Extract IP from avahi-resolve output
                for line in result.stdout.split('\n'):
                    if DeviceDiscovery.ZEROCONF_HOSTNAME in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            ip = parts[1]
                            devices.append(DeviceInfo(
                                uri=f"ip:{ip}",
                                connection_type=ConnectionType.ZEROCONF,
                                ip_address=ip
                            ))
                            logger.debug(f"Zeroconf found device at: {ip}")
                            break
        
        except subprocess.TimeoutExpired:
            logger.debug("Zeroconf discovery timed out")
        except FileNotFoundError:
            logger.debug("avahi-resolve not found - Zeroconf discovery unavailable")
        except Exception as e:
            logger.debug(f"Zeroconf discovery error: {e}")
        
        logger.debug(f"Zeroconf discovery found {len(devices)} device(s)")
        return devices


class PlutoSDRDevice:
    """Represents a connected PlutoSDR device"""
    
    def __init__(self, device_info: DeviceInfo):
        """
        Initialize PlutoSDR device
        
        Args:
            device_info: Information about the device
        """
        self.device_info = device_info
        self.sdr = None
        self.rx_device = None
        self.tx_device = None
        self._is_connected = False
        self._last_temperature_reading = None
    
    @property
    def is_connected(self) -> bool:
        """Check if device is connected"""
        return self._is_connected and self.sdr is not None
    
    @handle_device_error
    def connect(self) -> bool:
        """
        Connect to the PlutoSDR device
        
        Returns:
            True if connection successful, False otherwise
            
        Raises:
            DeviceConnectionError: If connection fails
        """
        if self.is_connected:
            logger.debug("Device already connected")
            return True
        
        if not ADI_AVAILABLE:
            raise DeviceConnectionError(
                self.device_info.uri, 
                "PyADI-IIO not available"
            )
        
        try:
            with PerformanceTimer("Device connection"):
                # Create SDR object
                self.sdr = adi.Pluto(uri=self.device_info.uri)
                
                # Get IIO context for low-level operations
                if IIO_AVAILABLE:
                    ctx = iio.Context(self.device_info.uri)
                    self.rx_device = ctx.find_device("cf-ad9361-lpc")
                    self.tx_device = ctx.find_device("cf-ad9361-dds-core-lpc")
                
                # Test basic functionality
                _ = self.sdr.rx_lo  # This will raise an exception if device is not working
                
                self._is_connected = True
                logger.info(f"Successfully connected to PlutoSDR at {self.device_info.uri}")
                
                # Update device info with additional details
                self._update_device_info()
                
                return True
        
        except Exception as e:
            self.sdr = None
            self.rx_device = None
            self.tx_device = None
            self._is_connected = False
            raise DeviceConnectionError(self.device_info.uri, str(e))
    
    def disconnect(self) -> None:
        """Disconnect from the device"""
        if self.is_connected:
            try:
                # Clean up resources
                if hasattr(self.sdr, 'rx_destroy_buffer'):
                    self.sdr.rx_destroy_buffer()
                if hasattr(self.sdr, 'tx_destroy_buffer'):
                    self.sdr.tx_destroy_buffer()
            except:
                pass  # Ignore cleanup errors
            
            self.sdr = None
            self.rx_device = None
            self.tx_device = None
            self._is_connected = False
            logger.info("Disconnected from PlutoSDR")
    
    def _update_device_info(self) -> None:
        """Update device info with additional details from connected device"""
        if not self.is_connected:
            return
        
        try:
            # Try to get firmware version and other details
            if hasattr(self.sdr, '_ctx'):
                ctx = self.sdr._ctx
                if hasattr(ctx, 'attrs'):
                    for attr_name in ctx.attrs:
                        attr = ctx.attrs[attr_name]
                        if 'fw_version' in attr_name.lower():
                            self.device_info.firmware_version = attr.value
                        elif 'serial' in attr_name.lower():
                            self.device_info.serial_number = attr.value
                        elif 'hw_model' in attr_name.lower():
                            self.device_info.hardware_revision = attr.value
        except Exception as e:
            logger.debug(f"Could not update device info: {e}")
    
    def configure_basic_settings(self, 
                                rx_lo: Optional[int] = None,
                                tx_lo: Optional[int] = None,
                                sample_rate: Optional[int] = None,
                                rx_bandwidth: Optional[int] = None,
                                tx_bandwidth: Optional[int] = None,
                                rx_gain: Optional[int] = None,
                                tx_gain: Optional[int] = None) -> bool:
        """
        Configure basic device settings with validation
        
        Args:
            rx_lo: RX LO frequency in Hz
            tx_lo: TX LO frequency in Hz
            sample_rate: Sample rate in Hz
            rx_bandwidth: RX bandwidth in Hz
            tx_bandwidth: TX bandwidth in Hz
            rx_gain: RX gain in dB
            tx_gain: TX gain in dB
            
        Returns:
            True if configuration successful, False otherwise
        """
        if not self.is_connected:
            raise DeviceNotConnectedError("configure_basic_settings")
        
        try:
            # Validate and set parameters
            if rx_lo is not None:
                validate_frequency(rx_lo, FrequencyLimits.MIN_FREQUENCY, FrequencyLimits.MAX_FREQUENCY)
                self.sdr.rx_lo = rx_lo
            
            if tx_lo is not None:
                validate_frequency(tx_lo, FrequencyLimits.MIN_FREQUENCY, FrequencyLimits.MAX_FREQUENCY)
                self.sdr.tx_lo = tx_lo
            
            if sample_rate is not None:
                validate_sample_rate(sample_rate, FrequencyLimits.MIN_SAMPLE_RATE, FrequencyLimits.MAX_SAMPLE_RATE)
                self.sdr.sample_rate = sample_rate
            
            if rx_bandwidth is not None:
                validate_sample_rate(rx_bandwidth, FrequencyLimits.MIN_SAMPLE_RATE, FrequencyLimits.MAX_SAMPLE_RATE)
                self.sdr.rx_rf_bandwidth = rx_bandwidth
            
            if tx_bandwidth is not None:
                validate_sample_rate(tx_bandwidth, FrequencyLimits.MIN_SAMPLE_RATE, FrequencyLimits.MAX_SAMPLE_RATE)
                self.sdr.tx_rf_bandwidth = tx_bandwidth
            
            if rx_gain is not None:
                validate_gain(rx_gain, GainLimits.MIN_RX_GAIN, GainLimits.MAX_RX_GAIN, "RX")
                self.sdr.rx_hardwaregain_chan0 = rx_gain
            
            if tx_gain is not None:
                validate_gain(tx_gain, GainLimits.MIN_TX_GAIN, GainLimits.MAX_TX_GAIN, "TX")
                self.sdr.tx_hardwaregain_chan0 = tx_gain
            
            logger.debug("Device configuration updated successfully")
            return True
        
        except Exception as e:
            logger.error(f"Configuration failed: {e}")
            return False
    
    def get_temperatures(self) -> TemperatureReading:
        """
        Get device temperature readings
        
        Returns:
            TemperatureReading object with current temperatures
            
        Raises:
            TemperatureReadError: If temperature reading fails
        """
        if not self.is_connected:
            raise DeviceNotConnectedError("get_temperatures")
        
        reading = TemperatureReading(timestamp=time.time())
        
        try:
            if hasattr(self.sdr, '_ctx'):
                ctx = self.sdr._ctx
                
                # Try to read AD9361 temperature
                try:
                    temp_device = ctx.find_device("ad9361-phy")
                    if temp_device:
                        temp_attr = temp_device.find_channel("temp0", False)
                        if temp_attr and hasattr(temp_attr, 'attrs') and 'input' in temp_attr.attrs:
                            temp_raw = int(temp_attr.attrs['input'].value)
                            reading.ad9361 = temp_raw / 1000.0  # Convert millidegrees to degrees
                except Exception as e:
                    logger.debug(f"Could not read AD9361 temperature: {e}")
                
                # Try to read Zynq temperature
                try:
                    zynq_device = ctx.find_device("xadc")
                    if zynq_device:
                        temp_attr = zynq_device.find_channel("temp0", False)
                        if temp_attr and hasattr(temp_attr, 'attrs') and 'raw' in temp_attr.attrs:
                            temp_raw = int(temp_attr.attrs['raw'].value)
                            # Zynq temperature conversion (device-specific)
                            reading.zynq = (temp_raw * 503.975 / 4096) - 273.15
                except Exception as e:
                    logger.debug(f"Could not read Zynq temperature: {e}")
            
            self._last_temperature_reading = reading
            
            # Check for temperature warnings
            warnings = reading.check_warnings()
            for warning in warnings:
                logger.warning(warning)
                if "critical" in warning.lower():
                    # Raise exception for critical temperatures
                    if "AD9361" in warning:
                        raise OvertemperatureError("AD9361", reading.ad9361, TemperatureThresholds.AD9361_CRITICAL)
                    elif "Zynq" in warning:
                        raise OvertemperatureError("Zynq", reading.zynq, TemperatureThresholds.ZYNQ_CRITICAL)
            
            return reading
        
        except OvertemperatureError:
            raise  # Re-raise overtemperature errors
        except Exception as e:
            raise TemperatureReadError("device", str(e))
    
    def set_loopback_mode(self, enable: bool) -> bool:
        """
        Enable or disable digital loopback mode
        
        Args:
            enable: True to enable loopback, False to disable
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected:
            raise DeviceNotConnectedError("set_loopback_mode")
        
        try:
            if hasattr(self.sdr, '_ctx'):
                ctx = self.sdr._ctx
                phy_device = ctx.find_device("ad9361-phy")
                
                if phy_device and hasattr(phy_device, 'attrs'):
                    if 'loopback' in phy_device.attrs:
                        phy_device.attrs['loopback'].value = '1' if enable else '0'
                        logger.debug(f"Loopback mode {'enabled' if enable else 'disabled'}")
                        return True
            
            logger.warning("Could not set loopback mode - attribute not found")
            return False
        
        except Exception as e:
            logger.error(f"Failed to set loopback mode: {e}")
            return False


class PlutoSDRManager:
    """
    Main manager class for PlutoSDR device operations

    This class provides high-level interface for device discovery,
    connection management, and basic operations.
    """

    def __init__(self, uri: Optional[str] = None, auto_discover: bool = True):
        """
        Initialize PlutoSDR manager

        Args:
            uri: Specific device URI to connect to
            auto_discover: Whether to auto-discover devices if no URI provided
        """
        self.device: Optional[PlutoSDRDevice] = None
        self.discoverers = [
            USBDiscoverer(),
            IPDiscoverer(),
            ZeroconfDiscoverer()
        ]

        if uri:
            # Connect to specific URI
            device_info = DeviceInfo(uri=uri, connection_type=ConnectionType.AUTO)
            self.device = PlutoSDRDevice(device_info)
            try:
                self.device.connect()
            except Exception as e:
                logger.error(f"Failed to connect to specified URI {uri}: {e}")
                self.device = None
        elif auto_discover:
            # Auto-discover and connect to first available device
            self._auto_connect()

    @property
    def is_connected(self) -> bool:
        """Check if a device is connected"""
        return self.device is not None and self.device.is_connected

    @property
    def uri(self) -> Optional[str]:
        """Get URI of connected device"""
        return self.device.device_info.uri if self.device else None

    @property
    def device_info(self) -> Optional[DeviceInfo]:
        """Get device information"""
        return self.device.device_info if self.device else None

    @property
    def sdr(self):
        """Get SDR object for direct access"""
        return self.device.sdr if self.device else None

    def discover_devices(self) -> List[DeviceInfo]:
        """
        Discover all available PlutoSDR devices

        Returns:
            List of discovered device information
        """
        all_devices = []

        with PerformanceTimer("Device discovery"):
            for discoverer in self.discoverers:
                try:
                    devices = discoverer.discover()
                    all_devices.extend(devices)
                except Exception as e:
                    logger.debug(f"Discovery method {discoverer.__class__.__name__} failed: {e}")

        # Remove duplicates based on URI
        unique_devices = []
        seen_uris = set()

        for device in all_devices:
            if device.uri not in seen_uris:
                unique_devices.append(device)
                seen_uris.add(device.uri)

        logger.info(f"Discovered {len(unique_devices)} unique device(s)")
        return unique_devices

    def _auto_connect(self) -> None:
        """Auto-discover and connect to first available device"""
        devices = self.discover_devices()

        if not devices:
            logger.warning("No PlutoSDR devices found during auto-discovery")
            return

        # Try to connect to each device until one succeeds
        for device_info in devices:
            try:
                self.device = PlutoSDRDevice(device_info)
                if self.device.connect():
                    logger.info(f"Auto-connected to device: {device_info.uri}")
                    return
            except Exception as e:
                logger.debug(f"Failed to connect to {device_info.uri}: {e}")
                self.device = None

        logger.warning("Could not auto-connect to any discovered device")

    def connect(self, uri: str) -> bool:
        """
        Connect to a specific device

        Args:
            uri: Device URI to connect to

        Returns:
            True if connection successful, False otherwise
        """
        # Disconnect current device if any
        self.disconnect()

        device_info = DeviceInfo(uri=uri, connection_type=ConnectionType.AUTO)
        self.device = PlutoSDRDevice(device_info)

        try:
            return self.device.connect()
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.device = None
            return False

    def disconnect(self) -> None:
        """Disconnect from current device"""
        if self.device:
            self.device.disconnect()
            self.device = None

    def configure_basic_settings(self, **kwargs) -> bool:
        """
        Configure basic device settings

        Args:
            **kwargs: Configuration parameters

        Returns:
            True if configuration successful, False otherwise
        """
        if not self.is_connected:
            raise DeviceNotConnectedError("configure_basic_settings")

        return self.device.configure_basic_settings(**kwargs)

    def get_temperatures(self) -> Dict[str, float]:
        """
        Get device temperatures as dictionary

        Returns:
            Dictionary with temperature readings
        """
        if not self.is_connected:
            raise DeviceNotConnectedError("get_temperatures")

        reading = self.device.get_temperatures()
        return reading.to_dict()

    def set_loopback_mode(self, enable: bool) -> bool:
        """
        Enable or disable loopback mode

        Args:
            enable: True to enable loopback, False to disable

        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected:
            raise DeviceNotConnectedError("set_loopback_mode")

        return self.device.set_loopback_mode(enable)

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure cleanup"""
        self.disconnect()

    def __del__(self):
        """Destructor - ensure cleanup"""
        try:
            self.disconnect()
        except:
            pass  # Ignore errors during cleanup
