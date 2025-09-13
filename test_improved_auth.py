#!/usr/bin/env python3
"""
Test the improved authentication with better timing and debugging.
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
    """Test improved authentication with debugging."""
    print("="*80)
    print("🧪 TESTING IMPROVED AUTHENTICATION (Visible Browser)")
    print("="*80)
    
    # Show what we've improved
    print("🔧 IMPROVEMENTS MADE:")
    print("   ✅ Increased timing delays for slower connections")
    print("   ✅ Better TOTP field detection with multiple selectors") 
    print("   ✅ Character-by-character TOTP entry for reliability")
    print("   ✅ TOTP retry logic (up to 3 attempts)")
    print("   ✅ Extended callback waiting with debugging")
    print("   ✅ Screenshot capture for debugging issues")
    print("   ✅ Better error handling and logging")
    
    print("\\n📋 TEST CONFIGURATION:")
    print(f"   🔑 API Key: {config.kite_api_key[:10]}...")
    print(f"   👤 Username: {config.zerodha_username}")
    print(f"   🔢 PIN: {'*' * len(config.zerodha_pin) if config.zerodha_pin else 'Not set'}")
    print(f"   📱 TOTP Secret: {'Configured' if config.zerodha_totp_secret else 'Not configured'}")
    print(f"   👁️  Headless: {config.headless_browser}")
    
    if config.headless_browser:
        print("\\n⚠️  RECOMMENDATION: Set HEADLESS_BROWSER=false in .env to see the browser")
        print("   This helps debug timing and element detection issues.")
    
    try:
        print("\\n" + "="*80)
        print("🚀 STARTING IMPROVED AUTHENTICATION TEST")
        print("="*80)
        
        # Initialize auth
        auth = KiteAuth(use_local_server=True, server_port=3000)
        
        # Start authentication
        print("\\n🤖 Starting fully automated authentication...")
        print("⏰ This will take 60-90 seconds with improved timing...")
        print("\\n💡 Watch the browser window to see the automation in action!")
        
        session_data = auth.authenticate_ultimate(timeout=300)
        
        print("\\n" + "="*80)
        print("🎉 SUCCESS! Authentication completed!")
        print("="*80)
        print(f"👤 User: {session_data.get('user_id', 'N/A')}")
        print(f"⏰ Method: {session_data.get('login_time', 'N/A')}")
        
        # Test API
        profile = auth.get_profile()
        print(f"📝 Name: {profile.get('user_name', 'N/A')}")
        
        print("\\n✅ All tests passed! Your automation is working perfectly!")
        return True
        
    except KeyboardInterrupt:
        print("\\n⏹️  Test cancelled")
        return False
    except Exception as e:
        print(f"\\n❌ Test failed: {e}")
        print("\\n🔍 DEBUG INFO:")
        print("   📸 Check for debug screenshots in the project directory")
        print("   📋 Check logs/zerodha_dashboard.log for detailed logs")
        print("   🌐 Set HEADLESS_BROWSER=false to see browser automation")
        print("   ⏰ Consider slower internet - timing delays may need adjustment")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
