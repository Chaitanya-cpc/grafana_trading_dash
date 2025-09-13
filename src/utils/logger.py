"""
Logging configuration using loguru.
"""

import sys
from pathlib import Path
from loguru import logger
from .config import config


def setup_logging():
    """
    Set up logging configuration with both file and console output.
    """
    # Remove default handler
    logger.remove()
    
    # Ensure log directory exists
    log_file = Path(config.log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Console handler with colored output
    logger.add(
        sys.stdout,
        level=config.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        colorize=True
    )
    
    # File handler
    logger.add(
        config.log_file,
        level=config.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="1 day",
        retention="30 days",
        compression="zip"
    )
    
    logger.info("Logging configured successfully")
    return logger


# Initialize logging when module is imported
setup_logging()
