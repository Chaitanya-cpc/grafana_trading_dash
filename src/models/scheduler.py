#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scheduler Module
Handles all periodic tasks and scheduling
"""

import os
import time
import threading
from datetime import datetime, time as dt_time
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import traceback

# Global scheduler instance
scheduler = None

# Global references to components
zerodha_api = None
websocket_client = None
db_client = None
state_manager = None
watchlist = None
sector_map = None
alerter = None
logger = None

def initialize(zerodha_api_inst, websocket_client_inst, db_client_inst, state_manager_inst, 
               watchlist_inst, sector_map_inst, alerter_inst, logger_inst):
    """Initialize the scheduler with references to all components"""
    global zerodha_api, websocket_client, db_client, state_manager, watchlist, sector_map, alerter, logger, scheduler
    
    # Store references
    zerodha_api = zerodha_api_inst
    websocket_client = websocket_client_inst
    db_client = db_client_inst
    state_manager = state_manager_inst
    watchlist = watchlist_inst
    sector_map = sector_map_inst
    alerter = alerter_inst
    logger = logger_inst
    
    # Create and start the scheduler
    scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Kolkata'))
    scheduler.start()
    
    # Schedule the jobs
    _schedule_jobs()
    
    logger.info("Scheduler initialized and started")

def _schedule_jobs():
    """Schedule all periodic jobs"""
    # Get polling intervals from env vars
    positions_interval = int(os.getenv("POSITIONS_POLL_INTERVAL", "15"))
    margins_interval = int(os.getenv("MARGINS_POLL_INTERVAL", "60"))
    orders_interval = int(os.getenv("ORDERS_POLL_INTERVAL", "30"))
    trades_interval = int(os.getenv("TRADES_POLL_INTERVAL", "30"))
    holdings_interval = int(os.getenv("HOLDINGS_POLL_INTERVAL", "300"))
    ohlc_interval = int(os.getenv("OHLC_POLL_INTERVAL", "300"))
    
    # Schedule the jobs
    scheduler.add_job(
        fetch_positions,
        IntervalTrigger(seconds=positions_interval),
        id='fetch_positions',
        replace_existing=True
    )
    
    scheduler.add_job(
        fetch_margins,
        IntervalTrigger(seconds=margins_interval),
        id='fetch_margins',
        replace_existing=True
    )
    
    scheduler.add_job(
        fetch_orders,
        IntervalTrigger(seconds=orders_interval),
        id='fetch_orders',
        replace_existing=True
    )
    
    scheduler.add_job(
        fetch_trades,
        IntervalTrigger(seconds=trades_interval),
        id='fetch_trades',
        replace_existing=True
    )
    
    scheduler.add_job(
        fetch_holdings,
        IntervalTrigger(seconds=holdings_interval),
        id='fetch_holdings',
        replace_existing=True
    )
    
    scheduler.add_job(
        fetch_ohlc,
        IntervalTrigger(seconds=ohlc_interval),
        id='fetch_ohlc',
        replace_existing=True
    )
    
    scheduler.add_job(
        update_watchlist_subscriptions,
        IntervalTrigger(seconds=60),  # Check every minute
        id='update_watchlist_subscriptions',
        replace_existing=True
    )
    
    scheduler.add_job(
        check_websocket_health,
        IntervalTrigger(seconds=30),  # Check every 30 seconds
        id='check_websocket_health',
        replace_existing=True
    )
    
    scheduler.add_job(
        log_system_metrics,
        IntervalTrigger(seconds=60),  # Log every minute
        id='log_system_metrics',
        replace_existing=True
    )
    
    scheduler.add_job(
        update_sector_exposure,
        IntervalTrigger(seconds=300),  # Update every 5 minutes
        id='update_sector_exposure',
        replace_existing=True
    )
    
    # Immediately execute initial data fetch
    fetch_positions()
    fetch_margins()
    fetch_orders()
    fetch_trades()
    fetch_holdings()
    fetch_ohlc()
    update_watchlist_subscriptions()
    
    logger.info("All jobs scheduled")

def fetch_positions():
    """Fetch positions from Zerodha API"""
    try:
        logger.debug("Fetching positions")
        positions = zerodha_api.get_positions()
        
        if positions:
            state_manager.update_positions(positions)
            logger.debug(f"Positions updated: {len(positions.get('net', []))} net positions")
            
            # Subscribe to WebSocket for all position instruments
            tokens = [pos["instrument_token"] for pos in positions.get("net", []) if pos.get("instrument_token")]
            if tokens:
                websocket_client.subscribe(tokens)
                
    except Exception as e:
        logger.error(f"Error fetching positions: {str(e)}")
        traceback.print_exc()

def fetch_margins():
    """Fetch margins from Zerodha API"""
    try:
        logger.debug("Fetching margins")
        margins = zerodha_api.get_margins()
        
        if margins:
            state_manager.update_margins(margins)
            logger.debug("Margins updated")
            
    except Exception as e:
        logger.error(f"Error fetching margins: {str(e)}")
        traceback.print_exc()

def fetch_orders():
    """Fetch orders from Zerodha API"""
    try:
        logger.debug("Fetching orders")
        orders = zerodha_api.get_orders()
        
        if orders:
            state_manager.update_orders(orders)
            logger.debug(f"Orders updated: {len(orders)} orders")
            
    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
        traceback.print_exc()

def fetch_trades():
    """Fetch trades from Zerodha API"""
    try:
        logger.debug("Fetching trades")
        trades = zerodha_api.get_trades()
        
        if trades:
            state_manager.update_trades(trades)
            logger.debug(f"Trades updated: {len(trades)} trades")
            
    except Exception as e:
        logger.error(f"Error fetching trades: {str(e)}")
        traceback.print_exc()

def fetch_holdings():
    """Fetch holdings from Zerodha API"""
    try:
        logger.debug("Fetching holdings")
        holdings = zerodha_api.get_holdings()
        
        if holdings:
            # We might not use holdings directly in the state manager,
            # but we'll store them in InfluxDB for reference
            # TODO: Implement holdings storage in InfluxDB
            logger.debug(f"Holdings updated: {len(holdings)} holdings")
            
    except Exception as e:
        logger.error(f"Error fetching holdings: {str(e)}")
        traceback.print_exc()

def fetch_ohlc():
    """Fetch OHLC data for watchlist"""
    try:
        logger.debug("Fetching OHLC data for watchlist")
        
        if not watchlist:
            logger.warning("Watchlist is empty, skipping OHLC fetch")
            return
        
        # Split the watchlist into chunks to avoid API limits
        chunk_size = 10
        chunks = [watchlist[i:i + chunk_size] for i in range(0, len(watchlist), chunk_size)]
        
        for chunk in chunks:
            ohlc_data = zerodha_api.get_ohlc(chunk)
            
            if ohlc_data:
                # TODO: Process and store OHLC data
                logger.debug(f"OHLC data fetched for {len(chunk)} symbols")
                
            # Slight delay between chunks to be kind to the API
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"Error fetching OHLC data: {str(e)}")
        traceback.print_exc()

def update_watchlist_subscriptions():
    """Update WebSocket subscriptions based on watchlist"""
    try:
        logger.debug("Updating watchlist subscriptions")
        
        if not watchlist:
            logger.warning("Watchlist is empty, skipping subscription update")
            return
        
        # Get instrument tokens for watchlist symbols
        # In a real implementation, we'd need to map symbols to tokens
        # This would require fetching and caching the instrument list
        # For now, we'll assume the watchlist already contains tokens
        
        # TODO: Implement proper symbol to token mapping
        
        # For testing, we'll just use a placeholder
        # In a real implementation, you'd need to use zerodha_api.get_instruments()
        # and match the trading symbols to get tokens
        tokens = []
        
        # Subscribe to WebSocket for all watchlist instruments
        if tokens:
            websocket_client.subscribe(tokens)
            logger.debug(f"Subscribed to {len(tokens)} watchlist instruments")
            
    except Exception as e:
        logger.error(f"Error updating watchlist subscriptions: {str(e)}")
        traceback.print_exc()

def check_websocket_health():
    """Check the health of the WebSocket connection"""
    try:
        logger.debug("Checking WebSocket health")
        
        if not websocket_client:
            logger.warning("WebSocket client not initialized")
            return
        
        # Check if we have a recent heartbeat
        if not websocket_client.last_heartbeat:
            logger.warning("No heartbeat received yet")
            return
        
        # Check if heartbeat is recent (within 1 minute)
        now = datetime.now(pytz.timezone('Asia/Kolkata'))
        heartbeat_age = (now - websocket_client.last_heartbeat).total_seconds()
        
        if heartbeat_age > 60:
            logger.warning(f"WebSocket heartbeat is stale ({heartbeat_age:.1f} seconds old)")
            
            # If it's been too long, attempt reconnection
            if heartbeat_age > 120:
                logger.warning("Attempting WebSocket reconnection due to stale heartbeat")
                websocket_client.disconnect()
                time.sleep(1)
                websocket_client.connect()
            
        else:
            logger.debug(f"WebSocket heartbeat is recent ({heartbeat_age:.1f} seconds old)")
            
    except Exception as e:
        logger.error(f"Error checking WebSocket health: {str(e)}")
        traceback.print_exc()

def log_system_metrics():
    """Log system performance metrics (CPU, memory, etc.)"""
    try:
        # Import here to avoid loading if not needed
        import psutil
        
        # Get CPU and memory usage
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent
        
        # Create data point
        data_point = {
            "measurement": "system_metrics",
            "tags": {
                "host": "backend"
            },
            "fields": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_percent": disk_percent
            },
            "time": datetime.now(pytz.timezone('Asia/Kolkata')).isoformat()
        }
        
        # Write to InfluxDB
        db_client.write_point(data_point)
        
        logger.debug(f"System metrics logged: CPU {cpu_percent}%, Mem {memory_percent}%, Disk {disk_percent}%")
            
    except Exception as e:
        logger.error(f"Error logging system metrics: {str(e)}")
        traceback.print_exc()

def update_sector_exposure():
    """Update sector exposure based on positions and sector mapping"""
    try:
        logger.debug("Updating sector exposure")
        
        if not sector_map:
            logger.warning("Sector map is empty, skipping sector exposure update")
            return
        
        # Update sector exposure based on current positions
        state_manager.update_sector_exposure(sector_map)
        logger.debug("Sector exposure updated")
            
    except Exception as e:
        logger.error(f"Error updating sector exposure: {str(e)}")
        traceback.print_exc()

def shutdown():
    """Shutdown the scheduler"""
    global scheduler
    
    if scheduler and scheduler.running:
        logger.info("Shutting down scheduler")
        scheduler.shutdown()
        logger.info("Scheduler shutdown complete")
        
    # Clear global references
    zerodha_api = None
    websocket_client = None
    db_client = None
    state_manager = None
    watchlist = None
    sector_map = None
    alerter = None
    logger = None 