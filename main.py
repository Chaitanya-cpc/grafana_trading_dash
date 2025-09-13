#!/usr/bin/env python3
"""
Zerodha Kite Connect - Full Automation Suite
Main entry point for the application.

This script provides ZERO-INTERVENTION authentication and trading integration.

Usage:
    python3 main.py

For more options, see main_ultimate.py directly.
"""

import sys
import os

# Simple redirect to the main ultimate script
if __name__ == "__main__":
    print("🚀 Zerodha Full Automation Suite")
    print("=" * 50)
    print("Redirecting to ultimate automation script...")
    print("For full control, use: python3 main_ultimate.py")
    print()
    
    # Import and run the ultimate main
    try:
        from main_ultimate import main
        success = main()
        sys.exit(0 if success else 1)
    except ImportError:
        print("❌ Error: main_ultimate.py not found")
        print("Please ensure all files are in the correct location.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
