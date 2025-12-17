# GEMSCAP Quant Project

## 📋 Overview

A fully functional end-to-end quantitative analytics system for pairs trading with real-time data ingestion, statistical analysis, and interactive visualization.

### ✨ Key Features

- ✅ Real-time tick data ingestion from Binance WebSocket
- ✅ Dual storage: SQLite (persistent) + Redis (live cache)
- ✅ OHLC sampling at 1s, 1m, 5m intervals
- ✅ Advanced analytics: OLS regression, spread analysis, z-score, ADF test, Kalman filter
- ✅ Real-time interactive Streamlit dashboard
- ✅ User-defined alert system
- ✅ REST API + WebSocket streaming
- ✅ Comprehensive debug panels
- ✅ CSV data export

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Binance WebSocket                    │
└──────────────────────┬──────────────────────────────────┘
                       │ Real-time ticks
                       ↓
┌─────────────────────────────────────────────────────────┐
│              Data Processor (Redis Pub/Sub)              │
└──────┬──────────────────────────────────────────────────┘
       │                                            │
       ↓                                            ↓
┌─────────────────┐                      ┌─────────────────┐
│  Redis Cache    │                      │ SQLite Database │
│  (Live data)    │                      │  (Persistent)   │
└────────┬────────┘                      └────────┬────────┘
         │                                        │
         └─────────────────┬──────────────────────┘
                           ↓
         ┌─────────────────────────────────────┐
         │      Analytics Engine               │
         │  • OLS Regression                   │
         │  • Spread & Z-Score                 │
         │  • Kalman Filter                    │
         │  • ADF Test, Correlation            │
         └─────────┬───────────────────────────┘
                   │
      ┌────────────┴──────────────┐
      ↓                           ↓
┌─────────────┐          ┌───────────────────┐
│  FastAPI    │          │ Streamlit         │
│  REST API   │          │ Dashboard         │
│  + WebSocket│          │ (Interactive UI)  │
└─────────────┘          └───────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Redis server running on localhost:6379
- Internet connection (for Binance WebSocket)

### Installation

```powershell
# Clone or navigate to project directory
cd f:\Gemscap_Quant_Project

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the System

**Single-command dashboard (recommended):**

```powershell
python run.py
```

This launches the Streamlit dashboard defined in `streamlit_main.py`.

**Optional: Run API server (if needed):**

```powershell
python app.py
```

**Option: Test Individual Components**

```powershell
# Test configuration
python config.py

# Test WebSocket client (10 seconds)
python src/ingestion/websocket_client.py

# Test analytics
python src/analytics/statistical.py
python src/analytics/spread_analysis.py
python src/analytics/kalman_filter.py

