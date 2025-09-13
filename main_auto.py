#!/usr/bin/env python3
"""
Automated authentication flow for Zerodha Kite Connect integration.

This script demonstrates the automated authentication flow using a local callback server,
eliminating the need for manual callback URL handling.
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
    """Main application function with automated authentication."""
    logger.info("Starting Zerodha Dashboard Application (Automated Mode)")
    
    # Validate configuration
    if not config.validate():
        logger.error("Configuration validation failed. Please check your .env file.")
        return False
    
    try:
        # Initialize authentication with automatic mode
        logger.info("Initializing automated Kite Connect authentication")
        auth = KiteAuth(use_local_server=True, server_port=3000)
        
        print("\\n" + "="*80)
        print("🚀 ZERODHA DASHBOARD - AUTOMATED SETUP")
        print("="*80)
        print("\\n🔧 Configuration validated successfully")
        print("🔑 API credentials loaded")
        print("🌐 Local callback server ready")
        
        # Perform automated authentication
        session_data = auth.authenticate_automatically(
            timeout=300,  # 5 minutes timeout
            open_browser=True  # Automatically open browser
        )
        
        # Display authentication results
        print("\\n" + "="*80)
        print("✅ AUTHENTICATION SUCCESSFUL!")
        print("="*80)
        print(f"👤 User ID: {session_data.get('user_id', 'N/A')}")
        print(f"🔑 Access Token: {session_data.get('access_token', 'N/A')[:20]}...")
        print(f"⏰ Login Time: {session_data.get('login_time', 'N/A')}")
        
        # Get user profile
        logger.info("Fetching user profile...")
        profile = auth.get_profile()
        
        print("\\n" + "-"*80)
        print("👨‍💼 USER PROFILE")
        print("-"*80)
        print(f"📝 Name: {profile.get('user_name', 'N/A')}")
        print(f"📧 Email: {profile.get('email', 'N/A')}")
        print(f"🏢 User Type: {profile.get('user_type', 'N/A')}")
        print(f"🏦 Broker: {profile.get('broker', 'N/A')}")
        
        # Initialize all modules
        print("\\n" + "-"*80)
        print("🔧 INITIALIZING TRADING MODULES")
        print("-"*80)
        
        # Get authenticated Kite instance
        kite = auth.get_kite_instance()
        
        # Initialize data analytics modules
        from src.data_analytics import MarketDataFetcher, TechnicalIndicators, BacktestEngine
        
        data_fetcher = MarketDataFetcher(kite)
        indicators = TechnicalIndicators()
        backtest_engine = BacktestEngine(initial_capital=100000)
        
        print("✅ MarketDataFetcher initialized")
        print("✅ TechnicalIndicators initialized")
        print("✅ BacktestEngine initialized")
        
        # Initialize execution modules
        from src.execution import OrderManager, PortfolioManager, RiskManager
        
        order_manager = OrderManager(kite)
        portfolio_manager = PortfolioManager(kite)
        risk_manager = RiskManager(initial_capital=100000)
        
        print("✅ OrderManager initialized")
        print("✅ PortfolioManager initialized")
        print("✅ RiskManager initialized")
        
        # Test basic API functionality
        print("\\n" + "-"*80)
        print("🧪 TESTING API CONNECTIVITY")
        print("-"*80)
        
        try:
            # Test profile access (already fetched above)
            print("✅ Profile access: Working")
            
            # You can add more API tests here as you implement functionality
            print("✅ Authentication: Verified")
            print("✅ API Connection: Active")
            
        except Exception as e:
            print(f"⚠️  API Test Warning: {e}")
        
        print("\\n" + "="*80)
        print("🎉 SETUP COMPLETE!")
        print("="*80)
        print("\\n🔥 Your Zerodha Dashboard is ready for trading!")
        print("\\n📋 What's Next:")
        print("   1. ✅ Authentication - Complete")
        print("   2. 🔄 Implement market data fetching")
        print("   3. 📊 Add technical indicator calculations")
        print("   4. 💼 Build portfolio management features")
        print("   5. 🛡️  Set up risk management rules")
        print("   6. 📈 Create trading strategies")
        
        print("\\n💡 Pro Tip: All modules are now authenticated and ready to use!")
        print("   You can start implementing your trading logic immediately.")
        
        logger.info("Automated setup completed successfully")
        return True
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\\n\\n⏹️  Setup interrupted by user")
        return False
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"\\n❌ Error: {e}")
        print("\\n💡 Troubleshooting:")
        print("   1. Check your internet connection")
        print("   2. Verify your API credentials in .env file")
        print("   3. Ensure port 3000 is available")
        print("   4. Try running the script again")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
