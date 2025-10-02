# mazda_tool/ui/main_window.py
import sys
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTabWidget, QStatusBar, QMessageBox, QApplication,
                             QToolBar, QAction, QLabel, QProgressBar)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor

# Import our modules
from mazda_tool.core.config_manager import ConfigManager
from mazda_tool.core.obd_connection import AdvancedOBD2Bluetooth
from mazda_tool.ui.ai_learning_tab import AILearningTab
from mazda_tool.ui.diagnostic_tab import DiagnosticTab
from mazda_tool.ui.tuning_tab import TuningTab
from mazda_tool.ui.help_system import MazdaspeedHelpSystem

class UltimateMazdaTechnicianSuite(QMainWindow):
    """
    MAIN APPLICATION WINDOW
    The complete Mazda Ultimate Technician Tool interface
    """
    
    # Signals for cross-tab communication
    vehicle_connected = pyqtSignal(bool)
    ai_recommendation_generated = pyqtSignal(object)
    
    def __init__(self, settings, config_manager):
        super().__init__()
        self.settings = settings
        self.config_manager = config_manager
        self.obd_connection = AdvancedOBD2Bluetooth()
        
        # Initialize UI components
        self.ai_learning_tab = None
        self.diagnostic_tab = None
        self.tuning_tab = None
        self.help_system = None
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Initialize the main window UI"""
        self.setWindowTitle("🚀 Mazda Ultimate Technician Suite")
        self.setGeometry(100, 100, 1400, 900)
        
        # Apply the professional theme
        self.apply_professional_theme()
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Setup toolbar
        self.setup_toolbar()
        
        # Setup main tab widget
        self.setup_main_tabs(main_layout)
        
        # Setup status bar
        self.setup_status_bar()
        
        # Apply saved window state
        self.load_window_state()
        
    def apply_professional_theme(self):
        """Apply the professional Mazda-themed styling"""
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #0a1f2e, stop:1 #1a2b3c);
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 2px solid #2a4d6a;
                background-color: #1a3a4f;
                border-radius: 8px;
                margin-top: 2px;
            }
            QTabBar::tab {
                background-color: #2a5a7a;
                color: #ffffff;
                padding: 12px 20px;
                margin-right: 3px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 10pt;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #00cc88, stop:1 #00aa66);
                color: #002211;
                border: 1px solid #00ff88;
            }
            QTabBar::tab:hover {
                background-color: #3a6a8a;
            }
            QTabBar::tab:!selected:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a7a9a, stop:1 #2a6a8a);
            }
            QGroupBox {
                color: #88ffcc;
                border: 2px solid #2a5a7a;
                border-radius: 8px;
                margin-top: 1ex;
                font-weight: bold;
                font-size: 11pt;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 12px 0 12px;
                background-color: #1a3a4f;
                border-radius: 4px;
            }
        """)
        
    def setup_toolbar(self):
        """Setup the main application toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setStyleSheet("""
            QToolBar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1a3a4f, stop:1 #2a4d6a);
                border: none;
                padding: 5px;
                spacing: 10px;
            }
            QToolButton {
                color: white;
                background: transparent;
                border: 1px solid #2a5a7a;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QToolButton:hover {
                background: #2a5a7a;
                border: 1px solid #3a6a8a;
            }
        """)
        self.addToolBar(toolbar)
        
        # Connection actions
        connect_action = QAction("🔗 Connect Vehicle", self)
        connect_action.setStatusTip("Connect to vehicle via OBD-II")
        connect_action.triggered.connect(self.connect_vehicle)
        toolbar.addAction(connect_action)
        
        disconnect_action = QAction("🔴 Disconnect", self)
        disconnect_action.setStatusTip("Disconnect from vehicle")
        disconnect_action.triggered.connect(self.disconnect_vehicle)
        toolbar.addAction(disconnect_action)
        
        toolbar.addSeparator()
        
        # AI Actions
        ai_quick_start = QAction("🧠 Quick AI Learn", self)
        ai_quick_start.setStatusTip("Start 10-minute AI learning session")
        ai_quick_start.triggered.connect(self.quick_ai_learn)
        toolbar.addAction(ai_quick_start)
        
        toolbar.addSeparator()
        
        # System actions
        settings_action = QAction("⚙️ Settings", self)
        settings_action.setStatusTip("Open application settings")
        settings_action.triggered.connect(self.open_settings)
        toolbar.addAction(settings_action)
        
        help_action = QAction("❓ Help", self)
        help_action.setStatusTip("Open help system")
        help_action.triggered.connect(self.open_help)
        toolbar.addAction(help_action)
        
        # Connection status indicator
        toolbar.addWidget(QLabel(" | "))
        self.connection_status_label = QLabel("🔴 DISCONNECTED")
        self.connection_status_label.setStyleSheet("color: #ff6666; font-weight: bold;")
        toolbar.addWidget(self.connection_status_label)
        
        toolbar.addWidget(QLabel(" | "))
        
        # Vehicle info
        self.vehicle_info_label = QLabel("No vehicle connected")
        self.vehicle_info_label.setStyleSheet("color: #aaddff;")
        toolbar.addWidget(self.vehicle_info_label)
        
    def setup_main_tabs(self, main_layout):
        """Setup the main tabbed interface"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setTabPosition(QTabWidget.North)
        
        # Create and add tabs
        self.setup_dashboard_tab()
        self.setup_ai_learning_tab()
        self.setup_diagnostic_tab()
        self.setup_tuning_tab()
        self.setup_help_tab()
        
        main_layout.addWidget(self.tab_widget)
        
    def setup_dashboard_tab(self):
        """Setup the dashboard/overview tab"""
        from PyQt5.QtWidgets import QTextEdit, QGridLayout, QFrame
        
        dashboard_tab = QWidget()
        layout = QVBoxLayout(dashboard_tab)
        
        # Header
        header = QLabel("🎯 MAZDA ULTIMATE TECHNICIAN SUITE")
        header.setFont(QFont("Arial", 20, QFont.Bold))
        header.setStyleSheet("""
            color: #00ff88; 
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #004422, stop:1 #006633);
            padding: 20px; 
            border-radius: 15px;
            border: 3px solid #00cc88;
        """)
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Quick actions grid
        actions_frame = QFrame()
        actions_frame.setStyleSheet("""
            QFrame {
                background: #1a3a4f;
                border: 2px solid #2a5a7a;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        actions_layout = QGridLayout(actions_frame)
        
        quick_actions = [
            ("🧠 Start AI Learning", self.start_ai_from_dashboard, "#00cc88"),
            ("🔍 Run Diagnostics", self.run_quick_diagnostics, "#4CAF50"),
            ("⚙️ Quick Tune", self.open_quick_tune, "#FF9800"),
            ("📊 View Reports", self.open_reports, "#2196F3"),
            ("🔧 Tools", self.open_tools, "#9C27B0"),
            ("📚 Learning", self.open_learning, "#795548")
        ]
        
        from PyQt5.QtWidgets import QPushButton
        row, col = 0, 0
        for text, slot, color in quick_actions:
            btn = QPushButton(text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {color}, stop:1 #2a5a7a);
                    color: white;
                    border: none;
                    padding: 15px;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 11pt;
                    min-height: 60px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {color}, stop:1 #3a6a8a);
                }}
            """)
            btn.clicked.connect(slot)
            actions_layout.addWidget(btn, row, col)
            
            col += 1
            if col > 2:
                col = 0
                row += 1
        
        layout.addWidget(actions_frame)
        
        # Recent activity
        recent_activity = QTextEdit()
        recent_activity.setReadOnly(True)
        recent_activity.setHtml("""
            <h3 style='color: #88ffcc;'>Welcome to Mazda Ultimate Technician Suite!</h3>
            <p style='color: #aaddff;'>Get started by:</p>
            <ul style='color: #aaddff;'>
                <li>Connecting to your vehicle using the toolbar</li>
                <li>Starting an AI learning session to personalize your tune</li>
                <li>Running diagnostics to check vehicle health</li>
                <li>Exploring the tuning options for your Mazdaspeed 3</li>
            </ul>
            <p style='color: #ffaa00;'><b>Pro Tip:</b> The AI Learning system adapts to your driving style for optimal performance!</p>
        """)
        recent_activity.setMaximumHeight(200)
        layout.addWidget(recent_activity)
        
        self.tab_widget.addTab(dashboard_tab, "🚀 Dashboard")
        
    def setup_ai_learning_tab(self):
        """Setup the AI Learning tab"""
        self.ai_learning_tab = AILearningTab(self.obd_connection, self.config_manager)
        self.tab_widget.addTab(self.ai_learning_tab, "🧠 AI Learning")
        
    def setup_diagnostic_tab(self):
        """Setup the Diagnostic tab"""
        self.diagnostic_tab = DiagnosticTab(self.obd_connection)
        self.tab_widget.addTab(self.diagnostic_tab, "🔍 Diagnostics")
        
    def setup_tuning_tab(self):
        """Setup the Tuning tab"""
        self.tuning_tab = TuningTab(self.obd_connection, self.config_manager)
        self.tab_widget.addTab(self.tuning_tab, "⚙️ Tuning")
        
    def setup_help_tab(self):
        """Setup the Help system tab"""
        self.help_system = MazdaspeedHelpSystem()
        self.tab_widget.addTab(self.help_system, "📚 Help & Guides")
        
    def setup_status_bar(self):
        """Setup the status bar"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # Main status message
        self.status_label = QLabel("Ready to connect to vehicle")
        status_bar.addWidget(self.status_label)
        
        # Progress bar for operations
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        status_bar.addPermanentWidget(self.progress_bar)
        
        # Version info
        version_label = QLabel("v1.0.0 - Mazda Ultimate Technician Suite")
        version_label.setStyleSheet("color: #88ffcc;")
        status_bar.addPermanentWidget(version_label)
        
    def setup_connections(self):
        """Setup signal connections between components"""
        # Connect AI tab signals
        if self.ai_learning_tab:
            self.ai_learning_tab.recommendation_generated.connect(self.handle_ai_recommendation)
            self.ai_learning_tab.session_status_changed.connect(self.handle_ai_session_change)
            
        # Connect vehicle connection signals
        self.vehicle_connected.connect(self.handle_vehicle_connection)
        
    def connect_vehicle(self):
        """Connect to vehicle via OBD-II"""
        self.status_label.setText("Searching for OBD-II adapter...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Simulate connection process (replace with actual OBD connection)
        QTimer.singleShot(2000, self.simulate_connection_success)
        
    def simulate_connection_success(self):
        """Simulate successful vehicle connection (for testing)"""
        self.connection_status_label.setText("🟢 CONNECTED")
        self.connection_status_label.setStyleSheet("color: #00ff88; font-weight: bold;")
        self.vehicle_info_label.setText("2011 Mazdaspeed 3 - MZR DISI 2.3L Turbo")
        self.status_label.setText("Connected to vehicle - Ready for operations")
        self.progress_bar.setVisible(False)
        self.vehicle_connected.emit(True)
        
        # Enable AI learning tab
        if self.ai_learning_tab:
            self.ai_learning_tab.set_obd_connection(self.obd_connection)
            
    def disconnect_vehicle(self):
        """Disconnect from vehicle"""
        self.connection_status_label.setText("🔴 DISCONNECTED")
        self.connection_status_label.setStyleSheet("color: #ff6666; font-weight: bold;")
        self.vehicle_info_label.setText("No vehicle connected")
        self.status_label.setText("Disconnected from vehicle")
        self.vehicle_connected.emit(False)
        
    def handle_vehicle_connection(self, connected: bool):
        """Handle vehicle connection state changes"""
        if connected:
            # Enable features that require vehicle connection
            pass
        else:
            # Disable vehicle-dependent features
            pass
            
    def handle_ai_recommendation(self, recommendation):
        """Handle AI-generated tuning recommendations"""
        self.ai_recommendation_generated.emit(recommendation)
        self.status_label.setText(f"AI Recommendation: {recommendation.parameter}")
        
        # Show notification
        QMessageBox.information(self, "🎯 AI Tuning Recommendation", 
                              f"Parameter: {recommendation.parameter}\n"
                              f"Recommended: {recommendation.recommended_value}\n"
                              f"Confidence: {recommendation.confidence:.1%}\n\n"
                              f"Click the Tuning tab to apply this recommendation.")
        
    def handle_ai_session_change(self, active: bool):
        """Handle AI learning session state changes"""
        if active:
            self.status_label.setText("AI Learning Session Active - Drive normally")
        else:
            self.status_label.setText("AI Learning Session Complete - Ready for analysis")
            
    def quick_ai_learn(self):
        """Start a quick AI learning session"""
        if self.connection_status_label.text() != "🟢 CONNECTED":
            QMessageBox.warning(self, "Not Connected", 
                              "Please connect to a vehicle first.")
            return
            
        # Switch to AI tab and start learning
        self.tab_widget.setCurrentIndex(1)  # AI Learning tab
        self.ai_learning_tab.start_ai_learning()
        
    def start_ai_from_dashboard(self):
        """Start AI learning from dashboard button"""
        self.quick_ai_learn()
        
    def run_quick_diagnostics(self):
        """Run quick diagnostics from dashboard"""
        self.tab_widget.setCurrentIndex(2)  # Diagnostics tab
        # Trigger quick diagnostics scan
        
    def open_quick_tune(self):
        """Open quick tune from dashboard"""
        self.tab_widget.setCurrentIndex(3)  # Tuning tab
        
    def open_reports(self):
        """Open reports section"""
        QMessageBox.information(self, "Reports", 
                              "Report system coming soon!")
        
    def open_tools(self):
        """Open tools section"""
        QMessageBox.information(self, "Tools", 
                              "Additional tools coming soon!")
        
    def open_learning(self):
        """Open learning section"""
        self.tab_widget.setCurrentIndex(4)  # Help tab
        
    def open_settings(self):
        """Open application settings"""
        QMessageBox.information(self, "Settings", 
                              "Settings dialog coming soon!")
        
    def open_help(self):
        """Open help system"""
        self.tab_widget.setCurrentIndex(4)  # Help tab
        
    def load_window_state(self):
        """Load saved window state and settings"""
        # Restore window geometry
        geometry = self.settings.value("window_geometry")
        if geometry:
            self.restoreGeometry(geometry)
            
        # Restore window state
        state = self.settings.value("window_state")
        if state:
            self.restoreState(state)
            
        # Restore last active tab
        last_tab = self.settings.value("last_active_tab", 0, type=int)
        self.tab_widget.setCurrentIndex(last_tab)
        
    def closeEvent(self, event):
        """Handle application close event"""
        # Save window state
        self.settings.setValue("window_geometry", self.saveGeometry())
        self.settings.setValue("window_state", self.saveState())
        self.settings.setValue("last_active_tab", self.tab_widget.currentIndex())
        
        # Stop any active sessions
        if self.ai_learning_tab and self.ai_learning_tab.session_active:
            reply = QMessageBox.question(self, "Active AI Session",
                                       "An AI learning session is active. Stop learning and close?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.ai_learning_tab.stop_ai_learning()
            else:
                event.ignore()
                return
                
        # Save configuration
        self.config_manager.save_settings()
        
        event.accept()

# Stub classes for missing dependencies (remove when actual classes are available)
class DiagnosticTab(QWidget):
    def __init__(self, obd_connection):
        super().__init__()
        layout = QVBoxLayout(self)
        label = QLabel("🔍 DIAGNOSTICS TAB - Coming Soon!")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #88ffcc; font-size: 16pt; padding: 50px;")
        layout.addWidget(label)

class TuningTab(QWidget):
    def __init__(self, obd_connection, config_manager):
        super().__init__()
        layout = QVBoxLayout(self)
        label = QLabel("⚙️ TUNING TAB - Coming Soon!")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #88ffcc; font-size: 16pt; padding: 50px;")
        layout.addWidget(label)