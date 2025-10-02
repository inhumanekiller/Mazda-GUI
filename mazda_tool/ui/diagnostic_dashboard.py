# mazda_tool/ui/diagnostic_dashboard.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QGroupBox, QLabel, QProgressBar, QTextEdit, 
                             QPushButton, QTabWidget)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor

class DiagnosticDashboard(QWidget):
    """
    Professional diagnostic dashboard with real-time health monitoring
    """
    
    def __init__(self, data_manager, diagnostic_system):
        super().__init__()
        self.data_manager = data_manager
        self.diagnostic_system = diagnostic_system
        self.health_scores = {}
        
        self.setup_ui()
        self.setup_data_connections()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # 1Hz update

    def setup_ui(self):
        """Create the professional diagnostic interface"""
        main_layout = QVBoxLayout()
        
        # Health Overview Section
        health_group = QGroupBox("Vehicle Health Overview")
        health_layout = QGridLayout()
        
        # Major system health indicators
        self.health_indicators = {
            'engine': self.create_health_indicator("Engine", 95),
            'turbo': self.create_health_indicator("Turbo System", 88),
            'fuel': self.create_health_indicator("Fuel System", 92),
            'ignition': self.create_health_indicator("Ignition", 96),
            'emissions': self.create_health_indicator("Emissions", 85),
            'overall': self.create_health_indicator("Overall Health", 90)
        }
        
        # Add to grid
        for i, (system, widget) in enumerate(self.health_indicators.items()):
            row = i // 3
            col = i % 3
            health_layout.addWidget(widget, row, col)
            
        health_group.setLayout(health_layout)
        
        # Real-time Parameters Section
        params_group = QGroupBox("Real-time Critical Parameters")
        params_layout = QGridLayout()
        
        self.parameter_displays = {
            'boost': self.create_parameter_display("Boost Pressure", "12.5", "PSI"),
            'hpfp': self.create_parameter_display("HPFP Pressure", "1650", "PSI"),
            'afr': self.create_parameter_display("Air/Fuel Ratio", "12.1", "λ"),
            'knock': self.create_parameter_display("Knock Retard", "0.5", "°"),
            'temps': self.create_parameter_display("Coolant Temp", "92", "°C"),
            'load': self.create_parameter_display("Engine Load", "78", "%")
        }
        
        for i, (param, widget) in enumerate(self.parameter_displays.items()):
            row = i // 3
            col = i % 3
            params_layout.addWidget(widget, row, col)
            
        params_group.setLayout(params_layout)
        
        # Issues & Recommendations Section
        issues_group = QGroupBox("Active Issues & Recommendations")
        issues_layout = QVBoxLayout()
        
        self.issues_display = QTextEdit()
        self.issues_display.setMaximumHeight(150)
        self.issues_display.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #ff4444;
                font-family: Consolas;
                font-size: 10pt;
                border: 1px solid #444;
            }
        """)
        
        issues_layout.addWidget(self.issues_display)
        issues_group.setLayout(issues_layout)
        
        # Control Buttons
        button_layout = QHBoxLayout()
        self.full_diagnostic_btn = QPushButton("Run Full Diagnostic")
        self.clear_codes_btn = QPushButton("Clear Diagnostic Codes")
        self.export_report_btn = QPushButton("Export Health Report")
        
        button_layout.addWidget(self.full_diagnostic_btn)
        button_layout.addWidget(self.clear_codes_btn)
        button_layout.addWidget(self.export_report_btn)
        
        # Assemble main layout
        main_layout.addWidget(health_group)
        main_layout.addWidget(params_group)
        main_layout.addWidget(issues_group)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)

    def create_health_indicator(self, system_name, initial_score):
        """Create a health indicator widget for a vehicle system"""
        group = QGroupBox(system_name)
        layout = QVBoxLayout()
        
        # Health score progress bar
        progress = QProgressBar()
        progress.setMinimum(0)
        progress.setMaximum(100)
        progress.setValue(initial_score)
        progress.setFormat(f"{initial_score}%")
        
        # Color coding based on health
        if initial_score >= 90:
            progress.setStyleSheet("QProgressBar::chunk { background-color: #00cc00; }")
        elif initial_score >= 75:
            progress.setStyleSheet("QProgressBar::chunk { background-color: #ffaa00; }")
        else:
            progress.setStyleSheet("QProgressBar::chunk { background-color: #ff4444; }")
            
        # Status label
        status_label = QLabel("Good")
        status_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(progress)
        layout.addWidget(status_label)
        group.setLayout(layout)
        
        return group

    def create_parameter_display(self, parameter_name, value, unit):
        """Create a parameter display widget"""
        group = QGroupBox(parameter_name)
        layout = QVBoxLayout()
        
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        
        unit_label = QLabel(unit)
        unit_label.setAlignment(Qt.AlignCenter)
        unit_label.setStyleSheet("color: #888;")
        
        layout.addWidget(value_label)
        layout.addWidget(unit_label)
        group.setLayout(layout)
        
        return group

    def update_display(self):
        """Update all displays with current data"""
        # Update health scores
        diagnostic_result = self.diagnostic_system.run_comprehensive_diagnostic()
        
        # Update parameter displays with live data
        if self.data_manager.live_data_buffer:
            current_data = self.data_manager.live_data_buffer[-1]
            
            # Update boost pressure
            if 'boost_pressure' in current_data:
                boost = current_data['boost_pressure']
                self.update_parameter_display('boost', f"{boost:.1f}")
                
                # Color code based on safety
                if boost > 22:
                    self.parameter_displays['boost'].setStyleSheet("QGroupBox { color: #ff4444; }")
                elif boost > 18:
                    self.parameter_displays['boost'].setStyleSheet("QGroupBox { color: #ffaa00; }")
                else:
                    self.parameter_displays['boost'].setStyleSheet("QGroupBox { color: #00cc00; }")
                    
            # Update other parameters similarly...
            
        # Update issues display
        active_issues = self.diagnostic_system.get_active_issues()
        issues_text = "✅ No active issues detected" if not active_issues else ""
        
        for issue in active_issues:
            issues_text += f"⚠️ {issue['description']} - Severity: {issue['severity']}\n"
            
        self.issues_display.setText(issues_text)