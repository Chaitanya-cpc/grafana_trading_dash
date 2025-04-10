#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration Utility Module
Handles loading and managing application configuration
"""

import os
import yaml
import json
from dotenv import load_dotenv

class Config:
    """Configuration manager"""
    
    def __init__(self, config_file=None):
        """Initialize configuration manager"""
        # Load .env file if not already loaded
        load_dotenv()
        
        # Initialize config dict
        self.config = {
            "zerodha": {
                "api_key": os.getenv("ZERODHA_API_KEY"),
                "api_secret": os.getenv("ZERODHA_API_SECRET"),
                "user_id": os.getenv("ZERODHA_USER_ID"),
                "password": os.getenv("ZERODHA_PASSWORD"),
                "totp_key": os.getenv("ZERODHA_TOTP_KEY")
            },
            "influxdb": {
                "url": os.getenv("INFLUXDB_URL"),
                "token": os.getenv("INFLUXDB_TOKEN"),
                "org": os.getenv("INFLUXDB_ORG"),
                "bucket": os.getenv("INFLUXDB_BUCKET")
            },
            "telegram": {
                "bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
                "chat_id": os.getenv("TELEGRAM_CHAT_ID")
            },
            "application": {
                "log_level": os.getenv("LOG_LEVEL", "INFO"),
                "watchlist_path": os.getenv("WATCHLIST_PATH"),
                "sector_map_path": os.getenv("SECTOR_MAP_PATH"),
                "benchmark_symbol": os.getenv("BENCHMARK_SYMBOL")
            },
            "polling_intervals": {
                "positions": int(os.getenv("POSITIONS_POLL_INTERVAL", "15")),
                "margins": int(os.getenv("MARGINS_POLL_INTERVAL", "60")),
                "orders": int(os.getenv("ORDERS_POLL_INTERVAL", "30")),
                "trades": int(os.getenv("TRADES_POLL_INTERVAL", "30")),
                "holdings": int(os.getenv("HOLDINGS_POLL_INTERVAL", "300")),
                "ohlc": int(os.getenv("OHLC_POLL_INTERVAL", "300"))
            },
            "risk_thresholds": {
                "margin_alert": float(os.getenv("MARGIN_ALERT_THRESHOLD", "80")),
                "drawdown_alert": float(os.getenv("DRAWDOWN_ALERT_THRESHOLD", "5"))
            },
            "indicators": {
                "timeframe": os.getenv("INDICATOR_TIMEFRAME", "5minute"),
                "rsi_period": int(os.getenv("RSI_PERIOD", "14")),
                "sma_periods": [int(p) for p in os.getenv("SMA_PERIODS", "20,50").split(",")]
            },
            "timezone": os.getenv("TIMEZONE", "Asia/Kolkata")
        }
        
        # Load YAML config file if provided
        if config_file and os.path.exists(config_file):
            self._load_yaml_config(config_file)
    
    def _load_yaml_config(self, config_file):
        """Load configuration from YAML file"""
        try:
            with open(config_file, 'r') as f:
                yaml_config = yaml.safe_load(f)
            
            # Merge YAML config with env var config
            # YAML overrides env vars
            self._deep_merge(self.config, yaml_config)
                
        except Exception as e:
            print(f"Error loading YAML config: {str(e)}")
    
    def _deep_merge(self, target, source):
        """Deep merge two dictionaries"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
    
    def get(self, key, default=None):
        """Get a configuration value by key"""
        # Handle nested keys with dot notation
        if '.' in key:
            keys = key.split('.')
            value = self.config
            for k in keys:
                if k in value:
                    value = value[k]
                else:
                    return default
            return value
        
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set a configuration value by key"""
        # Handle nested keys with dot notation
        if '.' in key:
            keys = key.split('.')
            config = self.config
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            config[keys[-1]] = value
        else:
            self.config[key] = value
    
    def to_dict(self):
        """Get the full configuration as a dictionary"""
        return self.config
    
    def to_json(self):
        """Get the full configuration as a JSON string"""
        return json.dumps(self.config, indent=2)
    
    def save_to_file(self, file_path):
        """Save the configuration to a file"""
        try:
            # Determine file format from extension
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == '.json':
                # Save as JSON
                with open(file_path, 'w') as f:
                    json.dump(self.config, f, indent=2)
            elif ext in ['.yaml', '.yml']:
                # Save as YAML
                with open(file_path, 'w') as f:
                    yaml.dump(self.config, f, default_flow_style=False)
            else:
                # Default to JSON
                with open(file_path, 'w') as f:
                    json.dump(self.config, f, indent=2)
                    
            return True
            
        except Exception as e:
            print(f"Error saving configuration to file: {str(e)}")
            return False 