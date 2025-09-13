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
    
    # Full automation credentials (optional)
    @property
    def zerodha_username(self) -> Optional[str]:
        """Get Zerodha username for full automation."""
        return os.getenv("ZERODHA_USERNAME")
    
    @property
    def zerodha_password(self) -> Optional[str]:
        """Get Zerodha password for full automation."""
        return os.getenv("ZERODHA_PASSWORD")
    
    @property
    def zerodha_pin(self) -> Optional[str]:
        """Get Zerodha trading PIN for full automation."""
        return os.getenv("ZERODHA_PIN")
    
    @property
    def zerodha_totp_secret(self) -> Optional[str]:
        """Get TOTP secret for 2FA automation."""
        return os.getenv("ZERODHA_TOTP_SECRET")
    
    @property
    def headless_browser(self) -> bool:
        """Get headless browser setting."""
        return os.getenv("HEADLESS_BROWSER", "false").lower() == "true"
    
    @property
    def browser_timeout(self) -> int:
        """Get browser timeout in seconds."""
        return int(os.getenv("BROWSER_TIMEOUT", "30"))
    
    @property
    def auto_login_enabled(self) -> bool:
        """Check if full automation is enabled."""
        return os.getenv("AUTO_LOGIN_ENABLED", "false").lower() == "true"
    
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
    
    def validate_full_automation(self) -> bool:
        """
        Validate that all credentials for full automation are present.
        
        Returns:
            True if full automation is possible, False otherwise.
        """
        if not self.auto_login_enabled:
            return False
        
        required_fields = [
            ("ZERODHA_USERNAME", self.zerodha_username),
            ("ZERODHA_PASSWORD", self.zerodha_password),
            ("ZERODHA_PIN", self.zerodha_pin),
            ("ZERODHA_TOTP_SECRET", self.zerodha_totp_secret)
        ]
        
        missing_fields = []
        for field_name, field_value in required_fields:
            if not field_value:
                missing_fields.append(field_name)
        
        if missing_fields:
            logger.warning(f"Full automation disabled - missing fields: {', '.join(missing_fields)}")
            return False
        
        logger.info("Full automation credentials validated successfully")
        return True


# Global configuration instance
config = Config()
