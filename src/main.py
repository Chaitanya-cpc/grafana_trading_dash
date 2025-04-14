#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main Application Entry Point
Initializes and coordinates all components of the Zerodha Dashboard
"""

import os
import sys
import time
import signal
import traceback
from datetime import datetime
import pytz

# Add project root to PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import components
from src.utils.logger import setup_logger, CustomLogger
from src.utils.config import Config
from src.utils.file_reader import read_watchlist, read_sector_map
from src.api.zerodha_api import ZerodhaAPI
from src.api.websocket_client import WebSocketClient
from src.database.influxdb_client import InfluxDBClient
from src.models.state_manager import StateManager
from src.alerts.telegram_alerter import TelegramAlerter
from src.models.scheduler import initialize as init_scheduler, shutdown as shutdown_scheduler

# Global variables for cleanup
components = {}

def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown"""
    def signal_handler(sig, frame):
        print("\nReceived shutdown signal. Cleaning up...")
        cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def cleanup():
    """Cleanup resources on shutdown"""
    print("Performing cleanup...")
    
    # Shutdown scheduler
    if "scheduler" in components:
        shutdown_scheduler()
    
    # Disconnect WebSocket
    if "websocket" in components and components["websocket"]:
        components["websocket"].disconnect()
    
    # Close DB connection
    if "db_client" in components and components["db_client"]:
        components["db_client"].close()
    
    print("Cleanup complete. Exiting.")

def main():
    """Main application entry point"""
    try:
        # Set up signal handlers
        setup_signal_handlers()
        
        # Initialize logger
        std_logger = setup_logger()
        print("Logger initialized")
        
        # Load configuration
        config = Config(config_file='config/application.yaml')
        print("Configuration loaded")
        
        # Initialize database client
        db_client = InfluxDBClient(
            url=config.get('influxdb.url'),
            token=config.get('influxdb.token'),
            org="zerodha",  # Fixed organization name per requirements
            bucket="zerodha_data"  # Fixed bucket name per requirements
        )
        components["db_client"] = db_client
        print("Database client initialized")
        
        # Initialize custom logger with DB
        logger = CustomLogger(std_logger, db_client)
        
        # Initialize Telegram alerter
        alerter = TelegramAlerter(
            token=config.get('telegram.bot_token'),
            chat_id=config.get('telegram.chat_id')
        )
        components["alerter"] = alerter
        
        # Read watchlist
        watchlist_path = config.get('application.watchlist_path', 'data/input/watchlist.csv')
        watchlist = read_watchlist(watchlist_path)
        
        # Read sector map
        sector_map_path = config.get('application.sector_map_path', 'data/input/symbol_sector_map.csv')
        sector_map = read_sector_map(sector_map_path)
        
        # Initialize Zerodha API
        zerodha_api = ZerodhaAPI(
            api_key=config.get('zerodha.api_key'),
            api_secret=config.get('zerodha.api_secret'),
            user_id=config.get('zerodha.user_id'),
            password=config.get('zerodha.password'),
            totp_key=config.get('zerodha.totp_key'),
            logger=logger
        )
        components["zerodha_api"] = zerodha_api
        logger.info("Zerodha API initialized")
        
        # Initialize state manager
        state_manager = StateManager(db_client, logger)
        components["state_manager"] = state_manager
        
        # Initialize WebSocket client
        websocket_client = WebSocketClient(
            api_key=config.get('zerodha.api_key'),
            access_token=zerodha_api.access_token,
            state_manager=state_manager,
            logger=logger
        )
        components["websocket"] = websocket_client
        
        # Initialize scheduler
        init_scheduler(
            zerodha_api, 
            websocket_client, 
            db_client, 
            state_manager, 
            watchlist, 
            sector_map, 
            alerter, 
            logger
        )
        components["scheduler"] = True
        
        # Connect to WebSocket
        websocket_client.connect()
        
        # Send startup notification
        alerter.send_alert(f"✅ Zerodha Dashboard started at {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S')}", priority=1)
        
        # Keep the main thread running
        logger.info("Application started. Press Ctrl+C to exit.")
        
        while True:
            time.sleep(1)
            
    except Exception as e:
        print(f"Error in main application: {str(e)}")
        traceback.print_exc()
        cleanup()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 