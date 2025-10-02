# mazda_tool/ui/ai_learning_tab.py - ENHANCED
class AILearningTab(QWidget):
    """AI Learning Tab with Real OBD Integration"""
    
    def __init__(self, obd_connection=None, config_manager=None):
        super().__init__()
        self.obd_connection = obd_connection
        self.config_manager = config_manager
        self.session_active = False
        self.real_data_points = 0
        
        self.setup_ui()
        self.setup_obd_connections()

    def setup_obd_connections(self):
        """Connect to OBD data signals"""
        if self.obd_connection:
            self.obd_connection.data_received.connect(self.process_real_data)

    def process_real_data(self, live_data):
        """Process REAL OBD data for AI learning"""
        if self.session_active and live_data:
            self.real_data_points += 1
            
            # Update UI with real data
            self.data_points_label.setText(f"Real Data Points: {self.real_data_points}")
            
            # Display current parameters
            self.update_live_display(live_data)
            
            # TODO: Send to AI engine for analysis
            # adjustment = self.ai_tuner.process_driving_data(live_data)

    def update_live_display(self, data):
        """Update the display with real OBD data"""
        display_text = "📊 LIVE OBD DATA:\n\n"
        
        if 'rpm' in data:
            display_text += f"• RPM: {data['rpm']:.0f}\n"
        if 'speed' in data:
            display_text += f"• Speed: {data['speed']:.0f} km/h\n"
        if 'engine_load' in data:
            display_text += f"• Engine Load: {data['engine_load']:.1f}%\n"
        if 'boost_pressure' in data:
            display_text += f"• Boost: {data['boost_pressure']:.1f} PSI\n"
        if 'intake_temp' in data:
            display_text += f"• Intake Temp: {data['intake_temp']:.0f}°C\n"
            
        self.stats_display.setText(display_text)

    def start_ai_learning(self):
        """Start AI learning with real OBD data"""
        if not self.obd_connection or not self.obd_connection.connected:
            QMessageBox.warning(self, "Not Connected", 
                              "Please connect to a vehicle first.")
            return False
            
        self.session_active = True
        self.real_data_points = 0
        self.update_ui_state(True)
        
        self.recommendations_display.setText(
            "🧠 AI LEARNING ACTIVE\n\n"
            "Collecting real driving data from OBD-II...\n"
            "Drive normally to establish your driving patterns.\n\n"
            "The AI will analyze:\n"
            "• Acceleration habits\n" 
            "• Shift points and RPM usage\n"
            "• Throttle application patterns\n"
            "• Boost and temperature behavior\n"
        )
        
        return True