# mazda_tool/ui/ai_learning_tab.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTextEdit, QLabel, QProgressBar, QGroupBox,
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QSplitter, QFrame, QScrollArea)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette, QLinearGradient
import json
from datetime import datetime

from mazda_tool.core.ai_tuner import MazdaAITuner, TuningAdjustment

class AILearningTab(QWidget):
    """
    MAZDA AI LEARNING INTERFACE
    Real-time visualization of AI learning and tuning optimization
    """
    
    # Signals for cross-tab communication
    recommendation_generated = pyqtSignal(TuningAdjustment)
    session_status_changed = pyqtSignal(bool)
    
    def __init__(self, obd_connection=None, config_manager=None):
        super().__init__()
        self.ai_tuner = MazdaAITuner(config_manager)
        self.obd_connection = obd_connection
        self.config_manager = config_manager
        
        # UI State
        self.session_active = False
        self.data_points_collected = 0
        self.last_recommendation = None
        
        # Timers
        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self.collect_driving_data)
        
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self.update_ui_elements)
        
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress_animation)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the AI Learning Tab interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header Section
        self.setup_header_section(main_layout)
        
        # Control Section
        self.setup_control_section(main_layout)
        
        # Main Content Splitter
        splitter = QSplitter(Qt.Horizontal)
        self.setup_left_panel(splitter)
        self.setup_right_panel(splitter)
        
        splitter.setSizes([400, 600])
        main_layout.addWidget(splitter)
        
        # Initialize UI state
        self.update_ui_state(False)
        
    def setup_header_section(self, layout):
        """Setup the header with title and status"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #1a3a4f, stop:1 #2a4d6a);
                border-radius: 10px;
                padding: 10px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        
        # Main title
        title_label = QLabel("🧠 MAZDA AI LEARNING TUNER")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setStyleSheet("color: #00ff88; padding: 5px;")
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Adaptive Tuning Powered by Mazda Engineering Intelligence")
        subtitle_label.setFont(QFont("Arial", 10))
        subtitle_label.setStyleSheet("color: #88ffcc; padding: 2px;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(subtitle_label)
        
        # Status bar
        self.status_label = QLabel("🔴 READY - Connect to vehicle and start AI learning")
        self.status_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                color: #ff6666;
                padding: 8px;
                border-radius: 5px;
                border: 1px solid #444444;
            }
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.status_label)
        
        layout.addWidget(header_frame)
    
    def setup_control_section(self, layout):
        """Setup the control buttons and progress section"""
        control_group = QGroupBox("🎛️ AI LEARNING CONTROLS")
        control_group.setStyleSheet("""
            QGroupBox {
                color: #88ffcc;
                font-weight: bold;
                font-size: 12pt;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)
        control_layout = QVBoxLayout(control_group)
        
        # Button Row
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("🧠 START AI LEARNING")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00cc88, stop:1 #00aa66);
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00dd99, stop:1 #00bb77);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00aa66, stop:1 #008855);
            }
            QPushButton:disabled {
                background: #445566;
                color: #888888;
            }
        """)
        self.start_btn.clicked.connect(self.start_ai_learning)
        
        self.stop_btn = QPushButton("🛑 STOP LEARNING")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff6666, stop:1 #cc5555);
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff7777, stop:1 #dd6666);
            }
            QPushButton:disabled {
                background: #445566;
                color: #888888;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_ai_learning)
        
        self.analyze_btn = QPushButton("📊 GENERATE AI REPORT")
        self.analyze_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5CBF60, stop:1 #55b059);
            }
            QPushButton:disabled {
                background: #445566;
                color: #888888;
            }
        """)
        self.analyze_btn.clicked.connect(self.generate_ai_report)
        
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.analyze_btn)
        button_layout.addStretch()
        
        control_layout.addLayout(button_layout)
        
        # Progress Section
        progress_layout = QVBoxLayout()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #2a5a7a;
                border-radius: 8px;
                text-align: center;
                color: white;
                font-weight: bold;
                height: 20px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00cc88, stop:0.5 #00aaff, stop:1 #8844ff);
                border-radius: 6px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        # Progress labels
        progress_labels_layout = QHBoxLayout()
        
        self.progress_label = QLabel("Learning Progress: 0%")
        self.progress_label.setStyleSheet("color: #aaddff; font-weight: bold;")
        
        self.data_points_label = QLabel("Data Points: 0")
        self.data_points_label.setStyleSheet("color: #aaddff;")
        
        progress_labels_layout.addWidget(self.progress_label)
        progress_labels_layout.addStretch()
        progress_labels_layout.addWidget(self.data_points_label)
        
        progress_layout.addLayout(progress_labels_layout)
        control_layout.addLayout(progress_layout)
        
        layout.addWidget(control_group)
    
    def setup_left_panel(self, splitter):
        """Setup the left panel with recommendations and analysis"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # AI Recommendations Group
        recommendations_group = QGroupBox("💡 AI TUNING RECOMMENDATIONS")
        recommendations_group.setStyleSheet("""
            QGroupBox {
                color: #88ffcc;
                font-weight: bold;
                font-size: 11pt;
            }
        """)
        recommendations_layout = QVBoxLayout(recommendations_group)
        
        self.recommendations_display = QTextEdit()
        self.recommendations_display.setReadOnly(True)
        self.recommendations_display.setFont(QFont("Consolas", 10))
        self.recommendations_display.setStyleSheet("""
            QTextEdit {
                background-color: #1a2b3c;
                color: #e8f4f8;
                border: 1px solid #2a5a7a;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        # Set initial welcome message
        welcome_message = """
🤖 WELCOME TO MAZDA AI TUNER!

I'm your intelligent tuning assistant that learns how you drive
and optimizes your Mazdaspeed 3's performance specifically for YOU.

WHAT I'LL DO:
• Analyze your driving patterns in real-time
• Learn your acceleration and shifting preferences  
• Understand your typical driving routes and conditions
• Recommend personalized tuning adjustments
• Ensure your tune matches your driving style

GET STARTED:
1. Ensure your OBD-II adapter is connected
2. Click 'START AI LEARNING' above
3. Drive normally for 20-30 minutes
4. Watch as I learn and optimize!

Ready to begin your personalized tuning journey?
"""
        self.recommendations_display.setText(welcome_message)
        
        recommendations_layout.addWidget(self.recommendations_display)
        left_layout.addWidget(recommendations_group)
        
        # Quick Stats Group
        stats_group = QGroupBox("📊 LIVE SESSION STATS")
        stats_group.setStyleSheet("""
            QGroupBox {
                color: #88ffcc;
                font-weight: bold;
                font-size: 11pt;
            }
        """)
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_display = QTextEdit()
        self.stats_display.setReadOnly(True)
        self.stats_display.setFont(QFont("Consolas", 9))
        self.stats_display.setMaximumHeight(120)
        self.stats_display.setStyleSheet("""
            QTextEdit {
                background-color: #1a2b3c;
                color: #aaddff;
                border: 1px solid #2a5a7a;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        self.stats_display.setText("Session inactive - Start learning to see stats")
        
        stats_layout.addWidget(self.stats_display)
        left_layout.addWidget(stats_group)
        
        splitter.addWidget(left_widget)
    
    def setup_right_panel(self, splitter):
        """Setup the right panel with analysis and insights"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Driving Analysis Group
        analysis_group = QGroupBox("🔍 DRIVING PATTERN ANALYSIS")
        analysis_group.setStyleSheet("""
            QGroupBox {
                color: #88ffcc;
                font-weight: bold;
                font-size: 11pt;
            }
        """)
        analysis_layout = QVBoxLayout(analysis_group)
        
        self.analysis_table = QTableWidget()
        self.analysis_table.setColumnCount(3)
        self.analysis_table.setHorizontalHeaderLabels(["Parameter", "Value", "Insight"])
        self.analysis_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.analysis_table.setStyleSheet("""
            QTableWidget {
                background-color: #1a2b3c;
                color: #e8f4f8;
                gridline-color: #2a5a7a;
                border: 1px solid #2a5a7a;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #2a4d6a;
            }
            QTableWidget::item:selected {
                background-color: #2a5a7a;
            }
            QHeaderView::section {
                background-color: #2a4d6a;
                color: #88ffcc;
                font-weight: bold;
                padding: 6px;
                border: none;
            }
        """)
        
        # Set initial empty state
        self.analysis_table.setRowCount(0)
        
        analysis_layout.addWidget(self.analysis_table)
        right_layout.addWidget(analysis_group)
        
        # Mazda Insights Group
        insights_group = QGroupBox("🎯 MAZDA ENGINEERING INSIGHTS")
        insights_group.setStyleSheet("""
            QGroupBox {
                color: #88ffcc;
                font-weight: bold;
                font-size: 11pt;
            }
        """)
        insights_layout = QVBoxLayout(insights_group)
        
        self.insights_display = QTextEdit()
        self.insights_display.setReadOnly(True)
        self.insights_display.setFont(QFont("Arial", 10))
        self.insights_display.setMaximumHeight(150)
        self.insights_display.setStyleSheet("""
            QTextEdit {
                background-color: #1a2b3c;
                color: #aaddff;
                border: 1px solid #2a5a7a;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        self.insights_display.setText("AI insights will appear here as I learn your driving patterns...")
        
        insights_layout.addWidget(self.insights_display)
        right_layout.addWidget(insights_group)
        
        splitter.addWidget(right_widget)
    
    def start_ai_learning(self):
        """Start the AI learning session"""
        try:
            # Create vehicle profile
            vehicle_profile = {
                "model": "Mazdaspeed 3",
                "year": 2011,
                "generation": "gen2",
                "modifications": self.config_manager.settings.get('vehicle', {}).get('modifications', ['stock']),
                "fuel_quality": self.config_manager.settings.get('vehicle', {}).get('fuel_quality', 'premium_93')
            }
            
            # Start AI session
            startup_message = self.ai_tuner.start_learning_session(vehicle_profile)
            self.recommendations_display.setText(startup_message)
            
            # Update UI state
            self.session_active = True
            self.update_ui_state(True)
            
            # Start timers
            self.data_timer.start(2000)  # Collect data every 2 seconds
            self.ui_timer.start(1000)    # Update UI every second
            self.progress_timer.start(500)  # Progress animation
            
            # Reset progress
            self.progress_bar.setValue(0)
            self.data_points_collected = 0
            
            # Emit signal
            self.session_status_changed.emit(True)
            
            self.log_message("🟢 AI LEARNING SESSION STARTED")
            
        except Exception as e:
            self.log_message(f"🔴 ERROR starting AI session: {str(e)}")
    
    def stop_ai_learning(self):
        """Stop the AI learning session"""
        try:
            # Stop timers
            self.data_timer.stop()
            self.ui_timer.stop()
            self.progress_timer.stop()
            
            # Stop AI session
            stop_message = self.ai_tuner.stop_learning_session()
            self.recommendations_display.append(stop_message)
            
            # Update UI state
            self.session_active = False
            self.update_ui_state(False)
            
            # Complete progress bar
            self.progress_bar.setValue(100)
            
            # Emit signal
            self.session_status_changed.emit(False)
            
            self.log_message("🟡 AI LEARNING SESSION STOPPED")
            
        except Exception as e:
            self.log_message(f"🔴 ERROR stopping AI session: {str(e)}")
    
    def collect_driving_data(self):
        """Collect driving data from OBD-II or simulation"""
        try:
            if self.obd_connection and self.obd_connection.connected:
                # Get real data from OBD-II
                live_data = self.obd_connection.read_live_data()
            else:
                # Simulate data for demonstration
                live_data = self._simulate_driving_data()
            
            # Process with AI tuner
            adjustment = self.ai_tuner.process_driving_data(live_data)
            
            if adjustment:
                self.display_ai_recommendation(adjustment)
                self.recommendation_generated.emit(adjustment)
            
            # Update data point counter
            self.data_points_collected += 1
            self.data_points_label.setText(f"Data Points: {self.data_points_collected}")
            
        except Exception as e:
            self.log_message(f"🔴 DATA COLLECTION ERROR: {str(e)}")
    
    def _simulate_driving_data(self) -> dict:
        """Simulate realistic driving data for demonstration"""
        import random
        import time
        
        # Simulate different driving scenarios
        scenarios = [
            {"rpm": random.randint(1800, 2500), "speed": random.randint(40, 60), "throttle": random.randint(20, 40)},  # Highway cruising
            {"rpm": random.randint(1500, 2200), "speed": random.randint(20, 35), "throttle": random.randint(10, 30)},  # City driving
            {"rpm": random.randint(3000, 4500), "speed": random.randint(50, 80), "throttle": random.randint(60, 90)},  # Performance
        ]
        
        scenario = random.choice(scenarios)
        
        return {
            'rpm': scenario["rpm"],
            'speed': scenario["speed"],
            'throttle_position': scenario["throttle"],
            'engine_load': random.uniform(25, 85),
            'intake_temp': random.randint(25, 45),
            'boost_pressure': random.uniform(0, 12),
            'ignition_timing': random.uniform(8, 20),
            'afr_commanded': random.uniform(14.2, 15.0),
            'fuel_pressure': random.randint(400, 600),
            'coolant_temp': random.randint(85, 95)
        }
    
    def display_ai_recommendation(self, adjustment: TuningAdjustment):
        """Display AI tuning recommendation in the UI"""
        try:
            recommendation_html = f"""
<div style="background: #2a4d6a; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #00cc88;">
    <h3 style="color: #00ff88; margin-top: 0;">🎯 AI TUNING ADJUSTMENT DETECTED</h3>
    
    <table style="width: 100%; color: #e8f4f8;">
        <tr>
            <td style="width: 30%;"><strong>Parameter:</strong></td>
            <td style="color: #88ffcc;">{adjustment.parameter}</td>
        </tr>
        <tr>
            <td><strong>Current Value:</strong></td>
            <td>{adjustment.current_value}</td>
        </tr>
        <tr>
            <td><strong>Recommended:</strong></td>
            <td style="color: #00ff88; font-weight: bold;">{adjustment.recommended_value}</td>
        </tr>
        <tr>
            <td><strong>Confidence:</strong></td>
            <td style="color: #ffaa00;">{adjustment.confidence:.1%}</td>
        </tr>
        <tr>
            <td><strong>Urgency:</strong></td>
            <td style="color: #ff6666;">{adjustment.urgency.upper()}</td>
        </tr>
    </table>
    
    <div style="background: #1a3a4f; padding: 10px; border-radius: 5px; margin-top: 10px;">
        <strong>Reasoning:</strong><br>
        {adjustment.reasoning.replace(chr(10), '<br>')}
    </div>
</div>
"""
            
            # Append to recommendations display
            current_html = self.recommendations_display.toHtml()
            new_html = recommendation_html + current_html
            self.recommendations_display.setHtml(new_html)
            
            # Store last recommendation
            self.last_recommendation = adjustment
            
            self.log_message(f"💡 New AI recommendation: {adjustment.parameter}")
            
        except Exception as e:
            self.log_message(f"🔴 ERROR displaying recommendation: {str(e)}")
    
    def update_ui_elements(self):
        """Update UI elements with current session data"""
        try:
            if self.session_active:
                # Get session stats
                stats = self.ai_tuner.get_session_stats()
                
                # Update status label
                if self.session_active:
                    self.status_label.setText("🟢 AI LEARNING ACTIVE - Collecting driving data...")
                    self.status_label.setStyleSheet("""
                        QLabel {
                            background-color: #1a3a1a;
                            color: #00ff88;
                            padding: 8px;
                            border-radius: 5px;
                            border: 1px solid #00aa66;
                        }
                    """)
                
                # Update stats display
                stats_text = f"""
Session Duration: {stats.get('session_duration', '0:00:00')}
Data Points: {stats.get('data_points', 0):,}
Driving Style: {stats.get('driving_style', 'Analyzing...')}
Confidence: {stats.get('confidence', 0):.1%}
Learning Progress: {self.progress_bar.value()}%
"""
                self.stats_display.setText(stats_text)
                
                # Update analysis table periodically
                if self.data_points_collected % 10 == 0:  # Update every 20 seconds
                    self.update_analysis_table()
                
        except Exception as e:
            print(f"UI update error: {e}")
    
    def update_analysis_table(self):
        """Update the driving analysis table with current data"""
        try:
            # Get analysis from AI tuner
            analysis = self.ai_tuner._analyze_driving_patterns()
            
            if not analysis:
                return
            
            # Clear and populate table
            self.analysis_table.setRowCount(len(analysis))
            
            row = 0
            for key, value in analysis.items():
                if key in ['analysis_timestamp', 'data_points_analyzed']:
                    continue
                    
                # Parameter name
                param_item = QTableWidgetItem(self.format_parameter_name(key))
                param_item.setFlags(param_item.flags() & ~Qt.ItemIsEditable)
                
                # Value
                if isinstance(value, (int, float)):
                    value_text = f"{value:.3f}" if isinstance(value, float) else str(value)
                elif isinstance(value, dict):
                    value_text = json.dumps(value, indent=2)
                else:
                    value_text = str(value)
                
                value_item = QTableWidgetItem(value_text)
                value_item.setFlags(value_item.flags() & ~Qt.ItemIsEditable)
                
                # Insight
                insight_item = QTableWidgetItem(self.generate_insight(key, value))
                insight_item.setFlags(insight_item.flags() & ~Qt.ItemIsEditable)
                
                self.analysis_table.setItem(row, 0, param_item)
                self.analysis_table.setItem(row, 1, value_item)
                self.analysis_table.setItem(row, 2, insight_item)
                
                row += 1
                
        except Exception as e:
            print(f"Analysis table update error: {e}")
    
    def format_parameter_name(self, param_name: str) -> str:
        """Format parameter names for display"""
        name_map = {
            'aggression_level': 'Aggression Level',
            'efficiency_score': 'Efficiency Score',
            'typical_rpm_range': 'Typical RPM Range',
            'throttle_usage_pattern': 'Throttle Usage',
            'context_distribution': 'Driving Contexts'
        }
        return name_map.get(param_name, param_name.replace('_', ' ').title())
    
    def generate_insight(self, parameter: str, value) -> str:
        """Generate insights for analysis parameters"""
        insights = {
            'aggression_level': {
                'high': "Performance-oriented driving detected",
                'medium': "Balanced driving style", 
                'low': "Economical driving pattern"
            },
            'efficiency_score': {
                'high': "Excellent fuel efficiency habits",
                'medium': "Moderate efficiency focus",
                'low': "Performance-focused driving"
            },
            'typical_rpm_range': "Optimal engine operation range",
            'throttle_usage_pattern': "Shows your throttle control preferences",
            'context_distribution': "Distribution of your driving environments"
        }
        
        if parameter == 'aggression_level':
            if value > 0.7: return insights[parameter]['high']
            elif value > 0.4: return insights[parameter]['medium']
            else: return insights[parameter]['low']
        elif parameter == 'efficiency_score':
            if value > 0.7: return insights[parameter]['high']
            elif value > 0.4: return insights[parameter]['medium']
            else: return insights[parameter]['low']
        elif parameter in insights:
            return insights[parameter]
        
        return "Pattern analysis in progress"
    
    def update_progress_animation(self):
        """Update progress bar with smooth animation"""
        if not self.session_active:
            return
            
        current_value = self.progress_bar.value()
        
        # Progressive slowing as we approach 90%
        if current_value < 50:
            increment = 3
        elif current_value < 80:
            increment = 2
        elif current_value < 90:
            increment = 1
        else:
            increment = 0  # Stop at 90% until session complete
        
        new_value = min(90, current_value + increment)
        self.progress_bar.setValue(new_value)
        self.progress_label.setText(f"Learning Progress: {new_value}%")
    
    def generate_ai_report(self):
        """Generate and display comprehensive AI tuning report"""
        try:
            report = self.ai_tuner.generate_ai_tuning_report()
            
            if "error" in report:
                self.recommendations_display.append(f"\n🔴 ERROR: {report['error']}")
                return
            
            # Format report for display
            report_html = self.format_ai_report(report)
            self.recommendations_display.setHtml(report_html)
            
            # Update insights
            insights_text = "\n".join(report.get('mazda_specific_insights', []))
            self.insights_display.setText(insights_text)
            
            self.log_message("📊 AI Tuning Report Generated")
            
        except Exception as e:
            self.log_message(f"🔴 ERROR generating report: {str(e)}")
    
    def format_ai_report(self, report: dict) -> str:
        """Format AI report as HTML for display"""
        session = report.get('session_summary', {})
        analysis = report.get('driving_analysis', {})
        recommendations = report.get('tuning_recommendations', [])
        insights = report.get('mazda_specific_insights', [])
        next_steps = report.get('next_steps', [])
        health = report.get('vehicle_health_check', {})
        
        html = f"""
<div style="font-family: 'Consolas', monospace; color: #e8f4f8;">
    <h1 style="color: #00ff88; text-align: center;">📊 MAZDA AI TUNING REPORT</h1>
    
    <div style="background: #2a4d6a; padding: 15px; border-radius: 8px; margin: 10px 0;">
        <h2 style="color: #88ffcc; margin-top: 0;">📈 SESSION SUMMARY</h2>
        <table style="width: 100%;">
            <tr><td><strong>Data Points:</strong></td><td>{session.get('data_points_collected', 0):,}</td></tr>
            <tr><td><strong>Duration:</strong></td><td>{session.get('learning_duration', 'N/A')}</td></tr>
            <tr><td><strong>Driving Style:</strong></td><td style="color: #00ff88;">{session.get('driving_style', 'N/A')}</td></tr>
            <tr><td><strong>Confidence:</strong></td><td>{session.get('confidence_score', 0):.1%}</td></tr>
        </table>
    </div>
    
    <div style="background: #2a4d6a; padding: 15px; border-radius: 8px; margin: 10px 0;">
        <h2 style="color: #88ffcc; margin-top: 0;">💡 TUNING RECOMMENDATIONS</h2>
"""
        
        if recommendations:
            for rec in recommendations:
                html += f"""
        <div style="background: #1a3a4f; padding: 10px; margin: 5px 0; border-radius: 5px; border-left: 3px solid #00cc88;">
            <strong>{rec.get('parameter', 'Unknown')}</strong><br>
            Adjustment: {rec.get('adjustment', 'N/A')}<br>
            Confidence: {rec.get('confidence', 0):.1%} | Category: {rec.get('category', 'N/A')}
        </div>
"""
        else:
            html += "<p>No specific recommendations yet. Continue driving for more data.</p>"
        
        html += """
    </div>
    
    <div style="background: #2a4d6a; padding: 15px; border-radius: 8px; margin: 10px 0;">
        <h2 style="color: #88ffcc; margin-top: 0;">🔧 VEHICLE HEALTH</h2>
        <p>Status: <strong style="color: #00ff88;">{}</strong></p>
""".format(health.get('status', 'unknown').replace('_', ' ').title())
        
        if health.get('issues'):
            html += "<p>Issues to monitor:</p><ul>"
            for issue in health['issues']:
                html += f"<li>{issue}</li>"
            html += "</ul>"
        
        html += """
    </div>
    
    <div style="background: #2a4d6a; padding: 15px; border-radius: 8px; margin: 10px 0;">
        <h2 style="color: #88ffcc; margin-top: 0;">🎯 NEXT STEPS</h2>
        <ul>
"""
        
        for step in next_steps:
            html += f"<li>{step}</li>"
        
        html += """
        </ul>
    </div>
</div>
"""
        return html
    
    def update_ui_state(self, active: bool):
        """Update UI elements based on session state"""
        self.start_btn.setEnabled(not active)
        self.stop_btn.setEnabled(active)
        self.analyze_btn.setEnabled(not active)  # Only enable when stopped
    
    def log_message(self, message: str):
        """Add timestamped message to recommendations display"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        formatted_message = f"[{timestamp}] {message}"
        print(formatted_message)  # Also print to console for debugging
    
    def set_obd_connection(self, obd_connection):
        """Set the OBD-II connection for real data collection"""
        self.obd_connection = obd_connection
    
    def get_session_data(self) -> dict:
        """Get current session data for saving/exporting"""
        return {
            'session_active': self.session_active,
            'data_points': self.data_points_collected,
            'last_recommendation': self.last_recommendation.__dict__ if self.last_recommendation else None,
            'ai_tuner_state': self.ai_tuner.get_session_stats()
        }