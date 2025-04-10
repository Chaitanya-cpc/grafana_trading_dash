#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram Alerter Module
Sends alerts and notifications via Telegram
"""

import os
import requests
import json
import time
import traceback
from datetime import datetime
import pytz
import threading

class TelegramAlerter:
    """Client for sending alerts and notifications via Telegram"""
    
    def __init__(self, token=None, chat_id=None):
        """Initialize the Telegram alerter"""
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.enabled = bool(self.token and self.chat_id)
        
        # For rate limiting
        self.last_message_time = 0
        self.min_interval = 1  # seconds between messages
        
        # For prioritizing critical alerts
        self.alert_queue = []
        self.lock = threading.Lock()
        
        # Init Indian timezone
        self.india_tz = pytz.timezone('Asia/Kolkata')
        
        # Check if Telegram alerting is enabled
        if not self.enabled:
            print("Telegram alerting disabled (missing token or chat ID)")
        else:
            print("Telegram alerter initialized")
    
    def send_alert(self, message, priority=0):
        """Send an alert message to Telegram chat"""
        if not self.enabled:
            return False
        
        # Add timestamp to message
        timestamp = datetime.now(self.india_tz).strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}"
        
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_message_time
        
        if time_since_last < self.min_interval:
            # We need to wait - add to queue
            with self.lock:
                self.alert_queue.append((full_message, priority))
                
            # If this is a high priority message, process the queue immediately
            if priority > 0:
                self._process_queue()
                
            return True
        
        # Send the message
        success = self._send_message(full_message)
        
        if success:
            self.last_message_time = time.time()
            
            # Process any queued messages
            self._process_queue()
            
        return success
    
    def _send_message(self, message):
        """Send a message to Telegram chat"""
        try:
            # Prepare API call
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML"  # Allow HTML formatting
            }
            
            # Make API call
            response = requests.post(url, json=data, timeout=10)
            
            # Check response
            if response.status_code == 200:
                return True
            else:
                print(f"Error sending Telegram message: {response.status_code} {response.text}")
                return False
                
        except Exception as e:
            print(f"Error sending Telegram message: {str(e)}")
            traceback.print_exc()
            return False
    
    def _process_queue(self):
        """Process queued messages"""
        with self.lock:
            # Only continue if we have queued messages
            if not self.alert_queue:
                return
            
            # Sort by priority (higher first)
            self.alert_queue.sort(key=lambda x: x[1], reverse=True)
            
            # Get the next message
            message, _ = self.alert_queue.pop(0)
        
        # Calculate wait time for rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_message_time
        
        if time_since_last < self.min_interval:
            # Wait the remaining time
            time.sleep(self.min_interval - time_since_last)
        
        # Send the message
        success = self._send_message(message)
        
        if success:
            self.last_message_time = time.time()
            
            # Schedule next queue processing
            if self.alert_queue:
                # Delay for rate limiting
                delay = self.min_interval
                threading.Timer(delay, self._process_queue).start()
    
    def send_chart(self, title, chart_data, caption=None):
        """
        Send a simple chart as a message
        
        chart_data should be a list of (x, y) values
        
        This is a simple text-based chart, for more complex charts,
        you would need to generate an image and send it.
        """
        if not self.enabled or not chart_data:
            return False
        
        # Generate a simple text chart
        chart = f"<b>{title}</b>\n\n"
        
        # Add caption if provided
        if caption:
            chart += f"{caption}\n\n"
        
        # Determine y-axis scale
        y_values = [y for _, y in chart_data]
        max_y = max(y_values)
        min_y = min(y_values)
        
        # Simple scale with 5 rows
        scale = (max_y - min_y) / 5 if max_y > min_y else 1
        
        # Generate chart rows
        for i in range(5, 0, -1):
            threshold = min_y + i * scale
            row = ""
            for _, y in chart_data:
                if y >= threshold:
                    row += "█"
                else:
                    row += " "
            chart += f"{row}\n"
        
        # Add a simple axis
        chart += "▁" * len(chart_data) + "\n"
        
        # Send the chart
        return self.send_alert(chart)
    
    def send_system_status(self, status_dict):
        """Send system status message"""
        if not self.enabled:
            return False
        
        # Create status message
        message = "<b>System Status</b>\n\n"
        
        for name, data in status_dict.items():
            # Get status value and emoji
            status = data.get("status", "unknown")
            
            if status == "ok":
                emoji = "✅"
            elif status == "warning":
                emoji = "⚠️"
            elif status == "error":
                emoji = "❌"
            else:
                emoji = "ℹ️"
            
            # Add to message
            message += f"{emoji} <b>{name}</b>: {status}"
            
            # Add details if present
            if "details" in data:
                message += f" ({data['details']})"
            
            message += "\n"
        
        # Send the message
        return self.send_alert(message) 