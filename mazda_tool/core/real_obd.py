# mazda_tool/core/real_obd.py
import obd
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import logging

class RealOBDConnection(QObject):
    """
    REAL OBD-II connection using python-OBD
    Works with Bluetooth OBD adapters on macOS
    """
    
    data_received = pyqtSignal(dict)
    connection_changed = pyqtSignal(bool, str)
    
    def __init__(self):
        super().__init__()
        self.connection = None
        self.connected = False
        self.logger = logging.getLogger(__name__)
        self.watch_timer = QTimer()
        self.watch_timer.timeout.connect(self._update_data)
        
        # Commands to monitor
        self.commands = [
            obd.commands.RPM,
            obd.commands.SPEED,
            obd.commands.ENGINE_LOAD,
            obd.commands.THROTTLE_POS,
            obd.commands.INTAKE_TEMP,
            obd.commands.COOLANT_TEMP,
            obd.commands.MAF,
            obd.commands.TIMING_ADVANCE,
            obd.commands.FUEL_PRESSURE,
            obd.commands.INTAKE_PRESSURE,  # For boost calculation
        ]

    def connect_to_vehicle(self):
        """Connect to real vehicle via OBD-II"""
        try:
            self.logger.info("Searching for OBD-II adapter...")
            
            # python-OBD will auto-detect Bluetooth/wired adapters
            self.connection = obd.Async()
            
            if self.connection.is_connected():
                self._setup_watching()
                self.connected = True
                self.connection_changed.emit(True, "Connected to vehicle")
                self.logger.info("Successfully connected to vehicle")
                return True
            else:
                self.connection_changed.emit(False, "No OBD adapter found")
                return False
                
        except Exception as e:
            error_msg = f"Connection failed: {str(e)}"
            self.logger.error(error_msg)
            self.connection_changed.emit(False, error_msg)
            return False

    def _setup_watching(self):
        """Setup asynchronous data watching"""
        for cmd in self.commands:
            self.connection.watch(cmd)
        
        self.connection.start()
        self.watch_timer.start(100)  # 10Hz updates

    def _update_data(self):
        """Update data from OBD connection"""
        if not self.connected or not self.connection:
            return
            
        try:
            data = {}
            
            for cmd in self.commands:
                response = self.connection.query(cmd)
                if not response.is_null():
                    data[cmd.name] = response.value.magnitude
            
            # Convert to our format
            formatted_data = self._format_data(data)
            self.data_received.emit(formatted_data)
            
        except Exception as e:
            self.logger.error(f"Data update error: {e}")

    def _format_data(self, obd_data):
        """Convert OBD data to our application format"""
        formatted = {}
        
        if 'RPM' in obd_data:
            formatted['rpm'] = obd_data['RPM']
        if 'SPEED' in obd_data:
            formatted['speed'] = obd_data['SPEED']
        if 'ENGINE_LOAD' in obd_data:
            formatted['engine_load'] = obd_data['ENGINE_LOAD']
        if 'THROTTLE_POS' in obd_data:
            formatted['throttle_position'] = obd_data['THROTTLE_POS']
        if 'INTAKE_TEMP' in obd_data:
            formatted['intake_temp'] = obd_data['INTAKE_TEMP']
        if 'COOLANT_TEMP' in obd_data:
            formatted['coolant_temp'] = obd_data['COOLANT_TEMP']
        if 'INTAKE_PRESSURE' in obd_data:
            # Convert kPa to PSI for boost
            formatted['boost_pressure'] = (obd_data['INTAKE_PRESSURE'] - 101.3) * 0.145038
        if 'TIMING_ADVANCE' in obd_data:
            formatted['ignition_timing'] = obd_data['TIMING_ADVANCE']
        if 'MAF' in obd_data:
            formatted['maf_flow'] = obd_data['MAF']
            
        return formatted

    def disconnect(self):
        """Disconnect from vehicle"""
        try:
            if self.connection:
                self.connection.stop()
                self.connection = None
            self.connected = False
            self.watch_timer.stop()
            self.connection_changed.emit(False, "Disconnected")
            self.logger.info("Disconnected from vehicle")
        except Exception as e:
            self.logger.error(f"Disconnection error: {e}")