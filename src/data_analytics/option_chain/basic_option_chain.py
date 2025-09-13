#!/usr/bin/env python3
"""
Basic Option Chain Display Module

This module creates a live, dynamically updating option chain table
for a given ticker using Zerodha Kite Connect API.

Features:
- Live option chain data with auto-refresh
- ATM strike detection and highlighting
- ITM/OTM color coding
- OI horizontal bar graphs
- Straddle price calculation
- Separate GUI window with table display

Usage:
    python src/data_analytics/basic_option_chain.py
"""

import json
import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.auth.kite_auth import KiteAuth
from src.utils.logger import logger
from src.utils.config import Config

# Logger is already configured in the imported module


class OptionChainConfig:
    """Enhanced configuration loader for multi-instrument option chain display."""
    
    def __init__(self, config_file: str = None):
        """Load configuration from JSON file."""
        if config_file is None:
            # Default to config file in the same directory as this module
            module_dir = os.path.dirname(os.path.abspath(__file__))
            config_file = os.path.join(module_dir, "config.json")
        
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load configuration from JSON file."""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {self.config_file}")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file {self.config_file} not found")
            logger.info("Run: python3 config_generator.py to create configuration")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise
    
    def get_active_instruments(self) -> List[str]:
        """Get list of active instruments."""
        active_instruments = []
        instruments = self.config.get("instruments", {})
        
        for instrument_name, details in instruments.items():
            if details.get("active", 0) == 1:
                active_instruments.append(instrument_name)
        
        return active_instruments
    
    def get_instrument_config(self, instrument_name: str) -> dict:
        """Get configuration for a specific instrument."""
        instruments = self.config.get("instruments", {})
        if instrument_name not in instruments:
            raise ValueError(f"Instrument {instrument_name} not found in configuration")
        
        return instruments[instrument_name]
    
    # Display settings properties
    @property
    def refresh_interval_seconds(self) -> int:
        return self.config.get("display_settings", {}).get("refresh_interval_seconds", 10)
    
    @property
    def window_width(self) -> int:
        return self.config.get("display_settings", {}).get("window_width", 1400)
    
    @property
    def window_height(self) -> int:
        return self.config.get("display_settings", {}).get("window_height", 700)
    
    @property
    def strikes_above_atm(self) -> int:
        return self.config.get("display_settings", {}).get("strikes_above_atm", 3)
    
    @property
    def strikes_below_atm(self) -> int:
        return self.config.get("display_settings", {}).get("strikes_below_atm", 3)
    
    @property
    def colors(self) -> dict:
        return self.config.get("display_settings", {}).get("colors", {})


class OptionData:
    """Data structure for option information."""
    
    def __init__(self, strike: float, call_price: float = 0.0, put_price: float = 0.0,
                 call_oi: int = 0, put_oi: int = 0):
        self.strike = strike
        self.call_price = call_price
        self.put_price = put_price
        self.call_oi = call_oi
        self.put_oi = put_oi
    
    @property
    def straddle_price(self) -> float:
        """Calculate straddle price (call + put)."""
        return self.call_price + self.put_price


class OptionChainGUI:
    """GUI class for displaying live option chain data for a specific instrument."""
    
    def __init__(self, config: OptionChainConfig, kite_instance, instrument_name: str):
        self.config = config
        self.kite = kite_instance
        self.instrument_name = instrument_name
        self.instrument_config = config.get_instrument_config(instrument_name)
        
        # GUI components
        self.root = None
        self.tree = None
        self.running = False
        
        # Data
        self.current_atm_strike = None
        self.option_data: List[OptionData] = []
        self.max_call_oi = 1
        self.max_put_oi = 1
        
        # Initialize GUI
        self._setup_gui()
        
        # Start data refresh thread
        self.running = True
        self.refresh_thread = threading.Thread(target=self._refresh_loop, daemon=True)
        self.refresh_thread.start()
    
    def _setup_gui(self):
        """Initialize the GUI window and components."""
        self.root = tk.Tk()
        self.root.title(self.instrument_config.get("window_title", f"Option Chain - {self.instrument_name}"))
        self.root.geometry(f"{self.config.window_width}x{self.config.window_height}")
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title label with instrument info
        strike_diff = self.instrument_config.get("strike_difference", 50)
        lot_size = self.instrument_config.get("lot_size", 1)
        title_label = ttk.Label(
            main_frame, 
            text=f"Live Option Chain - {self.instrument_name} | Strike Diff: {strike_diff} | Lot: {lot_size}",
            font=("Arial", 14, "bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 10))
        
        # Create treeview for option chain table
        columns = ("Strike", "Call Price", "Call OI", "Put Price", "Put OI", "Straddle")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=15)
        
        # Define column headings and widths
        column_widths = {
            "Strike": 100,
            "Call Price": 120,
            "Call OI": 200,
            "Put Price": 120,
            "Put OI": 200,
            "Straddle": 120
        }
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths.get(col, 100), anchor=tk.CENTER)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid the treeview and scrollbar
        self.tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Initializing...")
        self.status_label.grid(row=2, column=0, pady=(10, 0))
        
        logger.info("GUI setup completed")
    
    def _get_current_price(self) -> Optional[float]:
        """Get current price of the underlying asset."""
        try:
            # For indices, we need to get the index price
            if self.instrument_name in ["NIFTY", "BANKNIFTY", "FINNIFTY"]:
                index_map = {
                    "NIFTY": "NSE:NIFTY 50",
                    "BANKNIFTY": "NSE:NIFTY BANK", 
                    "FINNIFTY": "NSE:NIFTY FIN SERVICE"
                }
                index_symbol = index_map.get(self.instrument_name)
                if index_symbol:
                    quote = self.kite.quote([index_symbol])
                    if quote and index_symbol in quote:
                        return quote[index_symbol]["last_price"]
            else:
                # For stocks, get the stock price
                quote = self.kite.quote([f"NSE:{self.instrument_name}"])
                if quote and f"NSE:{self.instrument_name}" in quote:
                    return quote[f"NSE:{self.instrument_name}"]["last_price"]
            
            logger.warning(f"Could not fetch price for {self.instrument_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching current price: {e}")
            return None
    
    def _calculate_atm_strike(self, current_price: float) -> float:
        """Calculate ATM strike based on current price."""
        if current_price is None:
            return None
        
        strike_diff = self.instrument_config.get("strike_difference", 50)
        # Round to nearest strike
        atm_strike = round(current_price / strike_diff) * strike_diff
        return atm_strike
    
    def _generate_strike_list(self, atm_strike: float) -> List[float]:
        """Generate list of strikes to monitor."""
        strikes = []
        strike_diff = self.instrument_config.get("strike_difference", 50)
        
        # Add strikes below ATM
        for i in range(self.config.strikes_below_atm, 0, -1):
            strikes.append(atm_strike - (i * strike_diff))
        
        # Add ATM strike
        strikes.append(atm_strike)
        
        # Add strikes above ATM
        for i in range(1, self.config.strikes_above_atm + 1):
            strikes.append(atm_strike + (i * strike_diff))
        
        return strikes
    
    def _get_option_instruments(self) -> Dict[str, dict]:
        """Get option instruments for the ticker."""
        try:
            # Get all instruments from the exchange specified in config
            exchange = self.instrument_config.get("exchange", "NFO")
            instruments = self.kite.instruments(exchange)
            
            # Filter for current ticker options
            ticker_options = {}
            
            for instrument in instruments:
                if (instrument["name"] == self.instrument_name and 
                    instrument["instrument_type"] in ["CE", "PE"]):
                    
                    # Create a key for easy lookup
                    key = f"{instrument['strike']}_{instrument['instrument_type']}"
                    ticker_options[key] = instrument
            
            logger.info(f"Found {len(ticker_options)} option instruments for {self.instrument_name}")
            return ticker_options
            
        except Exception as e:
            logger.error(f"Error fetching option instruments: {e}")
            return {}
    
    def _fetch_option_data(self) -> List[OptionData]:
        """Fetch live option chain data."""
        try:
            # Get current price and ATM strike
            current_price = self._get_current_price()
            if current_price is None:
                return []
            
            atm_strike = self._calculate_atm_strike(current_price)
            if atm_strike is None:
                return []
            
            self.current_atm_strike = atm_strike
            strikes = self._generate_strike_list(atm_strike)
            
            # Get option instruments
            option_instruments = self._get_option_instruments()
            
            option_data = []
            instrument_tokens = []
            token_to_strike_type = {}
            
            # Collect instrument tokens for quotes
            for strike in strikes:
                call_key = f"{strike}_CE"
                put_key = f"{strike}_PE"
                
                if call_key in option_instruments:
                    token = option_instruments[call_key]["instrument_token"]
                    instrument_tokens.append(token)
                    token_to_strike_type[token] = (strike, "CE")
                
                if put_key in option_instruments:
                    token = option_instruments[put_key]["instrument_token"]
                    instrument_tokens.append(token)
                    token_to_strike_type[token] = (strike, "PE")
            
            # Get quotes for all instruments
            if not instrument_tokens:
                logger.warning("No option instruments found")
                return []
            
            quotes = self.kite.quote(instrument_tokens)
            
            # Process quotes and create OptionData objects
            strike_data = {}
            for token, quote_data in quotes.items():
                if token in token_to_strike_type:
                    strike, option_type = token_to_strike_type[token]
                    
                    if strike not in strike_data:
                        strike_data[strike] = OptionData(strike)
                    
                    last_price = quote_data.get("last_price", 0)
                    oi = quote_data.get("oi", 0)
                    
                    if option_type == "CE":
                        strike_data[strike].call_price = last_price
                        strike_data[strike].call_oi = oi
                    else:  # PE
                        strike_data[strike].put_price = last_price
                        strike_data[strike].put_oi = oi
            
            # Convert to list and sort by strike
            option_data = list(strike_data.values())
            option_data.sort(key=lambda x: x.strike)
            
            # Calculate max OI for scaling
            if option_data:
                self.max_call_oi = max([opt.call_oi for opt in option_data]) or 1
                self.max_put_oi = max([opt.put_oi for opt in option_data]) or 1
            
            logger.info(f"Fetched option data for {len(option_data)} strikes")
            return option_data
            
        except Exception as e:
            logger.error(f"Error fetching option data: {e}")
            return []
    
    def _create_oi_bar(self, oi_value: int, max_oi: int, bar_color: str) -> str:
        """Create a text-based horizontal bar for OI display."""
        if max_oi == 0:
            return f"{oi_value:,}"
        
        # Calculate bar length (max 20 characters)
        max_bar_length = 15
        bar_length = int((oi_value / max_oi) * max_bar_length)
        
        # Create bar with unicode block characters
        bar = "█" * bar_length + "░" * (max_bar_length - bar_length)
        
        return f"{bar} {oi_value:,}"
    
    def _update_display(self):
        """Update the GUI display with current option data."""
        if not self.option_data:
            return
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        current_price = self._get_current_price()
        
        # Insert new data
        for option in self.option_data:
            strike = option.strike
            
            # Determine ITM/OTM status
            call_color = "red" if current_price and strike < current_price else "green"
            put_color = "red" if current_price and strike > current_price else "green"
            
            # Create OI bars
            call_oi_bar = self._create_oi_bar(option.call_oi, self.max_call_oi, "green")
            put_oi_bar = self._create_oi_bar(option.put_oi, self.max_put_oi, "orange")
            
            # Insert row
            item = self.tree.insert("", "end", values=(
                f"{strike:.0f}",
                f"{option.call_price:.2f}",
                call_oi_bar,
                f"{option.put_price:.2f}",
                put_oi_bar,
                f"{option.straddle_price:.2f}"
            ))
            
            # Highlight ATM row
            if strike == self.current_atm_strike:
                self.tree.set(item, "Strike", f"● {strike:.0f}")  # Add bullet for ATM
        
        # Update status
        current_time = datetime.now().strftime("%H:%M:%S")
        status_text = f"Last Updated: {current_time}"
        if current_price:
            status_text += f" | Current Price: {current_price:.2f}"
        if self.current_atm_strike:
            status_text += f" | ATM Strike: {self.current_atm_strike:.0f}"
        
        self.status_label.config(text=status_text)
    
    def _refresh_loop(self):
        """Background thread for refreshing data."""
        logger.info("Starting data refresh loop")
        
        while self.running:
            try:
                # Fetch new data
                self.option_data = self._fetch_option_data()
                
                # Update GUI in main thread
                if self.root:
                    self.root.after(0, self._update_display)
                
                # Wait for next refresh
                time.sleep(self.config.refresh_interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in refresh loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _on_closing(self):
        """Handle window closing."""
        logger.info("Closing option chain display")
        self.running = False
        if self.refresh_thread and self.refresh_thread.is_alive():
            self.refresh_thread.join(timeout=2)
        self.root.destroy()
    
    def run(self):
        """Start the GUI application."""
        logger.info("Starting option chain GUI")
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            self._on_closing()


def main():
    """Main function to run the option chain display for all active instruments."""
    try:
        logger.info("Starting Multi-Instrument Option Chain Display")
        
        # Load configuration
        config = OptionChainConfig()
        active_instruments = config.get_active_instruments()
        
        if not active_instruments:
            print("❌ No active instruments found in configuration!")
            print("💡 Edit config.json and set 'active': 1 for instruments you want to monitor")
            print("🔧 Or run: python3 config_generator.py to regenerate configuration")
            return False
        
        logger.info(f"Found {len(active_instruments)} active instruments: {', '.join(active_instruments)}")
        
        # Initialize authentication
        logger.info("Initializing Zerodha authentication...")
        auth = KiteAuth()
        
        # Try to authenticate using existing token or full automation
        success = auth.authenticate_ultimate()
        
        if not success:
            messagebox.showerror(
                "Authentication Error", 
                "Failed to authenticate with Zerodha. Please check your credentials."
            )
            return False
        
        kite = auth.get_kite_instance()
        logger.info("Authentication successful")
        
        print(f"\n🚀 Launching option chains for {len(active_instruments)} instruments...")
        
        if len(active_instruments) == 1:
            # Single instrument - run directly in main thread
            instrument = active_instruments[0]
            try:
                logger.info(f"Creating option chain for {instrument}")
                gui = OptionChainGUI(config, kite, instrument)
                print(f"✅ {instrument} - Option chain window opened")
                print("🔄 Data refreshes every 10 seconds")
                print("💡 Close window or press Ctrl+C to exit")
                gui.run()
                
            except Exception as e:
                logger.error(f"Error creating GUI for {instrument}: {e}")
                print(f"❌ {instrument} - Failed to create option chain: {e}")
                return False
        
        else:
            # Multiple instruments - need special handling
            print("⚠️  Multiple instrument display detected!")
            print("💡 For best performance, activate only 1 instrument at a time")
            print("🔧 Use: python3 manage_instruments.py to manage active instruments")
            
            # Run the first instrument for now
            instrument = active_instruments[0]
            print(f"🎯 Launching {instrument} (first active instrument)")
            try:
                logger.info(f"Creating option chain for {instrument}")
                gui = OptionChainGUI(config, kite, instrument)
                print(f"✅ {instrument} - Option chain window opened")
                print("🔄 Data refreshes every 10 seconds")
                print("💡 Close window or press Ctrl+C to exit")
                gui.run()
                
            except Exception as e:
                logger.error(f"Error creating GUI for {instrument}: {e}")
                print(f"❌ {instrument} - Failed to create option chain: {e}")
                return False
        
        return True
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return True
    except Exception as e:
        logger.error(f"Error in main: {e}")
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
