#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WebSocket Client Module for Zerodha Kite Ticker
Handles real-time websocket connections and data streaming
"""

import os
import time
import json
import threading
import traceback
from datetime import datetime
import pytz
from kiteconnect import KiteTicker
import pandas as pd

class KiteTickerClient:
    """Client for Zerodha Kite Ticker WebSocket"""
    
    def __init__(self, api_key, access_token, db_client, state_manager, logger):
        """Initialize the WebSocket client"""
        self.api_key = api_key
        self.access_token = access_token
        self.db_client = db_client
        self.state_manager = state_manager
        self.logger = logger
        
        self.ticker = None
        self.is_connected = False
        self.last_heartbeat = None
        self.last_tick = {}  # Store last tick per instrument
        self.tick_count = 0
        self.reconnect_count = 0
        self.subscribed_tokens = set()
        
        # Lock for thread-safe operations
        self.lock = threading.Lock()
        
        # For building candles from ticks
        self.candle_data = {}  # Format: {token: {"timestamp": [], "open": [], "high": [], "low": [], "close": [], "volume": []}}
        
        # Init Indian timezone
        self.india_tz = pytz.timezone('Asia/Kolkata')
    
    def connect(self):
        """Connect to the Kite Ticker WebSocket"""
        try:
            self.logger.info("Connecting to Kite Ticker WebSocket")
            
            # Initialize the ticker
            self.ticker = KiteTicker(self.api_key, self.access_token)
            
            # Set callback functions
            self.ticker.on_ticks = self.on_ticks
            self.ticker.on_connect = self.on_connect
            self.ticker.on_close = self.on_close
            self.ticker.on_error = self.on_error
            self.ticker.on_reconnect = self.on_reconnect
            self.ticker.on_noreconnect = self.on_noreconnect
            self.ticker.on_order_update = self.on_order_update
            
            # Connect to WebSocket
            self.ticker.connect(threaded=True)
            
            # Wait for confirmation of connection
            timeout = 10  # seconds
            start_time = time.time()
            while not self.is_connected and time.time() - start_time < timeout:
                time.sleep(0.1)
            
            if not self.is_connected:
                raise Exception("Timed out waiting for WebSocket connection")
            
            self.logger.info("Successfully connected to Kite Ticker WebSocket")
            return True
            
        except Exception as e:
            self.logger.error(f"Error connecting to Kite Ticker: {str(e)}")
            traceback.print_exc()
            self._log_ws_health("connect", False, str(e))
            return False
    
    def disconnect(self):
        """Disconnect from the WebSocket"""
        try:
            if self.ticker:
                self.logger.info("Disconnecting from Kite Ticker WebSocket")
                self.ticker.close(1000, "Normal closure")
                self.is_connected = False
                self._log_ws_health("disconnect", True)
        except Exception as e:
            self.logger.error(f"Error disconnecting from Kite Ticker: {str(e)}")
            self._log_ws_health("disconnect", False, str(e))
    
    def subscribe(self, tokens):
        """Subscribe to given instrument tokens"""
        if not self.is_connected or not self.ticker:
            self.logger.warning("Cannot subscribe, WebSocket not connected")
            return False
        
        try:
            if isinstance(tokens, (int, str)):
                tokens = [int(tokens)]
            else:
                tokens = [int(t) for t in tokens]
            
            new_tokens = [t for t in tokens if t not in self.subscribed_tokens]
            if not new_tokens:
                self.logger.debug("No new tokens to subscribe")
                return True
            
            self.logger.info(f"Subscribing to {len(new_tokens)} instrument tokens")
            self.ticker.subscribe(new_tokens)
            self.ticker.set_mode(self.ticker.MODE_FULL, new_tokens)
            
            with self.lock:
                self.subscribed_tokens.update(new_tokens)
            
            self._log_ws_health("subscribe", True, None, len(new_tokens))
            return True
            
        except Exception as e:
            self.logger.error(f"Error subscribing to tokens: {str(e)}")
            self._log_ws_health("subscribe", False, str(e))
            return False
    
    def unsubscribe(self, tokens):
        """Unsubscribe from given instrument tokens"""
        if not self.is_connected or not self.ticker:
            self.logger.warning("Cannot unsubscribe, WebSocket not connected")
            return False
        
        try:
            if isinstance(tokens, (int, str)):
                tokens = [int(tokens)]
            else:
                tokens = [int(t) for t in tokens]
            
            existing_tokens = [t for t in tokens if t in self.subscribed_tokens]
            if not existing_tokens:
                self.logger.debug("No tokens to unsubscribe")
                return True
            
            self.logger.info(f"Unsubscribing from {len(existing_tokens)} instrument tokens")
            self.ticker.unsubscribe(existing_tokens)
            
            with self.lock:
                self.subscribed_tokens.difference_update(existing_tokens)
            
            self._log_ws_health("unsubscribe", True, None, len(existing_tokens))
            return True
            
        except Exception as e:
            self.logger.error(f"Error unsubscribing from tokens: {str(e)}")
            self._log_ws_health("unsubscribe", False, str(e))
            return False
    
    def on_ticks(self, ws, ticks):
        """Callback when ticks are received"""
        try:
            if not ticks:
                return
            
            # Update tick counter
            self.tick_count += len(ticks)
            
            # Process each tick
            for tick in ticks:
                token = tick['instrument_token']
                
                # Store the last tick for this instrument
                with self.lock:
                    self.last_tick[token] = tick
                    
                # Process the tick (update PnL, update candles, etc.)
                self._process_tick(tick)
                
            # Update last heartbeat time
            now = datetime.now(self.india_tz)
            self.last_heartbeat = now
            
            # Every 10th tick batch, log a tick rate sample
            if self.tick_count % 10 == 0:
                self._log_tick_rate()
                
        except Exception as e:
            self.logger.error(f"Error processing ticks: {str(e)}")
            traceback.print_exc()
    
    def on_connect(self, ws, response):
        """Callback when connection is established"""
        self.is_connected = True
        self.last_heartbeat = datetime.now(self.india_tz)
        self.logger.info("WebSocket connected successfully")
        self._log_ws_health("connect", True)
    
    def on_close(self, ws, code, reason):
        """Callback when connection is closed"""
        self.is_connected = False
        self.logger.info(f"WebSocket connection closed: {code} - {reason}")
        self._log_ws_health("close", True, f"Code: {code}, Reason: {reason}")
    
    def on_error(self, ws, error):
        """Callback when error occurs"""
        self.logger.error(f"WebSocket error: {str(error)}")
        self._log_ws_health("error", False, str(error))
    
    def on_reconnect(self, ws, attempt_count):
        """Callback on reconnection attempt"""
        self.reconnect_count += 1
        self.logger.warning(f"WebSocket reconnecting.. attempt {attempt_count}")
        self._log_ws_health("reconnect", True, f"Attempt: {attempt_count}")
    
    def on_noreconnect(self, ws):
        """Callback when reconnection fails permanently"""
        self.logger.error("WebSocket reconnection failed permanently")
        self._log_ws_health("noreconnect", False, "Reconnection failed permanently")
    
    def on_order_update(self, ws, data):
        """Callback when order update is received"""
        try:
            self.logger.info(f"Order update received: {data['order_id']}")
            
            # Process order update
            # This is where you'd handle order updates, possibly update state,
            # trigger PnL calculations, etc.
            
            # Log the order update to InfluxDB
            self._log_order_update(data)
            
        except Exception as e:
            self.logger.error(f"Error processing order update: {str(e)}")
            traceback.print_exc()
    
    def _process_tick(self, tick):
        """Process a single tick"""
        try:
            token = tick['instrument_token']
            
            # Write tick to InfluxDB
            self._write_tick_to_db(tick)
            
            # Update unrealized PnL if this is a position
            self.state_manager.update_pnl_for_tick(tick)
            
            # Update candle data for this token
            self._update_candle_data(tick)
            
        except Exception as e:
            self.logger.error(f"Error in _process_tick: {str(e)}")
    
    def _update_candle_data(self, tick):
        """Update candle data based on ticks"""
        try:
            token = tick['instrument_token']
            
            # Get current timestamp for the candle
            now = datetime.now(self.india_tz)
            interval = int(os.getenv("INDICATOR_TIMEFRAME", "5minute").replace("minute", ""))
            
            # Calculate the current candle's start time (truncate to nearest interval)
            minutes = now.minute - (now.minute % interval)
            candle_start = now.replace(minute=minutes, second=0, microsecond=0)
            candle_ts = int(candle_start.timestamp())
            
            # Initialize candle data for this token if needed
            if token not in self.candle_data:
                self.candle_data[token] = {
                    "timestamp": [],
                    "open": [],
                    "high": [],
                    "low": [],
                    "close": [],
                    "volume": []
                }
            
            # Check if we need to start a new candle
            if not self.candle_data[token]["timestamp"] or self.candle_data[token]["timestamp"][-1] != candle_ts:
                # New candle period started
                self.candle_data[token]["timestamp"].append(candle_ts)
                self.candle_data[token]["open"].append(tick['last_price'])
                self.candle_data[token]["high"].append(tick['last_price'])
                self.candle_data[token]["low"].append(tick['last_price'])
                self.candle_data[token]["close"].append(tick['last_price'])
                self.candle_data[token]["volume"].append(tick.get('volume', 0))
                
                # If we exceed a certain length, trim the lists
                max_candles = 100  # Keep at most 100 candles in memory
                if len(self.candle_data[token]["timestamp"]) > max_candles:
                    for key in self.candle_data[token].keys():
                        self.candle_data[token][key] = self.candle_data[token][key][-max_candles:]
                
                # If this is a completed candle, store it in InfluxDB
                if len(self.candle_data[token]["timestamp"]) > 1:
                    self._store_completed_candle(token, -2)  # Store the second-to-last candle
            else:
                # Update existing candle
                idx = -1  # Last item in the list
                self.candle_data[token]["high"][idx] = max(self.candle_data[token]["high"][idx], tick['last_price'])
                self.candle_data[token]["low"][idx] = min(self.candle_data[token]["low"][idx], tick['last_price'])
                self.candle_data[token]["close"][idx] = tick['last_price']
                self.candle_data[token]["volume"][idx] += tick.get('volume', 0) - self.candle_data[token]["volume"][idx]
        
        except Exception as e:
            self.logger.error(f"Error in _update_candle_data: {str(e)}")
    
    def _store_completed_candle(self, token, index):
        """Store a completed candle in InfluxDB"""
        try:
            # Create data point
            data_point = {
                "measurement": "candles",
                "tags": {
                    "instrument_token": token,
                    "interval": os.getenv("INDICATOR_TIMEFRAME", "5minute")
                },
                "fields": {
                    "open": self.candle_data[token]["open"][index],
                    "high": self.candle_data[token]["high"][index],
                    "low": self.candle_data[token]["low"][index],
                    "close": self.candle_data[token]["close"][index],
                    "volume": self.candle_data[token]["volume"][index]
                },
                "time": datetime.fromtimestamp(
                    self.candle_data[token]["timestamp"][index], 
                    self.india_tz
                ).isoformat()
            }
            
            # Write to InfluxDB
            self.db_client.write_point(data_point)
            
        except Exception as e:
            self.logger.error(f"Error storing candle in InfluxDB: {str(e)}")
    
    def _write_tick_to_db(self, tick):
        """Write a tick to InfluxDB"""
        try:
            # Extract fields we're interested in
            token = tick['instrument_token']
            
            # Create data point
            data_point = {
                "measurement": "ticks",
                "tags": {
                    "instrument_token": token,
                },
                "fields": {
                    "last_price": tick['last_price'],
                    "volume": tick.get('volume', 0),
                    "buy_quantity": tick.get('buy_quantity', 0),
                    "sell_quantity": tick.get('sell_quantity', 0),
                    "change": tick.get('change', 0)
                },
                "time": datetime.now(self.india_tz).isoformat()
            }
            
            # Optional fields if available
            for field in ['open', 'high', 'low', 'close']:
                if field in tick:
                    data_point["fields"][field] = tick[field]
            
            # Write to InfluxDB
            self.db_client.write_point(data_point)
            
        except Exception as e:
            self.logger.error(f"Error writing tick to InfluxDB: {str(e)}")
    
    def _log_tick_rate(self):
        """Log tick rate metrics to InfluxDB"""
        try:
            now = datetime.now(self.india_tz)
            
            # Create data point
            data_point = {
                "measurement": "tick_rate",
                "tags": {
                    "source": "websocket"
                },
                "fields": {
                    "ticks_per_minute": self.tick_count,
                    "instrument_count": len(self.subscribed_tokens)
                },
                "time": now.isoformat()
            }
            
            # Reset the tick counter after logging
            self.tick_count = 0
            
            # Write to InfluxDB
            self.db_client.write_point(data_point)
            
        except Exception as e:
            self.logger.error(f"Error logging tick rate to InfluxDB: {str(e)}")
    
    def _log_ws_health(self, event_type, success, error_message=None, count=None):
        """Log WebSocket health metrics to InfluxDB"""
        try:
            # Create data point
            data_point = {
                "measurement": "websocket_health",
                "tags": {
                    "event_type": event_type,
                    "success": success
                },
                "fields": {
                    "reconnect_count": self.reconnect_count
                },
                "time": datetime.now(self.india_tz).isoformat()
            }
            
            # Add error message if present
            if error_message:
                data_point["fields"]["error_message"] = str(error_message)
            
            # Add count if present
            if count is not None:
                data_point["fields"]["count"] = count
            
            # Write to InfluxDB
            self.db_client.write_point(data_point)
            
        except Exception as e:
            self.logger.error(f"Error logging WebSocket health to InfluxDB: {str(e)}")
    
    def _log_order_update(self, order_data):
        """Log order update to InfluxDB"""
        try:
            # Create data point
            data_point = {
                "measurement": "order_updates",
                "tags": {
                    "order_id": order_data.get('order_id', 'unknown'),
                    "status": order_data.get('status', 'unknown'),
                    "transaction_type": order_data.get('transaction_type', 'unknown')
                },
                "fields": {
                    "price": float(order_data.get('price', 0)),
                    "quantity": int(order_data.get('quantity', 0)),
                    "filled_quantity": int(order_data.get('filled_quantity', 0))
                },
                "time": datetime.now(self.india_tz).isoformat()
            }
            
            # Write to InfluxDB
            self.db_client.write_point(data_point)
            
        except Exception as e:
            self.logger.error(f"Error logging order update to InfluxDB: {str(e)}") 