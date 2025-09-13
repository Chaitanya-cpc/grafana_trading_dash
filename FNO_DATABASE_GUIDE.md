# F&O Instruments Database Generator

## 🎯 Purpose

Generate a comprehensive CSV database of all F&O (Futures & Options) instruments from Zerodha Kite Connect, including trading symbols, strike differences, lot sizes, and expiry dates.

## 🚀 Usage

### Run the Script

```bash
cd /path/to/zerodha-dashboard
python3 generate_fno_database.py
```

### Output Files

The script generates a single clean CSV file:

**`fno_summary_latest.csv`** - Contains everything you need:
- Strike differences (auto-calculated)
- Lot sizes for position sizing  
- Expiry dates for planning
- Instrument counts for liquidity assessment

**🧹 Auto-cleanup**: Old timestamped files are automatically deleted to keep your directory clean.

## 📊 CSV Structure

### Summary CSV Columns

| Column               | Description                                   |
| -------------------- | --------------------------------------------- |
| `name`               | Underlying asset name (e.g., NIFTY, RELIANCE) |
| `tradingsymbol`      | Trading symbol                                |
| `exchange`           | Exchange (NSE, MCX, etc.)                     |
| `segment`            | Market segment (NFO, MCX)                     |
| `lot_size`           | Standard lot size for trading                 |
| `strike_difference`  | **Auto-calculated strike difference**         |
| `tick_size`          | Minimum price movement                        |
| `expiry_dates`       | Next 3 expiry dates                           |
| `total_expiries`     | Total number of expiry dates                  |
| `futures_count`      | Number of futures contracts                   |
| `call_options_count` | Number of call options                        |
| `put_options_count`  | Number of put options                         |
| `total_instruments`  | Total instruments for this underlying         |

### Key Data Points

The single CSV file contains all essential F&O information:
- **252 Underlyings** (NIFTY, BANKNIFTY, stocks, commodities)
- **Auto-calculated strike differences** (50 for NIFTY, 100 for BANKNIFTY, etc.)
- **Lot sizes** for accurate position sizing
- **Expiry schedules** for strategy planning
- **Instrument counts** for liquidity assessment

## 🔄 Schedule

**Run Monthly**: Execute this script after monthly options expiry (usually last Thursday of each month) to keep the database current.

## 📈 Key Features

### ✅ Auto-Calculated Strike Differences

- Analyzes all option strikes for each underlying
- Finds the most common strike interval
- No manual input required

### ✅ Complete F&O Coverage

- NSE F&O segment (NFO)
- MCX commodities (if available)
- All futures, calls, and puts

### ✅ Rich Metadata

- Lot sizes for position sizing
- Expiry dates for strategy planning
- Instrument counts for liquidity assessment

## 💡 Usage Tips

### For Option Chain Analysis

```python
# Use the single CSV file to get all F&O data
import pandas as pd

summary = pd.read_csv('fno_summary_latest.csv')
nifty_data = summary[summary['name'] == 'NIFTY'].iloc[0]
strike_diff = nifty_data['strike_difference']  # 50
lot_size = nifty_data['lot_size']  # 50

# Get data for any ticker
reliance_strike = summary[summary['name'] == 'RELIANCE']['strike_difference'].iloc[0]  # 25
banknifty_strike = summary[summary['name'] == 'BANKNIFTY']['strike_difference'].iloc[0]  # 100
```

### For Trading Applications

- **Position Sizing**: Use `lot_size` for calculating position sizes
- **Strike Selection**: Use `strike_difference` for option chain displays
- **Expiry Planning**: Use `expiry_dates` for strategy scheduling

### For Analysis

- **Liquidity**: Higher `total_instruments` = more liquid
- **Activity**: More expiries = more active trading
- **Segments**: Filter by exchange/segment for specific markets

## 🛠️ Troubleshooting

### Authentication Issues

- Ensure `.env` file has valid Zerodha credentials
- Check if markets are open (script works anytime, but live data is better during market hours)

### Missing Data

- Some instruments might have 0 strike difference if insufficient option strikes
- MCX data might be limited based on your broker permissions

### File Permissions

- Ensure write permissions in the script directory
- Files are created in the same directory as the script

## 📋 Sample Output

```
📊 F&O INSTRUMENTS DATABASE STATISTICS
============================================================
📈 Total Underlyings: 183
📊 Total Instruments: 12,547
🏢 Exchanges: NFO, MCX
   • NFO: 165 underlyings
   • MCX: 18 underlyings

🔥 Top 10 Most Active Underlyings:
    1. NIFTY       - 156 instruments (Strike diff: 50)
    2. BANKNIFTY   - 142 instruments (Strike diff: 100)
    3. RELIANCE    - 89 instruments (Strike diff: 25)
    4. TCS         - 76 instruments (Strike diff: 50)
    5. HDFCBANK    - 71 instruments (Strike diff: 25)
```

## 🎯 Integration

Use the single `fno_summary_latest.csv` file with:

- **Excel/Google Sheets**: For manual analysis and reference
- **Python/Pandas**: For programmatic access to all F&O data
- **Option Chain Module**: Update `config.json` with correct strike differences
- **Trading Applications**: Single source of truth for all F&O metadata
- **Position Sizing**: Use lot_size column for accurate calculations

---

**Run this script monthly to keep your F&O database fresh and accurate!** 📅
