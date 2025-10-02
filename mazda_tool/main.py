# mazda_tool/main.py
import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtCore import QSettings, QTimer
from PyQt5.QtGui import QIcon

from mazda_tool.ui.main_window import UltimateMazdaTechnicianSuite
from mazda_tool.core.config_manager import ConfigManager
from mazda_tool.utils.logger import setup_logging

class MazdaTechnicianTool:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.settings = QSettings("MazdaTechnician", "UltimateTool")
        self.config = ConfigManager()
        
        # Setup logging
        setup_logging()
        self.logger = logging.getLogger(__name__)
        
    def setup_application(self):
        """Initialize application settings and configuration"""
        try:
            # Application metadata
            self.app.setApplicationName("Mazda Ultimate Technician Tool")
            self.app.setApplicationVersion("1.0.0")
            self.app.setOrganizationName("MazdaTechnician")
            
            # Load stylesheet
            self.load_stylesheet()
            
            self.logger.info("Application setup completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Application setup failed: {str(e)}")
            return False
    
    def load_stylesheet(self):
        """Load application stylesheet"""
        try:
            style_path = "assets/styles/main.qss"
            if os.path.exists(style_path):
                with open(style_path, 'r') as file:
                    self.app.setStyleSheet(file.read())
        except Exception as e:
            self.logger.warning(f"Could not load stylesheet: {str(e)}")
    
    def run(self):
        """Start the main application"""
        if not self.setup_application():
            QMessageBox.critical(None, "Startup Error", 
                               "Failed to initialize application. Check logs for details.")
            return 1
        
        try:
            # Create and show main window
            main_window = UltimateMazdaTechnicianSuite(self.settings, self.config)
            main_window.show()
            
            self.logger.info("Application started successfully")
            
            # Start main event loop
            return self.app.exec_()
            
        except Exception as e:
            self.logger.error(f"Application runtime error: {str(e)}")
            QMessageBox.critical(None, "Runtime Error", 
                               f"Application encountered an error: {str(e)}")
            return 1

def main():
    """Main entry point"""
    tool = MazdaTechnicianTool()
    sys.exit(tool.run())

if __name__ == "__main__":
    main()