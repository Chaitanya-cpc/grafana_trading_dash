#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
InfluxDB Client Module
Handles interactions with InfluxDB time-series database
"""

import os
import time
from datetime import datetime
import pytz
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
import traceback

class InfluxDBClient:
    """Client for interacting with InfluxDB"""
    
    def __init__(self, url, token, org, bucket):
        """Initialize the InfluxDB client"""
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        
        # Create InfluxDB client
        self.client = influxdb_client.InfluxDBClient(
            url=self.url,
            token=self.token,
            org=self.org
        )
        
        # Get write and query APIs
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()
        
        # Init Indian timezone
        self.india_tz = pytz.timezone('Asia/Kolkata')
    
    def write_point(self, data_point):
        """Write a data point to InfluxDB"""
        try:
            # Convert to InfluxDB Line Protocol
            point = influxdb_client.Point(data_point["measurement"])
            
            # Add tags
            for tag_key, tag_value in data_point.get("tags", {}).items():
                point = point.tag(tag_key, tag_value)
            
            # Add fields
            for field_key, field_value in data_point.get("fields", {}).items():
                if isinstance(field_value, bool):
                    point = point.field(field_key, field_value)
                elif isinstance(field_value, int):
                    point = point.field(field_key, field_value)
                elif isinstance(field_value, float):
                    point = point.field(field_key, field_value)
                else:
                    point = point.field(field_key, str(field_value))
            
            # Add timestamp if provided
            if "time" in data_point:
                point = point.time(data_point["time"])
            
            # Write to InfluxDB
            self.write_api.write(bucket=self.bucket, record=point)
            
            return True
            
        except Exception as e:
            print(f"Error writing to InfluxDB: {str(e)}")
            traceback.print_exc()
            return False
    
    def write_points(self, data_points):
        """Write multiple data points to InfluxDB"""
        try:
            points = []
            
            for data_point in data_points:
                # Convert to InfluxDB Line Protocol
                point = influxdb_client.Point(data_point["measurement"])
                
                # Add tags
                for tag_key, tag_value in data_point.get("tags", {}).items():
                    point = point.tag(tag_key, tag_value)
                
                # Add fields
                for field_key, field_value in data_point.get("fields", {}).items():
                    if isinstance(field_value, bool):
                        point = point.field(field_key, field_value)
                    elif isinstance(field_value, int):
                        point = point.field(field_key, field_value)
                    elif isinstance(field_value, float):
                        point = point.field(field_key, field_value)
                    else:
                        point = point.field(field_key, str(field_value))
                
                # Add timestamp if provided
                if "time" in data_point:
                    point = point.time(data_point["time"])
                
                points.append(point)
            
            # Write to InfluxDB
            self.write_api.write(bucket=self.bucket, record=points)
            
            return True
            
        except Exception as e:
            print(f"Error writing points to InfluxDB: {str(e)}")
            traceback.print_exc()
            return False
    
    def query(self, query):
        """Execute a Flux query against InfluxDB"""
        try:
            result = self.query_api.query(org=self.org, query=query)
            return result
        except Exception as e:
            print(f"Error querying InfluxDB: {str(e)}")
            traceback.print_exc()
            return None
    
    def get_latest_points(self, measurement, tag_key=None, tag_value=None, field_key=None, limit=1):
        """Get the latest data points for a measurement"""
        try:
            # Build the Flux query
            query = f'from(bucket: "{self.bucket}") |> range(start: -1h)'
            query += f' |> filter(fn: (r) => r._measurement == "{measurement}")'
            
            if tag_key and tag_value:
                query += f' |> filter(fn: (r) => r.{tag_key} == "{tag_value}")'
            
            if field_key:
                query += f' |> filter(fn: (r) => r._field == "{field_key}")'
            
            query += ' |> last()'
            
            # Execute the query
            result = self.query(query)
            
            # Process the result
            points = []
            for table in result:
                for record in table.records:
                    point = {
                        "measurement": record.get_measurement(),
                        "tags": {},
                        "fields": {
                            record.get_field(): record.get_value()
                        },
                        "time": record.get_time()
                    }
                    
                    # Add tags
                    for key, value in record.values.items():
                        if key.startswith("_"):
                            continue  # Skip internal fields
                        if key != record.get_field():
                            point["tags"][key] = value
                    
                    points.append(point)
            
            return points
            
        except Exception as e:
            print(f"Error getting latest points from InfluxDB: {str(e)}")
            traceback.print_exc()
            return []
    
    def get_time_series(self, measurement, field_key, tag_key=None, tag_value=None, 
                        start="-1d", stop="now()", window="1m"):
        """Get a time series for a field with optional aggregation"""
        try:
            # Build the Flux query
            query = f'from(bucket: "{self.bucket}") |> range(start: {start}, stop: {stop})'
            query += f' |> filter(fn: (r) => r._measurement == "{measurement}")'
            query += f' |> filter(fn: (r) => r._field == "{field_key}")'
            
            if tag_key and tag_value:
                query += f' |> filter(fn: (r) => r.{tag_key} == "{tag_value}")'
            
            # Optionally aggregate by window
            if window:
                query += f' |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)'
            
            query += ' |> yield(name: "result")'
            
            # Execute the query
            result = self.query(query)
            
            # Process the result
            timestamps = []
            values = []
            
            for table in result:
                for record in table.records:
                    timestamps.append(record.get_time())
                    values.append(record.get_value())
            
            return {
                "timestamps": timestamps,
                "values": values
            }
            
        except Exception as e:
            print(f"Error getting time series from InfluxDB: {str(e)}")
            traceback.print_exc()
            return {"timestamps": [], "values": []}
    
    def close(self):
        """Close the InfluxDB client connection"""
        try:
            if hasattr(self, 'write_api') and self.write_api:
                self.write_api.close()
            
            if hasattr(self, 'client') and self.client:
                self.client.close()
                
        except Exception as e:
            print(f"Error closing InfluxDB client: {str(e)}")
            traceback.print_exc() 