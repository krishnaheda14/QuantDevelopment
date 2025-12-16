# GEMSCAP Quantitative Trading System v2.0

**Professional Architecture** - FastAPI backend + Streamlit frontend with Redis for real-time data.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    STREAMLIT FRONTEND                       │
│                   (http://localhost:8501)                   │
│  • 6 Tabs: Spread, Signals, Stats, Backtest, Alerts, System│
│  • Interactive Plotly charts                                 │
│  • Real-time WebSocket connection to backend                │
└──────────────┬──────────────────────────────────────────────┘
               │ HTTP REST + WebSocket
               ↓
┌─────────────────────────────────────────────────────────────┐
│                   FASTAPI BACKEND                           │
│                  (http://localhost:8000)                    │
│                                                             │
│  REST APIs:                                                 │
│  • /api/analytics  - OLS, spread, ADF, correlation         │
│  • /api/alerts     - Alert rules & management               │
│  • /api/export     - CSV/JSON data export                   │
│  • /api/debug      - System diagnostics & validation        │
│                                                             │
│  WebSocket:                                                 │
│  • /ws/live       - Real-time data streaming                │
│                                                             │
│  Background Services:                                       │
│  • Data Ingestion  - Binance WebSocket consumer            │
│  • Sampling Engine - 1s/1m/5m/15m/1h OHLC aggregation      │
│  • Alert Engine    - Real-time threshold monitoring         │
└──────────────┬──────────────────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────────────────┐
│                      REDIS DATABASE                         │
│                  (redis://localhost:6379)                   │
│                                                             │
│  • Tick data (stream)                                       │
│  • OHLC bars (1s, 1m, 5m, 15m, 1h)                         │
│  • Analytics cache                                          │
│  • Alert rules & history                                    │
│  • Pub/Sub for real-time updates                           │
└──────────────┬──────────────────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────────────────┐
│                  BINANCE WEBSOCKET API                      │
│               wss://stream.binance.com:9443                 │
│  • 13 crypto pairs (BTC, ETH, BNB, SOL, etc.)              │
│  • Real-time trade data                                     │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

✅ **FastAPI Backend** - Modern async API framework with automatic OpenAPI docs  
✅ **Redis for Real-Time Data** - High-performance in-memory storage with pub/sub  
✅ **WebSocket API** - `/ws/live` endpoint for real-time frontend updates  
✅ **Modular Services** - Loose coupling between ingestion, sampling, and alerting  
✅ **RESTful Endpoints** - Standard HTTP APIs for all analytics operations  
✅ **Configurable Sampling** - 1s/1m/5m/15m/1h timeframes  
✅ **Backend-Driven Alerts** - Alert rules managed via API, not just UI  
✅ **Debug/Validation Layer** - `/api/debug` endpoints for system diagnostics  
✅ **Data Export APIs** - `/api/export` for CSV/JSON downloads  
✅ **Separation of Concerns** - Frontend for display, backend for logic

## Setup Instructions

### Prerequisites
- Python 3.9+ (tested on 3.11)
- Virtual environment (recommended)

### Installation

1. **Clone the repository** (or navigate to project root):
   ```bash
   cd F:\Gemscap_Quant_Project
   ```

2. **Activate virtual environment**:
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # Linux/Mac
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the application**:
   ```bash
   python run.py
   ```
   
   Or directly with Streamlit:
   ```bash
   streamlit run streamlit_main.py
   ```

5. **Access the app**:
   Open browser at `http://localhost:8501`

## Usage Guide

### Tab 1: Spread Analysis
- **Select Symbols**: Choose 2 cryptos from sidebar dropdown
- **View Metrics**: Hedge ratio, R², current z-score, correlation, trading signal
- **Chart**: 3-row subplot showing:
  - Spread with Bollinger bands and entry/exit markers
  - Z-score with threshold lines
  - Price series for both symbols
- **What-If Sliders**: Test scenarios (correlation ±%, volatility multiplier, hedge ratio adjustment)

### Tab 2: Strategy Signals
- **Indicator Dashboard**: RSI status, MACD crossover, Bollinger position
- **Combined Chart**: 3-row visualization with price, RSI, MACD

### Tab 3: Statistical Tests
- **ADF Tests**: Side-by-side stationarity tests for both symbols
- **Cointegration Test**: Johansen test with trace/eigenvalue statistics

### Tab 4: Backtesting
- **Select Strategy**: Z-Score, RSI, MACD, or Multi-Strategy
- **Set Capital**: Initial backtest capital
- **Run Backtest**: Click button to execute
- **View Results**: Performance metrics, equity curve, trade log

### Tab 5: Alerts
- **Configure**: Enable/disable alert types (z-score, RSI, MACD)
- **Monitor**: Active alerts with severity colors (red=high, yellow=medium, blue=low)
- **Clear**: Remove old alerts

### Tab 6: System
- **Connection Status**: WebSocket health, active symbols
- **Database Stats**: OHLC record counts
- **Recent Data**: Latest tick data table
- **Export**: Download raw data and analytics (CSV, JSON)

## Project Structure

```
F:\Gemscap_Quant_Project\
├── streamlit_main.py          # Unified Streamlit app (6 tabs)
├── run.py                     # Launcher script
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── .venv\                     # Virtual environment
├── data\                      # SQLite database
│   └── market_data.db
├── logs\                      # Error logs (if any)
├── src\
│   ├── __init__.py
│   ├── core\
│   │   ├── __init__.py
│   │   ├── data_manager.py    # WebSocket + in-memory + SQLite
│   │   └── strategy_engine.py # Spread, signals, alerts
│   └── analytics\
│       ├── __init__.py
│       ├── indicators.py      # RSI, MACD, Bollinger, etc.
│       ├── backtester.py      # Strategy backtesting
│       └── statistical.py     # OLS, ADF, cointegration
└── tools\                     # Debugging utilities
    └── format_spread_error.py
```

## Configuration

### Strategy Settings (Sidebar)
- **Lookback Window**: 5-60 minutes (default 30)
- **Z-Score Entry Threshold**: 1.0-3.0 (default 2.0)
- **Z-Score Exit Threshold**: 0.0-1.0 (default 0.5)
- **RSI Oversold**: 20-40 (default 30)
- **RSI Overbought**: 60-80 (default 70)

### Data Retention (In-Memory)
- Ticks: 10,000 per symbol (~5-10 minutes at high frequency)
- 1s OHLC: 3,600 bars (1 hour)
- 1m OHLC: 1,440 bars (24 hours)
- 5m OHLC: 288 bars (24 hours)

### Database Persistence
- 1m OHLC bars saved to SQLite (`data/market_data.db`)
- Survives app restarts
- Can be queried for historical analysis

## Troubleshooting

### WebSocket Won't Connect
- Check internet connection
- Verify Binance API is accessible (no VPN blocking)
- Wait 10-20 seconds for initial connection
- Check System tab for connection status

### No Data Showing
- Ensure WebSocket is connected (System tab)
- Wait 30-60 seconds for data accumulation
- Check if selected symbols have recent data
- Look for errors in terminal output

### Import Errors
- Verify all dependencies installed: `pip list`
- Reinstall if needed: `pip install -r requirements.txt --force-reinstall`
- Check Python version: `python --version` (need 3.9+)

### Backtests Fail
- Need sufficient data (at least 100-200 bars)
- Try increasing lookback window in sidebar
- Check data quality in System tab

## Performance Tips

1. **Data Accumulation**: Let app run 2-3 minutes before intensive analysis
2. **Symbol Selection**: Start with high-liquidity pairs (BTC/ETH)
3. **Lookback Window**: Longer = more data but slower calculations
4. **Auto-Refresh**: Disable when not actively monitoring to save CPU

## Export Formats

### CSV Export
- Raw OHLC data for both symbols
- Includes open, high, low, close, volume

### JSON Export (comprehensive)
- OHLC data
- Spread analysis (z-scores, Bollinger bands)
- Statistical tests (OLS, ADF, correlation)
- Strategy signals
- Alert history

### Chart Export (optional)
- Uncomment `kaleido` in requirements.txt
- Right-click charts → Save as PNG/SVG

## Changelog

### v2.0.0 (Current - Major Refactor)
- ✅ Removed Redis dependency (simplified architecture)
- ✅ Unified Streamlit-only app (removed separate FastAPI)
- ✅ Expanded from 3 to 13 crypto symbols
- ✅ Implemented RSI, MACD, Bollinger Bands strategies
- ✅ Added backtesting engine with 4 strategy types
- ✅ Added what-if analysis sliders
- ✅ Enhanced visualizations (entry/exit markers, Bollinger bands overlay)
- ✅ Improved alert system with severity levels
- ✅ Fixed ADF frontend display (Tab 3)
- ✅ One-click export functionality

### v1.0.0 (Original)
- Real-time tick ingestion (3 symbols)
- Basic spread analysis
- FastAPI + Streamlit split architecture
- Redis-based data storage

## Future Enhancements (Optional)

- [ ] Kalman filter for dynamic hedge ratio estimation
- [ ] Robust regression options (Huber, Theil-Sen)
- [ ] Liquidity heatmap visualization
- [ ] Cross-product correlation matrix
- [ ] Microstructure analytics (order flow, tape reading)
- [ ] More strategy types (momentum, pairs rotation)
- [ ] Multi-timeframe backtesting

## License

Proprietary - GEMSCAP Quantitative Trading Project

## Support

For issues or questions, check:
1. Terminal output for error messages
2. `logs/` directory for error logs
3. System tab in app for connection/data status

---

**Built with:** Python 3.11, Streamlit, Plotly, Binance WebSocket API
