# Zerodha Kite Connect API Integration

A modular Python package for integrating with Zerodha's Kite Connect API, providing authentication, data analytics, and execution capabilities.

## 🚀 Features

- **Secure Authentication**: Complete OAuth flow with API key/secret management
- **Data Analytics**: Market data fetching, technical indicators, and backtesting
- **Order Execution**: Order placement, portfolio management, and risk controls
- **Modular Design**: Clean separation of concerns with well-defined modules
- **Comprehensive Logging**: Structured logging with file and console output
- **Configuration Management**: Environment-based configuration with validation

## 📁 Project Structure

```
zerodha-dashboard/
├── src/
│   ├── auth/                    # Authentication module
│   │   ├── __init__.py
│   │   └── kite_auth.py        # Kite Connect authentication
│   ├── data_analytics/         # Data analysis and indicators
│   │   ├── __init__.py
│   │   ├── market_data.py      # Market data fetching
│   │   ├── indicators.py       # Technical indicators
│   │   └── backtesting.py      # Backtesting engine
│   ├── execution/              # Order execution and portfolio
│   │   ├── __init__.py
│   │   ├── order_manager.py    # Order management
│   │   ├── portfolio_manager.py # Portfolio tracking
│   │   └── risk_manager.py     # Risk management
│   └── utils/                  # Utility modules
│       ├── __init__.py
│       ├── config.py           # Configuration management
│       └── logger.py           # Logging setup
├── tests/                      # Test files
├── logs/                       # Log files
├── data/                       # Data files
├── .gitignore
├── requirements.txt
├── env.example                 # Environment template
└── README.md
```

## 🛠️ Setup Instructions

### 1. Clone and Setup Environment

```bash
git clone <your-repo-url>
cd zerodha-dashboard

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

1. Copy the environment template:
   ```bash
   cp env.example .env
   ```

2. Edit `.env` file with your Kite Connect credentials:
   ```env
   KITE_API_KEY=your_api_key_here
   KITE_API_SECRET=your_api_secret_here
   KITE_REDIRECT_URL=http://localhost:3000/callback
   LOG_LEVEL=INFO
   LOG_FILE=logs/zerodha_dashboard.log
   ```

3. Get your API credentials from [Kite Connect Developer Console](https://developers.kite.trade/)

### 3. Test Authentication

```bash
python main.py
```

## 🔐 Authentication Flow

The authentication process follows Kite Connect's OAuth flow:

1. **Generate Login URL**: Create login URL with your API key
2. **User Login**: User logs in via Zerodha and grants permissions
3. **Extract Request Token**: Get request token from callback URL
4. **Generate Access Token**: Exchange request token for access token
5. **API Access**: Use access token for all subsequent API calls

### Example Usage

```python
from src.auth import KiteAuth
from src.utils.logger import logger

# Initialize authentication
auth = KiteAuth()

# Step 1: Generate login URL
login_url = auth.generate_login_url()
print(f"Please visit: {login_url}")

# Step 2: After login, paste the callback URL
callback_url = input("Paste callback URL: ")

# Step 3: Complete authentication
try:
    session_data = auth.authenticate_with_callback_url(callback_url)
    print(f"Authentication successful! User ID: {session_data['user_id']}")
    
    # Get user profile
    profile = auth.get_profile()
    print(f"Welcome, {profile['user_name']}!")
    
except Exception as e:
    logger.error(f"Authentication failed: {e}")
```

## 📊 Module Usage

### Data Analytics

```python
from src.data_analytics import MarketDataFetcher, TechnicalIndicators

# Get authenticated Kite instance
kite = auth.get_kite_instance()

# Fetch market data
data_fetcher = MarketDataFetcher(kite)
instruments = data_fetcher.get_instruments("NSE")

# Calculate indicators
indicators = TechnicalIndicators()
# Implementation coming soon...
```

### Order Execution

```python
from src.execution import OrderManager, PortfolioManager, RiskManager

# Order management
order_manager = OrderManager(kite)
# Implementation coming soon...

# Portfolio tracking
portfolio = PortfolioManager(kite)
# Implementation coming soon...

# Risk management
risk_manager = RiskManager(initial_capital=100000)
# Implementation coming soon...
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `KITE_API_KEY` | Your Kite Connect API key | Yes | - |
| `KITE_API_SECRET` | Your Kite Connect API secret | Yes | - |
| `KITE_REDIRECT_URL` | Registered redirect URL | No | `http://localhost:3000/callback` |
| `LOG_LEVEL` | Logging level | No | `INFO` |
| `LOG_FILE` | Log file path | No | `logs/zerodha_dashboard.log` |

### Logging

The application uses structured logging with both console and file output:
- **Console**: Colored output for development
- **File**: Rotated logs with 30-day retention
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test module
pytest tests/test_auth.py

# Run with coverage
pytest --cov=src tests/
```

## 🚧 Current Status

### ✅ Completed
- [x] Project structure setup
- [x] Authentication flow implementation
- [x] Configuration management
- [x] Logging system
- [x] Module stubs and interfaces

### 🔄 In Progress
- [ ] Market data fetching implementation
- [ ] Technical indicators calculation
- [ ] Order management implementation
- [ ] Portfolio tracking
- [ ] Risk management rules

### 📋 Planned
- [ ] WebSocket real-time data
- [ ] Advanced backtesting features
- [ ] Dashboard UI
- [ ] Database integration
- [ ] Comprehensive test coverage

## 📚 API Documentation

- [Kite Connect API Documentation](https://kite.trade/docs/connect/v3/)
- [Python SDK Documentation](https://github.com/zerodhatech/pykiteconnect)

## ⚠️ Important Notes

1. **Paper Trading**: Always test with paper trading before live trading
2. **Risk Management**: Implement proper risk controls before live trading
3. **API Limits**: Be aware of Kite Connect API rate limits
4. **Security**: Never commit API keys to version control
5. **Compliance**: Ensure compliance with SEBI regulations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the [Kite Connect documentation](https://kite.trade/docs/connect/v3/)
2. Review existing GitHub issues
3. Create a new issue with detailed information

---

**Disclaimer**: This software is for educational and development purposes. Use at your own risk for live trading.
