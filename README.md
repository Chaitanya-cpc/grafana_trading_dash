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
│   ├── grafana/                # Grafana configuration
│   │   ├── dashboards/         # Dashboard definitions
│   │   └── provisioning/       # Auto-provisioning configs
│   └── influxdb/               # InfluxDB configuration
├── data/                       # Data storage
│   ├── influxdb/               # InfluxDB data files
│   ├── logs/                   # Application logs
│   └── input/                  # Input files (watchlist, etc.)
├── docker/                     # Docker configuration
│   ├── Dockerfile              # Main application Dockerfile
│   └── docker-compose.yml      # Docker Compose configuration
└── src/                        # Source code
    ├── alerts/                 # Alert modules
    │   └── telegram_alerter.py # Telegram alerting
    ├── api/                    # API clients
    │   ├── zerodha_api.py      # Zerodha API client
    │   └── websocket_client.py # WebSocket client
    ├── db/                     # Database modules
    │   └── influxdb_client.py  # InfluxDB client
    ├── indicators/             # Technical indicators
    │   └── technical_indicators.py # Technical analysis
    ├── models/                 # Data models
    │   ├── instrument.py       # Instrument data model
    │   ├── order.py            # Order data model
    │   ├── position.py         # Position data model
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
INFLUXDB_TOKEN=your_influxdb_token
INFLUXDB_ORG=zerodha
INFLUXDB_BUCKET=trading_data

# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Application Settings
LOG_LEVEL=INFO
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
2. Log in with default credentials (admin/admin)
3. View the pre-configured Zerodha Trading Dashboard

## Customization

- Add your watchlist in `data/input/watchlist.csv`
- Configure sector mappings in `data/input/symbol_sector_map.csv`
- Adjust alert thresholds in the `.env` file

## License

MIT 