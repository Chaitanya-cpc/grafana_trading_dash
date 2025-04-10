#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Zerodha API Client Module
Handles all interactions with the Kite Connect REST API
"""

import os
import time
import pyotp
from datetime import datetime, timedelta
import pandas as pd
import pytz
from kiteconnect import KiteConnect
import requests
import json
import traceback

class ZerodhaAPI:
    """Client for interacting with Zerodha Kite Connect API"""
    
    def __init__(self, api_key, api_secret, user_id, password, totp_key, db_client, alerter, logger):
        """Initialize the Zerodha API client"""
        self.api_key = api_key
        self.api_secret = api_secret
        self.user_id = user_id
        self.password = password
        self.totp_key = totp_key
        self.db_client = db_client
        self.alerter = alerter
        self.logger = logger
        
        self.kite = KiteConnect(api_key=self.api_key)
        self.access_token = None
        self.session_expiry = None
        
        # API call metrics
        self.api_calls = {
            "total": 0,
            "success": 0,
            "error": 0,
            "endpoints": {}
        }
        
        # Init Indian timezone
        self.india_tz = pytz.timezone('Asia/Kolkata')
    
    def connect(self):
        """Connect to Zerodha API and obtain access token"""
        try:
            # Check if we have a valid token already
            if self.access_token and self.session_expiry and datetime.now() < self.session_expiry:
                self.logger.info("Using existing access token")
                return True
            
            self.logger.info("Generating new access token")
            
            # First step: Obtain request token using credentials
            # This is a critical step that requires credential-based login
            # For production, we might need to handle this differently
            # based on how Zerodha's login flow works (QR scan, etc.)
            
            # For automatic login, we generate TOTP if key is provided
            totp = None
            if self.totp_key:
                totp = pyotp.TOTP(self.totp_key).now()
                
            # Here we're assuming you'd need to use credential-based login to get a request token
            # In a real scenario, this might need manual intervention or a different flow
            # This is a placeholder for the actual login process
            request_token = self._obtain_request_token(self.user_id, self.password, totp)
            
            if not request_token:
                self.logger.error("Failed to obtain request token")
                self.alerter.send_alert("⚠️ Failed to login to Zerodha. Please check credentials.")
                return False
            
            # Second step: Exchange request token for access token
            data = self.kite.generate_session(request_token, api_secret=self.api_secret)
            self.access_token = data["access_token"]
            self.kite.set_access_token(self.access_token)
            
            # Set session expiry (typically 1 day for Zerodha)
            self.session_expiry = datetime.now() + timedelta(days=1)
            
            self.logger.info("Successfully connected to Zerodha API")
            self.alerter.send_alert("✅ Successfully logged in to Zerodha")
            
            # Write connection success to database
            self._log_api_health("connect", True, 0)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error connecting to Zerodha: {str(e)}")
            traceback.print_exc()
            self.alerter.send_alert(f"❌ Zerodha API Connection Error: {str(e)}")
            
            # Write connection failure to database
            self._log_api_health("connect", False, 0, str(e))
            
            return False
    
    def _obtain_request_token(self, user_id, password, totp=None):
        """
        Placeholder for obtaining request token
        
        In a real implementation, this might:
        1. Use a headless browser via Selenium to log in 
        2. Interact with Zerodha's private/undocumented APIs
        3. Require manual intervention via QR code
        4. Use Kite Connect's documented login flow if available
        
        For now, we'll assume we have some way to obtain this token
        In a real implementation, you'll need to replace this with the actual login logic
        """
        # This is a placeholder - you need to implement the actual login flow
        # For testing, you might manually obtain this token and hardcode it temporarily
        self.logger.warning("_obtain_request_token is a placeholder - implement actual login flow")
        
        # Return a mock request token for now
        # In a real implementation, return the actual request token from Zerodha
        return "your_request_token_here"  # Replace with actual implementation
    
    def get_profile(self):
        """Get user profile information"""
        return self._make_api_call("profile", self.kite.profile)
    
    def get_margins(self):
        """Get user margins"""
        return self._make_api_call("margins", self.kite.margins)
    
    def get_positions(self):
        """Get user positions"""
        return self._make_api_call("positions", self.kite.positions)
    
    def get_holdings(self):
        """Get user holdings"""
        return self._make_api_call("holdings", self.kite.holdings)
    
    def get_orders(self):
        """Get user orders"""
        return self._make_api_call("orders", self.kite.orders)
    
    def get_trades(self):
        """Get user trades"""
        return self._make_api_call("trades", self.kite.trades)
    
    def get_instruments(self, exchange=None):
        """Get all instruments or for a specific exchange"""
        return self._make_api_call("instruments", lambda: self.kite.instruments(exchange))
    
    def get_quote(self, symbols):
        """Get quotes for given symbols"""
        if isinstance(symbols, str):
            symbols = [symbols]
        
        return self._make_api_call("quote", lambda: self.kite.quote(symbols))
    
    def get_ohlc(self, symbols):
        """Get OHLC data for given symbols"""
        if isinstance(symbols, str):
            symbols = [symbols]
        
        return self._make_api_call("ohlc", lambda: self.kite.ohlc(symbols))
    
    def get_historical_data(self, instrument_token, from_date, to_date, interval):
        """Get historical data for an instrument"""
        # Convert dates to string format if they're datetime objects
        if isinstance(from_date, datetime):
            from_date = from_date.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(to_date, datetime):
            to_date = to_date.strftime('%Y-%m-%d %H:%M:%S')
            
        return self._make_api_call(
            "historical_data", 
            lambda: self.kite.historical_data(
                instrument_token, from_date, to_date, interval
            )
        )
    
    def _make_api_call(self, endpoint, func, max_retries=3, retry_delay=1):
        """Make an API call with retry logic and metrics tracking"""
        self.api_calls["total"] += 1
        if endpoint not in self.api_calls["endpoints"]:
            self.api_calls["endpoints"][endpoint] = {"count": 0, "errors": 0}
        
        self.api_calls["endpoints"][endpoint]["count"] += 1
        
        start_time = time.time()
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                # Make the API call
                response = func()
                
                # Record success
                self.api_calls["success"] += 1
                latency = time.time() - start_time
                
                # Log the API call to InfluxDB
                self._log_api_call(endpoint, True, latency)
                
                return response
                
            except Exception as e:
                retry_count += 1
                last_error = e
                
                # Log the error
                self.logger.warning(f"API call to {endpoint} failed (attempt {retry_count}/{max_retries}): {str(e)}")
                
                # If we've used all retries, record as an error
                if retry_count >= max_retries:
                    self.api_calls["error"] += 1
                    self.api_calls["endpoints"][endpoint]["errors"] += 1
                    
                    # Log the API error to InfluxDB
                    latency = time.time() - start_time
                    self._log_api_call(endpoint, False, latency, str(e))
                    
                    # For serious errors, alert
                    if "session expired" in str(e).lower() or "invalid api key" in str(e).lower():
                        self.alerter.send_alert(f"⚠️ Zerodha API Error: {str(e)}")
                        # Try reconnecting
                        self.connect()
                    
                    raise e
                
                # Wait before retrying
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
        
        return None
    
    def _log_api_call(self, endpoint, success, latency, error_message=None):
        """Log API call metrics to InfluxDB"""
        try:
            # Create data point
            data_point = {
                "measurement": "api_calls",
                "tags": {
                    "endpoint": endpoint,
                    "success": success
                },
                "fields": {
                    "count": 1,
                    "latency_ms": latency * 1000  # Convert to milliseconds
                },
                "time": datetime.now(self.india_tz).isoformat()
            }
            
            # Add error message if present
            if error_message:
                data_point["fields"]["error_message"] = str(error_message)
            
            # Write to InfluxDB
            self.db_client.write_point(data_point)
            
        except Exception as e:
            self.logger.error(f"Error logging API call to InfluxDB: {str(e)}")
    
    def _log_api_health(self, event_type, success, latency, error_message=None):
        """Log API health events to InfluxDB"""
        try:
            # Create data point
            data_point = {
                "measurement": "api_health",
                "tags": {
                    "event_type": event_type,
                    "success": success
                },
                "fields": {
                    "latency_ms": latency * 1000  # Convert to milliseconds
                },
                "time": datetime.now(self.india_tz).isoformat()
            }
            
            # Add error message if present
            if error_message:
                data_point["fields"]["error_message"] = str(error_message)
            
            # Write to InfluxDB
            self.db_client.write_point(data_point)
            
        except Exception as e:
            self.logger.error(f"Error logging API health to InfluxDB: {str(e)}") 