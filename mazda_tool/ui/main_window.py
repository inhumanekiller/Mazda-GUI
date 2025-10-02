# mazda_tool/ui/main_window.py - UPDATED INTEGRATION VERSION
class UltimateMazdaTechnicianSuite(QMainWindow):
    def __init__(self, settings, config_manager):
        super().__init__()
        self.settings = settings
        self.config_manager = config_manager
        
        # CENTRAL DATA MANAGER - The communication hub
        self.data_manager = DataManager()
        
        # Initialize components with shared data manager
        self.obd_connection = AdvancedOBD2Bluetooth(self.data_manager)
        self.ai_learning_tab = AILearningTab(self.data_manager, self.config_manager)
        self.diagnostic_tab = DiagnosticTab(self.data_manager)
        self.tuning_tab = TuningTab(self.data_manager, self.config_manager)
        
        self.setup_ui()
        self.setup_cross_component_connections()

    def setup_cross_component_connections(self):
        """Connect all components through the data manager"""
        
        # AI → Tuning: When AI makes recommendation, show in tuning tab
        self.data_manager.ai_recommendation_added.connect(
            self.tuning_tab.handle_ai_recommendation
        )
        
        # Diagnostics → AI: When issues found, inform AI for safety
        self.data_manager.diagnostic_codes_updated.connect(
            self.ai_learning_tab.handle_diagnostic_issues
        )
        
        # Live Data → All: When new OBD data arrives, update all tabs
        self.data_manager.live_data_updated.connect(
            self.ai_learning_tab.update_live_data_display
        )
        self.data_manager.live_data_updated.connect(
            self.diagnostic_tab.update_live_gauges
        )
        self.data_manager.live_data_updated.connect(
            self.tuning_tab.update_performance_metrics
        )
        
        # Vehicle Connection → All: Enable/disable features
        self.data_manager.vehicle_connection_changed.connect(
            self.handle_global_connection_change
        )

    def handle_global_connection_change(self, connected: bool):
        """Enable/disable features across all tabs based on connection"""
        self.ai_learning_tab.setEnabled(connected)
        self.diagnostic_tab.setEnabled(connected) 
        self.tuning_tab.setEnabled(connected)
        
        if connected:
            self.status_label.setText("Vehicle connected - All features enabled")
        else:
            self.status_label.setText("Vehicle disconnected - Features limited")