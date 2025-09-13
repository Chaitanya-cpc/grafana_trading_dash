#!/usr/bin/env python3
"""
Main application entry point for Zerodha Kite Connect integration.

This script demonstrates the complete authentication flow and basic usage
of the various modules in the package.
"""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.auth import KiteAuth
from src.utils.logger import logger
from src.utils.config import config


def main():
    """Main application function."""
    logger.info("Starting Zerodha Dashboard Application")
    
    # Validate configuration
    if not config.validate():
        logger.error("Configuration validation failed. Please check your .env file.")
        return False
    
    try:
        # Initialize authentication
        logger.info("Initializing Kite Connect authentication")
        auth = KiteAuth()
        
        # Step 1: Generate and display login URL
        logger.info("Generating login URL...")
        login_url = auth.generate_login_url()
        
        print("\\n" + "="*80)
        print("ZERODHA KITE CONNECT AUTHENTICATION")
        print("="*80)
        print(f"\\n1. Please visit the following URL to login:")
        print(f"   {login_url}")
        print("\\n2. After successful login, you'll be redirected to your callback URL")
        print("3. Copy the complete callback URL and paste it below")
        print("\\n" + "-"*80)
        
        # Step 2: Get callback URL from user
        callback_url = input("\\nPaste the callback URL here: ").strip()
        
        if not callback_url:
            logger.error("No callback URL provided")
            return False
        
        # Step 3: Complete authentication
        logger.info("Processing authentication...")
        session_data = auth.authenticate_with_callback_url(callback_url)
        
        print("\\n" + "="*80)
        print("AUTHENTICATION SUCCESSFUL!")
        print("="*80)
        print(f"User ID: {session_data.get('user_id', 'N/A')}")
        print(f"Access Token: {session_data.get('access_token', 'N/A')[:20]}...")
        print(f"Login Time: {session_data.get('login_time', 'N/A')}")
        
        # Step 4: Get user profile
        logger.info("Fetching user profile...")
        profile = auth.get_profile()
        
        print("\\n" + "-"*80)
        print("USER PROFILE")
        print("-"*80)
        print(f"Name: {profile.get('user_name', 'N/A')}")
        print(f"Email: {profile.get('email', 'N/A')}")
        print(f"User Type: {profile.get('user_type', 'N/A')}")
        print(f"Broker: {profile.get('broker', 'N/A')}")
        
        # Step 5: Demonstrate module initialization
        print("\\n" + "-"*80)
        print("MODULE INITIALIZATION")
        print("-"*80)
        
        # Get authenticated Kite instance
        kite = auth.get_kite_instance()
        
        # Initialize data analytics modules
        from src.data_analytics import MarketDataFetcher, TechnicalIndicators, BacktestEngine
        
        data_fetcher = MarketDataFetcher(kite)
        indicators = TechnicalIndicators()
        backtest_engine = BacktestEngine(initial_capital=100000)
        
        print("✓ MarketDataFetcher initialized")
        print("✓ TechnicalIndicators initialized")
        print("✓ BacktestEngine initialized")
        
        # Initialize execution modules
        from src.execution import OrderManager, PortfolioManager, RiskManager
        
        order_manager = OrderManager(kite)
        portfolio_manager = PortfolioManager(kite)
        risk_manager = RiskManager(initial_capital=100000)
        
        print("✓ OrderManager initialized")
        print("✓ PortfolioManager initialized")
        print("✓ RiskManager initialized")
        
        print("\\n" + "="*80)
        print("SETUP COMPLETE!")
        print("="*80)
        print("All modules are now ready for use.")
        print("You can now implement your trading strategies and analytics.")
        print("\\nNext steps:")
        print("1. Implement market data fetching functions")
        print("2. Add technical indicator calculations")
        print("3. Build order management logic")
        print("4. Set up portfolio tracking")
        print("5. Configure risk management rules")
        
        logger.info("Application setup completed successfully")
        return True
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return False
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"\\nError: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
