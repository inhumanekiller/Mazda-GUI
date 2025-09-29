#!/usr/bin/env python3
"""
Mazdaspeed 3 Enhanced Diagnostics & Tuning Suite
With VersaTuner/Alientech-style Features & AI Tuner
Optimized for 2011 Mazdaspeed 3 with ELM327
macOS Native Implementation
"""

import sys
import serial
import serial.tools.list_ports
import time
import csv
import json
import threading
import numpy as np
from datetime import datetime
from collections import deque
import math
import pickle
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QPushButton, QLabel, 
                             QLineEdit, QGroupBox, QStatusBar, QScrollArea,
                             QTabWidget, QListWidget, QSplitter, QFrame,
                             QProgressBar, QMessageBox, QComboBox, QCheckBox,
                             QTableWidget, QTableWidgetItem, QSlider, QDial,
                             QGraphicsView, QGraphicsScene, QGraphicsItem,
                             QFileDialog, QSpinBox, QDoubleSpinBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QPointF, QRectF
from PyQt5.QtGui import QFont, QTextCursor, QPalette, QColor, QPen, QBrush, QPainter

# ELM327 Command Set
class ELM327Commands:
    # Basic AT Commands
    ATZ = "ATZ"           # Reset
    ATE0 = "ATE0"         # Echo off
    ATL0 = "ATL0"         # Line feeds off
    ATH1 = "ATH1"         # Headers on
    ATSP0 = "ATSP0"       # Auto protocol detection
    ATS0 = "ATS0"         # Spaces off
    
    # Mode 01 PIDs
    ENGINE_LOAD = "0104"
    COOLANT_TEMP = "0105"
    SHORT_FUEL_TRIM_1 = "0106"
    LONG_FUEL_TRIM_1 = "0107"
    INTAKE_PRESSURE = "010B"
    RPM = "010C"
    SPEED = "010D"
    TIMING_ADVANCE = "010E"
    INTAKE_TEMP = "010F"
    MAF_FLOW = "0110"
    THROTTLE_POS = "0111"

class Mazdaspeed3PIDs:
    """Mazdaspeed 3 specific parameter definitions"""
    PID_DEFINITIONS = {
        "0104": {"name": "Engine Load", "units": "%", "formula": lambda x: x * 100 / 255},
        "0105": {"name": "Coolant Temp", "units": "°C", "formula": lambda x: x - 40},
        "010C": {"name": "Engine RPM", "units": "RPM", "formula": lambda x: x / 4},
        "010D": {"name": "Vehicle Speed", "units": "km/h", "formula": lambda x: x},
        "010B": {"name": "Intake Pressure", "units": "kPa", "formula": lambda x: x},
        "010F": {"name": "Intake Temp", "units": "°C", "formula": lambda x: x - 40},
        "0111": {"name": "Throttle Position", "units": "%", "formula": lambda x: x * 100 / 255},
        "0110": {"name": "MAF Flow", "units": "g/s", "formula": lambda x: x / 100},
        "010E": {"name": "Timing Advance", "units": "°", "formula": lambda x: x / 2 - 64},
    }

