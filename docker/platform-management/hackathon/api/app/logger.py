import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Create logs directory if it doesn't exist
logs_dir = Path("/app/logs")
logs_dir.mkdir(exist_ok=True, parents=True)

# Configure logger
def get_logger(name):
    """
    Get a logger instance configured with the specified name.
    
    Args:
        name: The name for the logger, typically __name__ from the calling module
        
    Returns:
        A configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure handlers if they haven't been added yet
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        
        # Create file handlers
        info_file_handler = RotatingFileHandler(
            logs_dir / "info.log", 
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        info_file_handler.setLevel(logging.INFO)
        info_file_handler.setFormatter(file_formatter)
        
        error_file_handler = RotatingFileHandler(
            logs_dir / "error.log", 
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(file_formatter)
        
        debug_file_handler = RotatingFileHandler(
            logs_dir / "debug.log", 
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        debug_file_handler.setLevel(logging.DEBUG)
        debug_file_handler.setFormatter(file_formatter)
        
        # Add handlers to logger
        logger.addHandler(console_handler)
        logger.addHandler(info_file_handler)
        logger.addHandler(error_file_handler)
        logger.addHandler(debug_file_handler)
    
    return logger

# Create a default logger for import
logger = get_logger("hackathon_api")
