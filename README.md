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

**Option 1: Run Everything (Recommended)**

```powershell
# Terminal 1: Start FastAPI backend
python app.py

# Terminal 2: Start Streamlit dashboard
streamlit run streamlit_app.py
```

**Option 2: Test Individual Components**

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

1. **📊 Price Charts**: Live candlestick and volume charts for selected symbols
2. **📈 Spread Analysis**: Spread, z-score, and trading signals for pairs
3. **🔗 Correlation**: Rolling correlation analysis
4. **📉 Statistics**: ADF stationarity tests
5. **🚨 Alerts**: Alert management and history
6. **🔧 Debug**: System health, component status, API testing

### Dashboard Controls (Sidebar)

- **Symbol Selection**: Choose trading pairs
- **Interval**: Select sampling interval (1s/1m/5m)
- **Rolling Window**: Adjust window for rolling statistics
- **Z-Score Threshold**: Set alert threshold
- **Auto-refresh**: Enable periodic dashboard updates

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

### OLS Regression

Computes hedge ratio between two assets:
```
price2 = alpha + beta * price1
```
- **Hedge Ratio (beta)**: Number of units of asset1 to hedge asset2
- **R-squared**: Goodness of fit

### Spread Analysis

```
Spread = price2 - (alpha + hedge_ratio * price1)
Z-Score = (spread - mean) / std_dev
```

### Trading Signals

- **Z-score > 2.0**: Short spread (price2 overvalued)
- **Z-score < -2.0**: Long spread (price2 undervalued)
- **|Z-score| < 0.5**: Exit position (mean reversion)

### Kalman Filter

Dynamically estimates time-varying hedge ratio using Bayesian filtering.

### ADF Test

Tests for stationarity (requirement for mean reversion):
- **p-value < 0.05**: Stationary (good for pairs trading)
- **p-value >= 0.05**: Non-stationary (avoid)

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
├── app.py                      # Main FastAPI application
├── streamlit_app.py            # Streamlit dashboard
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

## 🤝 Contributing

This is a template/learning project. Feel free to:
- Add new analytics methods
- Improve UI/UX
- Add more data sources
- Implement backtesting
- Add machine learning models

## ⚠️ Disclaimer

**This is for educational purposes only. Not financial advice.**

- Do not use real money without thorough testing
- Past performance ≠ future results
- Cryptocurrency markets are highly volatile
- Always do your own research

## 📄 License

MIT License - feel free to use and modify

## 🙏 Acknowledgments

- Built with FastAPI, Streamlit, Plotly
- Data from Binance WebSocket API
- Statistical analysis powered by Statsmodels, Scipy, NumPy
- This project was developed with assistance from AI (ChatGPT/Claude)

---

**Made with ❤️ for quant enthusiasts**
