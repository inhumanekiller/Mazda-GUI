# mazda_tool/ui/ai_learning_tab.py - REAL VERSION
class AILearningTab(QWidget):
    def __init__(self, data_manager: DataManager, config_manager=None):
        super().__init__()
        self.data_manager = data_manager
        self.config_manager = config_manager
        self.ai_tuner = MazdaAITuner(config_manager)
        
        # REAL state - no simulations
        self.session_active = False
        self.data_points_collected = 0
        
        self.setup_ui()
        self.setup_data_manager_connections()

    def collect_driving_data(self):
        """ONLY processes REAL data from Data Manager"""
        # This method is now triggered by Data Manager signals
        # No simulated data collection
        pass

    def start_ai_learning(self):
        """Start AI learning with REAL vehicle connection"""
        vehicle_state = self.data_manager.get_vehicle_state()
        
        if not vehicle_state.connected:
            QMessageBox.warning(self, "Not Connected", 
                              "Please connect to a REAL vehicle first.")
            return False
            
        # Get REAL vehicle info
        vehicle_profile = {
            "model": vehicle_state.model,
            "year": vehicle_state.year, 
            "vin": vehicle_state.vin,
            "modifications": self.config_manager.settings.get('vehicle', {}).get('modifications', ['stock'])
        }
        
        # Start REAL AI session
        startup_message = self.ai_tuner.start_learning_session(vehicle_profile)
        self.recommendations_display.setText(startup_message)
        
        self.session_active = True
        self.update_ui_state(True)
        
        self.log_message("🟢 AI LEARNING STARTED - Analyzing REAL driving data")
        return True

    def process_live_data(self, live_data: Dict):
        """Process REAL OBD data through AI system"""
        if not self.session_active or not live_data:
            return
            
        try:
            # Validate we have real data (not empty dict)
            if any(key in live_data for key in ['rpm', 'speed', 'engine_load']):
                self.data_points_collected += 1
                
                # Send REAL data to AI tuner
                adjustment = self.ai_tuner.process_driving_data(live_data)
                
                if adjustment:
                    # Send REAL recommendation to Data Manager
                    self.data_manager.add_ai_recommendation(adjustment)
                    self.display_ai_recommendation(adjustment)
                    
                # Update UI with REAL data count
                self.data_points_label.setText(f"Real Data Points: {self.data_points_collected}")
                
        except Exception as e:
            self.log_message(f"🔴 AI Processing Error: {str(e)}")

    # REMOVED: _simulate_driving_data() - No more fake data!