# Test database
python src/storage/database.py
```

### Access Points

- **API Server:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Streamlit Dashboard:** http://localhost:8501
- **WebSocket Stream:** ws://localhost:8000/ws/live

## 📊 Using the Dashboard

### Tabs Overview

1. **� Spread Analysis**: OLS/Kalman hedge ratio, spread, z-score, Bollinger Bands, what-if scenarios, trading signals
2. **🎯 Strategy Signals**: RSI, MACD, Bollinger Bands indicators with visual signals
3. **📊 Statistical Tests**: ADF stationarity tests for both symbols, cointegration test with residual analysis
4. **🔍 Backtesting**: Strategy backtesting (z-score, RSI, MACD, multi-strategy) with equity curves and performance metrics
5. **🔔 Alerts**: Alert management, history, and custom threshold configuration
6. **⚙️ System**: Connection status, data diagnostics, database stats, JSON export
7. **🔎 Quick Compare**: Side-by-side price and volume comparison with tick fallback
8. **🧮 Kalman & Robust Regression**: Dynamic hedge estimation, OLS vs Huber vs Theil-Sen comparison, outlier detection
9. **💧 Liquidity & Heatmap**: Volume profile with POC, 2D liquidity heatmap (time × price), value area identification
10. **🔬 Microstructure**: Order flow classification (buy/sell pressure), VWAP deviation, trade intensity, effective spread
11. **🔗 Correlation Matrix**: Multi-asset correlation heatmap, pair rankings, best/worst correlated pairs
12. **📋 Time-Series Stats Table**: Comprehensive table with all features at each timestamp, CSV/JSON export with column selection

### Dashboard Controls (Sidebar)

- **Symbol Selection**: Choose trading pairs
- **Interval**: Select sampling interval (1s/5s/10s/1m/5m)
- **Lookback**: Adjust time window (1-60 minutes)
- **Z-Score Threshold**: Set entry/exit thresholds for mean-reversion
- **RSI Levels**: Configure overbought/oversold levels
- **Apply Changes**: Commit configuration updates
- **Auto-refresh**: Enable/disable periodic dashboard updates (5s default)

## 🔍 API Endpoints

### Core Endpoints

- `GET /` - Service status
- `GET /health` - Component health check
- `GET /symbols` - Available symbols

### Data Endpoints

- `GET /ohlc/{symbol}?interval=1m&limit=100` - OHLC data
- `GET /ticks/{symbol}?limit=100` - Recent ticks

### Analytics Endpoints

- `GET /analytics/spread?symbol1=BTCUSDT&symbol2=ETHUSDT` - Spread analysis
- `GET /analytics/correlation?symbol1=BTCUSDT&symbol2=ETHUSDT&window=50` - Correlation
- `GET /analytics/adf?symbol=BTCUSDT` - ADF stationarity test

### Export

- `GET /export/csv?symbol=BTCUSDT&interval=1m` - Download CSV

### Debug Endpoints

- `GET /debug/system` - Full system status
- `GET /debug/redis/{symbol}` - Redis data for symbol
- `GET /debug/db/tables` - Database table counts
- `GET /debug/endpoints` - List all endpoints

## 📈 Analytics Methodology

### Regression Methods

**OLS Regression** - Standard linear regression:
```
price2 = alpha + beta * price1
```
- **Hedge Ratio (beta)**: Number of units of asset1 to hedge asset2
- **R-squared**: Goodness of fit (0-1, higher is better)

**Huber Regression** - Robust M-estimator less sensitive to outliers:
- Detects and reports outlier percentage
- Better for real-world noisy data

**Theil-Sen Regression** - Median-based, highly resistant to outliers:
- Uses median of pairwise slopes
- Most robust against extreme values

**Kalman Filter** - Dynamic hedge ratio estimation:
- Adapts to time-varying relationships
- Provides confidence intervals
- Updates online with each new observation

### Spread Analysis

```
Spread = price2 - (alpha + hedge_ratio * price1)
Z-Score = (spread - mean) / std_dev
```

### Trading Signals

- **Z-score > 2.0**: Short spread (price2 overvalued relative to price1)
- **Z-score < -2.0**: Long spread (price2 undervalued relative to price1)
- **|Z-score| < 0.5**: Exit position (mean reversion complete)

### Microstructure Metrics

**Order Flow Imbalance (OFI)**:
```
OFI = (Buy Volume - Sell Volume) / Total Volume
```

**VWAP (Volume-Weighted Average Price)**:
```
VWAP = Σ(Price × Volume) / Σ(Volume)
```

**Effective Spread**:
```
Effective Spread = 2 × |Trade Price - Mid Price|
```

### Liquidity Metrics

**Point of Control (POC)**: Price level with highest traded volume

**Value Area**: Price range containing 70% of traded volume

**Volume Profile**: Distribution of volume across price levels

### Statistical Tests

**ADF Test** - Tests for stationarity (requirement for mean reversion):
- **p-value < 0.05**: Stationary (good for pairs trading)
- **p-value >= 0.05**: Non-stationary (avoid pairs trading)

**Cointegration Test** - Tests if two assets have long-term equilibrium:
- Runs OLS regression
- Performs ADF test on residuals (spread)
- If spread is stationary → assets are cointegrated

## 🚨 Alert System

### Default Alert Rules

1. **High Z-Score**: Triggers when |z-score| > 2.0
2. **Large Spread Deviation**: Triggers when spread deviates > 0.5% from mean
3. **Price Spike**: Triggers when price changes > 2%
4. **Volume Spike**: Triggers when volume > 3x average

### Adding Custom Rules

```python
from src.alerting.alert_rules import create_custom_rule

def custom_condition(data, threshold):
    return data['custom_metric'] > threshold

