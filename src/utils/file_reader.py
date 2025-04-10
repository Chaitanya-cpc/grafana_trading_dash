#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File Reader Utility Module
Handles reading files like watchlist and sector map
"""

import os
import csv
import pandas as pd

def read_watchlist(file_path):
    """Read watchlist from CSV file"""
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"Watchlist file not found: {file_path}")
            return []
        
        # Read the file
        watchlist = []
        
        # Check file extension
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.csv':
            # Read CSV file using pandas
            df = pd.read_csv(file_path)
            
            # Check if 'symbol' column exists
            if 'symbol' in df.columns:
                watchlist = df['symbol'].tolist()
            else:
                # If no 'symbol' column, try to use the first column
                watchlist = df.iloc[:, 0].tolist()
                
        elif ext in ['.txt', '']:
            # Read plain text file (one symbol per line)
            with open(file_path, 'r') as f:
                for line in f:
                    symbol = line.strip()
                    if symbol and not symbol.startswith('#'):  # Skip empty lines and comments
                        watchlist.append(symbol)
        else:
            print(f"Unsupported watchlist file format: {ext}")
            return []
        
        # Remove any empty or None values
        watchlist = [s for s in watchlist if s]
        
        print(f"Loaded {len(watchlist)} symbols from watchlist")
        return watchlist
        
    except Exception as e:
        print(f"Error reading watchlist file: {str(e)}")
        return []

def read_sector_map(file_path):
    """Read sector map from CSV file"""
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"Sector map file not found: {file_path}")
            return {}
        
        # Read the file
        sector_map = {}
        
        # Read CSV file using pandas
        df = pd.read_csv(file_path)
        
        # Check if required columns exist
        if 'symbol' in df.columns and 'sector' in df.columns:
            # Create dictionary from dataframe
            sector_map = dict(zip(df['symbol'], df['sector']))
        else:
            print(f"Required columns (symbol, sector) not found in sector map file")
            return {}
        
        print(f"Loaded {len(sector_map)} symbols with sector mapping")
        return sector_map
        
    except Exception as e:
        print(f"Error reading sector map file: {str(e)}")
        return {}

def read_indicator_config(file_path):
    """Read technical indicator configuration from file"""
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"Indicator config file not found: {file_path}")
            return {}
        
        # Read the file
        config = {}
        
        # Check file extension
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.csv':
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # Convert DataFrame to dict
            # Assuming format: indicator, parameter, value
            for _, row in df.iterrows():
                if 'indicator' in row and 'parameter' in row and 'value' in row:
                    indicator = row['indicator']
                    parameter = row['parameter']
                    value = row['value']
                    
                    if indicator not in config:
                        config[indicator] = {}
                    
                    config[indicator][parameter] = value
                    
        elif ext == '.json':
            # Read JSON file
            import json
            with open(file_path, 'r') as f:
                config = json.load(f)
                
        elif ext in ['.yaml', '.yml']:
            # Read YAML file
            import yaml
            with open(file_path, 'r') as f:
                config = yaml.safe_load(f)
                
        else:
            print(f"Unsupported indicator config file format: {ext}")
            return {}
        
        print(f"Loaded indicator configuration with {len(config)} indicators")
        return config
        
    except Exception as e:
        print(f"Error reading indicator config file: {str(e)}")
        return {} 