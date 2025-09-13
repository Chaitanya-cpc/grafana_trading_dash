"""
Token persistence and management for reducing login frequency.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict
from loguru import logger


class TokenManager:
    """
    Manages access token persistence to reduce login frequency.
    
    Note: Access tokens from Zerodha are valid until market close (3:30 PM IST)
    or until the next trading day starts.
    """
    
    def __init__(self, token_file: str = "data/auth_token.json"):
        """
        Initialize TokenManager.
        
        Args:
            token_file: Path to store token data.
        """
        self.token_file = Path(token_file)
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"TokenManager initialized with file: {token_file}")
    
    def save_token(self, access_token: str, user_id: str, additional_data: Optional[Dict] = None) -> bool:
        """
        Save access token and related data to file.
        
        Args:
            access_token: The access token to save.
            user_id: User ID associated with the token.
            additional_data: Additional session data to save.
            
        Returns:
            True if saved successfully.
        """
        try:
            # Convert datetime objects to strings for JSON serialization
            additional_data_clean = {}
            if additional_data:
                for key, value in additional_data.items():
                    if isinstance(value, datetime):
                        additional_data_clean[key] = value.isoformat()
                    else:
                        additional_data_clean[key] = value
            
            token_data = {
                "access_token": access_token,
                "user_id": user_id,
                "created_at": datetime.now().isoformat(),
                "expires_at": self._calculate_expiry().isoformat(),
                "additional_data": additional_data_clean
            }
            
            with open(self.token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
            
            # Set restrictive file permissions (readable only by owner)
            os.chmod(self.token_file, 0o600)
            
            logger.info(f"Token saved successfully for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save token: {e}")
            return False
    
    def load_token(self) -> Optional[Dict]:
        """
        Load saved token data if valid.
        
        Returns:
            Token data if valid, None if expired or not found.
        """
        try:
            if not self.token_file.exists():
                logger.info("No saved token found")
                return None
            
            with open(self.token_file, 'r') as f:
                token_data = json.load(f)
            
            # Check if token is still valid
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            if datetime.now() > expires_at:
                logger.info("Saved token has expired")
                self.clear_token()
                return None
            
            logger.info(f"Valid token loaded for user: {token_data['user_id']}")
            return token_data
            
        except Exception as e:
            logger.error(f"Failed to load token: {e}")
            return None
    
    def clear_token(self) -> bool:
        """
        Clear/delete saved token.
        
        Returns:
            True if cleared successfully.
        """
        try:
            if self.token_file.exists():
                self.token_file.unlink()
                logger.info("Token cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to clear token: {e}")
            return False
    
    def is_token_valid(self) -> bool:
        """
        Check if saved token is still valid.
        
        Returns:
            True if token exists and is valid.
        """
        token_data = self.load_token()
        return token_data is not None
    
    def _calculate_expiry(self) -> datetime:
        """
        Calculate token expiry time.
        
        Zerodha tokens typically expire at market close (3:30 PM IST)
        or at the start of next trading day.
        
        Returns:
            Estimated expiry datetime.
        """
        now = datetime.now()
        
        # If it's before 3:30 PM today, expire at 3:30 PM
        market_close_today = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        if now < market_close_today:
            return market_close_today
        else:
            # If after market close, expire tomorrow at 3:30 PM
            return market_close_today + timedelta(days=1)
    
    def get_token_status(self) -> Dict:
        """
        Get detailed token status information.
        
        Returns:
            Dictionary with token status details.
        """
        token_data = self.load_token()
        
        if not token_data:
            return {
                "exists": False,
                "valid": False,
                "user_id": None,
                "created_at": None,
                "expires_at": None,
                "time_remaining": None
            }
        
        expires_at = datetime.fromisoformat(token_data['expires_at'])
        time_remaining = expires_at - datetime.now()
        
        return {
            "exists": True,
            "valid": time_remaining.total_seconds() > 0,
            "user_id": token_data['user_id'],
            "created_at": token_data['created_at'],
            "expires_at": token_data['expires_at'],
            "time_remaining": str(time_remaining) if time_remaining.total_seconds() > 0 else "Expired"
        }
