#!/usr/bin/env python3
"""
Configuration Generator for Option Chain Display

This script generates a comprehensive config.json file based on the F&O database,
allowing users to easily select which instruments to monitor.
"""

import json
import pandas as pd
import os
import sys
from typing import Dict, List

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.utils.logger import logger


class FNOConfigGenerator:
    """Generates option chain configuration from F&O database."""
    
    def __init__(self, fno_csv_path: str = None):
        """Initialize with path to F&O database CSV."""
        if fno_csv_path is None:
            # Default to the generated F&O database in project root
            project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
            fno_csv_path = os.path.join(project_root, 'fno_summary_latest.csv')
        
        self.fno_csv_path = os.path.abspath(fno_csv_path)
        self.fno_data = None
        
        # Load F&O data
        self._load_fno_data()
    
    def _load_fno_data(self):
        """Load F&O database from CSV."""
        try:
            if not os.path.exists(self.fno_csv_path):
                logger.error(f"F&O database not found at: {self.fno_csv_path}")
                logger.info("Please run: python3 generate_fno_database.py")
                raise FileNotFoundError(f"F&O database not found: {self.fno_csv_path}")
            
            self.fno_data = pd.read_csv(self.fno_csv_path)
            logger.info(f"Loaded {len(self.fno_data)} F&O instruments from database")
            
            # Filter only instruments with options (call_options_count > 0)
            self.fno_data = self.fno_data[
                (self.fno_data['call_options_count'] > 0) & 
                (self.fno_data['put_options_count'] > 0)
            ]
            logger.info(f"Filtered to {len(self.fno_data)} instruments with options")
            
        except Exception as e:
            logger.error(f"Error loading F&O data: {e}")
            raise
    
    def generate_config_template(self) -> Dict:
        """Generate a comprehensive config template with all available instruments."""
        
        config = {
            "metadata": {
                "description": "Option Chain Configuration - Generated from F&O Database",
                "generated_at": pd.Timestamp.now().isoformat(),
                "total_instruments": len(self.fno_data),
                "fno_database_source": self.fno_csv_path
            },
            "display_settings": {
                "refresh_interval_seconds": 10,
                "window_width": 1400,
                "window_height": 700,
                "strikes_above_atm": 3,
                "strikes_below_atm": 3,
                "colors": {
                    "atm_background": "#E6F3FF",
                    "itm_text": "#CC0000",
                    "otm_text": "#008000",
                    "call_oi_bar": "#4CAF50",
                    "put_oi_bar": "#FF5722",
                    "header_background": "#2196F3",
                    "header_text": "#FFFFFF"
                }
            },
            "instruments": {}
        }
        
        # Add all instruments with their metadata
        for _, row in self.fno_data.iterrows():
            instrument_name = row['name']
            
            # Default most popular instruments to active
            popular_instruments = {
                'NIFTY', 'BANKNIFTY', 'FINNIFTY', 'RELIANCE', 'TCS', 
                'HDFCBANK', 'ICICIBANK', 'INFY', 'ITC', 'SBIN'
            }
            
            is_active = 1 if instrument_name in popular_instruments else 0
            
            config["instruments"][instrument_name] = {
                "active": is_active,
                "trading_symbol": row['tradingsymbol'],
                "exchange": row['exchange'],
                "segment": row['segment'],
                "lot_size": int(row['lot_size']),
                "strike_difference": float(row['strike_difference']),
                "tick_size": float(row['tick_size']),
                "call_options_count": int(row['call_options_count']),
                "put_options_count": int(row['put_options_count']),
                "expiry_dates": row['expiry_dates'],
                "last_updated": row['last_updated'],
                "display_name": instrument_name,
                "window_title": f"Live Option Chain - {instrument_name}"
            }
        
        return config
    
    def save_config(self, config: Dict, output_path: str = None):
        """Save configuration to JSON file."""
        if output_path is None:
            # Save in the same directory as this script
            output_path = os.path.join(os.path.dirname(__file__), 'config.json')
        
        try:
            with open(output_path, 'w') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise
    
    def get_active_instruments(self, config: Dict) -> List[str]:
        """Get list of active instruments from config."""
        active_instruments = []
        
        for instrument_name, details in config["instruments"].items():
            if details.get("active", 0) == 1:
                active_instruments.append(instrument_name)
        
        return active_instruments
    
    def generate_and_save(self, output_path: str = None) -> str:
        """Generate config and save to file."""
        config = self.generate_config_template()
        saved_path = self.save_config(config, output_path)
        
        # Log summary
        active_count = len(self.get_active_instruments(config))
        logger.info(f"Generated config with {len(config['instruments'])} total instruments")
        logger.info(f"Default active instruments: {active_count}")
        
        return saved_path


def main():
    """Main function to generate option chain configuration."""
    try:
        logger.info("Generating Option Chain Configuration from F&O Database")
        
        # Create config generator
        generator = FNOConfigGenerator()
        
        # Generate and save configuration
        config_path = generator.generate_and_save()
        
        # Load and show summary
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        active_instruments = generator.get_active_instruments(config)
        
        print("\n" + "="*80)
        print("✅ OPTION CHAIN CONFIGURATION GENERATED!")
        print("="*80)
        print(f"📁 Config file: {config_path}")
        print(f"📊 Total instruments: {len(config['instruments'])}")
        print(f"🎯 Active by default: {len(active_instruments)}")
        print("\n🔥 Default Active Instruments:")
        for instrument in sorted(active_instruments):
            strike_diff = config['instruments'][instrument]['strike_difference']
            lot_size = config['instruments'][instrument]['lot_size']
            print(f"   • {instrument:<12} | Strike Diff: {strike_diff:>6.0f} | Lot Size: {lot_size:>6}")
        
        print("\n" + "="*80)
        print("🎯 NEXT STEPS:")
        print("="*80)
        print("1. Edit config.json to set 'active': 1 for instruments you want to monitor")
        print("2. Run: python3 basic_option_chain.py")
        print("3. The system will open separate windows for each active instrument")
        print("\n💡 TIP: Start with just 1-2 active instruments to test performance!")
        
        return True
        
    except Exception as e:
        logger.error(f"Error generating configuration: {e}")
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
