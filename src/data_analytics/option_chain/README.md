# Multi-Instrument Option Chain Display

A sophisticated, real-time option chain system that can display multiple instruments simultaneously, each in its own window. Built with data from your F&O database.

## 🚀 Key Features

- **📊 Multi-Instrument Support**: Monitor multiple instruments simultaneously
- **🔥 Smart Configuration**: Auto-populated from F&O database with strike differences and lot sizes
- **⚡ Live Data**: Real-time option prices and Open Interest (OI)
- **🎯 ATM Detection**: Automatically identifies and highlights At-The-Money strikes
- **📈 Visual OI Bars**: Horizontal bar graphs showing relative interest levels
- **🌈 Color Coding**: ITM strikes in red, OTM strikes in green
- **💰 Straddle Pricing**: Live calculation of call + put premiums
- **🔄 Auto-refresh**: Updates every 10 seconds (configurable)
- **🎛️ Easy Management**: Simple tools to activate/deactivate instruments

## 🎯 Quick Start

### 1. Generate Configuration

```bash
# Generate config from F&O database (run this first!)
python3 config_generator.py
```

### 2. Manage Active Instruments

```bash
# Check current status
python3 manage_instruments.py status

# Activate specific instruments
python3 manage_instruments.py activate NIFTY BANKNIFTY

# Interactive management
python3 manage_instruments.py
```

### 3. Launch Option Chains

```bash
# Launch all active instruments
python3 basic_option_chain.py
```

## 📋 Configuration Structure

The `config.json` file contains:

```json
{
  "metadata": {
    "description": "Option Chain Configuration - Generated from F&O Database",
    "total_instruments": 224
  },
  "display_settings": {
    "refresh_interval_seconds": 10,
    "window_width": 1400,
    "window_height": 700,
    "strikes_above_atm": 3,
    "strikes_below_atm": 3
  },
  "instruments": {
    "NIFTY": {
      "active": 1, // 1 = active, 0 = inactive
      "strike_difference": 50.0,
      "lot_size": 75,
      "exchange": "NFO",
      "window_title": "Live Option Chain - NIFTY"
    }
  }
}
```

## Usage

From repository root:

```bash
python3 src/data_analytics/option_chain/basic_option_chain.py
```

Or from this directory:

```bash
cd src/data_analytics/option_chain
python3 basic_option_chain.py
```

## Display Columns

| Column             | Description                                  |
| ------------------ | -------------------------------------------- |
| **Strike Price**   | Option strike price (ATM highlighted with ●) |
| **Call Price**     | Current call option premium                  |
| **Call OI**        | Call Open Interest with horizontal bar       |
| **Put Price**      | Current put option premium                   |
| **Put OI**         | Put Open Interest with horizontal bar        |
| **Straddle Price** | Sum of call + put premiums                   |

## Color Coding

- **ATM Strike**: Marked with bullet (●)
- **ITM Options**: Red text
- **OTM Options**: Green text
- **OI Bars**: Visual representation of relative interest levels

## Requirements

- Authenticated Zerodha Kite Connect session
- GUI support (tkinter - usually included with Python)
- Active market hours for live data

## Troubleshooting

1. **No data displayed**: Check if markets are open and ticker symbol is correct
2. **Authentication errors**: Ensure your .env file has valid credentials
3. **GUI not opening**: Verify tkinter is installed and GUI support is available
4. **Slow updates**: Check network connection and consider increasing refresh interval
