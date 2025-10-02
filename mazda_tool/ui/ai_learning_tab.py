# mazda_tool/ui/ai_learning_tab.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTextEdit, QLabel, QProgressBar, QGroupBox,
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont

from mazda_tool.core.ai_tuner import MazdaAITuner

class AILearningTab(QWidget):
    """AI Learning and Adaptive Tuning Interface"""
    
    def __init__(self, obd_connection=None):
        super().__init__()
        self.ai_tuner = MazdaAITuner()
        self.obd_connection = obd_connection
        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self.collect_driving_data)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("🧠 MAZDA AI LEARNING TUNER")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        header.setStyleSheet("color: #00ff88; padding: 10px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # AI Controls
        controls_group = QGroupBox("🎛️ AI LEARNING CONTROLS")
        controls_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("🧠 START AI LEARNING")
        self.stop_btn = QPushButton("🛑 STOP LEARNING")
        self.analyze_btn = QPushButton("📊 GENERATE AI REPORT")
        
        self.start_btn.clicked.connect(self.start_ai_learning)
        self.stop_btn.clicked.connect(self.stop_ai_learning)
        self.analyze_btn.clicked.connect(self.generate_ai_report)
        
        self.stop_btn.setEnabled(False)
        self.analyze_btn.setEnabled(False)
        
        controls_layout.addWidget(self.start_btn)
        controls_layout.addWidget(self.stop_btn)
        controls_layout.addWidget(self.analyze_btn)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Learning Progress
        progress_group = QGroupBox("📈 LEARNING PROGRESS")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        self.status_label = QLabel("Ready to start AI learning session")
        self.status_label.setStyleSheet("color: #aaddff; padding: 5px;")
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # AI Recommendations
        recommendations_group = QGroupBox("💡 AI TUNING RECOMMENDATIONS")
        recommendations_layout = QVBoxLayout()
        
        self.recommendations_display = QTextEdit()
        self.recommendations_display.setReadOnly(True)
        self.recommendations_display.setFont(QFont("Consolas", 10))
        
        recommendations_layout.addWidget(self.recommendations_display)
        recommendations_group.setLayout(recommendations_layout)
        layout.addWidget(recommendations_group)
        
        # Driving Analysis
        analysis_group = QGroupBox("🔍 DRIVING PATTERN ANALYSIS")
        analysis_layout = QVBoxLayout()
        
        self.analysis_table = QTableWidget()
        self.analysis_table.setColumnCount(3)
        self.analysis_table.setHorizontalHeaderLabels(["Parameter", "Value", "Insight"])
        self.analysis_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        analysis_layout.addWidget(self.analysis_table)
        analysis_group.setLayout(analysis_layout)
        layout.addWidget(analysis_group)
    
    def start_ai_learning(self):
        """Start AI learning session"""
        vehicle_profile = {
            "model": "Mazdaspeed 3",
            "year": 2011,
            "modifications": ["stock", "cobb_intake"]  # Example mods
        }
        
        startup_message = self.ai_tuner.start_learning_session(vehicle_profile)
        self.recommendations_display.setText(startup_message)
        
        # Enable/disable buttons
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.analyze_btn.setEnabled(False)
        
        # Start data collection timer (every 2 seconds)
        self.data_timer.start(2000)
        self.status_label.setText("🟢 AI LEARNING ACTIVE - Driving data collection running")
        
        # Start progress simulation
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(1000)
    
    def stop_ai_learning(self):
        """Stop AI learning session"""
        self.data_timer.stop()
        if hasattr(self, 'progress_timer'):
            self.progress_timer.stop()
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.analyze_btn.setEnabled(True)
        
        self.status_label.setText("🟡 AI LEARNING PAUSED - Ready for analysis")
        self.recommendations_display.append("\n\n--- AI LEARNING SESSION COMPLETE ---")
        self.recommendations_display.append("Use 'Generate AI Report' to see tuning recommendations")
    
    def collect_driving_data(self):
        """Collect driving data from OBD-II connection"""
        if self.obd_connection and self.obd_connection.connected:
            try:
                # Get real-time data from OBD
                live_data = self.obd_connection.read_live_data()
                
                # Process with AI tuner
                adjustment = self.ai_tuner.process_driving_data(live_data)
                
                if adjustment:
                    self.display_ai_recommendation(adjustment)
                    
            except Exception as e:
                self.status_label.setText(f"🔴 DATA COLLECTION ERROR: {str(e)}")
        else:
            # Simulate data for demo purposes
            simulated_data = self._simulate_driving_data()
            adjustment = self.ai_tuner.process_driving_data(simulated_data)
            
            if adjustment:
                self.display_ai_recommendation(adjustment)
    
    def _simulate_driving_data(self) -> Dict:
        """Simulate driving data for demonstration"""
        import random
        return {
            'rpm': random.randint(1500, 3500),
            'speed': random.randint(30, 80),
            'throttle_position': random.randint(20, 60),
            'engine_load': random.uniform(30, 70),
            'intake_temp': random.randint(25, 45),
            'boost_pressure': random.uniform(0, 5)
        }
    
    def display_ai_recommendation(self, adjustment):
        """Display AI tuning recommendation"""
        recommendation_text = f"""
🎯 AI TUNING ADJUSTMENT DETECTED

Parameter: {adjustment.parameter}
Current Value: {adjustment.current_value}
Recommended: {adjustment.recommended_value}
Confidence: {adjustment.confidence:.1%}

Reasoning:
{adjustment.reasoning}

---
"""
        self.recommendations_display.append(recommendation_text)
    
    def update_progress(self):
        """Update learning progress bar"""
        current_value = self.progress_bar.value()
        if current_value < 90:  # Cap at 90% until complete
            self.progress_bar.setValue(current_value + 2)
    
    def generate_ai_report(self):
        """Generate comprehensive AI tuning report"""
        report = self.ai_tuner.generate_ai_tuning_report()
        
        report_text = """
📊 MAZDA AI TUNING REPORT
=========================

"""
        if "error" in report:
            report_text += f"Error: {report['error']}"
        else:
            # Session Summary
            summary = report['session_summary']
            report_text += f"""
SESSION SUMMARY:
• Data Points Collected: {summary['data_points_collected']:,}
• Learning Duration: {summary['learning_duration']}
• Your Driving Style: {summary['driving_style']}

"""
            # Driving Analysis
            analysis = report['driving_analysis']
            report_text += f"""
DRIVING ANALYSIS:
• Aggression Level: {analysis.get('aggression_level', 0):.1%}
• Efficiency Score: {analysis.get('efficiency_score', 0):.1%}
• Typical RPM Range: {analysis.get('typical_rpm_range', 'N/A')}

"""
            # Mazda Insights
            insights = report['mazda_specific_insights']
            report_text += "MAZDA ENGINEERING INSIGHTS:\n"
            for insight in insights:
                report_text += f"• {insight}\n"
        
        self.recommendations_display.setText(report_text)
        
        # Update analysis table
        self.update_analysis_table(report)
    
    def update_analysis_table(self, report: Dict):
        """Update the driving analysis table"""
        if "driving_analysis" not in report:
            return
        
        analysis = report['driving_analysis']
        self.analysis_table.setRowCount(len(analysis))
        
        for i, (key, value) in enumerate(analysis.items()):
            self.analysis_table.setItem(i, 0, QTableWidgetItem(str(key)))
            self.analysis_table.setItem(i, 1, QTableWidgetItem(str(value)))
            
            # Add insights based on values
            insight = self._generate_insight(key, value)
            self.analysis_table.setItem(i, 2, QTableWidgetItem(insight))
    
    def _generate_insight(self, parameter: str, value) -> str:
        """Generate insight for analysis parameter"""
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
            }
        }
        
        if parameter == 'aggression_level':
            if value > 0.7: return insights[parameter]['high']
            elif value > 0.4: return insights[parameter]['medium']
            else: return insights[parameter]['low']
        elif parameter == 'efficiency_score':
            if value > 0.7: return insights[parameter]['high']
            elif value > 0.4: return insights[parameter]['medium']
            else: return insights[parameter]['low']
        
        return "No specific insight available"