"""
Configuration management using environment variables and .env files.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from loguru import logger


class Config:
    """Configuration management class."""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            env_file: Path to .env file. If None, looks for .env in project root.
        """
        if env_file is None:
            # Look for .env file in project root
            project_root = Path(__file__).parent.parent.parent
            env_file = project_root / ".env"
        
        if Path(env_file).exists():
            load_dotenv(env_file)
            logger.info(f"Loaded environment variables from {env_file}")
        else:
            logger.warning(f"Environment file {env_file} not found. Using system environment variables.")
    
    @property
    def kite_api_key(self) -> str:
        """Get Kite Connect API key."""
        api_key = os.getenv("KITE_API_KEY")
        if not api_key:
            raise ValueError("KITE_API_KEY environment variable is required")
        return api_key
    
    @property
    def kite_api_secret(self) -> str:
        """Get Kite Connect API secret."""
        api_secret = os.getenv("KITE_API_SECRET")
        if not api_secret:
            raise ValueError("KITE_API_SECRET environment variable is required")
        return api_secret
    
    @property
    def kite_redirect_url(self) -> str:
        """Get Kite Connect redirect URL."""
        return os.getenv("KITE_REDIRECT_URL", "http://localhost:3000/callback")
    
    @property
    def log_level(self) -> str:
        """Get logging level."""
        return os.getenv("LOG_LEVEL", "INFO")
    
    @property
    def log_file(self) -> str:
        """Get log file path."""
        return os.getenv("LOG_FILE", "logs/zerodha_dashboard.log")
    
    def validate(self) -> bool:
        """
        Validate that all required configuration is present.
        
        Returns:
            True if all required config is present, False otherwise.
        """
        try:
            # Check required fields
            self.kite_api_key
            self.kite_api_secret
            logger.info("Configuration validation successful")
            return True
        except ValueError as e:
            logger.error(f"Configuration validation failed: {e}")
            return False


# Global configuration instance
config = Config()