# Base ELM327 Interface Class
class ELM327Interface(QThread):
    data_received = pyqtSignal(str, float)
    connection_status = pyqtSignal(bool, str)
    dtc_received = pyqtSignal(list)
    raw_data = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.serial_connection = None
        self.is_connected = False
        self.monitoring_pids = []
        self.logging_active = False
        self.log_file = None
        self.csv_writer = None
        self.running = False
        
    def discover_devices(self):
        """Discover available serial/Bluetooth devices"""
        ports = serial.tools.list_ports.comports()
        obd_devices = []
        for port in ports:
            if any(name in port.description.upper() for name in ['OBD', 'ELM327', 'VAG', 'BLUETOOTH']):
                obd_devices.append({
                    'port': port.device,
                    'description': port.description,
                    'hwid': port.hwid
                })
        return obd_devices
    
    def connect_to_device(self, port_name, baudrate=38400):
        """Connect to ELM327 device"""
        try:
            self.serial_connection = serial.Serial(
                port=port_name,
                baudrate=baudrate,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=1
            )
            
            # Initialize ELM327
            self.send_command(ELM327Commands.ATZ)
            time.sleep(1)
            self.send_command(ELM327Commands.ATE0)
            self.send_command(ELM327Commands.ATL0)
            self.send_command(ELM327Commands.ATH1)
            self.send_command(ELM327Commands.ATSP0)
            
            self.is_connected = True
            self.connection_status.emit(True, f"Connected to {port_name}")
            return True
            
        except Exception as e:
            self.connection_status.emit(False, f"Connection failed: {str(e)}")
            return False
    
    def disconnect(self):
        """Disconnect from device"""
        self.running = False
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        self.is_connected = False
        self.connection_status.emit(False, "Disconnected")
    
    def send_command(self, command):
        """Send command to ELM327"""
        if self.serial_connection and self.serial_connection.is_open:
            full_command = command + '\r\n'
            self.serial_connection.write(full_command.encode())
            time.sleep(0.1)
            return self.read_response()
        return None
    
    def read_response(self):
        """Read response from ELM327"""
        if self.serial_connection and self.serial_connection.is_open:
            response = b''
            start_time = time.time()
            while time.time() - start_time < 2:
                if self.serial_connection.in_waiting > 0:
                    response += self.serial_connection.read(self.serial_connection.in_waiting)
                    if b'>' in response:
                        break
                time.sleep(0.01)
            
            decoded_response = response.decode('ascii', errors='ignore').strip()
            self.raw_data.emit(decoded_response)
            return decoded_response
        return None
    
    def parse_obd_response(self, response, pid):
        """Parse OBD-II response and convert to actual value"""
        try:
            clean_response = response.replace(' ', '').replace('>', '').strip()
            
            if len(clean_response) >= 8:
                data_bytes = clean_response[6:10]
                hex_value = int(data_bytes, 16)
                
                if pid in Mazdaspeed3PIDs.PID_DEFINITIONS:
                    formula = Mazdaspeed3PIDs.PID_DEFINITIONS[pid]["formula"]
                    value = formula(hex_value)
                    return value
                    
            return None
        except Exception as e:
            print(f"Parse error for PID {pid}: {e}")
            return None
    
    def start_monitoring(self, pids):
        """Start monitoring specified PIDs"""
        self.monitoring_pids = pids
        self.running = True
        self.start()
    
    def run(self):
        """Main monitoring loop"""
        while self.running and self.is_connected:
            for pid in self.monitoring_pids:
                if not self.running:
                    break
                    
                response = self.send_command(pid)
                if response:
                    value = self.parse_obd_response(response, pid)
                    if value is not None:
                        pid_name = Mazdaspeed3PIDs.PID_DEFINITIONS.get(pid, {}).get("name", pid)
                        self.data_received.emit(pid_name, value)
                        
                        if self.logging_active and self.csv_writer:
                            timestamp = datetime.now()
                            self.csv_writer.writerow([timestamp.isoformat(), pid_name, value])
                
                time.sleep(0.1)
    
    def read_dtcs(self):
        """Read Diagnostic Trouble Codes"""
        response = self.send_command("03")
        if response:
            dtcs = self.parse_dtc_codes(response)
            self.dtc_received.emit(dtcs)
            return dtcs
        return []
    
    def parse_dtc_codes(self, response):
        """Parse DTC codes from response"""
        dtcs = []
        try:
            clean_response = response.replace(' ', '').replace('>', '').strip()
            if clean_response.startswith('43'):
                dtc_data = clean_response[2:]
                for i in range(0, len(dtc_data), 4):
                    if i + 4 <= len(dtc_data):
                        dtc_hex = dtc_data[i:i+4]
                        dtc = self.hex_to_dtc(dtc_hex)
                        if dtc:
                            dtcs.append(dtc)
        except Exception as e:
            print(f"DTC parse error: {e}")
        return dtcs
    
    def hex_to_dtc(self, hex_code):
        """Convert hex code to standard DTC format"""
        if len(hex_code) != 4:
            return None
        
        first_char = int(hex_code[0], 16)
        dtc_prefix = ""
        
        if first_char == 0: dtc_prefix = "P0"
        elif first_char == 1: dtc_prefix = "P1"
        elif first_char == 2: dtc_prefix = "P2"
        elif first_char == 3: dtc_prefix = "P3"
        elif first_char == 4: dtc_prefix = "C0"
        elif first_char == 5: dtc_prefix = "C1"
        elif first_char == 6: dtc_prefix = "C2"
        elif first_char == 7: dtc_prefix = "C3"
        elif first_char == 8: dtc_prefix = "B0"
        elif first_char == 9: dtc_prefix = "B1"
        elif first_char == 10: dtc_prefix = "B2"
        elif first_char == 11: dtc_prefix = "B3"
        elif first_char == 12: dtc_prefix = "U0"
        elif first_char == 13: dtc_prefix = "U1"
        elif first_char == 14: dtc_prefix = "U2"
        elif first_char == 15: dtc_prefix = "U3"
        
        return dtc_prefix + hex_code[1:]
    
    def clear_dtcs(self):
        """Clear Diagnostic Trouble Codes"""
        response = self.send_command("04")
        return "OK" in response if response else False
    
    def start_logging(self, filename):
        """Start data logging to CSV"""
        try:
            self.log_file = open(filename, 'w', newline='')
            self.csv_writer = csv.writer(self.log_file)
            self.csv_writer.writerow(['Timestamp', 'Parameter', 'Value'])
            self.logging_active = True
            return True
        except Exception as e:
            print(f"Logging error: {e}")
            return False
    
    def stop_logging(self):
        """Stop data logging"""
        self.logging_active = False
        if self.log_file:
            self.log_file.close()
            self.log_file = None
            self.csv_writer = None

# AI Tuner Class
class AITuner:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.is_trained = False
        self.training_data = []
        self.feature_names = ['rpm', 'load', 'boost', 'iat', 'timing']
        
    def add_training_point(self, features, target_timing):
        """Add data point for training"""
        self.training_data.append({
            'features': features,
            'target_timing': target_timing,
            'timestamp': datetime.now()
        })
        
    def train_model(self):
        """Train AI model on collected data"""
        if len(self.training_data) < 10:
            return False, "Need at least 10 data points for training"
            
        try:
            # Try to import sklearn, but provide fallback if not available
            try:
                from sklearn.ensemble import RandomForestRegressor
                from sklearn.preprocessing import StandardScaler
            except ImportError:
                return False, "scikit-learn not installed. Run: pip install scikit-learn"
            
            X = np.array([point['features'] for point in self.training_data])
            y = np.array([point['target_timing'] for point in self.training_data])
            
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
            self.model.fit(X_scaled, y)
            self.is_trained = True
            
            return True, f"Model trained on {len(self.training_data)} data points"
            
        except Exception as e:
            return False, f"Training failed: {str(e)}"
    
    def predict_optimal_timing(self, current_conditions):
        """Predict optimal timing advance for current conditions"""
        if not self.is_trained:
            return None, "Model not trained"
            
        try:
            if len(current_conditions) != len(self.feature_names):
                return None, f"Expected {len(self.feature_names)} features, got {len(current_conditions)}"
                
            X = np.array([current_conditions])
            X_scaled = self.scaler.transform(X)
            
            prediction = self.model.predict(X_scaled)[0]
            return prediction, "Success"
            
        except Exception as e:
            return None, f"Prediction failed: {str(e)}"
    
    def save_model(self, filename):
        """Save trained model to file"""
        try:
            with open(filename, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'scaler': self.scaler,
                    'training_data': self.training_data,
                    'is_trained': self.is_trained
                }, f)
            return True, "Model saved successfully"
        except Exception as e:
            return False, f"Save failed: {str(e)}"
    
    def load_model(self, filename):
        """Load trained model from file"""
        try:
            with open(filename, 'rb') as f:
                data = pickle.load(f)
                self.model = data['model']
                self.scaler = data['scaler']
                self.training_data = data['training_data']
                self.is_trained = data['is_trained']
            return True, "Model loaded successfully"
        except Exception as e:
            return False, f"Load failed: {str(e)}"

