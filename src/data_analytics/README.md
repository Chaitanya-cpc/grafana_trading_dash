# Data Analytics Module

This module contains various data analysis and visualization tools for trading data. Each analysis tool is organized in its own subdirectory for better modularity and maintainability.

## Available Modules

### 📊 Option Chain Analysis (`option_chain/`)

A live, dynamically updating option chain display with real-time data visualization.

**Features:**

- Live option prices and Open Interest tracking
- ATM strike detection and highlighting
- Visual OI bars and color coding
- Straddle price calculations
- Configurable refresh intervals

**Usage:**

```bash
python3 src/data_analytics/option_chain/basic_option_chain.py
```

**Documentation:** See [`option_chain/README.md`](option_chain/README.md)

---

## Module Structure

Each analysis module follows this structure:

```
data_analytics/
├── module_name/
│   ├── __init__.py           # Module initialization
│   ├── main_script.py        # Main application
│   ├── config.json           # Module configuration
│   └── README.md             # Module documentation
```

## Adding New Modules

When creating new analysis modules:

1. **Create subdirectory**: `mkdir src/data_analytics/new_module/`
2. **Add module files**:
   - `__init__.py` - Module initialization
   - `main_script.py` - Main application logic
   - `config.json` - Configuration settings
   - `README.md` - Module documentation
3. **Update this README** with module information
4. **Follow naming conventions**: Use snake_case for directories and files

## Authentication

All modules use the existing authentication system from `src/auth/`. No separate login is required - modules will automatically use your authenticated Zerodha session.

## Common Requirements

- Python 3.11+
- Authenticated Zerodha Kite Connect session
- Required packages (see main `requirements.txt`)
- GUI support for visualization modules

## Development Guidelines

- **Self-contained**: Each module should be independent
- **Configurable**: Use JSON config files for settings
- **Documented**: Include comprehensive README for each module
- **Modular**: Keep related functionality together
- **Clean imports**: Use relative imports within modules where possible
