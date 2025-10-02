# mazda_tool/ui/help_system.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, 
                             QListWidget, QSplitter, QLineEdit, QPushButton)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from mazda_tool.core.mazdaspeed_knowledge import MazdaspeedKnowledgeEngine

class MazdaspeedHelpSystem(QWidget):
    """Interactive help system with your technical documentation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.knowledge_engine = MazdaspeedKnowledgeEngine()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Search bar
        search_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search Mazdaspeed 3 technical documentation...")
        self.search_bar.textChanged.connect(self.search_content)
        search_layout.addWidget(self.search_bar)
        
        layout.addLayout(search_layout)
        
        # Splitter for topics and content
        splitter = QSplitter(Qt.Horizontal)
        
        # Topics list
        self.topics_list = QListWidget()
        self.load_topics()
        self.topics_list.currentItemChanged.connect(self.display_topic)
        splitter.addWidget(self.topics_list)
        
        # Content browser
        self.content_browser = QTextBrowser()
        self.content_browser.setFont(QFont("Consolas", 10))
        splitter.addWidget(self.content_browser)
        
        splitter.setSizes([200, 600])
        layout.addWidget(splitter)
        
        # Set initial content
        self.display_load_vs_boost()
        
    def load_topics(self):
        topics = [
            "🎯 Load vs Boost: The Secret Sauce",
            "🚀 High HP / Low Boost Strategies", 
            "🔧 Common Issues & Solutions",
            "📚 Tuning Best Practices",
            "⚙️ Hardware Requirements",
            "💡 Overboost (P0234) Fix Guide",
            "⛽ Fuel Pressure (P0087) Solutions",
            "🔥 Knock & Misfire Resolution"
        ]
        self.topics_list.addItems(topics)
    
    def display_topic(self, current, previous):
        topic_map = {
            0: self.display_load_vs_boost,
            1: self.display_high_hp_strategies,
            2: self.display_common_issues,
            3: self.display_best_practices,
            4: self.display_hardware_guide,
            5: self.display_overboost_guide,
            6: self.display_fuel_pressure_guide,
            7: self.display_knock_guide
        }
        
        if current and current.row() in topic_map:
            topic_map[current.row()]()
    
    def display_load_vs_boost(self):
        content = """
        <h2>🎯 LOAD vs BOOST: The Mazdaspeed 3 Secret Sauce</h2>
        
        <h3>What is Engine Load?</h3>
        <ul>
        <li>Engine Load is a <b>CALCULATED</b> value representing the engine's output demand</li>
        <li>Measured as a percentage of maximum theoretical airflow</li>
        <li>The ECU uses Load as its <b>primary performance target</b>, NOT boost pressure</li>
        </ul>
        
        <h3>Why Load Targeting Matters:</h3>
        <ol>
        <li><b>Consistent Performance</b>: Load targeting adapts to environmental conditions</li>
        <li><b>Safety First</b>: Multiple load limit tables protect the engine</li>
        <li><b>Better Driveability</b>: Smoother power delivery across RPM range</li>
        </ol>
        
        <h3>The Load Calculation Flow:</h3>
        <code>Accelerator Position → Load Request Tables → Multiple Limit Tables → FINAL LOAD TARGET</code>
        
        <h3>Limit Tables Include:</h3>
        <ul>
        <li>Load vs RPM (main performance curve)</li>
        <li>Load by Gear (prevents wheelspin in lower gears)</li>  
        <li>BAT Compensation (reduces load in hot weather)</li>
        <li>Barometric Compensation (altitude adjustment)</li>
        </ul>
        
        <h3>Boost is a RESULT of Load:</h3>
        The ECU uses the final Load Target to determine:
        <ul>
        <li>Wastegate Duty Cycle (boost pressure)</li>
        <li>Throttle Plate Position (airflow control)</li>
        <li>Fuel and Timing Maps (appropriate for the load)</li>
        </ul>
        
        <div style="background-color: #2a4d6a; padding: 10px; border-radius: 5px;">
        <b>KEY INSIGHT:</b> You tune for Load, and Boost follows!
        </div>
        """
        self.content_browser.setHtml(content)
    
    def display_high_hp_strategies(self):
        # Similar detailed HTML content for each topic
        pass
    
    def search_content(self, search_text):
        """Search through all technical content"""
        if search_text:
            # Implement search functionality
            pass