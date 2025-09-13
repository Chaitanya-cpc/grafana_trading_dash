"""
Zerodha Kite Connect authentication implementation.
"""

import webbrowser
from typing import Optional
from urllib.parse import urlparse, parse_qs
from kiteconnect import KiteConnect
from loguru import logger
from ..utils.config import config
from .callback_server import CallbackServer
from .token_manager import TokenManager
from .browser_automation import ZerodhaAutomatedLogin


class KiteAuth:
    """
    Handles Zerodha Kite Connect authentication flow.
    
    This class manages the complete authentication process:
    1. Generate login URL
    2. Handle redirect and extract request token
    3. Generate access token
    4. Maintain authenticated session
    """
    
    def __init__(self, use_local_server: bool = True, server_port: int = 3000):
        """
        Initialize KiteAuth with API credentials.
        
        Args:
            use_local_server: Whether to use local callback server (default: True).
            server_port: Port for local callback server (default: 3000).
        """
        self.api_key = config.kite_api_key
        self.api_secret = config.kite_api_secret
        self.use_local_server = use_local_server
        self.server_port = server_port
        
        # Set redirect URL based on server mode
        if use_local_server:
            self.redirect_url = f"http://localhost:{server_port}/callback"
        else:
            self.redirect_url = config.kite_redirect_url
        
        # Initialize KiteConnect instance
        self.kite = KiteConnect(api_key=self.api_key)
        self.access_token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.callback_server: Optional[CallbackServer] = None
        self.token_manager = TokenManager()
        
        logger.info(f"KiteAuth initialized successfully (local_server: {use_local_server})")
    
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
    
    def authenticate_with_saved_token(self) -> bool:
        """
        Try to authenticate using saved token.
        
        Returns:
            True if authentication successful with saved token.
        """
        try:
            token_data = self.token_manager.load_token()
            if not token_data:
                return False
            
            # Set token data
            self.access_token = token_data['access_token']
            self.user_id = token_data['user_id']
            self.kite.set_access_token(self.access_token)
            
            # Verify token is still working by making a test API call
            profile = self.kite.profile()
            logger.info(f"Successfully authenticated with saved token for user: {self.user_id}")
            return True
            
        except Exception as e:
            logger.warning(f"Saved token authentication failed: {e}")
            # Clear invalid token
            self.token_manager.clear_token()
            self.access_token = None
            self.user_id = None
            self.kite.set_access_token(None)
            return False
    
    def authenticate_automatically(self, timeout: int = 300, open_browser: bool = True) -> dict:
        """
        Complete authentication flow automatically using local callback server.
        
        Args:
            timeout: Maximum time to wait for callback (default: 5 minutes).
            open_browser: Whether to open browser automatically (default: True).
            
        Returns:
            Dictionary containing session data.
            
        Raises:
            Exception: If authentication fails or times out.
        """
        if not self.use_local_server:
            raise Exception("Automatic authentication requires local server mode")
        
        try:
            # Start callback server
            self.callback_server = CallbackServer(port=self.server_port)
            if not self.callback_server.start():
                raise Exception("Failed to start callback server")
            
            # Generate login URL
            login_url = self.generate_login_url()
            
            logger.info("Starting automatic authentication flow")
            print("\\n" + "="*80)
            print("🔐 AUTOMATIC ZERODHA AUTHENTICATION")
            print("="*80)
            print(f"\\n📍 Callback server started on: http://localhost:{self.server_port}")
            print(f"🌐 Opening login page: {login_url}")
            
            if open_browser:
                webbrowser.open(login_url)
                print("\\n✅ Browser opened automatically")
            else:
                print(f"\\n🔗 Please visit: {login_url}")
            
            print("\\n⏳ Waiting for authentication (this may take a few moments)...")
            print("   💡 Complete the login in your browser and authorize the app")
            
            # Wait for callback
            request_token = self.callback_server.wait_for_callback(timeout)
            
            if not request_token:
                raise Exception(f"Authentication timed out after {timeout} seconds")
            
            # Complete authentication
            session_data = self.generate_session(request_token)
            
            # Save token for future use
            self.token_manager.save_token(
                access_token=self.access_token,
                user_id=self.user_id,
                additional_data=session_data
            )
            
            print("\\n🎉 Authentication successful!")
            print(f"👤 User ID: {session_data.get('user_id', 'N/A')}")
            print("💾 Token saved for future sessions")
            
            return session_data
            
        except Exception as e:
            logger.error(f"Automatic authentication failed: {e}")
            raise
        finally:
            # Clean up server
            if self.callback_server:
                self.callback_server.stop()
    
    def authenticate_smart(self, timeout: int = 300, open_browser: bool = True, force_new: bool = False) -> dict:
        """
        Smart authentication that tries saved token first, then falls back to OAuth.
        
        Args:
            timeout: Maximum time to wait for OAuth callback if needed.
            open_browser: Whether to open browser for OAuth if needed.
            force_new: Force new authentication even if saved token exists.
            
        Returns:
            Dictionary containing session data.
        """
        # Check token status
        token_status = self.token_manager.get_token_status()
        
        if not force_new and token_status['valid']:
            print("\\n" + "="*80)
            print("🔄 CHECKING SAVED AUTHENTICATION")
            print("="*80)
            print(f"💾 Found saved token for user: {token_status['user_id']}")
            print(f"⏰ Token expires: {token_status['expires_at']}")
            print(f"⏳ Time remaining: {token_status['time_remaining']}")
            print("\\n🔍 Verifying token validity...")
            
            if self.authenticate_with_saved_token():
                print("\\n✅ Successfully authenticated with saved token!")
                print("🚀 No login required - you're ready to trade!")
                
                # Get profile to return session-like data
                profile = self.get_profile()
                return {
                    'user_id': self.user_id,
                    'access_token': self.access_token,
                    'login_time': 'Restored from saved token',
                    'profile': profile
                }
        
        # If no saved token or token invalid, use OAuth flow
        print("\\n💡 Saved token not available or invalid")
        print("🔐 Starting OAuth authentication flow...")
        
        return self.authenticate_automatically(timeout, open_browser)
    
    def authenticate_fully_automated(self, timeout: int = 300) -> dict:
        """
        Complete authentication flow with ZERO manual intervention.
        
        This method performs:
        1. Automated browser login with credentials
        2. Automated 2FA/TOTP handling
        3. Automated PIN entry
        4. Token extraction and session generation
        
        Args:
            timeout: Maximum time to wait for completion.
            
        Returns:
            Dictionary containing session data.
            
        Raises:
            Exception: If full automation is not configured or fails.
        """
        if not config.validate_full_automation():
            raise Exception(
                "Full automation not configured. Please set ZERODHA_USERNAME, "
                "ZERODHA_PASSWORD, ZERODHA_PIN, ZERODHA_TOTP_SECRET, and "
                "AUTO_LOGIN_ENABLED=true in your .env file."
            )
        
        try:
            # Start callback server
            self.callback_server = CallbackServer(port=self.server_port)
            if not self.callback_server.start():
                raise Exception("Failed to start callback server")
            
            # Generate login URL
            login_url = self.generate_login_url()
            callback_url_base = f"http://localhost:{self.server_port}"
            
            logger.info("Starting FULLY AUTOMATED authentication flow")
            print("\\n" + "="*80)
            print("🤖 FULLY AUTOMATED ZERODHA AUTHENTICATION")
            print("="*80)
            print(f"\\n📍 Callback server: http://localhost:{self.server_port}")
            print(f"🔐 Login URL: {login_url}")
            print("\\n⚡ ZERO MANUAL INTERVENTION REQUIRED")
            print("   🤖 Automated browser login")
            print("   🔑 Automated credential entry")
            print("   📱 Automated 2FA/TOTP handling")
            print("   🔢 Automated PIN entry")
            print("\\n🚀 Starting automated login process...")
            
            # Perform automated browser login
            browser_login = ZerodhaAutomatedLogin()
            callback_url = browser_login.perform_automated_login(
                login_url=login_url,
                callback_url_base=callback_url_base
            )
            
            if not callback_url:
                raise Exception("Automated browser login failed")
            
            print("\\n✅ Automated login successful!")
            print("🔗 Callback received, processing authentication...")
            
            # Extract request token from callback URL
            request_token = self.extract_request_token(callback_url)
            
            # Complete authentication
            session_data = self.generate_session(request_token)
            
            # Save token for future use
            self.token_manager.save_token(
                access_token=self.access_token,
                user_id=self.user_id,
                additional_data=session_data
            )
            
            print("\\n🎉 FULL AUTOMATION SUCCESSFUL!")
            print(f"👤 User ID: {session_data.get('user_id', 'N/A')}")
            print("💾 Token saved for future sessions")
            print("🤖 Next run will be even faster (token-based)")
            
            return session_data
            
        except Exception as e:
            logger.error(f"Fully automated authentication failed: {e}")
            print(f"\\n❌ Automation failed: {e}")
            print("\\n💡 Troubleshooting:")
            print("   1. Verify all credentials in .env file")
            print("   2. Check TOTP secret is correct")
            print("   3. Ensure Chrome browser is installed")
            print("   4. Try with HEADLESS_BROWSER=false for debugging")
            raise
        finally:
            # Clean up server
            if self.callback_server:
                self.callback_server.stop()
    
    def authenticate_ultimate(self, timeout: int = 300) -> dict:
        """
        Ultimate authentication that tries all methods in order of preference:
        1. Saved token (instant)
        2. Full automation (if configured)
        3. Manual OAuth flow (fallback)
        
        Args:
            timeout: Maximum time to wait for authentication.
            
        Returns:
            Dictionary containing session data.
        """
        # Try saved token first
        token_status = self.token_manager.get_token_status()
        
        if token_status['valid']:
            print("\\n" + "="*80)
            print("⚡ INSTANT AUTHENTICATION (SAVED TOKEN)")
            print("="*80)
            print(f"💾 Using saved token for: {token_status['user_id']}")
            print(f"⏰ Valid until: {token_status['expires_at']}")
            
            if self.authenticate_with_saved_token():
                print("\\n✅ Instant authentication successful!")
                profile = self.get_profile()
                return {
                    'user_id': self.user_id,
                    'access_token': self.access_token,
                    'login_time': 'Instant (saved token)',
                    'profile': profile
                }
        
        # Try full automation if configured
        if config.validate_full_automation():
            print("\\n💡 Saved token not available")
            print("🤖 Full automation configured - using automated login")
            return self.authenticate_fully_automated(timeout)
        
        # Fallback to manual OAuth
        print("\\n💡 Full automation not configured")
        print("🔐 Falling back to manual OAuth authentication")
        return self.authenticate_automatically(timeout, open_browser=True)
    
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
            
            # Stop callback server if running
            if self.callback_server:
                self.callback_server.stop()
                self.callback_server = None
            
            # Clear saved token
            self.token_manager.clear_token()
            
            return True
        except Exception as e:
            logger.error(f"Logout failed: {e}")
            return False
