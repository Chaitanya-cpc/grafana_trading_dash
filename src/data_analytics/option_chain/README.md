# Option Chain Analysis Module

A live, dynamically updating option chain display that shows real-time option data in a separate GUI window.

## Features

- **Live Data**: Real-time option prices and Open Interest (OI)
- **ATM Detection**: Automatically identifies and highlights At-The-Money strikes
- **Visual OI Bars**: Horizontal bar graphs showing relative OI levels
- **Color Coding**: ITM strikes in red, OTM strikes in green
- **Straddle Pricing**: Live calculation of call + put premiums
- **Auto-refresh**: Updates every 10 seconds (configurable)

## Configuration

Edit `config.json` in this directory to customize:

```json
{
  "ticker_symbol": "NIFTY",
  "strike_difference": 50,
  "strikes_above_atm": 3,
  "strikes_below_atm": 3,
  "refresh_interval_seconds": 10,
  "window_title": "Live Option Chain - Zerodha",
  "window_width": 1200,
  "window_height": 600
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
