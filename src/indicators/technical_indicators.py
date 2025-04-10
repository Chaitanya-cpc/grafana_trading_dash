#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Technical Indicators Module
Calculates various technical indicators for analysis
"""

import numpy as np
import pandas as pd
import talib  # Requires TA-Lib
import pandas_ta as ta  # Fallback if TA-Lib doesn't have an indicator

def calculate_sma(data, period=20):
    """Calculate Simple Moving Average"""
    try:
        if isinstance(data, list):
            # Convert to numpy array
            data = np.array(data)
        
        # Use TA-Lib for calculation
        sma = talib.SMA(data, timeperiod=period)
        
        return sma
    except Exception as e:
        print(f"Error calculating SMA: {str(e)}")
        return None

def calculate_ema(data, period=20):
    """Calculate Exponential Moving Average"""
    try:
        if isinstance(data, list):
            # Convert to numpy array
            data = np.array(data)
        
        # Use TA-Lib for calculation
        ema = talib.EMA(data, timeperiod=period)
        
        return ema
    except Exception as e:
        print(f"Error calculating EMA: {str(e)}")
        return None

def calculate_rsi(data, period=14):
    """Calculate Relative Strength Index"""
    try:
        if isinstance(data, list):
            # Convert to numpy array
            data = np.array(data)
        
        # Use TA-Lib for calculation
        rsi = talib.RSI(data, timeperiod=period)
        
        return rsi
    except Exception as e:
        print(f"Error calculating RSI: {str(e)}")
        return None

def calculate_macd(data, fastperiod=12, slowperiod=26, signalperiod=9):
    """Calculate MACD (Moving Average Convergence Divergence)"""
    try:
        if isinstance(data, list):
            # Convert to numpy array
            data = np.array(data)
        
        # Use TA-Lib for calculation
        macd, macd_signal, macd_hist = talib.MACD(
            data, fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod
        )
        
        return macd, macd_signal, macd_hist
    except Exception as e:
        print(f"Error calculating MACD: {str(e)}")
        return None, None, None

def calculate_bollinger_bands(data, period=20, deviations=2):
    """Calculate Bollinger Bands"""
    try:
        if isinstance(data, list):
            # Convert to numpy array
            data = np.array(data)
        
        # Use TA-Lib for calculation
        upper, middle, lower = talib.BBANDS(
            data, timeperiod=period, nbdevup=deviations, nbdevdn=deviations
        )
        
        return upper, middle, lower
    except Exception as e:
        print(f"Error calculating Bollinger Bands: {str(e)}")
        return None, None, None

def calculate_atr(high, low, close, period=14):
    """Calculate Average True Range"""
    try:
        if isinstance(high, list):
            # Convert to numpy array
            high = np.array(high)
            low = np.array(low)
            close = np.array(close)
        
        # Use TA-Lib for calculation
        atr = talib.ATR(high, low, close, timeperiod=period)
        
        return atr
    except Exception as e:
        print(f"Error calculating ATR: {str(e)}")
        return None

def calculate_stochastic(high, low, close, k_period=14, d_period=3, slowing=3):
    """Calculate Stochastic Oscillator"""
    try:
        if isinstance(high, list):
            # Convert to numpy array
            high = np.array(high)
            low = np.array(low)
            close = np.array(close)
        
        # Use TA-Lib for calculation
        slowk, slowd = talib.STOCH(
            high, low, close, 
            fastk_period=k_period, 
            slowk_period=slowing, 
            slowk_matype=0, 
            slowd_period=d_period, 
            slowd_matype=0
        )
        
        return slowk, slowd
    except Exception as e:
        print(f"Error calculating Stochastic Oscillator: {str(e)}")
        return None, None

def calculate_adx(high, low, close, period=14):
    """Calculate Average Directional Index"""
    try:
        if isinstance(high, list):
            # Convert to numpy array
            high = np.array(high)
            low = np.array(low)
            close = np.array(close)
        
        # Use TA-Lib for calculation
        adx = talib.ADX(high, low, close, timeperiod=period)
        
        return adx
    except Exception as e:
        print(f"Error calculating ADX: {str(e)}")
        return None

def calculate_volume_sma(volume, period=20):
    """Calculate Volume Simple Moving Average"""
    try:
        if isinstance(volume, list):
            # Convert to numpy array
            volume = np.array(volume)
        
        # Use TA-Lib for calculation
        volume_sma = talib.SMA(volume, timeperiod=period)
        
        return volume_sma
    except Exception as e:
        print(f"Error calculating Volume SMA: {str(e)}")
        return None

def calculate_all_indicators(ohlcv_df, config=None):
    """
    Calculate all configured indicators for OHLCV data
    
    Parameters:
    ohlcv_df (pandas.DataFrame): DataFrame with 'open', 'high', 'low', 'close', 'volume' columns
    config (dict): Configuration dictionary with indicator parameters
    
    Returns:
    pandas.DataFrame: DataFrame with indicators added as columns
    """
    try:
        # Make a copy of the input DataFrame
        df = ohlcv_df.copy()
        
        # Default configuration if none provided
        if config is None:
            config = {
                "sma": [20, 50, 200],
                "ema": [9, 21],
                "rsi": [14],
                "macd": {"fast": 12, "slow": 26, "signal": 9},
                "bollinger": {"period": 20, "deviations": 2},
                "atr": [14],
                "stochastic": {"k_period": 14, "d_period": 3, "slowing": 3},
                "adx": [14],
                "volume_sma": [20]
            }
        
        # Calculate configured indicators
        
        # SMA - Simple Moving Averages
        for period in config.get("sma", []):
            df[f'sma_{period}'] = calculate_sma(df['close'].values, period)
        
        # EMA - Exponential Moving Averages
        for period in config.get("ema", []):
            df[f'ema_{period}'] = calculate_ema(df['close'].values, period)
        
        # RSI - Relative Strength Index
        for period in config.get("rsi", []):
            df[f'rsi_{period}'] = calculate_rsi(df['close'].values, period)
        
        # MACD - Moving Average Convergence Divergence
        if "macd" in config:
            macd_config = config["macd"]
            fast = macd_config.get("fast", 12)
            slow = macd_config.get("slow", 26)
            signal = macd_config.get("signal", 9)
            
            macd, macd_signal, macd_hist = calculate_macd(
                df['close'].values, 
                fastperiod=fast, 
                slowperiod=slow, 
                signalperiod=signal
            )
            
            df['macd'] = macd
            df['macd_signal'] = macd_signal
            df['macd_hist'] = macd_hist
        
        # Bollinger Bands
        if "bollinger" in config:
            bb_config = config["bollinger"]
            period = bb_config.get("period", 20)
            deviations = bb_config.get("deviations", 2)
            
            upper, middle, lower = calculate_bollinger_bands(
                df['close'].values, 
                period=period, 
                deviations=deviations
            )
            
            df['bb_upper'] = upper
            df['bb_middle'] = middle
            df['bb_lower'] = lower
            
            # Calculate percentage bandwidth and %B
            df['bb_bandwidth'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle'] * 100
            df['bb_pct_b'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # ATR - Average True Range
        for period in config.get("atr", []):
            df[f'atr_{period}'] = calculate_atr(
                df['high'].values, 
                df['low'].values, 
                df['close'].values, 
                period
            )
        
        # Stochastic Oscillator
        if "stochastic" in config:
            stoch_config = config["stochastic"]
            k_period = stoch_config.get("k_period", 14)
            d_period = stoch_config.get("d_period", 3)
            slowing = stoch_config.get("slowing", 3)
            
            slowk, slowd = calculate_stochastic(
                df['high'].values, 
                df['low'].values, 
                df['close'].values, 
                k_period=k_period, 
                d_period=d_period, 
                slowing=slowing
            )
            
            df['stoch_k'] = slowk
            df['stoch_d'] = slowd
        
        # ADX - Average Directional Index
        for period in config.get("adx", []):
            df[f'adx_{period}'] = calculate_adx(
                df['high'].values, 
                df['low'].values, 
                df['close'].values, 
                period
            )
        
        # Volume SMA
        if 'volume' in df.columns:
            for period in config.get("volume_sma", []):
                df[f'volume_sma_{period}'] = calculate_volume_sma(df['volume'].values, period)
            
            # Volume relative to SMA
            if len(config.get("volume_sma", [])) > 0:
                period = config["volume_sma"][0]
                df['volume_ratio'] = df['volume'] / df[f'volume_sma_{period}']
        
        return df
        
    except Exception as e:
        print(f"Error calculating all indicators: {str(e)}")
        return ohlcv_df

def detect_signals(df):
    """
    Detect technical signals based on calculated indicators
    
    Parameters:
    df (pandas.DataFrame): DataFrame with calculated indicators
    
    Returns:
    dict: Dictionary of detected signals
    """
    try:
        signals = {}
        
        # RSI Overbought/Oversold
        if 'rsi_14' in df.columns:
            last_rsi = df['rsi_14'].iloc[-1]
            
            if last_rsi < 30:
                signals['rsi'] = {"signal": "oversold", "value": last_rsi}
            elif last_rsi > 70:
                signals['rsi'] = {"signal": "overbought", "value": last_rsi}
        
        # MACD Crossover
        if all(col in df.columns for col in ['macd', 'macd_signal']):
            macd_last = df['macd'].iloc[-1]
            macd_prev = df['macd'].iloc[-2] if len(df) > 1 else None
            signal_last = df['macd_signal'].iloc[-1]
            signal_prev = df['macd_signal'].iloc[-2] if len(df) > 1 else None
            
            if macd_prev is not None and signal_prev is not None:
                if macd_prev < signal_prev and macd_last > signal_last:
                    signals['macd'] = {"signal": "bullish_crossover", "value": macd_last}
                elif macd_prev > signal_prev and macd_last < signal_last:
                    signals['macd'] = {"signal": "bearish_crossover", "value": macd_last}
        
        # Bollinger Band Squeeze and Breakouts
        if all(col in df.columns for col in ['bb_upper', 'bb_lower', 'bb_bandwidth']):
            bandwidth = df['bb_bandwidth'].iloc[-1]
            bandwidth_prev = df['bb_bandwidth'].iloc[-5:].mean() if len(df) > 5 else None
            
            if bandwidth_prev is not None:
                if bandwidth < bandwidth_prev * 0.8:
                    signals['bollinger_squeeze'] = {"signal": "squeeze", "value": bandwidth}
            
            price = df['close'].iloc[-1]
            upper = df['bb_upper'].iloc[-1]
            lower = df['bb_lower'].iloc[-1]
            
            if price > upper:
                signals['bollinger_breakout'] = {"signal": "upper_breakout", "value": price}
            elif price < lower:
                signals['bollinger_breakout'] = {"signal": "lower_breakout", "value": price}
        
        # Moving Average Crossovers
        for fast_ma in ['sma_20', 'ema_9']:
            for slow_ma in ['sma_50', 'sma_200', 'ema_21']:
                if fast_ma in df.columns and slow_ma in df.columns:
                    fast_last = df[fast_ma].iloc[-1]
                    fast_prev = df[fast_ma].iloc[-2] if len(df) > 1 else None
                    slow_last = df[slow_ma].iloc[-1]
                    slow_prev = df[slow_ma].iloc[-2] if len(df) > 1 else None
                    
                    if fast_prev is not None and slow_prev is not None:
                        if fast_prev < slow_prev and fast_last > slow_last:
                            signals[f'{fast_ma}_{slow_ma}_crossover'] = {
                                "signal": "bullish_crossover", 
                                "value": fast_last
                            }
                        elif fast_prev > slow_prev and fast_last < slow_last:
                            signals[f'{fast_ma}_{slow_ma}_crossover'] = {
                                "signal": "bearish_crossover", 
                                "value": fast_last
                            }
        
        # Volume Spike
        if 'volume_ratio' in df.columns:
            volume_ratio = df['volume_ratio'].iloc[-1]
            
            if volume_ratio > 2.0:
                signals['volume_spike'] = {"signal": "high_volume", "value": volume_ratio}
            elif volume_ratio < 0.5:
                signals['volume_spike'] = {"signal": "low_volume", "value": volume_ratio}
        
        # Stochastic Crossover
        if all(col in df.columns for col in ['stoch_k', 'stoch_d']):
            k_last = df['stoch_k'].iloc[-1]
            k_prev = df['stoch_k'].iloc[-2] if len(df) > 1 else None
            d_last = df['stoch_d'].iloc[-1]
            d_prev = df['stoch_d'].iloc[-2] if len(df) > 1 else None
            
            if k_prev is not None and d_prev is not None:
                if k_prev < d_prev and k_last > d_last:
                    signals['stochastic'] = {"signal": "bullish_crossover", "value": k_last}
                elif k_prev > d_prev and k_last < d_last:
                    signals['stochastic'] = {"signal": "bearish_crossover", "value": k_last}
                
                # Overbought/Oversold
                if k_last < 20 and d_last < 20:
                    signals['stochastic_level'] = {"signal": "oversold", "value": k_last}
                elif k_last > 80 and d_last > 80:
                    signals['stochastic_level'] = {"signal": "overbought", "value": k_last}
        
        # ADX Trend Strength
        if 'adx_14' in df.columns:
            adx = df['adx_14'].iloc[-1]
            
            if adx > 25:
                signals['adx'] = {"signal": "strong_trend", "value": adx}
            elif adx < 20:
                signals['adx'] = {"signal": "weak_trend", "value": adx}
        
        return signals
        
    except Exception as e:
        print(f"Error detecting signals: {str(e)}")
        return {} 