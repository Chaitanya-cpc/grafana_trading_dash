#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
State Manager Module
Manages application state, positions, PNL tracking, etc.
"""

import os
import time
import threading
from datetime import datetime
import pytz
import json

class StateManager:
    """Manages application state, positions, PNL tracking, etc."""
    
    def __init__(self, db_client, logger):
        """Initialize the state manager"""
        self.db_client = db_client
        self.logger = logger
        
        # Application state
        self.is_market_open = False
        self.app_start_time = datetime.now()
        
        # Position tracking
        self.positions = {}  # Format: {instrument_token: {"quantity": int, "average_price": float, "pnl": float, ...}}
        self.last_position_update = None
        
        # PNL tracking
        self.day_pnl = 0.0  # Total PNL (realized + unrealized) for the day
        self.realized_pnl = 0.0  # Realized PNL for the day
        self.unrealized_pnl = 0.0  # Current unrealized PNL
        self.peak_day_pnl = 0.0  # Peak intraday PNL
        self.max_drawdown = 0.0  # Maximum drawdown from peak
        self.current_drawdown = 0.0  # Current drawdown from peak
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Init Indian timezone
        self.india_tz = pytz.timezone('Asia/Kolkata')
    
    def update_positions(self, position_data):
        """Update the position state from Zerodha API response"""
        with self.lock:
            try:
                # Clear current positions
                self.positions = {}
                
                # Extract day and net positions
                day_positions = position_data.get("day", [])
                net_positions = position_data.get("net", [])
                
                # Process positions
                all_positions = day_positions + net_positions
                for position in all_positions:
                    # Skip if not a valid position
                    if not position or not position.get("instrument_token"):
                        continue
                    
                    token = position["instrument_token"]
                    
                    # Only process each instrument once
                    if token in self.positions:
                        continue
                    
                    # Add to our positions dict
                    self.positions[token] = {
                        "instrument_token": token,
                        "tradingsymbol": position.get("tradingsymbol", ""),
                        "quantity": position.get("quantity", 0),
                        "average_price": position.get("average_price", 0.0),
                        "last_price": position.get("last_price", 0.0),
                        "pnl": position.get("pnl", 0.0),
                        "product": position.get("product", ""),
                        "exchange": position.get("exchange", ""),
                        "unrealized_pnl": 0.0,  # Will be calculated when ticks arrive
                        "last_update": datetime.now(self.india_tz)
                    }
                
                # Log the positions update
                self.last_position_update = datetime.now(self.india_tz)
                self.logger.info(f"Updated positions: {len(self.positions)} active positions")
                
                # Write positions snapshot to InfluxDB
                self._write_positions_to_db()
                
                # Calculate unrealized PNL based on positions
                self._calculate_unrealized_pnl()
                
                return True
                
            except Exception as e:
                self.logger.error(f"Error updating positions: {str(e)}")
                return False
    
    def update_pnl_for_tick(self, tick):
        """Update the unrealized PNL for a position when a new tick arrives"""
        with self.lock:
            try:
                token = tick["instrument_token"]
                
                # If we don't have this instrument in our positions, nothing to do
                if token not in self.positions:
                    return
                
                position = self.positions[token]
                
                # Update last price
                position["last_price"] = tick["last_price"]
                position["last_update"] = datetime.now(self.india_tz)
                
                # Calculate unrealized PNL for this position
                qty = position["quantity"]
                avg_price = position["average_price"]
                last_price = position["last_price"]
                
                # PNL calculation (depends on long/short position)
                if qty > 0:  # Long position
                    position["unrealized_pnl"] = (last_price - avg_price) * qty
                elif qty < 0:  # Short position
                    position["unrealized_pnl"] = (avg_price - last_price) * abs(qty)
                else:  # No position
                    position["unrealized_pnl"] = 0.0
                
                # Recalculate total unrealized PNL
                self._calculate_unrealized_pnl()
                
                # Update total day PNL (unrealized + realized)
                self.day_pnl = self.unrealized_pnl + self.realized_pnl
                
                # Check for new peak PNL and calculate drawdown
                if self.day_pnl > self.peak_day_pnl:
                    self.peak_day_pnl = self.day_pnl
                    self.current_drawdown = 0.0
                else:
                    # Calculate current drawdown
                    if self.peak_day_pnl > 0:
                        self.current_drawdown = self.peak_day_pnl - self.day_pnl
                    else:
                        self.current_drawdown = abs(self.day_pnl)
                    
                    # Update max drawdown if current is greater
                    if self.current_drawdown > self.max_drawdown:
                        self.max_drawdown = self.current_drawdown
                
                # Write PNL update to InfluxDB
                self._write_pnl_to_db()
                
                return True
                
            except Exception as e:
                self.logger.error(f"Error updating PNL for tick: {str(e)}")
                return False
    
    def _calculate_unrealized_pnl(self):
        """Calculate the total unrealized PNL across all positions"""
        try:
            total_unrealized = 0.0
            
            for token, position in self.positions.items():
                total_unrealized += position.get("unrealized_pnl", 0.0)
            
            self.unrealized_pnl = total_unrealized
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error calculating unrealized PNL: {str(e)}")
            return False
    
    def _write_positions_to_db(self):
        """Write positions snapshot to InfluxDB"""
        try:
            # Create a data point for each position
            data_points = []
            
            for token, position in self.positions.items():
                data_point = {
                    "measurement": "positions_snapshot",
                    "tags": {
                        "instrument_token": token,
                        "tradingsymbol": position["tradingsymbol"],
                        "exchange": position["exchange"],
                        "product": position["product"]
                    },
                    "fields": {
                        "quantity": position["quantity"],
                        "average_price": position["average_price"],
                        "last_price": position["last_price"],
                        "unrealized_pnl": position["unrealized_pnl"]
                    },
                    "time": datetime.now(self.india_tz).isoformat()
                }
                
                data_points.append(data_point)
            
            # Write to InfluxDB
            if data_points:
                self.db_client.write_points(data_points)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing positions to InfluxDB: {str(e)}")
            return False
    
    def _write_pnl_to_db(self):
        """Write PNL update to InfluxDB"""
        try:
            # Create data point
            data_point = {
                "measurement": "pnl",
                "tags": {
                    "type": "intraday"
                },
                "fields": {
                    "unrealized_pnl": self.unrealized_pnl,
                    "realized_pnl": self.realized_pnl,
                    "day_pnl": self.day_pnl,
                    "peak_day_pnl": self.peak_day_pnl,
                    "current_drawdown": self.current_drawdown,
                    "max_drawdown": self.max_drawdown
                },
                "time": datetime.now(self.india_tz).isoformat()
            }
            
            # Write to InfluxDB
            self.db_client.write_point(data_point)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing PNL to InfluxDB: {str(e)}")
            return False 