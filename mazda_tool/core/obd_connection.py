# mazda_tool/core/obd_connection.py - REAL VERSION
import bluetooth
import serial
import time
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
import logging
from typing import Dict, List, Any, Optional
import struct

class AdvancedOBD2Bluetooth(QObject):
    """
    REAL OBD-II Bluetooth Connection - No Simulations
    Only communicates with actual vehicle hardware
    """
    
    connection_status_changed = pyqtSignal(bool)
    data_error = pyqtSignal(str)
    
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.connected = False
        self.socket = None
        self.logger = logging.getLogger(__name__)
        
        # Real OBD-II parameters for Mazdaspeed 3
        self.mazdaspeed_pids = {
            'RPM': '010C',
            'SPEED': '010D', 
            'ENGINE_LOAD': '0104',
            'THROTTLE_POSITION': '0111',
            'INTAKE_TEMP': '010F',
            'COOLANT_TEMP': '0105',
            'MAF_FLOW': '0110',
            'TIMING_ADVANCE': '010E',
            'FUEL_PRESSURE': '010A',
            'BOOST_PRESSURE': '0124',  # Calculated from MAP
            'VVT_POSITION': '0134',
            'KNOCK_RETARD': '0135',
            'AFR_COMMANDED': '0144'
        }
        
        # Data collection timer
        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self.collect_real_live_data)

    def connect_vehicle(self) -> tuple:
        """Connect to REAL OBD-II Bluetooth adapter"""
        try:
            self.logger.info("Scanning for OBD-II Bluetooth adapters...")
            
            # Discover Bluetooth devices
            devices = bluetooth.discover_devices(lookup_names=True, duration=8)
            obd_adapters = []
            
            for addr, name in devices:
                if any(obd_keyword in name.upper() for obd_keyword in ['OBD', 'ELM327', 'Vgate', 'OBDII']):
                    obd_adapters.append({'address': addr, 'name': name})
                    self.logger.info(f"Found OBD adapter: {name} - {addr}")
            
            if not obd_adapters:
                return False, "No OBD-II Bluetooth adapters found"
            
            # Try to connect to first found adapter
            adapter = obd_adapters[0]
            self.logger.info(f"Connecting to {adapter['name']}...")
            
            self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.socket.connect((adapter['address'], 1))
            
            # Initialize OBD-II connection
            self._send_at_command("ATZ")  # Reset
            time.sleep(2)
            self._send_at_command("ATE0")  # Echo off
            self._send_at_command("ATL0")  # Line feeds off
            self._send_at_command("ATH1")  # Headers on
            self._send_at_command("ATSP0") # Auto protocol
            
            # Test connection
            response = self._send_obd_command("010C")  # RPM
            if not response or "41 0C" not in response:
                return False, "OBD adapter connected but vehicle not responding"
            
            self.connected = True
            self.connection_status_changed.emit(True)
            
            # Start real data collection
            self.data_timer.start(100)  # 10Hz data collection
            
            self.logger.info("Successfully connected to vehicle via OBD-II")
            return True, f"Connected to {adapter['name']}"
            
        except bluetooth.BluetoothError as e:
            self.logger.error(f"Bluetooth connection failed: {e}")
            return False, f"Bluetooth error: {str(e)}"
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False, str(e)

    def disconnect_vehicle(self) -> tuple:
        """Disconnect from vehicle"""
        try:
            if self.data_timer.isActive():
                self.data_timer.stop()
                
            if self.socket:
                self.socket.close()
                self.socket = None
                
            self.connected = False
            self.connection_status_changed.emit(False)
            self.data_manager.update_vehicle_state(False)
            
            self.logger.info("Disconnected from vehicle")
            return True, "Disconnected successfully"
            
        except Exception as e:
            self.logger.error(f"Disconnection error: {e}")
            return False, str(e)

    def collect_real_live_data(self):
        """Collect REAL data from OBD-II"""
        if not self.connected or not self.socket:
            return
            
        try:
            live_data = {}
            
            # Collect critical parameters first
            rpm = self._get_rpm()
            if rpm is not None:
                live_data['rpm'] = rpm
                
            speed = self._get_speed() 
            if speed is not None:
                live_data['speed'] = speed
                
            engine_load = self._get_engine_load()
            if engine_load is not None:
                live_data['engine_load'] = engine_load
                
            throttle = self._get_throttle_position()
            if throttle is not None:
                live_data['throttle_position'] = throttle
                
            # Collect additional parameters
            intake_temp = self._get_intake_temp()
            if intake_temp is not None:
                live_data['intake_temp'] = intake_temp
                
            coolant_temp = self._get_coolant_temp()
            if coolant_temp is not None:
                live_data['coolant_temp'] = coolant_temp
                
            # Send REAL data to Data Manager
            if live_data:
                self.data_manager.update_live_data(live_data)
                
        except Exception as e:
            self.logger.error(f"Data collection error: {e}")
            self.data_error.emit(str(e))

    def _send_at_command(self, command: str) -> Optional[str]:
        """Send AT command to OBD adapter"""
        try:
            self.socket.send(command + "\r\n")
            time.sleep(0.1)
            return self._read_response()
        except Exception as e:
            self.logger.error(f"AT command failed: {command} - {e}")
            return None

    def _send_obd_command(self, pid: str) -> Optional[str]:
        """Send OBD PID request"""
        try:
            command = f"01{pid}"
            self.socket.send(command + "\r\n")
            time.sleep(0.05)  # Faster polling for real-time data
            return self._read_response()
        except Exception as e:
            self.logger.error(f"OBD command failed: {pid} - {e}")
            return None

    def _read_response(self) -> Optional[str]:
        """Read response from OBD adapter"""
        try:
            response = ""
            self.socket.settimeout(0.5)
            
            while True:
                try:
                    data = self.socket.recv(1024).decode('utf-8', errors='ignore')
                    response += data
                    if ">" in data or len(data) == 0:
                        break
                except bluetooth.BluetoothError:
                    break
                    
            return response.strip()
        except Exception as e:
            self.logger.error(f"Response read failed: {e}")
            return None

    def _get_rpm(self) -> Optional[float]:
        """Get REAL RPM from vehicle"""
        response = self._send_obd_command("010C")
        if response and "41 0C" in response:
            try:
                lines = response.split('\n')
                for line in lines:
                    if '41 0C' in line:
                        data = line.strip().split()
                        if len(data) >= 4:
                            a = int(data[2], 16)
                            b = int(data[3], 16)
                            return (256 * a + b) / 4
            except Exception as e:
                self.logger.error(f"RPM parse error: {e}")
        return None

    def _get_speed(self) -> Optional[float]:
        """Get REAL speed from vehicle"""
        response = self._send_obd_command("010D")
        if response and "41 0D" in response:
            try:
                lines = response.split('\n')
                for line in lines:
                    if '41 0D' in line:
                        data = line.strip().split()
                        if len(data) >= 3:
                            return int(data[2], 16)
            except Exception as e:
                self.logger.error(f"Speed parse error: {e}")
        return None

    def _get_engine_load(self) -> Optional[float]:
        """Get REAL engine load from vehicle"""
        response = self._send_obd_command("0104")
        if response and "41 04" in response:
            try:
                lines = response.split('\n')
                for line in lines:
                    if '41 04' in line:
                        data = line.strip().split()
                        if len(data) >= 3:
                            return int(data[2], 16) / 2.55
            except Exception as e:
                self.logger.error(f"Engine load parse error: {e}")
        return None

    def _get_throttle_position(self) -> Optional[float]:
        """Get REAL throttle position from vehicle"""
        response = self._send_obd_command("0111")
        if response and "41 11" in response:
            try:
                lines = response.split('\n')
                for line in lines:
                    if '41 11' in line:
                        data = line.strip().split()
                        if len(data) >= 3:
                            return int(data[2], 16) / 2.55
            except Exception as e:
                self.logger.error(f"Throttle position parse error: {e}")
        return None

    def _get_intake_temp(self) -> Optional[float]:
        """Get REAL intake air temperature"""
        response = self._send_obd_command("010F")
        if response and "41 0F" in response:
            try:
                lines = response.split('\n')
                for line in lines:
                    if '41 0F' in line:
                        data = line.strip().split()
                        if len(data) >= 3:
                            return int(data[2], 16) - 40
            except Exception as e:
                self.logger.error(f"Intake temp parse error: {e}")
        return None

    def _get_coolant_temp(self) -> Optional[float]:
        """Get REAL coolant temperature"""
        response = self._send_obd_command("0105")
        if response and "41 05" in response:
            try:
                lines = response.split('\n')
                for line in lines:
                    if '41 05' in line:
                        data = line.strip().split()
                        if len(data) >= 3:
                            return int(data[2], 16) - 40
            except Exception as e:
                self.logger.error(f"Coolant temp parse error: {e}")
        return None

    def read_diagnostic_codes(self, module: str = "ENGINE") -> List[str]:
        """Read REAL diagnostic trouble codes"""
        try:
            if not self.connected:
                return []
                
            response = self._send_obd_command("03")
            codes = []
            
            if response and "43" in response:
                lines = response.split('\n')
                for line in lines:
                    if '43' in line:
                        data = line.strip().split()
                        # Parse DTCs from response
                        for i in range(2, len(data), 2):
                            if i+1 < len(data):
                                first_byte = data[i]
                                second_byte = data[i+1]
                                if first_byte and second_byte:
                                    dtc = self._hex_to_dtc(first_byte, second_byte)
                                    if dtc:
                                        codes.append(dtc)
            
            # Update Data Manager with REAL codes
            self.data_manager.update_diagnostic_codes(codes, module)
            return codes
            
        except Exception as e:
            self.logger.error(f"DTC read error: {e}")
            return []

    def _hex_to_dtc(self, first_byte: str, second_byte: str) -> Optional[str]:
        """Convert hex bytes to DTC code"""
        try:
            first_int = int(first_byte, 16)
            second_int = int(second_byte, 16)
            
            byte1 = (first_int & 0xC0) >> 6
            byte2 = first_int & 0x3F
            byte3 = (second_int & 0xF0) >> 4
            byte4 = second_int & 0x0F
            
            dtc_letter = ['P', 'C', 'B', 'U'][byte1]
            dtc_code = f"{dtc_letter}{byte2:02d}{byte3:X}{byte4:X}"
            
            return dtc_code
        except:
            return None

    def clear_diagnostic_codes(self, module: str = "ENGINE") -> bool:
        """Clear REAL diagnostic trouble codes"""
        try:
            if not self.connected:
                return False
                
            response = self._send_obd_command("04")
            success = "44" in response if response else False
            
            if success:
                self.data_manager.update_diagnostic_codes([], module)
                
            return success
            
        except Exception as e:
            self.logger.error(f"DTC clear error: {e}")
            return False