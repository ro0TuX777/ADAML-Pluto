#!/usr/bin/env python3
"""
Configuration Manager for Enhanced ADALM-Pluto SDR Toolkit

This module provides configuration management including device settings,
user preferences, and profile management with improved validation
and error handling.

Author: Enhanced SDR Tools - Refactored
License: GPL-2 (compatible with original ADI scripts)
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime

from .constants import (
    FileConstants, DEFAULT_SPECTRUM_CONFIG, DEFAULT_WATERFALL_CONFIG,
    DEFAULT_CALIBRATION_CONFIG, FrequencyLimits, GainLimits
)
from .exceptions import ConfigurationFileError, InvalidParameterError
from .utils import ensure_directory, get_timestamp_string

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class DeviceConfiguration:
    """Device configuration parameters"""
    rx_lo: int = DEFAULT_SPECTRUM_CONFIG['center_frequency']
    tx_lo: int = DEFAULT_SPECTRUM_CONFIG['center_frequency']
    sample_rate: int = DEFAULT_SPECTRUM_CONFIG['sample_rate']
    rx_bandwidth: int = DEFAULT_SPECTRUM_CONFIG['sample_rate']
    tx_bandwidth: int = DEFAULT_SPECTRUM_CONFIG['sample_rate']
    rx_gain: int = DEFAULT_SPECTRUM_CONFIG['rx_gain']
    tx_gain: int = DEFAULT_SPECTRUM_CONFIG['tx_gain']
    
    def validate(self) -> None:
        """Validate configuration parameters"""
        # Validate frequencies
        for freq_param in ['rx_lo', 'tx_lo']:
            freq = getattr(self, freq_param)
            if not (FrequencyLimits.MIN_FREQUENCY <= freq <= FrequencyLimits.MAX_FREQUENCY):
                raise InvalidParameterError(
                    freq_param, freq, 
                    f"{FrequencyLimits.MIN_FREQUENCY}-{FrequencyLimits.MAX_FREQUENCY}"
                )
        
        # Validate sample rates and bandwidths
        for rate_param in ['sample_rate', 'rx_bandwidth', 'tx_bandwidth']:
            rate = getattr(self, rate_param)
            if not (FrequencyLimits.MIN_SAMPLE_RATE <= rate <= FrequencyLimits.MAX_SAMPLE_RATE):
                raise InvalidParameterError(
                    rate_param, rate,
                    f"{FrequencyLimits.MIN_SAMPLE_RATE}-{FrequencyLimits.MAX_SAMPLE_RATE}"
                )
        
        # Validate gains
        if not (GainLimits.MIN_RX_GAIN <= self.rx_gain <= GainLimits.MAX_RX_GAIN):
            raise InvalidParameterError(
                'rx_gain', self.rx_gain,
                f"{GainLimits.MIN_RX_GAIN}-{GainLimits.MAX_RX_GAIN}"
            )
        
        if not (GainLimits.MIN_TX_GAIN <= self.tx_gain <= GainLimits.MAX_TX_GAIN):
            raise InvalidParameterError(
                'tx_gain', self.tx_gain,
                f"{GainLimits.MIN_TX_GAIN}-{GainLimits.MAX_TX_GAIN}"
            )


@dataclass
class SpectrumConfiguration:
    """Spectrum analyzer configuration"""
    fft_size: int = DEFAULT_SPECTRUM_CONFIG['fft_size']
    window_function: str = DEFAULT_SPECTRUM_CONFIG['window_function']
    averaging_factor: float = 0.1
    peak_hold_enabled: bool = False
    sweep_start: int = int(FrequencyLimits.DEFAULT_CENTER_FREQ - FrequencyLimits.DEFAULT_SAMPLE_RATE)
    sweep_stop: int = int(FrequencyLimits.DEFAULT_CENTER_FREQ + FrequencyLimits.DEFAULT_SAMPLE_RATE)
    sweep_steps: int = 1000


@dataclass
class WaterfallConfiguration:
    """Waterfall display configuration"""
    fft_size: int = DEFAULT_WATERFALL_CONFIG['fft_size']
    history_size: int = DEFAULT_WATERFALL_CONFIG['history_size']
    update_rate_ms: int = DEFAULT_WATERFALL_CONFIG['update_rate_ms']
    center_frequency: int = DEFAULT_WATERFALL_CONFIG['center_frequency']
    sample_rate: int = DEFAULT_WATERFALL_CONFIG['sample_rate']
    gain: int = DEFAULT_WATERFALL_CONFIG['gain']
    colormap: str = DEFAULT_WATERFALL_CONFIG['colormap']
    intensity_min: float = DEFAULT_WATERFALL_CONFIG['intensity_min']
    intensity_max: float = DEFAULT_WATERFALL_CONFIG['intensity_max']
    averaging_factor: float = DEFAULT_WATERFALL_CONFIG['averaging_factor']


@dataclass
class CalibrationConfiguration:
    """Calibration configuration"""
    rx_lo: int = DEFAULT_CALIBRATION_CONFIG['rx_lo']
    tx_lo: int = DEFAULT_CALIBRATION_CONFIG['tx_lo']
    sample_rate: int = DEFAULT_CALIBRATION_CONFIG['sample_rate']
    correlation_threshold: float = DEFAULT_CALIBRATION_CONFIG['correlation_threshold']
    auto_calibrate_on_connect: bool = False
    temperature_compensation: bool = True


@dataclass
class UserPreferences:
    """User preferences and settings"""
    default_profile: Optional[str] = None
    auto_connect: bool = True
    auto_discover: bool = True
    temperature_monitoring: bool = True
    temperature_warning_threshold: float = 70.0
    log_level: str = "INFO"
    gui_theme: str = "default"
    plot_style: str = "default"


@dataclass
class ConfigurationProfile:
    """Complete configuration profile"""
    name: str
    description: str = ""
    created_date: str = ""
    modified_date: str = ""
    device_config: DeviceConfiguration = None
    spectrum_config: SpectrumConfiguration = None
    waterfall_config: WaterfallConfiguration = None
    calibration_config: CalibrationConfiguration = None
    
    def __post_init__(self):
        """Initialize default configurations if not provided"""
        if self.device_config is None:
            self.device_config = DeviceConfiguration()
        if self.spectrum_config is None:
            self.spectrum_config = SpectrumConfiguration()
        if self.waterfall_config is None:
            self.waterfall_config = WaterfallConfiguration()
        if self.calibration_config is None:
            self.calibration_config = CalibrationConfiguration()
        
        # Set timestamps if not provided
        current_time = datetime.now().isoformat()
        if not self.created_date:
            self.created_date = current_time
        if not self.modified_date:
            self.modified_date = current_time
    
    def validate(self) -> None:
        """Validate all configuration components"""
        self.device_config.validate()
        # Additional validation can be added for other config components


class ConfigurationManager:
    """
    Manages configuration profiles and user preferences
    """
    
    def __init__(self, config_dir: Optional[Union[str, Path]] = None):
        """
        Initialize configuration manager
        
        Args:
            config_dir: Directory for configuration files. If None, uses default.
        """
        if config_dir is None:
            # Use user's home directory for config
            self.config_dir = Path.home() / ".pluto_sdr_toolkit"
        else:
            self.config_dir = Path(config_dir)
        
        # Ensure config directory exists
        ensure_directory(self.config_dir)
        
        self.profiles_dir = self.config_dir / "profiles"
        ensure_directory(self.profiles_dir)
        
        self.preferences_file = self.config_dir / "preferences.json"
        
        # Load user preferences
        self.preferences = self._load_preferences()
    
    def save_profile(self, profile: ConfigurationProfile) -> bool:
        """
        Save configuration profile to file
        
        Args:
            profile: Configuration profile to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate profile before saving
            profile.validate()
            
            # Update modification timestamp
            profile.modified_date = datetime.now().isoformat()
            
            # Create filename
            safe_name = self._sanitize_filename(profile.name)
            filename = self.profiles_dir / f"{safe_name}{FileConstants.CONFIG_FILE_EXTENSION}"
            
            # Convert to dictionary
            profile_dict = asdict(profile)
            
            # Save to file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(profile_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved configuration profile: {profile.name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to save profile '{profile.name}': {e}")
            raise ConfigurationFileError(profile.name, "save", str(e))
    
    def load_profile(self, profile_name: str) -> Optional[ConfigurationProfile]:
        """
        Load configuration profile from file
        
        Args:
            profile_name: Name of profile to load
            
        Returns:
            ConfigurationProfile object or None if not found
        """
        try:
            safe_name = self._sanitize_filename(profile_name)
            filename = self.profiles_dir / f"{safe_name}{FileConstants.CONFIG_FILE_EXTENSION}"
            
            if not filename.exists():
                logger.warning(f"Profile '{profile_name}' not found")
                return None
            
            with open(filename, 'r', encoding='utf-8') as f:
                profile_dict = json.load(f)
            
            # Convert nested dictionaries back to dataclass objects
            profile_dict['device_config'] = DeviceConfiguration(**profile_dict['device_config'])
            profile_dict['spectrum_config'] = SpectrumConfiguration(**profile_dict['spectrum_config'])
            profile_dict['waterfall_config'] = WaterfallConfiguration(**profile_dict['waterfall_config'])
            profile_dict['calibration_config'] = CalibrationConfiguration(**profile_dict['calibration_config'])
            
            profile = ConfigurationProfile(**profile_dict)
            
            logger.info(f"Loaded configuration profile: {profile_name}")
            return profile
        
        except Exception as e:
            logger.error(f"Failed to load profile '{profile_name}': {e}")
            raise ConfigurationFileError(profile_name, "load", str(e))
    
    def delete_profile(self, profile_name: str) -> bool:
        """
        Delete configuration profile
        
        Args:
            profile_name: Name of profile to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            safe_name = self._sanitize_filename(profile_name)
            filename = self.profiles_dir / f"{safe_name}{FileConstants.CONFIG_FILE_EXTENSION}"
            
            if filename.exists():
                filename.unlink()
                logger.info(f"Deleted configuration profile: {profile_name}")
                return True
            else:
                logger.warning(f"Profile '{profile_name}' not found for deletion")
                return False
        
        except Exception as e:
            logger.error(f"Failed to delete profile '{profile_name}': {e}")
            raise ConfigurationFileError(profile_name, "delete", str(e))
    
    def list_profiles(self) -> List[str]:
        """
        List all available configuration profiles
        
        Returns:
            List of profile names
        """
        try:
            profiles = []
            for file_path in self.profiles_dir.glob(f"*{FileConstants.CONFIG_FILE_EXTENSION}"):
                # Extract profile name from filename
                profile_name = file_path.stem
                profiles.append(profile_name)
            
            profiles.sort()
            return profiles
        
        except Exception as e:
            logger.error(f"Failed to list profiles: {e}")
            return []
    
    def get_profile_info(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """
        Get basic information about a profile without loading it completely
        
        Args:
            profile_name: Name of profile
            
        Returns:
            Dictionary with profile information or None if not found
        """
        try:
            safe_name = self._sanitize_filename(profile_name)
            filename = self.profiles_dir / f"{safe_name}{FileConstants.CONFIG_FILE_EXTENSION}"
            
            if not filename.exists():
                return None
            
            with open(filename, 'r', encoding='utf-8') as f:
                profile_dict = json.load(f)
            
            # Return basic info only
            return {
                'name': profile_dict.get('name', profile_name),
                'description': profile_dict.get('description', ''),
                'created_date': profile_dict.get('created_date', ''),
                'modified_date': profile_dict.get('modified_date', ''),
                'file_size': filename.stat().st_size
            }
        
        except Exception as e:
            logger.error(f"Failed to get profile info for '{profile_name}': {e}")
            return None
    
    def save_preferences(self, preferences: UserPreferences) -> bool:
        """
        Save user preferences
        
        Args:
            preferences: User preferences to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            preferences_dict = asdict(preferences)
            
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(preferences_dict, f, indent=2, ensure_ascii=False)
            
            self.preferences = preferences
            logger.info("Saved user preferences")
            return True
        
        except Exception as e:
            logger.error(f"Failed to save preferences: {e}")
            return False
    
    def _load_preferences(self) -> UserPreferences:
        """Load user preferences from file"""
        try:
            if self.preferences_file.exists():
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    preferences_dict = json.load(f)
                
                return UserPreferences(**preferences_dict)
            else:
                # Return default preferences
                return UserPreferences()
        
        except Exception as e:
            logger.warning(f"Failed to load preferences, using defaults: {e}")
            return UserPreferences()
    
    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize profile name for use as filename
        
        Args:
            name: Profile name to sanitize
            
        Returns:
            Sanitized filename
        """
        # Replace invalid characters with underscores
        invalid_chars = '<>:"/\\|?*'
        sanitized = name
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Limit length and strip whitespace
        sanitized = sanitized.strip()[:50]
        
        return sanitized
    
    def export_profile(self, profile_name: str, export_path: Union[str, Path]) -> bool:
        """
        Export profile to specified path
        
        Args:
            profile_name: Name of profile to export
            export_path: Path to export to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            profile = self.load_profile(profile_name)
            if profile is None:
                return False
            
            export_file = Path(export_path)
            profile_dict = asdict(profile)
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(profile_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported profile '{profile_name}' to {export_path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to export profile '{profile_name}': {e}")
            return False
    
    def import_profile(self, import_path: Union[str, Path], 
                      new_name: Optional[str] = None) -> bool:
        """
        Import profile from specified path
        
        Args:
            import_path: Path to import from
            new_name: Optional new name for imported profile
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import_file = Path(import_path)
            
            if not import_file.exists():
                logger.error(f"Import file not found: {import_path}")
                return False
            
            with open(import_file, 'r', encoding='utf-8') as f:
                profile_dict = json.load(f)
            
            # Convert to profile object
            profile_dict['device_config'] = DeviceConfiguration(**profile_dict['device_config'])
            profile_dict['spectrum_config'] = SpectrumConfiguration(**profile_dict['spectrum_config'])
            profile_dict['waterfall_config'] = WaterfallConfiguration(**profile_dict['waterfall_config'])
            profile_dict['calibration_config'] = CalibrationConfiguration(**profile_dict['calibration_config'])
            
            profile = ConfigurationProfile(**profile_dict)
            
            # Use new name if provided
            if new_name:
                profile.name = new_name
            
            # Save imported profile
            return self.save_profile(profile)
        
        except Exception as e:
            logger.error(f"Failed to import profile from '{import_path}': {e}")
            return False
