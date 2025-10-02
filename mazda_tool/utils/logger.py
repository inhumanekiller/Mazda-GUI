# mazda_tool/utils/logger.py
import logging
import os
from pathlib import Path

def setup_logging():
    """Setup application logging"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "mazda_tool.log"),
            logging.StreamHandler()
        ]
    )