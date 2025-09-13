"""
Zerodha Kite Connect authentication implementation.
"""

import webbrowser
from typing import Optional
from urllib.parse import urlparse, parse_qs
from kiteconnect import KiteConnect
from loguru import logger
from ..utils.config import config


class KiteAuth:
    """
    Handles Zerodha Kite Connect authentication flow.
    
    This class manages the complete authentication process:
    1. Generate login URL
    2. Handle redirect and extract request token
    3. Generate access token
    4. Maintain authenticated session
    """
    
    def __init__(self):
        """Initialize KiteAuth with API credentials."""
        self.api_key = config.kite_api_key
        self.api_secret = config.kite_api_secret
        self.redirect_url = config.kite_redirect_url
        
        # Initialize KiteConnect instance
        self.kite = KiteConnect(api_key=self.api_key)
        self.access_token: Optional[str] = None
        self.user_id: Optional[str] = None
        
        logger.info("KiteAuth initialized successfully")
    
    def generate_login_url(self) -> str:
        """
        Generate the login URL for Kite Connect authentication.
        
        Returns:
            Login URL that user needs to visit for authentication.
        """
        login_url = self.kite.login_url()
        logger.info(f"Generated login URL: {login_url}")
        return login_url
    
    def open_login_page(self) -> str:
        """
        Open the login page in the default web browser.
        
        Returns:
            Login URL that was opened.
        """
        login_url = self.generate_login_url()
        webbrowser.open(login_url)
        logger.info("Opened login page in browser")
        return login_url
    
    def extract_request_token(self, callback_url: str) -> str:
        """
        Extract request token from the callback URL.
        
        Args:
            callback_url: The full callback URL received after login.
            
        Returns:
            Request token extracted from the URL.
            
        Raises:
            ValueError: If request token cannot be extracted.
        """
        try:
            parsed_url = urlparse(callback_url)
            query_params = parse_qs(parsed_url.query)
            
            if 'request_token' not in query_params:
                raise ValueError("Request token not found in callback URL")
            
            request_token = query_params['request_token'][0]
            logger.info("Successfully extracted request token")
            return request_token
            
        except Exception as e:
            logger.error(f"Failed to extract request token: {e}")
            raise ValueError(f"Invalid callback URL: {e}")
    
    def generate_session(self, request_token: str) -> dict:
        """
        Generate session using request token.
        
        Args:
            request_token: Request token obtained from login callback.
            
        Returns:
            Dictionary containing access token and user info.
            
        Raises:
            Exception: If session generation fails.
        """
        try:
            # Generate session
            data = self.kite.generate_session(request_token, api_secret=self.api_secret)
            
            # Store access token and user ID
            self.access_token = data["access_token"]
            self.user_id = data["user_id"]
            
            # Set access token in KiteConnect instance
            self.kite.set_access_token(self.access_token)
            
            logger.info(f"Session generated successfully for user: {self.user_id}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to generate session: {e}")
            raise
    
    def authenticate_with_request_token(self, request_token: str) -> dict:
        """
        Complete authentication flow with request token.
        
        Args:
            request_token: Request token from login callback.
            
        Returns:
            Dictionary containing session data.
        """
        return self.generate_session(request_token)
    
    def authenticate_with_callback_url(self, callback_url: str) -> dict:
        """
        Complete authentication flow with callback URL.
        
        Args:
            callback_url: Full callback URL from login redirect.
            
        Returns:
            Dictionary containing session data.
        """
        request_token = self.extract_request_token(callback_url)
        return self.generate_session(request_token)
    
    def is_authenticated(self) -> bool:
        """
        Check if the session is authenticated.
        
        Returns:
            True if authenticated, False otherwise.
        """
        return self.access_token is not None
    
    def get_profile(self) -> dict:
        """
        Get user profile information.
        
        Returns:
            User profile data.
            
        Raises:
            Exception: If not authenticated or API call fails.
        """
        if not self.is_authenticated():
            raise Exception("Not authenticated. Please authenticate first.")
        
        try:
            profile = self.kite.profile()
            logger.info("Retrieved user profile successfully")
            return profile
        except Exception as e:
            logger.error(f"Failed to get profile: {e}")
            raise
    
    def get_kite_instance(self) -> KiteConnect:
        """
        Get the authenticated KiteConnect instance.
        
        Returns:
            Authenticated KiteConnect instance.
            
        Raises:
            Exception: If not authenticated.
        """
        if not self.is_authenticated():
            raise Exception("Not authenticated. Please authenticate first.")
        
        return self.kite
    
    def logout(self) -> bool:
        """
        Logout and invalidate the session.
        
        Returns:
            True if logout successful, False otherwise.
        """
        try:
            if self.is_authenticated():
                # Note: Kite Connect doesn't have a logout endpoint
                # We just clear local session data
                self.access_token = None
                self.user_id = None
                self.kite.set_access_token(None)
                logger.info("Logged out successfully")
            return True
        except Exception as e:
            logger.error(f"Logout failed: {e}")
            return False
