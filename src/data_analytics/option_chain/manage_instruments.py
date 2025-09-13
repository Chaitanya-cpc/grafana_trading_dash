#!/usr/bin/env python3
"""
Instrument Management Tool for Option Chain Display

This script helps you easily enable/disable instruments in the option chain configuration.
"""

import json
import sys
import os
from typing import List, Dict

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.utils.logger import logger


class InstrumentManager:
    """Manages instrument activation in option chain configuration."""
    
    def __init__(self, config_file: str = None):
        """Initialize with config file path."""
        if config_file is None:
            config_file = os.path.join(os.path.dirname(__file__), "config.json")
        
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load configuration from JSON file."""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_file}")
            raise
    
    def _save_config(self):
        """Save configuration to JSON file."""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        logger.info(f"Configuration saved to {self.config_file}")
    
    def list_instruments(self) -> Dict[str, dict]:
        """List all available instruments with their status."""
        instruments = self.config.get("instruments", {})
        return {name: details for name, details in instruments.items()}
    
    def get_active_instruments(self) -> List[str]:
        """Get list of currently active instruments."""
        instruments = self.config.get("instruments", {})
        return [name for name, details in instruments.items() if details.get("active", 0) == 1]
    
    def activate_instrument(self, instrument_name: str) -> bool:
        """Activate an instrument."""
        instruments = self.config.get("instruments", {})
        if instrument_name not in instruments:
            print(f"❌ Instrument '{instrument_name}' not found!")
            return False
        
        instruments[instrument_name]["active"] = 1
        self._save_config()
        print(f"✅ Activated: {instrument_name}")
        return True
    
    def deactivate_instrument(self, instrument_name: str) -> bool:
        """Deactivate an instrument."""
        instruments = self.config.get("instruments", {})
        if instrument_name not in instruments:
            print(f"❌ Instrument '{instrument_name}' not found!")
            return False
        
        instruments[instrument_name]["active"] = 0
        self._save_config()
        print(f"🔴 Deactivated: {instrument_name}")
        return True
    
    def activate_multiple(self, instrument_names: List[str]) -> int:
        """Activate multiple instruments."""
        count = 0
        for name in instrument_names:
            if self.activate_instrument(name):
                count += 1
        return count
    
    def deactivate_all(self) -> int:
        """Deactivate all instruments."""
        instruments = self.config.get("instruments", {})
        count = 0
        for name in instruments:
            instruments[name]["active"] = 0
            count += 1
        self._save_config()
        print(f"🔴 Deactivated all {count} instruments")
        return count
    
    def show_status(self):
        """Display current status of all instruments."""
        instruments = self.list_instruments()
        active_instruments = self.get_active_instruments()
        
        print("\n" + "="*80)
        print("📊 OPTION CHAIN INSTRUMENT STATUS")
        print("="*80)
        print(f"📈 Total instruments: {len(instruments)}")
        print(f"✅ Active instruments: {len(active_instruments)}")
        print(f"🔴 Inactive instruments: {len(instruments) - len(active_instruments)}")
        
        if active_instruments:
            print("\n🔥 ACTIVE INSTRUMENTS:")
            for name in sorted(active_instruments):
                details = instruments[name]
                strike_diff = details.get("strike_difference", 0)
                lot_size = details.get("lot_size", 0)
                print(f"   ✅ {name:<12} | Strike Diff: {strike_diff:>6.0f} | Lot Size: {lot_size:>6}")
        
        # Show popular inactive instruments
        popular = ['BANKNIFTY', 'FINNIFTY', 'RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 'INFY', 'ITC', 'SBIN']
        inactive_popular = [name for name in popular if name in instruments and name not in active_instruments]
        
        if inactive_popular:
            print("\n💡 POPULAR INACTIVE INSTRUMENTS (consider activating):")
            for name in inactive_popular:
                details = instruments[name]
                strike_diff = details.get("strike_difference", 0)
                lot_size = details.get("lot_size", 0)
                print(f"   🔴 {name:<12} | Strike Diff: {strike_diff:>6.0f} | Lot Size: {lot_size:>6}")
        
        print("\n" + "="*80)


def main():
    """Main interactive interface."""
    try:
        manager = InstrumentManager()
        
        if len(sys.argv) == 1:
            # Interactive mode
            while True:
                manager.show_status()
                print("\n🎯 INSTRUMENT MANAGEMENT OPTIONS:")
                print("1. Activate instrument(s)")
                print("2. Deactivate instrument(s)")  
                print("3. Deactivate all")
                print("4. Show status")
                print("5. Quick activate popular set")
                print("6. Exit")
                
                choice = input("\nEnter your choice (1-6): ").strip()
                
                if choice == "1":
                    instruments = input("Enter instrument name(s) (comma-separated): ").strip().upper()
                    names = [name.strip() for name in instruments.split(",") if name.strip()]
                    if names:
                        manager.activate_multiple(names)
                
                elif choice == "2":
                    instruments = input("Enter instrument name(s) (comma-separated): ").strip().upper()
                    names = [name.strip() for name in instruments.split(",") if name.strip()]
                    for name in names:
                        manager.deactivate_instrument(name)
                
                elif choice == "3":
                    confirm = input("Deactivate ALL instruments? (y/N): ").strip().lower()
                    if confirm == 'y':
                        manager.deactivate_all()
                
                elif choice == "4":
                    continue  # Will show status at top of loop
                
                elif choice == "5":
                    popular = ['NIFTY', 'BANKNIFTY', 'FINNIFTY']
                    print("Activating popular set: NIFTY, BANKNIFTY, FINNIFTY")
                    manager.deactivate_all()
                    manager.activate_multiple(popular)
                
                elif choice == "6":
                    print("👋 Goodbye!")
                    break
                
                else:
                    print("❌ Invalid choice. Please try again.")
                
                input("\nPress Enter to continue...")
        
        else:
            # Command line mode
            command = sys.argv[1].lower()
            
            if command == "status":
                manager.show_status()
            
            elif command == "activate":
                if len(sys.argv) < 3:
                    print("Usage: python3 manage_instruments.py activate INSTRUMENT1 [INSTRUMENT2 ...]")
                    return False
                instruments = [name.upper() for name in sys.argv[2:]]
                manager.activate_multiple(instruments)
            
            elif command == "deactivate":
                if len(sys.argv) < 3:
                    print("Usage: python3 manage_instruments.py deactivate INSTRUMENT1 [INSTRUMENT2 ...]")
                    return False
                instruments = [name.upper() for name in sys.argv[2:]]
                for name in instruments:
                    manager.deactivate_instrument(name)
            
            elif command == "clear":
                manager.deactivate_all()
            
            else:
                print("❌ Unknown command. Available commands:")
                print("  status - Show current status")
                print("  activate INSTRUMENT1 [INSTRUMENT2 ...] - Activate instruments")
                print("  deactivate INSTRUMENT1 [INSTRUMENT2 ...] - Deactivate instruments")
                print("  clear - Deactivate all instruments")
                print("  (no arguments) - Interactive mode")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error in instrument manager: {e}")
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
