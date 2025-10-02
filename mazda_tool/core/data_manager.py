# mazda_tool/core/data_manager.py
from PyQt5.QtCore import QObject, pyqtSignal
from typing import Dict, List, Any
import json
from datetime import datetime

class DataManager(QObject):
    """
    CENTRAL DATA HUB - Makes all components talk to each other
    """
    
    # Signals for cross-component communication
    live_data_updated = pyqtSignal(dict)           # New OBD data available
    ai_recommendation_added = pyqtSignal(object)   # New AI recommendation
    diagnostic_codes_updated = pyqtSignal(list)    # DTCs changed
    vehicle_connection_changed = pyqtSignal(bool)  # Connection status
    tuning_parameters_changed = pyqtSignal(dict)   # Tuning values updated
    
    def __init__(self):
        super().__init__()
        self.live_data = {}
        self.ai_recommendations = []
        self.diagnostic_codes = []
        self.tuning_parameters = {}
        self.vehicle_connected = False
        self.current_vehicle_profile = {}
        
    def update_live_data(self, new_data: Dict[str, Any]):
        """Update live OBD data and notify all components"""
        self.live_data.update(new_data)
        self.live_data['timestamp'] = datetime.now()
        self.live_data_updated.emit(self.live_data)
        
        # Auto-detect potential issues
        self._check_for_issues(new_data)
        
    def add_ai_recommendation(self, recommendation):
        """Add AI recommendation and notify tuning tab"""
        self.ai_recommendations.append(recommendation)
        self.ai_recommendation_added.emit(recommendation)
        
    def update_diagnostic_codes(self, codes: List[str]):
        """Update DTCs and notify AI system for safety"""
        self.diagnostic_codes = codes
        self.diagnostic_codes_updated.emit(codes)
        
        # Notify AI system about safety issues
        if codes:
            self._handle_diagnostic_issues(codes)
            
    def set_vehicle_connection(self, connected: bool, vehicle_info: Dict = None):
        """Update vehicle connection status across all tabs"""
        self.vehicle_connected = connected
        if vehicle_info:
            self.current_vehicle_profile = vehicle_info
        self.vehicle_connection_changed.emit(connected)
        
    def update_tuning_parameters(self, parameters: Dict[str, Any]):
        """Update tuning parameters and notify AI system"""
        self.tuning_parameters.update(parameters)
        self.tuning_parameters_changed.emit(parameters)
        
    def _check_for_issues(self, data: Dict):
        """Automatically detect potential issues from live data"""
        issues = []
        
        # Check for overboost
        if data.get('boost_pressure', 0) > 18.5:
            issues.append("⚠️ Boost pressure exceeding safe limits")
            
        # Check for high temperatures
        if data.get('intake_temp', 0) > 50:
            issues.append("🌡️ High intake temperatures detected")
            
        # Check for knock
        if data.get('knock_retard', 0) > 3.0:
            issues.append("🔨 Significant knock detected")
            
        if issues:
            print("Auto-detected issues:", issues)
            # Could trigger AI safety recommendations here
            
    def _handle_diagnostic_issues(self, codes: List[str]):
        """Handle diagnostic codes for AI safety system"""
        critical_codes = ['P0234', 'P0087', 'P0300']  # Overboost, Fuel pressure, Misfire
        
        for code in codes:
            if code in critical_codes:
                print(f"🚨 CRITICAL DTC: {code} - AI may adjust recommendations")
                
    def get_ai_training_data(self) -> Dict[str, Any]:
        """Provide comprehensive data for AI training"""
        return {
            'live_data': self.live_data,
            'current_tune': self.tuning_parameters,
            'vehicle_profile': self.current_vehicle_profile,
            'recent_issues': self.diagnostic_codes
        }
        
    def get_tuning_context(self) -> Dict[str, Any]:
        """Provide context for tuning decisions"""
        return {
            'current_parameters': self.tuning_parameters,
            'ai_recommendations': self.ai_recommendations,
            'vehicle_health': {
                'has_critical_codes': len(self.diagnostic_codes) > 0,
                'recent_issues': self.diagnostic_codes
            },
            'driving_conditions': {
                'current_boost': self.live_data.get('boost_pressure', 0),
                'current_temp': self.live_data.get('intake_temp', 0)
            }
        }