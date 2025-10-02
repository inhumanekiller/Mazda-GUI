# mazda_tool/core/config_manager.py
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
import logging

class ConfigManager:
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.settings_file = self.config_dir / "settings.json"
        self.vehicle_profiles_file = self.config_dir / "vehicle_profiles.json"
        self.logger = logging.getLogger(__name__)
        
        # Initialize default configurations
        self.default_settings = {
            "application": {
                "version": "1.0.0",
                "auto_update_check": True,
                "log_level": "INFO"
            },
            "vehicle": {
                "default_interface": "AUTO",
                "communication_timeout": 30,
                "retry_attempts": 3
            },
            "ui": {
                "theme": "dark",
                "language": "en",
                "window_width": 1400,
                "window_height": 900
            },
            "modules": {
                "diagnostics_enabled": True,
                "tuning_enabled": True,
                "programming_enabled": False,
                "infotainment_tweaks_enabled": True
            }
        }
        
        self.default_vehicle_profiles = {
            "mazdaspeed3": {
                "generations": ["gen1", "gen2"],
                "engine": "MZR 2.3L DISI TURBO",
                "supported_features": ["ECU_TUNING", "DTC_READING", "DATA_LOGGING"],
                "max_safe_boost": 18.0,
                "redline": 6700
            },
            "mazda3_skyactiv": {
                "generations": ["gen3", "gen4"],
                "engine": "SKYACTIV-G 2.0L/2.5L",
                "supported_features": ["ECU_TUNING", "DTC_READING", "FUEL_ECONOMY"],
                "compression_ratio": 13.0
            }
        }
        
        self.load_configurations()
    
    def load_configurations(self):
        """Load or create configuration files"""
        self.settings = self.load_json_file(self.settings_file, self.default_settings)
        self.vehicle_profiles = self.load_json_file(
            self.vehicle_profiles_file, self.default_vehicle_profiles
        )
    
    def load_json_file(self, file_path: Path, default_data: Dict[str, Any]) -> Dict[str, Any]:
        """Load JSON file or create with default data"""
        try:
            if file_path.exists():
                with open(file_path, 'r') as file:
                    return json.load(file)
            else:
                with open(file_path, 'w') as file:
                    json.dump(default_data, file, indent=4)
                return default_data
        except Exception as e:
            self.logger.error(f"Error loading {file_path}: {str(e)}")
            return default_data
    
    def save_settings(self):
        """Save current settings to file"""
        try:
            with open(self.settings_file, 'w') as file:
                json.dump(self.settings, file, indent=4)
            self.logger.info("Settings saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving settings: {str(e)}")
    
    def get_vehicle_profile(self, model: str) -> Optional[Dict[str, Any]]:
        """Get vehicle profile by model name"""
        return self.vehicle_profiles.get(model.lower())
    
    def update_setting(self, category: str, key: str, value: Any):
        """Update a specific setting"""
        if category in self.settings and key in self.settings[category]:
            self.settings[category][key] = value
            self.save_settings()
        else:
            self.logger.warning(f"Setting not found: {category}.{key}")