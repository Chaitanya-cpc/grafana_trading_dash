# Unified Zerodha Trading Monitoring Dashboard

A comprehensive real-time monitoring system for Zerodha trading accounts, featuring an InfluxDB time-series database and Grafana dashboards.

## Features

- Real-time monitoring of positions, orders, and P&L
- Technical indicator calculations and alerts
- Sector exposure tracking and analysis
- WebSocket connection for live market data
- Telegram alerts for important events
- Performance and system metrics monitoring

## Project Structure

```
zerodha-dashboard/
├── config/                     # Configuration files
│   ├── application.yaml        # Application configuration
│   ├── grafana/                # Grafana configuration
│   │   ├── dashboards/         # Dashboard definitions
│   │   └── provisioning/       # Auto-provisioning configs
├── data/                       # Data storage
│   ├── logs/                   # Application logs
│   └── input/                  # Input files (watchlist, etc.)
├── docker/                     # Docker configuration
│   └── Dockerfile              # Main application Dockerfile
├── docker-compose.yml          # Docker Compose configuration
└── src/                        # Source code
    ├── alerts/                 # Alert modules
    │   └── telegram_alerter.py # Telegram alerting
    ├── api/                    # API clients
    │   ├── zerodha_api.py      # Zerodha API client
    │   └── websocket_client.py # WebSocket client
    ├── database/               # Database modules
    │   └── influxdb_client.py  # InfluxDB client
    ├── indicators/             # Technical indicators
    │   └── technical_indicators.py # Technical analysis
    ├── models/                 # Data models
    │   ├── state_manager.py    # Application state manager
    │   └── scheduler.py        # Task scheduler
    ├── utils/                  # Utility modules
    │   ├── config.py           # Configuration utility
    │   ├── file_reader.py      # File reading utility
    │   └── logger.py           # Logging utility
    └── main.py                 # Main application entry point
```

## Setup and Installation

### Prerequisites

- Docker and Docker Compose
- Python 3.9 (for local development)
- Zerodha Trading Account with API access
- Telegram Bot (optional, for alerts)

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# Zerodha API Credentials
ZERODHA_API_KEY=your_api_key
ZERODHA_API_SECRET=your_api_secret
ZERODHA_USER_ID=your_user_id
ZERODHA_PASSWORD=your_password
ZERODHA_TOTP_KEY=your_totp_key

# InfluxDB Configuration
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_ADMIN_PASSWORD=your_influxdb_password
INFLUXDB_TOKEN=your_influxdb_token

# Grafana Configuration
GRAFANA_ADMIN_PASSWORD=your_grafana_password

# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Application Settings
LOG_LEVEL=INFO
WATCHLIST_PATH=/app/data/input/watchlist.csv
SECTOR_MAP_PATH=/app/data/input/symbol_sector_map.csv
BENCHMARK_SYMBOL=NIFTY 50

# API Polling Intervals (in seconds)
POSITIONS_POLL_INTERVAL=15
MARGINS_POLL_INTERVAL=60
ORDERS_POLL_INTERVAL=30
TRADES_POLL_INTERVAL=30
HOLDINGS_POLL_INTERVAL=300
OHLC_POLL_INTERVAL=300

# Risk Thresholds
MARGIN_ALERT_THRESHOLD=20
DRAWDOWN_ALERT_THRESHOLD=5

# Technical Indicators Configuration
INDICATOR_TIMEFRAME=5minute
RSI_PERIOD=14
SMA_PERIODS=20,50

# Timezone
TIMEZONE=Asia/Kolkata
```

### Running the Application

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## Usage

1. Access the Grafana dashboard at: http://localhost:3000
2. Log in with the credentials specified in the .env file
3. View the pre-configured Zerodha Trading Dashboard

## Customization

- Add your watchlist in `data/input/watchlist.csv`
- Configure sector mappings in `data/input/symbol_sector_map.csv`
- Adjust alert thresholds in the `.env` file or in `config/application.yaml`
- Modify dashboard layouts in Grafana

## Fixed Configuration Values

The application uses the following fixed values for consistency:

- InfluxDB organization name: `zerodha`
- InfluxDB bucket name: `zerodha_data`

## License

MIT 