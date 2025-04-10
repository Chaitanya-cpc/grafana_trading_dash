#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Logger Utility Module
Sets up logging for the application
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime
import pytz

def setup_logger():
    """Set up and configure the logger"""
    # Get log level from environment or default to INFO
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    # Create logger
    logger = logging.getLogger("zerodha_dashboard")
    logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Create file handler for rotating log file
    log_dir = os.path.join(os.getcwd(), "data", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "zerodha_dashboard.log")
    
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setLevel(log_level)
    
    # Create formatter - JSON for structured logging
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            # Get the original formatted message
            message = super().format(record)
            
            # Create a structured log entry
            log_entry = {
                "timestamp": datetime.now(pytz.timezone('Asia/Kolkata')).isoformat(),
                "level": record.levelname,
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
                "message": record.getMessage()
            }
            
            # Add exception info if present
            if record.exc_info:
                log_entry["exception"] = self.formatException(record.exc_info)
            
            # Convert to JSON
            return json.dumps(log_entry)
    
    # Create simpler formatter for console
    console_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(module)s:%(funcName)s:%(lineno)d] - %(message)s"
    )
    
    # Create JSON formatter for file
    json_formatter = JSONFormatter()
    
    # Set formatters
    console_handler.setFormatter(console_formatter)
    file_handler.setFormatter(json_formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

class CustomLogger:
    """
    Custom logger class that wraps the standard logger
    and adds additional functionality like recording logs to the database
    """
    
    def __init__(self, std_logger, db_client=None):
        """Initialize the custom logger"""
        self.std_logger = std_logger
        self.db_client = db_client
        self.india_tz = pytz.timezone('Asia/Kolkata')
    
    def _log_to_db(self, level, message):
        """Log a message to the database"""
        if not self.db_client:
            return
        
        try:
            # Create data point
            data_point = {
                "measurement": "application_logs",
                "tags": {
                    "level": level
                },
                "fields": {
                    "message": message
                },
                "time": datetime.now(self.india_tz).isoformat()
            }
            
            # Write to InfluxDB
            self.db_client.write_point(data_point)
            
        except Exception as e:
            # We can't log this error or we'll get a recursion
            # Just print to stderr
            print(f"Error logging to database: {str(e)}", file=sys.stderr)
    
    def debug(self, message):
        """Log a debug message"""
        self.std_logger.debug(message)
    
    def info(self, message):
        """Log an info message"""
        self.std_logger.info(message)
        self._log_to_db("INFO", message)
    
    def warning(self, message):
        """Log a warning message"""
        self.std_logger.warning(message)
        self._log_to_db("WARNING", message)
    
    def error(self, message):
        """Log an error message"""
        self.std_logger.error(message)
        self._log_to_db("ERROR", message)
    
    def critical(self, message):
        """Log a critical message"""
        self.std_logger.critical(message)
        self._log_to_db("CRITICAL", message)
    
    def exception(self, message):
        """Log an exception message"""
        self.std_logger.exception(message)
        self._log_to_db("ERROR", message) 