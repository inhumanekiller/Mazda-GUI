# mazda_tool/core/data_manager.py
from collections import deque, defaultdict
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import logging
import json
import time

class MazdaDataManager(QObject):
    """
    Central nervous system for all Mazda vehicle data flow
    Implements professional-grade data handling with safety interlocks
    """
    
    # Real-time data signals
    live_data_updated = pyqtSignal(dict)                    # 10Hz OBD-II data
    ai_recommendation_ready = pyqtSignal(dict)              # AI tuning suggestions
    diagnostic_codes_updated = pyqtSignal(list)             # DTC updates
    vehicle_connection_changed = pyqtSignal(bool, str)      # Connection status
    safety_event_detected = pyqtSignal(dict)                # Critical conditions
    tuning_parameters_updated = pyqtSignal(dict)            # Tune changes
    
    # Mazdaspeed 3 specific safety thresholds
    MAZDASPEED_SAFETY_LIMITS = {
        'boost_pressure': {'warning': 22.0, 'critical': 25.0, 'shutdown': 28.0},  # PSI
        'engine_temp': {'warning': 105.0, 'critical': 115.0, 'shutdown': 125.0},  # °C
        'hpfp_pressure': {'warning': 1500, 'critical': 1400, 'shutdown': 1300},   # PSI
        'knock_retard': {'warning': 3.0, 'critical': 5.0, 'shutdown': 8.0},       # Degrees
        'afr': {'warning': (10.5, 12.0), 'critical': (9.8, 13.5)},                # Lambda
    }

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Data storage with rolling buffers
        self.live_data_buffer = deque(maxlen=500)      # 50 seconds at 10Hz
        self.ai_training_dataset = []
        self.vehicle_health_history = []
        self.tuning_revision_history = []
        self.diagnostic_codes = []
        
        # Component state tracking
        self.connected_components = defaultdict(dict)
        self.safety_interlocks = {
            'flash_in_progress': False,
            'critical_fault_active': False,
            'vehicle_moving': False,
            'high_load_condition': False
        }
        
        # Real-time monitoring timer
        self.safety_monitor = QTimer()
        self.safety_monitor.timeout.connect(self._safety_check)
        self.safety_monitor.start(100)  # 10Hz safety monitoring

    def register_component(self, component_name, capabilities):
        """Register a component with the data manager"""
        self.connected_components[component_name] = {
            'capabilities': capabilities,
            'last_heartbeat': time.time(),
            'status': 'active'
        }
        self.logger.info(f"Component registered: {component_name}")

    def update_live_data(self, new_data):
        """Process and distribute live OBD-II data with safety checks"""
        # Validate data integrity
        validated_data = self._validate_data(new_data)
        if not validated_data:
            return
            
        # Apply smoothing filters
        smoothed_data = self._apply_smoothing(validated_data)
        
        # Store in buffer
        self.live_data_buffer.append(smoothed_data)
        
        # Emit to all subscribers
        self.live_data_updated.emit(smoothed_data)
        
        # Update AI training dataset
        if self._should_sample_for_ai(smoothed_data):
            self.ai_training_dataset.append(smoothed_data)

    def _safety_check(self):
        """Real-time safety monitoring with Mazdaspeed-specific logic"""
        if not self.live_data_buffer:
            return
            
        current_data = self.live_data_buffer[-1]
        
        # Check boost pressure safety
        if 'boost_pressure' in current_data:
            boost = current_data['boost_pressure']
            if boost > self.MAZDASPEED_SAFETY_LIMITS['boost_pressure']['critical']:
                self._trigger_safety_event('overboost', {
                    'parameter': 'boost_pressure',
                    'value': boost,
                    'limit': self.MAZDASPEED_SAFETY_LIMITS['boost_pressure']['critical'],
                    'action': 'reduce_boost'
                })

        # Check HPFP pressure (critical for direct injection)
        if 'fuel_pressure_high' in current_data:
            hpfp = current_data['fuel_pressure_high']
            if hpfp < self.MAZDASPEED_SAFETY_LIMITS['hpfp_pressure']['critical']:
                self._trigger_safety_event('hpfp_failure', {
                    'parameter': 'fuel_pressure_high', 
                    'value': hpfp,
                    'limit': self.MAZDASPEED_SAFETY_LIMITS['hpfp_pressure']['critical'],
                    'action': 'emergency_rich_afr'
                })

        # Check knock detection
        if 'knock_retard' in current_data:
            knock = current_data['knock_retard']
            if knock > self.MAZDASPEED_SAFETY_LIMITS['knock_retard']['critical']:
                self._trigger_safety_event('excessive_knock', {
                    'parameter': 'knock_retard',
                    'value': knock,
                    'limit': self.MAZDASPEED_SAFETY_LIMITS['knock_retard']['critical'],
                    'action': 'reduce_timing_boost'
                })

    def _trigger_safety_event(self, event_type, event_data):
        """Handle safety-critical events with appropriate actions"""
        event_data['timestamp'] = time.time()
        event_data['event_type'] = event_type
        event_data['severity'] = 'critical'
        
        self.logger.critical(f"SAFETY EVENT: {event_type} - {event_data}")
        self.safety_event_detected.emit(event_data)
        
        # Take automatic protective actions
        self._execute_safety_protocols(event_type, event_data)

    def _execute_safety_protocols(self, event_type, event_data):
        """Execute automatic safety protocols for critical events"""
        if event_type == 'overboost':
            # Reduce boost via ECU or electronic boost controller
            self._reduce_boost_pressure(event_data['value'])
            
        elif event_type == 'hpfp_failure':
            # Enrich AFR to protect engine
            self._enrich_air_fuel_ratio()
            
        elif event_type == 'excessive_knock':
            # Reduce timing and boost
            self._reduce_ignition_timing()
            self._reduce_boost_pressure(15.0)  # Safe boost level

    def get_vehicle_health_score(self):
        """Calculate comprehensive vehicle health score"""
        if not self.vehicle_health_history:
            return 100.0
            
        recent_data = list(self.live_data_buffer)[-100:]  # Last 10 seconds
        
        health_factors = {
            'engine_efficiency': self._calculate_engine_efficiency(recent_data),
            'turbo_health': self._calculate_turbo_health(recent_data),
            'fuel_system_health': self._calculate_fuel_system_health(recent_data),
            'ignition_health': self._calculate_ignition_health(recent_data)
        }
        
        return sum(health_factors.values()) / len(health_factors)

    def _calculate_turbo_health(self, data_samples):
        """Calculate K04 turbocharger health based on spool characteristics"""
        # Analyze turbo spool time, boost stability, etc.
        boost_values = [s.get('boost_pressure', 0) for s in data_samples if 'boost_pressure' in s]
        
        if not boost_values:
            return 85.0  # Conservative estimate
            
        boost_stability = self._calculate_boost_stability(boost_values)
        spool_time = self._calculate_spool_time(data_samples)
        
        return min(100.0, (boost_stability * 0.7 + spool_time * 0.3))

    def _calculate_boost_stability(self, boost_values):
        """Calculate how stable boost pressure is maintained"""
        if len(boost_values) < 5:
            return 90.0
            
        variance = np.var(boost_values)
        # Mazdaspeed 3 should have < 1.5 PSI variance under stable conditions
        max_variance = 1.5
        stability = max(0, 100 - (variance / max_variance * 50))
        return stability