rule = create_custom_rule(
    name="Custom Alert",
    condition_func=custom_condition,
    threshold=1.5,
    message="Custom alert triggered"
)

alert_manager.add_rule(rule)
```

## 🐛 Debugging Guide

### Check Component Status

```powershell
# View logs
cat gemscap_quant.log

# Check system debug
curl http://localhost:8000/debug/system

# Check Redis data
curl http://localhost:8000/debug/redis/BTCUSDT

# Check database
curl http://localhost:8000/debug/db/tables
```

### Common Issues

**Redis Connection Error**
```powershell
# Start Redis server
redis-server
```

**No Data in Dashboard**
- Wait 30-60 seconds for data collection
- Check WebSocket connection in debug tab
- Verify Binance WebSocket is accessible

**Import Errors**
```powershell
pip install -r requirements.txt --upgrade
```

## 📦 Project Structure

```
GEMSCAP_QUANT_PROJECT/
├── app.py                      # FastAPI application (optional)
├── run.py                      # Single-command launcher for Streamlit
├── streamlit_main.py           # Streamlit dashboard (12 tabs)
├── config.py                   # Configuration & logging
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── data/
│   └── tick_data.db           # SQLite database
├── src/
│   ├── ingestion/
│   │   ├── websocket_client.py   # Binance WebSocket
│   │   └── data_processor.py     # Data processing
│   ├── storage/
│   │   ├── redis_manager.py      # Redis operations
│   │   ├── database.py           # SQLite operations
│   │   └── data_sampler.py       # OHLC sampling
│   ├── analytics/
│   │   ├── statistical.py        # OLS, ADF, correlation
│   │   ├── spread_analysis.py    # Spread & z-score
│   │   ├── kalman_filter.py      # Dynamic hedge ratio
│   │   └── advanced_metrics.py   # Liquidity, momentum
│   ├── visualization/
│   │   ├── chart_builder.py      # Plotly charts
│   │   └── dashboard_components.py # Streamlit components
│   ├── alerting/
│   │   ├── alert_manager.py      # Alert system
│   │   └── alert_rules.py        # Alert conditions
│   └── api/
│       ├── endpoints.py          # REST endpoints
│       └── websocket_handler.py  # WebSocket streaming
├── tests/
│   ├── test_analytics.py
│   └── test_ingestion.py
└── notebooks/
    └── analysis_examples.ipynb
```

## 🧪 Testing

```powershell
# Run all tests
pytest

# Run specific test
pytest tests/test_analytics.py -v

# Test with coverage
pytest --cov=src tests/
```

## 📝 Configuration

Edit `config.py` to customize:

- **Symbols**: Trading pairs to track
- **Intervals**: Sampling intervals
- **Thresholds**: Alert thresholds
- **Database paths**: SQLite/Redis URLs
- **API ports**: FastAPI/Streamlit ports

## 🎓 Learning Resources

- **Pairs Trading**: https://en.wikipedia.org/wiki/Pairs_trade
- **OLS Regression**: Statsmodels documentation
- **Kalman Filters**: https://filterpy.readthedocs.io/
- **ADF Test**: Understanding stationarity

## 📦 Minimal Exam Package

For examiner-friendly execution, include only essential files:

- `run.py` — single-command launcher
- `streamlit_main.py` — Streamlit UI
- `src/` — core modules actually used by the UI (analytics, core)
- `requirements.txt` — dependencies
- `data/` — SQLite DB (if pre-seeded) and optional CSV template
- `README.md` — setup, dependencies, methodology, analytics explanation

Exclude large or unused folders (e.g., `tests/`, `notebooks/`, heavy logs) from the zip unless explicitly requested.

## 🤝 Contributing

This is a template/learning project. Feel free to:
- Add new analytics methods
- Improve UI/UX
- Add more data sources
- Implement backtesting
- Add machine learning models



## 📄 License

MIT License - feel free to use and modify

## 🙏 Acknowledgments

- Built with FastAPI, Streamlit, Plotly
- Data from Binance WebSocket API
- Statistical analysis powered by Statsmodels, Scipy, NumPy
- This project was developed with assistance from AI (ChatGPT/Claude)

---