# Advanced Tuning Maps
class AdvancedTuningMaps:
    def __init__(self):
        self.boost_maps = {
            'stage0': self._create_boost_map(15.0),
            'stage1': self._create_boost_map(18.0),
            'stage2': self._create_boost_map(20.0),
        }
        
        self.timing_maps = {
            'conservative': self._create_timing_map(-2.0),
            'aggressive': self._create_timing_map(2.0),
        }
        
        self.current_boost_map = 'stage0'
        self.current_timing_map = 'conservative'
    
    def _create_boost_map(self, peak_boost):
        rpm_points = [1000, 2000, 3000, 4000, 5000, 6000, 7000]
        boost_values = []
        
        for rpm in rpm_points:
            if rpm < 2500:
                boost = peak_boost * 0.6
            elif rpm < 4000:
                boost = peak_boost * 0.9
            elif rpm < 5500:
                boost = peak_boost
            else:
                boost = peak_boost * 0.8
            boost_values.append(boost)
            
        return {'rpm': rpm_points, 'boost': boost_values}
    
    def _create_timing_map(self, adjustment):
        load_points = [0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
        rpm_points = [1000, 3000, 5000, 7000]
        
        base_timing = [
            [18, 16, 14, 12],
            [16, 14, 12, 10],
            [14, 12, 10, 8],
            [12, 10, 8, 6],
            [10, 8, 6, 4],
            [8, 6, 4, 2]
        ]
        
        timing_map = []
        for row in base_timing:
            adjusted_row = [timing + adjustment for timing in row]
            timing_map.append(adjusted_row)
            
        return {
            'load': load_points,
            'rpm': rpm_points,
            'timing': timing_map
        }

# Virtual Dyno
class VirtualDyno:
    def __init__(self):
        self.vehicle_mass = 1500
        self.drag_coefficient = 0.31
        self.frontal_area = 2.3
        self.rolling_resistance = 0.015
        self.wheel_radius = 0.33
        self.gear_ratios = [3.136, 1.888, 1.330, 1.000, 0.825]
        self.final_drive = 4.105
    
    def calculate_engine_torque(self, rpm, boost, timing):
        base_torque = self._get_base_torque(rpm)
        boost_multiplier = 1.0 + (boost / 15.0) * 0.3
        timing_multiplier = 1.0 + (timing / 10.0) * 0.1
        return base_torque * boost_multiplier * timing_multiplier
    
    def _get_base_torque(self, rpm):
        if rpm < 2000:
            return 200 * (rpm / 2000)
        elif rpm < 3000:
            return 200 + (80 * (rpm - 2000) / 1000)
        elif rpm < 5500:
            return 280
        else:
            return 280 * (1 - (rpm - 5500) / 3000)

# Enhanced ELM327 Interface
class EnhancedELM327Interface(ELM327Interface):
    def __init__(self):
        super().__init__()
        self.enhanced_pids = {
            'KNOCK_RETARD': '2110',
            'WASTEGATE_DUTY': '2140',
            'FUEL_PRESSURE': '2230',
            'VVT_ANGLE': '2210',
        }
    
    def read_knock_data(self):
        response = self.send_command(self.enhanced_pids['KNOCK_RETARD'])
        if response:
            return self.parse_enhanced_response(response)
        return None
    
    def read_wastegate_duty(self):
        response = self.send_command(self.enhanced_pids['WASTEGATE_DUTY'])
        if response:
            return self.parse_enhanced_response(response)
        return None
    
    def parse_enhanced_response(self, response):
        try:
            clean_response = response.replace(' ', '').replace('>', '').strip()
            if len(clean_response) >= 4:
                data_bytes = clean_response[-4:]
                return int(data_bytes, 16)
        except Exception as e:
            print(f"Enhanced parse error: {e}")
        return None

# GUI Widgets
class RealTimeGauge(QWidget):
    value_changed = pyqtSignal(float)
    
    def __init__(self, title, min_val, max_val, units, warning_threshold=None):
        super().__init__()
        self.title = title
        self.min_val = min_val
        self.max_val = max_val
        self.units = units
        self.warning_threshold = warning_threshold
        self.current_value = min_val
        self.setMinimumSize(150, 200)
        
    def set_value(self, value):
        self.current_value = max(self.min_val, min(self.max_val, value))
        self.value_changed.emit(value)
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        painter.setPen(QPen(QColor(100, 100, 100), 3))
        painter.drawArc(10, 10, width - 20, width - 20, 30 * 16, 120 * 16)
        
        value_ratio = (self.current_value - self.min_val) / (self.max_val - self.min_val)
        angle = 30 + (120 * value_ratio)
        
        if self.warning_threshold and self.current_value > self.warning_threshold:
            painter.setPen(QPen(QColor(255, 50, 50), 4))
        else:
            painter.setPen(QPen(QColor(50, 150, 255), 4))
            
        painter.drawArc(10, 10, width - 20, width - 20, 30 * 16, int(angle * 16))
        
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        value_text = f"{self.current_value:.1f} {self.units}"
        painter.drawText(0, width + 20, width, 30, Qt.AlignCenter, value_text)
        
        painter.setFont(QFont("Arial", 10))
        painter.drawText(0, width + 50, width, 30, Qt.AlignCenter, self.title)

class DataGraphWidget(QWidget):
    def __init__(self, title, max_points=100):
        super().__init__()
        self.title = title
        self.max_points = max_points
        self.data_points = deque(maxlen=max_points)
        self.timestamps = deque(maxlen=max_points)
        self.setMinimumSize(400, 200)
        
    def add_data_point(self, value, timestamp=None):
        if timestamp is None:
            timestamp = time.time()
        self.data_points.append(value)
        self.timestamps.append(timestamp)
        self.update()
    
    def paintEvent(self, event):
        if len(self.data_points) < 2:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        painter.fillRect(0, 0, width, height, QColor(40, 40, 40))
        
        min_val = min(self.data_points)
        max_val = max(self.data_points)
        val_range = max_val - min_val if max_val != min_val else 1
        
        painter.setPen(QPen(QColor(50, 150, 255), 2))
        
        points = []
        for i, (timestamp, value) in enumerate(zip(self.timestamps, self.data_points)):
            x = (i / (len(self.data_points) - 1)) * (width - 40) + 20
            y = height - 20 - ((value - min_val) / val_range) * (height - 40)
            points.append(QPointF(x, y))
        
        for i in range(1, len(points)):
            painter.drawLine(points[i-1], points[i])
        
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(10, 20, self.title)
        painter.drawText(width - 60, height - 5, f"{max_val:.1f}")
        painter.drawText(10, height - 5, f"{min_val:.1f}")

class TuningMapWidget(QWidget):
    def __init__(self, map_data, title):
        super().__init__()
        self.map_data = map_data
        self.title = title
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        title_label = QLabel(self.title)
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(title_label)
        
        self.map_table = QTableWidget()
        
        if 'rpm' in self.map_data and 'boost' in self.map_data:
            self.setup_1d_map()
        elif 'rpm' in self.map_data and 'load' in self.map_data and 'timing' in self.map_data:
            self.setup_2d_map()
            
        layout.addWidget(self.map_table)
        
        edit_layout = QHBoxLayout()
        self.global_adjust = QDoubleSpinBox()
        self.global_adjust.setRange(-10.0, 10.0)
        self.global_adjust.setSingleStep(0.5)
        self.global_adjust.valueChanged.connect(self.adjust_map_globally)
        
        edit_layout.addWidget(QLabel("Global Adjustment:"))
        edit_layout.addWidget(self.global_adjust)
        edit_layout.addStretch()
        
        layout.addLayout(edit_layout)
        
    def setup_1d_map(self):
        rpm_data = self.map_data['rpm']
        boost_data = self.map_data['boost']
        
        self.map_table.setColumnCount(2)
        self.map_table.setRowCount(len(rpm_data))
        self.map_table.setHorizontalHeaderLabels(["RPM", "Boost (PSI)"])
        
        for i, (rpm, boost) in enumerate(zip(rpm_data, boost_data)):
            self.map_table.setItem(i, 0, QTableWidgetItem(str(rpm)))
            self.map_table.setItem(i, 1, QTableWidgetItem(f"{boost:.1f}"))
    
    def setup_2d_map(self):
        rpm_data = self.map_data['rpm']
        load_data = self.map_data['load']
        timing_data = self.map_data['timing']
        
        self.map_table.setColumnCount(len(rpm_data) + 1)
        self.map_table.setRowCount(len(load_data))
        
        headers = ["Load/RPM"] + [str(rpm) for rpm in rpm_data]
        self.map_table.setHorizontalHeaderLabels(headers)
        
        for i, load in enumerate(load_data):
            self.map_table.setVerticalHeaderItem(i, QTableWidgetItem(f"{load:.1f}"))
        
        for i, load_row in enumerate(timing_data):
            for j, timing in enumerate(load_row):
                self.map_table.setItem(i, j + 1, QTableWidgetItem(f"{timing:.1f}"))
    
    def adjust_map_globally(self, adjustment):
        if 'boost' in self.map_data:
            self.map_data['boost'] = [boost + adjustment for boost in self.map_data['boost']]
            self.setup_1d_map()
        elif 'timing' in self.map_data:
            for i in range(len(self.map_data['timing'])):
                for j in range(len(self.map_data['timing'][i])):
                    self.map_data['timing'][i][j] += adjustment
            self.setup_2d_map()

# Main GUI Class
class MazdaspeedTunerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.obd_interface = ELM327Interface()
        self.current_data = {}
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        self.setWindowTitle("Mazdaspeed 3 Enhanced Diagnostics & Tuner")
        self.setGeometry(100, 100, 1200, 800)
        
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        self.dashboard_tab = QWidget()
        self.diagnostics_tab = QWidget()
        self.tuning_tab = QWidget()
        self.logging_tab = QWidget()
        self.connection_tab = QWidget()
        
        self.tabs.addTab(self.dashboard_tab, "Live Dashboard")
        self.tabs.addTab(self.diagnostics_tab, "Diagnostics")
        self.tabs.addTab(self.tuning_tab, "Performance Tuning")
        self.tabs.addTab(self.logging_tab, "Data Logging")
        self.tabs.addTab(self.connection_tab, "Connection")
        
        self.setup_dashboard_tab()
        self.setup_diagnostics_tab()
        self.setup_tuning_tab()
        self.setup_logging_tab()
        self.setup_connection_tab()
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready to connect")
        
    def setup_dashboard_tab(self):
        layout = QHBoxLayout(self.dashboard_tab)
        
        left_column = QVBoxLayout()
        
        gauges_layout = QHBoxLayout()
        
        self.rpm_gauge = RealTimeGauge("RPM", 0, 8000, "RPM", 6500)
        self.boost_gauge = RealTimeGauge("Boost", -10, 25, "PSI", 18)
        self.speed_gauge = RealTimeGauge("Speed", 0, 200, "km/h")
        self.temp_gauge = RealTimeGauge("Coolant", 0, 120, "°C", 105)
        
        gauges_layout.addWidget(self.rpm_gauge)
        gauges_layout.addWidget(self.boost_gauge)
        gauges_layout.addWidget(self.speed_gauge)
        gauges_layout.addWidget(self.temp_gauge)
        
        left_column.addLayout(gauges_layout)
        
        graphs_layout = QHBoxLayout()
        self.rpm_graph = DataGraphWidget("RPM")
        self.boost_graph = DataGraphWidget("Boost Pressure")
        graphs_layout.addWidget(self.rpm_graph)
        graphs_layout.addWidget(self.boost_graph)
        
        left_column.addLayout(graphs_layout)
        layout.addLayout(left_column)
        
        right_column = QVBoxLayout()
        
        values_group = QGroupBox("Live Parameters")
        values_layout = QVBoxLayout()
        
        self.parameter_labels = {}
        parameters = [
            ("Engine Load", "%"), ("Intake Temp", "°C"), ("Throttle Pos", "%"),
            ("MAF Flow", "g/s"), ("Timing Adv", "°"), ("Fuel Trim", "%")
        ]
        
        for param, units in parameters:
            param_layout = QHBoxLayout()
            label = QLabel(f"{param}:")
            value_label = QLabel("0.0")
            value_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            unit_label = QLabel(units)
            
            param_layout.addWidget(label)
            param_layout.addWidget(value_label)
            param_layout.addWidget(unit_label)
            param_layout.addStretch()
            
            values_layout.addLayout(param_layout)
            self.parameter_labels[param] = value_label
        
        values_group.setLayout(values_layout)
        right_column.addWidget(values_group)
        
        alerts_group = QGroupBox("System Alerts")
        alerts_layout = QVBoxLayout()
        self.alerts_list = QListWidget()
        alerts_layout.addWidget(self.alerts_list)
        alerts_group.setLayout(alerts_layout)
        right_column.addWidget(alerts_group)
        
        layout.addLayout(right_column)
        
    def setup_diagnostics_tab(self):
        layout = QVBoxLayout(self.diagnostics_tab)
        
        dtc_controls = QHBoxLayout()
        self.read_dtc_button = QPushButton("Read DTCs")
        self.clear_dtc_button = QPushButton("Clear DTCs")
        self.dtc_status_label = QLabel("No DTCs read")
        
        dtc_controls.addWidget(self.read_dtc_button)
        dtc_controls.addWidget(self.clear_dtc_button)
        dtc_controls.addWidget(self.dtc_status_label)
        dtc_controls.addStretch()
        
        layout.addLayout(dtc_controls)
        
        self.dtc_table = QTableWidget()
        self.dtc_table.setColumnCount(3)
        self.dtc_table.setHorizontalHeaderLabels(["DTC Code", "Description", "Status"])
        layout.addWidget(self.dtc_table)
        
        freeze_frame_group = QGroupBox("Freeze Frame Data")
        freeze_layout = QVBoxLayout()
        self.freeze_frame_text = QTextEdit()
        self.freeze_frame_text.setReadOnly(True)
        freeze_layout.addWidget(self.freeze_frame_text)
        freeze_frame_group.setLayout(freeze_layout)
        layout.addWidget(freeze_frame_group)
        
    def setup_tuning_tab(self):
        layout = QVBoxLayout(self.tuning_tab)
        
        perf_group = QGroupBox("Performance Monitoring")
        perf_layout = QHBoxLayout()
        
        metrics = [
            ("0-60 Time", "N/A"), ("1/4 Mile", "N/A"), 
            ("Max Boost", "0.0 PSI"), ("Peak RPM", "0")
        ]
        
        for metric, value in metrics:
            metric_layout = QVBoxLayout()
            label = QLabel(metric)
            value_label = QLabel(value)
            value_label.setStyleSheet("font-size: 14pt; color: #FF9800;")
            metric_layout.addWidget(label)
            metric_layout.addWidget(value_label)
            perf_layout.addLayout(metric_layout)
        
        perf_group.setLayout(perf_layout)
        layout.addWidget(perf_group)
        
        tuning_group = QGroupBox("Engine Parameters (Monitoring Only)")
        tuning_layout = QVBoxLayout()
        
        tuning_info = QLabel("For actual tuning, use dedicated tuning software.\nThis display shows current engine management parameters.")
        tuning_layout.addWidget(tuning_info)
        
        self.tuning_params_text = QTextEdit()
        self.tuning_params_text.setReadOnly(True)
        tuning_layout.addWidget(self.tuning_params_text)
        
        tuning_group.setLayout(tuning_layout)
        layout.addWidget(tuning_group)
        
    def setup_logging_tab(self):
        layout = QVBoxLayout(self.logging_tab)
        
        controls_layout = QHBoxLayout()
        self.start_log_button = QPushButton("Start Logging")
        self.stop_log_button = QPushButton("Stop Logging")
        self.log_status_label = QLabel("Logging: Inactive")
        
        controls_layout.addWidget(self.start_log_button)
        controls_layout.addWidget(self.stop_log_button)
        controls_layout.addWidget(self.log_status_label)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        config_group = QGroupBox("Logging Configuration")
        config_layout = QVBoxLayout()
        
        pid_layout = QHBoxLayout()
        pid_layout.addWidget(QLabel("Parameters to log:"))
        
        self.pid_checkboxes = {}
        pids_to_log = ["RPM", "Boost", "Speed", "Coolant Temp", "Throttle Position"]
        for pid in pids_to_log:
            checkbox = QCheckBox(pid)
            checkbox.setChecked(True)
            self.pid_checkboxes[pid] = checkbox
            pid_layout.addWidget(checkbox)
        
        pid_layout.addStretch()
        config_layout.addLayout(pid_layout)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        preview_group = QGroupBox("Live Data Preview")
        preview_layout = QVBoxLayout()
        self.log_preview = QTextEdit()
        self.log_preview.setReadOnly(True)
        preview_layout.addWidget(self.log_preview)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
    def setup_connection_tab(self):
        layout = QVBoxLayout(self.connection_tab)
        
        connection_controls = QHBoxLayout()
        self.scan_button = QPushButton("Scan for Devices")
        self.connect_button = QPushButton("Connect")
        self.disconnect_button = QPushButton("Disconnect")
        
        connection_controls.addWidget(self.scan_button)
        connection_controls.addWidget(self.connect_button)
        connection_controls.addWidget(self.disconnect_button)
        connection_controls.addStretch()
        
        layout.addLayout(connection_controls)
        
        self.device_list = QListWidget()
        layout.addWidget(self.device_list)
        
        status_group = QGroupBox("Connection Status")
        status_layout = QVBoxLayout()
        self.connection_status = QLabel("Not connected")
        self.raw_data_display = QTextEdit()
        self.raw_data_display.setReadOnly(True)
        self.raw_data_display.setMaximumHeight(150)
        
        status_layout.addWidget(self.connection_status)
        status_layout.addWidget(QLabel("Raw Data:"))
        status_layout.addWidget(self.raw_data_display)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
    def connect_signals(self):
        self.obd_interface.data_received.connect(self.on_data_received)
        self.obd_interface.connection_status.connect(self.on_connection_status)
        self.obd_interface.dtc_received.connect(self.on_dtc_received)
        self.obd_interface.raw_data.connect(self.on_raw_data)
        
        self.scan_button.clicked.connect(self.scan_devices)
        self.connect_button.clicked.connect(self.connect_to_device)
        self.disconnect_button.clicked.connect(self.disconnect_device)
        self.read_dtc_button.clicked.connect(self.read_dtcs)
        self.clear_dtc_button.clicked.connect(self.clear_dtcs)
        self.start_log_button.clicked.connect(self.start_logging)
        self.stop_log_button.clicked.connect(self.stop_logging)
        
        QTimer.singleShot(1000, self.scan_devices)
        
    def scan_devices(self):
        self.device_list.clear()
        devices = self.obd_interface.discover_devices()
        for device in devices:
            self.device_list.addItem(f"{device['port']} - {device['description']}")
        
    def connect_to_device(self):
        current_item = self.device_list.currentItem()
        if current_item:
            port_name = current_item.text().split(' - ')[0]
            if self.obd_interface.connect_to_device(port_name):
                monitoring_pids = [
                    ELM327Commands.RPM,
                    ELM327Commands.SPEED,
                    ELM327Commands.ENGINE_LOAD,
                    ELM327Commands.COOLANT_TEMP,
                    ELM327Commands.INTAKE_PRESSURE,
                    ELM327Commands.THROTTLE_POS
                ]
                self.obd_interface.start_monitoring(monitoring_pids)
                
    def disconnect_device(self):
        self.obd_interface.disconnect()
        
    def on_data_received(self, parameter, value):
        if parameter == "Engine RPM":
            self.rpm_gauge.set_value(value)
            self.rpm_graph.add_data_point(value)
        elif parameter == "Intake Pressure":
            boost_psi = (value - 101.3) / 6.895
            self.boost_gauge.set_value(boost_psi)
            self.boost_graph.add_data_point(boost_psi)
        elif parameter == "Vehicle Speed":
            self.speed_gauge.set_value(value)
        elif parameter == "Coolant Temp":
            self.temp_gauge.set_value(value)
            
        if parameter in self.parameter_labels:
            self.parameter_labels[parameter].setText(f"{value:.1f}")
            
        self.current_data[parameter] = value
        
        self.check_alerts(parameter, value)
        
    def check_alerts(self, parameter, value):
        alerts = {
            "Engine RPM": (value > 6500, "High RPM! Shift up!"),
            "Intake Pressure": (value > 180, "High boost pressure!"),
            "Coolant Temp": (value > 105, "Engine overheating!"),
        }
        
        if parameter in alerts:
            condition, message = alerts[parameter]
            if condition:
                self.add_alert(message)
                
    def add_alert(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.alerts_list.addItem(f"[{timestamp}] {message}")
        if self.alerts_list.count() > 10:
            self.alerts_list.takeItem(0)
            
    def on_connection_status(self, connected, message):
        self.status_bar.showMessage(message)
        self.connection_status.setText(message)
        
    def on_dtc_received(self, dtcs):
        self.dtc_table.setRowCount(len(dtcs))
        for i, dtc in enumerate(dtcs):
            self.dtc_table.setItem(i, 0, QTableWidgetItem(dtc))
            self.dtc_table.setItem(i, 1, QTableWidgetItem(self.get_dtc_description(dtc)))
            self.dtc_table.setItem(i, 2, QTableWidgetItem("Active"))
            
        self.dtc_status_label.setText(f"Found {len(dtcs)} DTCs")
        
    def get_dtc_description(self, dtc_code):
        dtc_database = {
            "P0101": "MAF Sensor Circuit Range/Performance",
            "P0300": "Random/Multiple Cylinder Misfire Detected",
            "P0420": "Catalyst System Efficiency Below Threshold",
        }
        return dtc_database.get(dtc_code, "Unknown DTC")
        
    def on_raw_data(self, data):
        self.raw_data_display.append(data)
        lines = self.raw_data_display.toPlainText().split('\n')
        if len(lines) > 100:
            self.raw_data_display.setPlainText('\n'.join(lines[-100:]))
            
    def read_dtcs(self):
        self.obd_interface.read_dtcs()
        
    def clear_dtcs(self):
        if self.obd_interface.clear_dtcs():
            QMessageBox.information(self, "Success", "DTCs cleared successfully")
            self.dtc_table.setRowCount(0)
            self.dtc_status_label.setText("DTCs cleared")
        else:
            QMessageBox.warning(self, "Error", "Failed to clear DTCs")
            
    def start_logging(self):
        filename = f"mazdaspeed_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        if self.obd_interface.start_logging(filename):
            self.log_status_label.setText(f"Logging: {filename}")
            self.start_log_button.setEnabled(False)
            self.stop_log_button.setEnabled(True)
            
    def stop_logging(self):
        self.obd_interface.stop_logging()
        self.log_status_label.setText("Logging: Inactive")
        self.start_log_button.setEnabled(True)
        self.stop_log_button.setEnabled(False)

# Enhanced GUI with AI Tuner
class EnhancedMazdaspeedTunerGUI(MazdaspeedTunerGUI):
    def __init__(self):
        self.ai_tuner = AITuner()
        self.advanced_maps = AdvancedTuningMaps()
        self.virtual_dyno = VirtualDyno()
        self.obd_interface = EnhancedELM327Interface()
        
        super().__init__()
        
    def setup_ui(self):
        super().setup_ui()
        
        self.advanced_tuning_tab = QWidget()
        self.ai_tuner_tab = QWidget()
        self.virtual_dyno_tab = QWidget()
        
        self.tabs.addTab(self.advanced_tuning_tab, "Advanced Tuning")
        self.tabs.addTab(self.ai_tuner_tab, "AI Tuner")
        self.tabs.addTab(self.virtual_dyno_tab, "Virtual Dyno")
        
        self.setup_advanced_tuning_tab()
        self.setup_ai_tuner_tab()
        self.setup_virtual_dyno_tab()
        
    def setup_advanced_tuning_tab(self):
        layout = QVBoxLayout(self.advanced_tuning_tab)
        
        map_selector_layout = QHBoxLayout()
        
        map_selector_layout.addWidget(QLabel("Boost Map:"))
        self.boost_map_combo = QComboBox()
        self.boost_map_combo.addItems(["Stage 0 (Stock)", "Stage 1 (+3 PSI)", "Stage 2 (+5 PSI)"])
        self.boost_map_combo.currentIndexChanged.connect(self.change_boost_map)
        map_selector_layout.addWidget(self.boost_map_combo)
        
        map_selector_layout.addWidget(QLabel("Timing Map:"))
        self.timing_map_combo = QComboBox()
        self.timing_map_combo.addItems(["Conservative", "Aggressive"])
        self.timing_map_combo.currentIndexChanged.connect(self.change_timing_map)
        map_selector_layout.addWidget(self.timing_map_combo)
        
        map_selector_layout.addStretch()
        layout.addLayout(map_selector_layout)
        
        maps_tabs = QTabWidget()
        
        self.boost_map_widget = TuningMapWidget(
            self.advanced_maps.boost_maps['stage0'], 
            "Boost Control Map"
        )
        maps_tabs.addTab(self.boost_map_widget, "Boost")
        
        self.timing_map_widget = TuningMapWidget(
            self.advanced_maps.timing_maps['conservative'],
            "Ignition Timing Map"
        )
        maps_tabs.addTab(self.timing_map_widget, "Timing")
        
        layout.addWidget(maps_tabs)
        
        tuning_params_group = QGroupBox("Real-time Tuning Parameters")
        tuning_layout = QHBoxLayout()
        
        wg_layout = QVBoxLayout()
        wg_layout.addWidget(QLabel("Wastegate Duty:"))
        self.wastegate_duty_label = QLabel("0%")
        wg_layout.addWidget(self.wastegate_duty_label)
        tuning_layout.addLayout(wg_layout)
        
        knock_layout = QVBoxLayout()
        knock_layout.addWidget(QLabel("Knock Retard:"))
        self.knock_retard_label = QLabel("0°")
        knock_layout.addWidget(self.knock_retard_label)
        tuning_layout.addLayout(knock_layout)
        
        fp_layout = QVBoxLayout()
        fp_layout.addWidget(QLabel("Fuel Pressure:"))
        self.fuel_pressure_label = QLabel("0 PSI")
        fp_layout.addWidget(self.fuel_pressure_label)
        tuning_layout.addLayout(fp_layout)
        
        vvt_layout = QVBoxLayout()
        vvt_layout.addWidget(QLabel("VVT Angle:"))
        self.vvt_angle_label = QLabel("0°")
        vvt_layout.addWidget(self.vvt_angle_label)
        tuning_layout.addLayout(vvt_layout)
        
        tuning_params_group.setLayout(tuning_layout)
        layout.addWidget(tuning_params_group)
        
    def setup_ai_tuner_tab(self):
        layout = QVBoxLayout(self.ai_tuner_tab)
        
        training_group = QGroupBox("AI Model Training")
        training_layout = QVBoxLayout()
        
        training_status_layout = QHBoxLayout()
        training_status_layout.addWidget(QLabel("Training Status:"))
        self.training_status_label = QLabel("Not trained")
        training_status_layout.addWidget(self.training_status_label)
        training_status_layout.addStretch()
        
        training_layout.addLayout(training_status_layout)
        
        training_controls_layout = QHBoxLayout()
        
        self.start_training_button = QPushButton("Start Data Collection")
        self.start_training_button.clicked.connect(self.start_ai_training)
        training_controls_layout.addWidget(self.start_training_button)
        
        self.train_model_button = QPushButton("Train Model")
        self.train_model_button.clicked.connect(self.train_ai_model)
        training_controls_layout.addWidget(self.train_model_button)
        
        self.save_model_button = QPushButton("Save Model")
        self.save_model_button.clicked.connect(self.save_ai_model)
        training_controls_layout.addWidget(self.save_model_button)
        
        self.load_model_button = QPushButton("Load Model")
        self.load_model_button.clicked.connect(self.load_ai_model)
        training_controls_layout.addWidget(self.load_model_button)
        
        training_layout.addLayout(training_controls_layout)
        
        training_info_layout = QHBoxLayout()
        training_info_layout.addWidget(QLabel("Data Points Collected:"))
        self.data_points_label = QLabel("0")
        training_info_layout.addWidget(self.data_points_label)
        training_info_layout.addStretch()
        
        training_layout.addLayout(training_info_layout)
        training_group.setLayout(training_layout)
        layout.addWidget(training_group)
        
        recommendations_group = QGroupBox("AI Tuning Recommendations")
        recommendations_layout = QVBoxLayout()
        
        self.ai_recommendations_text = QTextEdit()
        self.ai_recommendations_text.setReadOnly(True)
        recommendations_layout.addWidget(self.ai_recommendations_text)
        
        self.get_recommendation_button = QPushButton("Get AI Recommendation")
        self.get_recommendation_button.clicked.connect(self.get_ai_recommendation)
        recommendations_layout.addWidget(self.get_recommendation_button)
        
        recommendations_group.setLayout(recommendations_layout)
        layout.addWidget(recommendations_group)
        
    def setup_virtual_dyno_tab(self):
        layout = QVBoxLayout(self.virtual_dyno_tab)
        
        controls_layout = QHBoxLayout()
        
        self.simulate_dyno_button = QPushButton("Run Dyno Simulation")
        self.simulate_dyno_button.clicked.connect(self.run_dyno_simulation)
        controls_layout.addWidget(self.simulate_dyno_button)
        
        self.simulate_quarter_button = QPushButton("Simulate 1/4 Mile")
        self.simulate_quarter_button.clicked.connect(self.simulate_quarter_mile)
        controls_layout.addWidget(self.simulate_quarter_button)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        results_group = QGroupBox("Simulation Results")
        results_layout = QVBoxLayout()
        
        self.dyno_results_text = QTextEdit()
        self.dyno_results_text.setReadOnly(True)
        results_layout.addWidget(self.dyno_results_text)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
    def change_boost_map(self, index):
        maps = ['stage0', 'stage1', 'stage2']
        if index < len(maps):
            self.advanced_maps.current_boost_map = maps[index]
            new_map_data = self.advanced_maps.boost_maps[maps[index]]
            self.boost_map_widget.map_data = new_map_data
            self.boost_map_widget.setup_1d_map()
            
    def change_timing_map(self, index):
        maps = ['conservative', 'aggressive']
        if index < len(maps):
            self.advanced_maps.current_timing_map = maps[index]
            new_map_data = self.advanced_maps.timing_maps[maps[index]]
            self.timing_map_widget.map_data = new_map_data
            self.timing_map_widget.setup_2d_map()
            
    def start_ai_training(self):
        self.ai_training_active = True
        self.training_status_label.setText("Collecting training data...")
        self.start_training_button.setEnabled(False)
        
    def train_ai_model(self):
        success, message = self.ai_tuner.train_model()
        self.training_status_label.setText(message)
        
        if success:
            self.get_recommendation_button.setEnabled(True)
            
    def save_ai_model(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save AI Model", "", "Model Files (*.model)"
        )
        if filename:
            success, message = self.ai_tuner.save_model(filename)
            QMessageBox.information(self, "Save Model", message)
            
    def load_ai_model(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load AI Model", "", "Model Files (*.model)"
        )
        if filename:
            success, message = self.ai_tuner.load_model(filename)
            QMessageBox.information(self, "Load Model", message)
            if success:
                self.get_recommendation_button.setEnabled(True)
                self.training_status_label.setText("Model loaded successfully")
                
    def get_ai_recommendation(self):
        if not self.ai_tuner.is_trained:
            QMessageBox.warning(self, "AI Not Trained", "Please train the AI model first.")
            return
            
        current_conditions = [
            self.current_data.get('Engine RPM', 3000),
            self.current_data.get('Engine Load', 50),
            self.current_data.get('Intake Pressure', 100) - 101.3,
            self.current_data.get('Intake Temp', 25),
            self.current_data.get('Timing Advance', 10)
        ]
        
        optimal_timing, message = self.ai_tuner.predict_optimal_timing(current_conditions)
        
        if optimal_timing is not None:
            current_timing = self.current_data.get('Timing Advance', 10)
            recommendation = (
                f"AI Tuning Recommendation:\n"
                f"Current Timing: {current_timing:.1f}°\n"
                f"Optimal Timing: {optimal_timing:.1f}°\n"
                f"Suggested Change: {optimal_timing - current_timing:+.1f}°\n\n"
                f"Based on:\n"
                f"- RPM: {current_conditions[0]:.0f}\n"
                f"- Load: {current_conditions[1]:.1f}%\n"
                f"- Boost: {current_conditions[2]:.1f} PSI\n"
                f"- IAT: {current_conditions[3]:.1f}°C"
            )
            
            self.ai_recommendations_text.setText(recommendation)
            
            if abs(optimal_timing - current_timing) > 0.5:
                self.ai_tuner.add_training_point(current_conditions, optimal_timing)
                self.data_points_label.setText(str(len(self.ai_tuner.training_data)))
        else:
            self.ai_recommendations_text.setText(f"Error: {message}")
            
    def run_dyno_simulation(self):
        rpm_range = list(range(2000, 7000, 500))
        power_curve = {'speed': [], 'power': []}
        
        for rpm in rpm_range:
            boost = 18.0 if self.advanced_maps.current_boost_map == 'stage1' else 15.0
            torque = self.virtual_dyno.calculate_engine_torque(rpm, boost, 10)
            power_kw = (torque * rpm) / 9549
            power_hp = power_kw * 1.341
            
            speed = (rpm * 60 * 2 * math.pi * self.virtual_dyno.wheel_radius) / (
                self.virtual_dyno.gear_ratios[2] * self.virtual_dyno.final_drive * 1000
            )
            
            power_curve['speed'].append(speed)
            power_curve['power'].append(power_hp)
            
        peak_power = max(power_curve['power'])
        peak_torque = max([(power * 9549) / rpm for power, rpm in zip(power_curve['power'], rpm_range)])
        
        results = (
            f"Virtual Dyno Results - {self.advanced_maps.current_boost_map.upper()}\n"
            f"Peak Power: {peak_power:.1f} HP\n"
            f"Peak Torque: {peak_torque:.1f} Nm\n"
            f"Power Band: 2000-7000 RPM\n\n"
            f"Estimated Gains vs Stock:\n"
            f"+{peak_power - 263:.1f} HP (Stock: 263 HP)\n"
            f"+{peak_torque - 380:.1f} Nm (Stock: 380 Nm)"
        )
        
        self.dyno_results_text.setText(results)
        
    def simulate_quarter_mile(self):
        speed_range = list(range(0, 200, 10))
        power_curve = {'speed': speed_range, 'power': []}
        
        for speed in speed_range:
            if speed < 40:
                power = 50 + (speed / 40) * 150
            elif speed < 120:
                power = 200
            else:
                power = 200 * (1 - (speed - 120) / 80)
            power_curve['power'].append(power)
            
        # Simple quarter mile calculation
        time = 14.5 - (0.5 if self.advanced_maps.current_boost_map == 'stage1' else 0)
        trap_speed = 150 if self.advanced_maps.current_boost_map == 'stage1' else 140
        
        results = (
            f"Quarter Mile Simulation\n"
            f"Elapsed Time: {time:.2f} seconds\n"
            f"Trap Speed: {trap_speed:.1f} km/h\n"
            f"Trap Speed: {trap_speed / 1.609:.1f} mph\n\n"
        )
        
        if time < 13.5:
            results += "Excellent - Highly tuned vehicle"
        elif time < 14.5:
            results += "Good - Well tuned"
        elif time < 15.5:
            results += "Average - Stock performance"
        else:
            results += "Below average - Check vehicle health"
            
        self.dyno_results_text.setText(results)
        
    def on_data_received(self, parameter, value):
        super().on_data_received(parameter, value)
        
        if parameter == "Engine RPM" and hasattr(self, 'obd_interface'):
            current_time = time.time()
            if hasattr(self, 'last_enhanced_read'):
                if current_time - self.last_enhanced_read > 2.0:
                    self.read_enhanced_parameters()
                    self.last_enhanced_read = current_time
            else:
                self.last_enhanced_read = current_time
                
        if hasattr(self, 'ai_training_active') and self.ai_training_active:
            self.collect_training_data()
            
    def read_enhanced_parameters(self):
        try:
            knock = self.obd_interface.read_knock_data()
            if knock is not None:
                self.knock_retard_label.setText(f"{knock}°")
                
            wg_duty = self.obd_interface.read_wastegate_duty()
            if wg_duty is not None:
                self.wastegate_duty_label.setText(f"{wg_duty}%")
                
        except Exception as e:
            print(f"Enhanced parameter read error: {e}")
            
    def collect_training_data(self):
        try:
            current_load = self.current_data.get('Engine Load', 0)
            current_rpm = self.current_data.get('Engine RPM', 0)
            
            if current_load > 50 and current_rpm > 2500:
                features = [
                    current_rpm,
                    current_load,
                    (self.current_data.get('Intake Pressure', 100) - 101.3),
                    self.current_data.get('Intake Temp', 25),
                    self.current_data.get('Timing Advance', 10)
                ]
                
                target_timing = self.current_data.get('Timing Advance', 10)
                
                self.ai_tuner.add_training_point(features, target_timing)
                self.data_points_label.setText(str(len(self.ai_tuner.training_data)))
                
        except Exception as e:
            print(f"Training data collection error: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Set dark theme
    app.setStyle('Fusion')
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Highlight, QColor(142, 45, 197).lighter())
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    
    window = EnhancedMazdaspeedTunerGUI()
    window.show()
    
    sys.exit(app.exec_())