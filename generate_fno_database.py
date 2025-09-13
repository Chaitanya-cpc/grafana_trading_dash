#!/usr/bin/env python3
"""
F&O Instruments Database Generator

This script generates a comprehensive CSV database of all F&O instruments
including their trading symbols, strike differences, lot sizes, and expiry dates.

Usage:
    python3 generate_fno_database.py

Output:
    - fno_instruments.csv: Complete F&O instruments database
    - fno_summary.csv: Summary by underlying asset

Run this script monthly after options expiry to keep the database updated.
"""

import sys
import os
import csv
import json
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Set
import pandas as pd

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.auth.kite_auth import KiteAuth
from src.utils.logger import logger


class FNODatabaseGenerator:
    """Generator for F&O instruments database."""
    
    def __init__(self, kite_instance):
        self.kite = kite_instance
        self.instruments_data = []
        self.summary_data = []
    
    def fetch_instruments(self) -> List[dict]:
        """Fetch all F&O instruments from Zerodha."""
        try:
            logger.info("Fetching F&O instruments from Zerodha...")
            
            # Get NFO instruments (National Stock Exchange F&O segment)
            nfo_instruments = self.kite.instruments("NFO")
            logger.info(f"Fetched {len(nfo_instruments)} NFO instruments")
            
            # Get MCX instruments (Multi Commodity Exchange)
            try:
                mcx_instruments = self.kite.instruments("MCX")
                logger.info(f"Fetched {len(mcx_instruments)} MCX instruments")
            except Exception as e:
                logger.warning(f"Could not fetch MCX instruments: {e}")
                mcx_instruments = []
            
            # Combine all instruments
            all_instruments = nfo_instruments + mcx_instruments
            logger.info(f"Total F&O instruments: {len(all_instruments)}")
            
            return all_instruments
            
        except Exception as e:
            logger.error(f"Error fetching instruments: {e}")
            return []
    
    def calculate_strike_difference(self, instruments: List[dict], name: str) -> float:
        """Calculate strike difference for a given underlying."""
        try:
            # Get all option strikes for this underlying
            option_strikes = []
            for inst in instruments:
                if (inst['name'] == name and 
                    inst['instrument_type'] in ['CE', 'PE'] and
                    inst['strike'] > 0):
                    option_strikes.append(inst['strike'])
            
            if len(option_strikes) < 2:
                return 0.0
            
            # Sort strikes and find the most common difference
            option_strikes = sorted(set(option_strikes))
            differences = []
            
            for i in range(1, len(option_strikes)):
                diff = option_strikes[i] - option_strikes[i-1]
                differences.append(diff)
            
            if not differences:
                return 0.0
            
            # Return the most common difference
            diff_counts = {}
            for diff in differences:
                diff_counts[diff] = diff_counts.get(diff, 0) + 1
            
            most_common_diff = max(diff_counts.items(), key=lambda x: x[1])[0]
            return most_common_diff
            
        except Exception as e:
            logger.warning(f"Error calculating strike difference for {name}: {e}")
            return 0.0
    
    def get_expiry_dates(self, instruments: List[dict], name: str) -> List[str]:
        """Get all expiry dates for a given underlying."""
        expiry_dates = set()
        
        for inst in instruments:
            if inst['name'] == name and inst['expiry']:
                # Convert datetime to string if needed
                expiry = inst['expiry']
                if hasattr(expiry, 'strftime'):
                    expiry_str = expiry.strftime('%Y-%m-%d')
                else:
                    expiry_str = str(expiry)
                expiry_dates.add(expiry_str)
        
        return sorted(list(expiry_dates))
    
    def process_instruments(self, instruments: List[dict]):
        """Process instruments and generate database."""
        logger.info("Processing instruments data...")
        
        # Group instruments by underlying name
        grouped = defaultdict(list)
        for inst in instruments:
            grouped[inst['name']].append(inst)
        
        # Process each underlying
        for name, inst_list in grouped.items():
            logger.info(f"Processing {name}...")
            
            # Get base instrument (futures or equity)
            base_inst = None
            lot_size = 0
            
            # Look for futures first, then equity
            for inst in inst_list:
                if inst['instrument_type'] == 'FUT':
                    base_inst = inst
                    lot_size = inst.get('lot_size', 0)
                    break
            
            if not base_inst:
                # Look for any instrument to get basic info
                base_inst = inst_list[0]
                lot_size = base_inst.get('lot_size', 0)
            
            # Calculate strike difference
            strike_diff = self.calculate_strike_difference(inst_list, name)
            
            # Get expiry dates
            expiry_dates = self.get_expiry_dates(inst_list, name)
            
            # Count instruments by type
            inst_types = defaultdict(int)
            for inst in inst_list:
                inst_types[inst['instrument_type']] += 1
            
            # Create summary record
            summary_record = {
                'name': name,
                'tradingsymbol': base_inst.get('tradingsymbol', name),
                'exchange': base_inst.get('exchange', ''),
                'segment': base_inst.get('segment', ''),
                'instrument_type': base_inst.get('instrument_type', ''),
                'lot_size': lot_size,
                'strike_difference': strike_diff,
                'tick_size': base_inst.get('tick_size', 0),
                'expiry_dates': ', '.join(expiry_dates[:3]),  # First 3 expiries
                'total_expiries': len(expiry_dates),
                'futures_count': inst_types.get('FUT', 0),
                'call_options_count': inst_types.get('CE', 0),
                'put_options_count': inst_types.get('PE', 0),
                'total_instruments': len(inst_list),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.summary_data.append(summary_record)
            
            # Add all individual instruments to detailed data
            for inst in inst_list:
                detailed_record = {
                    'instrument_token': inst.get('instrument_token', ''),
                    'exchange_token': inst.get('exchange_token', ''),
                    'tradingsymbol': inst.get('tradingsymbol', ''),
                    'name': inst.get('name', ''),
                    'exchange': inst.get('exchange', ''),
                    'segment': inst.get('segment', ''),
                    'instrument_type': inst.get('instrument_type', ''),
                    'strike': inst.get('strike', 0),
                    'lot_size': inst.get('lot_size', 0),
                    'tick_size': inst.get('tick_size', 0),
                    'expiry': inst.get('expiry', ''),
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                self.instruments_data.append(detailed_record)
        
        logger.info(f"Processed {len(grouped)} underlyings")
        logger.info(f"Generated {len(self.instruments_data)} detailed records")
        logger.info(f"Generated {len(self.summary_data)} summary records")
    
    def export_to_csv(self):
        """Export summary data to CSV and clean up unnecessary files."""
        try:
            # Export only summary data (the one we actually need)
            summary_filename = 'fno_summary_latest.csv'
            logger.info(f"Exporting F&O summary data to {summary_filename}...")
            
            if self.summary_data:
                df_summary = pd.DataFrame(self.summary_data)
                # Sort by name for easier reading
                df_summary = df_summary.sort_values('name')
                df_summary.to_csv(summary_filename, index=False)
                logger.info(f"✅ Exported {len(self.summary_data)} summary records")
            
            # Clean up any existing timestamped or detailed CSV files
            self._cleanup_old_csv_files()
            
            logger.info("✅ Export completed successfully!")
            
            return summary_filename
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return None
    
    def _cleanup_old_csv_files(self):
        """Remove old CSV files to keep only the summary file."""
        try:
            import glob
            
            # Patterns to match old CSV files
            patterns_to_delete = [
                'fno_instruments_*.csv',  # All detailed instrument files
                'fno_summary_[0-9]*.csv', # Timestamped summary files
            ]
            
            files_deleted = 0
            for pattern in patterns_to_delete:
                files = glob.glob(pattern)
                for file in files:
                    try:
                        os.remove(file)
                        files_deleted += 1
                        logger.info(f"🗑️ Deleted old file: {file}")
                    except Exception as e:
                        logger.warning(f"Could not delete {file}: {e}")
            
            if files_deleted > 0:
                logger.info(f"🧹 Cleaned up {files_deleted} old CSV files")
            else:
                logger.info("🧹 No old CSV files to clean up")
                
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")
    
    def print_statistics(self):
        """Print summary statistics."""
        if not self.summary_data:
            return
        
        print("\n" + "="*60)
        print("📊 F&O INSTRUMENTS DATABASE STATISTICS")
        print("="*60)
        
        # Count by exchange
        exchanges = {}
        total_instruments = 0
        
        for record in self.summary_data:
            exchange = record['exchange']
            exchanges[exchange] = exchanges.get(exchange, 0) + 1
            total_instruments += record['total_instruments']
        
        print(f"📈 Total Underlyings: {len(self.summary_data)}")
        print(f"📊 Total Instruments: {total_instruments}")
        print(f"🏢 Exchanges: {', '.join(exchanges.keys())}")
        
        for exchange, count in exchanges.items():
            print(f"   • {exchange}: {count} underlyings")
        
        # Top 10 by total instruments
        sorted_data = sorted(self.summary_data, 
                           key=lambda x: x['total_instruments'], 
                           reverse=True)
        
        print(f"\n🔥 Top 10 Most Active Underlyings:")
        for i, record in enumerate(sorted_data[:10], 1):
            print(f"   {i:2d}. {record['name']:<12} - {record['total_instruments']:3d} instruments "
                  f"(Strike diff: {record['strike_difference']})")
        
        print(f"\n⏰ Database generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)


def main():
    """Main function to generate F&O database."""
    try:
        print("🚀 F&O Instruments Database Generator")
        print("=" * 50)
        
        # Initialize authentication
        logger.info("Initializing Zerodha authentication...")
        auth = KiteAuth()
        
        # Try to authenticate
        success = auth.authenticate_ultimate()
        
        if not success:
            print("❌ Authentication failed. Please check your credentials.")
            return False
        
        kite = auth.get_kite_instance()
        print("✅ Authentication successful")
        
        # Generate database
        generator = FNODatabaseGenerator(kite)
        
        # Fetch instruments
        instruments = generator.fetch_instruments()
        if not instruments:
            print("❌ No instruments found")
            return False
        
        # Process instruments
        generator.process_instruments(instruments)
        
        # Export to CSV
        summary_file = generator.export_to_csv()
        
        if summary_file:
            print(f"\n✅ F&O Database generated successfully:")
            print(f"   📋 File: {summary_file}")
            print(f"   📊 Contains: Strike differences, lot sizes, expiry data")
            print(f"   🧹 Old files automatically cleaned up")
        
        # Print statistics
        generator.print_statistics()
        
        print(f"\n💡 Usage Tips:")
        print(f"   • Single file 'fno_summary_latest.csv' contains everything you need")
        print(f"   • Use strike_difference column for option chain configurations")
        print(f"   • Use lot_size column for position sizing calculations")
        print(f"   • Run this script monthly after options expiry")
        print(f"   • Import CSV into Excel/Google Sheets for analysis")
        
        return True
        
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
        return True
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"❌ Error: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
