# 🚀 Zerodha Kite Connect - Complete Trading Suite

**Zero-intervention authentication and F&O trading integration with Zerodha Kite Connect API**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Status: Production Ready](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

---

## 🎯 **What This Provides**

### **🤖 Complete Automation Suite**
- ✅ **ZERO manual login** - Fully automated browser authentication
- ✅ **Automated 2FA/TOTP** - Handles OTP automatically using pyotp
- ✅ **Persistent tokens** - Instant subsequent logins (< 1 second)
- ✅ **F&O Database Generator** - Auto-calculates strike differences for all instruments
- ✅ **Live Option Chain Display** - Real-time GUI with OI bars and color coding

### **🏆 Key Features**
- 🤖 **100% Automation**: No manual intervention after setup
- ⚡ **Lightning Fast**: Ultra-optimized login (0.025s TOTP entry)
- 🔒 **Secure**: Encrypted credential storage with proper security practices
- 📊 **Production Ready**: Complete error handling and logging
- 🏗️ **Modular**: Clean separation of auth, data analytics, and execution

---

## 🚀 **Quick Start**

### **1. Installation**
```bash
git clone https://github.com/your-username/zerodha-dashboard.git
cd zerodha-dashboard
pip install -r requirements.txt
```

### **2. Configuration**
```bash
cp env.example .env
# Edit .env with your credentials
```

**Required in `.env`:**
```env
# Zerodha API
KITE_API_KEY=your_api_key
KITE_API_SECRET=your_api_secret

# Full Automation (for zero manual intervention)
ZERODHA_USERNAME=your_user_id
ZERODHA_PASSWORD=your_password
ZERODHA_PIN=your_trading_pin
ZERODHA_TOTP_SECRET=your_totp_secret

# Optional Settings
AUTO_LOGIN_ENABLED=true
HEADLESS_BROWSER=false
```

### **3. Run Applications**

#### **Main Authentication Demo**
```bash
python3 main.py
```

#### **Generate F&O Database (Monthly)**
```bash
python3 generate_fno_database.py
```

#### **Live Option Chain Display**
```bash
python3 src/data_analytics/option_chain/basic_option_chain.py
```

---

## 🏗️ **Project Structure**

```
zerodha-dashboard/
├── main.py                          # 🎯 Main authentication demo
├── generate_fno_database.py         # 📊 F&O database generator
├── requirements.txt                 # 📦 Dependencies
├── env.example                      # ⚙️ Configuration template
├── fno_summary_latest.csv          # 📋 F&O instruments database
├── src/
│   ├── auth/                        # 🔐 Authentication System
│   │   ├── kite_auth.py            # Main auth handler
│   │   ├── browser_automation.py   # Selenium automation
│   │   ├── callback_server.py      # OAuth callback handler
│   │   └── token_manager.py        # Token persistence
│   ├── data_analytics/             # 📊 Analysis Tools
│   │   └── option_chain/           # Live option chain display
│   │       ├── basic_option_chain.py
│   │       ├── config.json
│   │       └── README.md
│   ├── execution/                  # 💼 Trading Operations (Ready for development)
│   └── utils/                      # 🛠️ Utilities
│       ├── config.py               # Configuration loader
│       └── logger.py               # Logging setup
└── data/                           # 💾 Data storage
    └── logs/                       # 📝 Log files
```

---

## 🔐 **Authentication Modes**

### **⚡ Instant Authentication (< 1 second)**
- Uses saved token from previous successful login
- Zero network calls or browser interaction
- Available after first successful authentication

### **🤖 Full Automation (60-90 seconds)**
- Completely automated browser login with Selenium
- Handles username, password, 2FA/TOTP, PIN automatically
- Ultra-fast TOTP entry (0.025s per character)
- Saves token for future instant logins

### **🔄 Manual Fallback**
- Traditional OAuth flow with local callback server
- Used only if full automation fails
- Still eliminates manual URL copying

---

## 📊 **F&O Database Generator**

### **Monthly Workflow**
```bash
python3 generate_fno_database.py
```

**Generates:** `fno_summary_latest.csv` with:
- **252 F&O Underlyings** (NIFTY, BANKNIFTY, stocks, commodities)
- **Auto-calculated strike differences** (50 for NIFTY, 100 for BANKNIFTY, etc.)
- **Lot sizes** for position sizing
- **Expiry schedules** for strategy planning
- **Instrument counts** for liquidity assessment

### **Key Data Points**
```csv
name,strike_difference,lot_size,total_instruments
NIFTY,50.0,50,1521
BANKNIFTY,100.0,15,908
RELIANCE,25.0,250,89
```

### **Usage in Code**
```python
import pandas as pd
df = pd.read_csv('fno_summary_latest.csv')

# Get strike differences for any ticker
nifty_strike = df[df['name'] == 'NIFTY']['strike_difference'].iloc[0]  # 50
banknifty_strike = df[df['name'] == 'BANKNIFTY']['strike_difference'].iloc[0]  # 100
```

---

## 📈 **Live Option Chain Display**

### **Features**
- **Real-time option prices** and Open Interest
- **ATM detection** with dynamic highlighting
- **Visual OI bars** showing relative interest levels
- **Color coding**: ITM (red), OTM (green), ATM (highlighted)
- **Straddle pricing** with live calculations
- **Auto-refresh** every 10 seconds

### **Configuration**
Edit `src/data_analytics/option_chain/config.json`:
```json
{
  "ticker_symbol": "NIFTY",
  "strike_difference": 50,
  "strikes_above_atm": 3,
  "strikes_below_atm": 3,
  "refresh_interval_seconds": 10
}
```

### **Usage**
```bash
python3 src/data_analytics/option_chain/basic_option_chain.py
```

---

## 🔧 **Development**

### **Adding New Analysis Modules**
```bash
mkdir src/data_analytics/new_module
cd src/data_analytics/new_module
touch __init__.py main.py config.json README.md
```

### **Module Pattern**
```
new_module/
├── __init__.py        # Module exports
├── main.py            # Main application
├── config.json        # Settings
└── README.md          # Documentation
```

### **Authentication Integration**
```python
from src.auth.kite_auth import KiteAuth

# Initialize and authenticate
auth = KiteAuth()
success = auth.authenticate_ultimate()  # Smart authentication
kite = auth.get_kite_instance()

# Use authenticated kite instance for API calls
```

---

## ⚡ **Performance Optimizations**

### **Login Speed**
- **TOTP Entry**: 0.025s per character (75% faster than original)
- **Page Transitions**: Optimized wait times
- **Token Persistence**: Instant subsequent logins

### **F&O Processing**
- **47K+ instruments** processed in seconds
- **Auto-cleanup** of temporary files
- **Single clean output** file

---

## 🛠️ **Configuration**

### **Environment Variables**
| Variable | Description | Required |
|----------|-------------|----------|
| `KITE_API_KEY` | Zerodha API key | ✅ Yes |
| `KITE_API_SECRET` | Zerodha API secret | ✅ Yes |
| `ZERODHA_USERNAME` | User ID for automation | ⚠️ For full automation |
| `ZERODHA_PASSWORD` | Password for automation | ⚠️ For full automation |
| `ZERODHA_PIN` | Trading PIN | ⚠️ For full automation |
| `ZERODHA_TOTP_SECRET` | TOTP secret key | ⚠️ For full automation |
| `AUTO_LOGIN_ENABLED` | Enable automation | No (default: false) |
| `HEADLESS_BROWSER` | Headless mode | No (default: false) |

### **Getting TOTP Secret**
1. Enable 2FA in Zerodha account settings
2. When setting up authenticator, save the secret key
3. Use this key as `ZERODHA_TOTP_SECRET`

---

## 🚨 **Security & Compliance**

### **Security Practices**
- Never commit `.env` files to version control
- Use secure file permissions (600) for sensitive data
- Encrypted token storage with automatic expiration
- Comprehensive audit logging

### **Compliance**
- Respects Zerodha's daily login requirements
- Complies with SEBI regulations
- Use responsibly and within broker's terms of service

---

## 🧪 **Testing**

### **Test Authentication**
```bash
# With visible browser for debugging
HEADLESS_BROWSER=false python3 main.py
```

### **Common Issues**
1. **Chrome driver**: Ensure Chrome browser is installed
2. **TOTP failures**: Verify TOTP secret is correct
3. **Network timeouts**: Check connection and increase timeouts
4. **Element detection**: XPaths are tested and working

---

## 📋 **Usage Examples**

### **Monthly F&O Update**
```bash
# Run after options expiry (last Thursday)
python3 generate_fno_database.py
# Use generated fno_summary_latest.csv in your applications
```

### **Live Option Chain**
```bash
# Configure ticker in config.json, then:
python3 src/data_analytics/option_chain/basic_option_chain.py
```

### **Custom Development**
```python
from src.auth.kite_auth import KiteAuth

# Authenticate
auth = KiteAuth()
auth.authenticate_ultimate()
kite = auth.get_kite_instance()

# Use kite instance for your trading logic
positions = kite.positions()
orders = kite.orders()
```

---

## 🤝 **Contributing**

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes with tests
4. Commit: `git commit -am 'Add feature'`
5. Push: `git push origin feature-name`
6. Submit Pull Request

---

## 📄 **License**

MIT License - see LICENSE file for details.

---

## 🆘 **Support**

### **Getting Help**
1. Check [Kite Connect documentation](https://kite.trade/docs/connect/v3/)
2. Review existing GitHub issues
3. Create new issue with detailed description and logs

### **Quick Commands**
```bash
# Main authentication
python3 main.py

# Generate F&O database
python3 generate_fno_database.py

# Live option chain
python3 src/data_analytics/option_chain/basic_option_chain.py

# Setup
cp env.example .env && pip install -r requirements.txt
```

---

**🎯 Complete trading automation ready to deploy!** 🚀

*Built for serious traders who value automation and efficiency*