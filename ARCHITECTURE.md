# GEMSCAP Quantitative Trading System v2.0 - Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     BROWSER (http://localhost:8501)                     │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                   Streamlit Web Application                       │ │
│  │                                                                   │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │ │
│  │  │  Spread  │ │ Strategy │ │   Stats  │ │ Backtest │ │ Alerts │ │ │
│  │  │ Analysis │ │ Signals  │ │  Tests   │ │          │ │        │ │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └────────┘ │ │
│  │       Tab 1        Tab 2        Tab 3        Tab 4       Tab 5   │ │
│  │                                                                   │ │
│  │  ┌─────────────────────────────────────────────────────────────┐ │ │
│  │  │                       Tab 6: System                         │ │ │
│  │  │  Connection Status | DB Stats | Recent Data | Export       │ │ │
│  │  └─────────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                          Sidebar Controls                         │ │
│  │  • Symbol Selection (13 cryptos)                                │ │
│  │  • Lookback Window (5-60 min)                                   │ │
│  │  • Strategy Settings (z-score, RSI thresholds)                  │ │
│  │  • Refresh & Export Buttons                                     │ │
│  └───────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↕
                        Streamlit Session State
                    (Persistent objects across reruns)
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                          APPLICATION LAYER                              │
│                                                                         │
│  ┌──────────────────────┐        ┌──────────────────────┐             │
│  │   DataManager        │        │  StrategyEngine      │             │
│  │                      │        │                      │             │
│  │  • WebSocket client  │───────▶│  • Spread calc       │             │
│  │  • In-memory deques  │        │  • Z-score & signals │             │
│  │  • SQLite persist    │        │  • Hedge ratio opt   │             │
│  │  • OHLC aggregation  │        │  • Position sizing   │             │
│  └──────────────────────┘        └──────────────────────┘             │
│           ↓                                                            │
│  ┌──────────────────────┐        ┌──────────────────────┐             │
│  │ TechnicalIndicators  │        │     Backtester       │             │
│  │                      │        │                      │             │
│  │  • RSI, MACD         │───────▶│  • Z-score strategy  │             │
│  │  • Bollinger Bands   │        │  • RSI strategy      │             │
│  │  • Stochastic        │        │  • MACD strategy     │             │
│  │  • ATR, OBV, VWAP    │        │  • Multi-strategy    │             │
│  └──────────────────────┘        └──────────────────────┘             │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │              StatisticalAnalytics                              │   │
│  │  • OLS regression (with polyfit/median fallbacks)              │   │
│  │  • ADF test (stationarity)                                     │   │
│  │  • Cointegration test (Johansen)                               │   │
│  └────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                    │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                   In-Memory Storage (deques)                     │  │
│  │                                                                  │  │
│  │  Per Symbol (13 cryptos):                                       │  │
│  │   • Ticks: 10,000 max    (~5-10 min high freq)                  │  │
│  │   • OHLC 1s: 3,600 bars  (1 hour)                              │  │
│  │   • OHLC 1m: 1,440 bars  (24 hours)                            │  │
│  │   • OHLC 5m: 288 bars    (24 hours)                            │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                    ↓                                    │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │               SQLite Database (data/market_data.db)              │  │
│  │                                                                  │  │
│  │  Tables:                                                         │  │
│  │   • ohlc_1m: Persistent 1-minute bars                           │  │
│  │   • analytics_cache: Cached calculation results                 │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↑
                    Background Thread (daemon)
                    asyncio event loop
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                       EXTERNAL DATA SOURCE                              │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │            Binance WebSocket API (Combined Streams)              │  │
│  │                                                                  │  │
│  │  Stream URL:                                                     │  │
│  │  wss://stream.binance.com:9443/stream?streams=                   │  │
│  │    btcusdt@trade/ethusdt@trade/bnbusdt@trade/...                │  │
│  │                                                                  │  │
│  │  Real-time Market Data (13 symbols):                             │  │
│  │   • BTC/USDT  • ETH/USDT  • BNB/USDT  • SOL/USDT                │  │
│  │   • ADA/USDT  • DOT/USDT  • MATIC/USDT • AVAX/USDT              │  │
│  │   • LINK/USDT • UNI/USDT  • ATOM/USDT  • LTC/USDT               │  │
│  │   • XRP/USDT                                                     │  │
│  │                                                                  │  │
│  │  Message Format:                                                 │  │
│  │    {"stream": "btcusdt@trade",                                   │  │
│  │     "data": {"p": "43521.50", "q": "0.015", "T": 1703001234567}}│  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
┌────────────┐
│  Binance   │
│ WebSocket  │
└─────┬──────┘
      │ Trade events @ ~100-1000 Hz
      ↓
┌─────────────────────────┐
│ WebSocket Handler       │
│ (_handle_message)       │
│  • Parse JSON           │
│  • Extract p, q, T      │
│  • Store in tick deque  │
└─────────┬───────────────┘
          │
          ↓
┌─────────────────────────────────────────────────┐
│ OHLC Aggregation (_aggregate_ticks)            │
│  • Check time windows: 1s, 1m, 5m              │
│  • Create bars: open, high, low, close, volume │
│  • Persist 1m bars to SQLite                   │
└─────────┬───────────────────────────────────────┘
          │
          ↓
┌─────────────────────────────────────────────────┐
│ In-Memory Storage (deques)                      │
│  • Fast access for recent data                  │
│  • Auto-rotation (maxlen)                       │
└─────────┬───────────────────────────────────────┘
          │
          ↓
┌─────────────────────────────────────────────────┐
│ Streamlit UI Requests                           │
│  • get_ohlc(symbol, interval, limit)            │
│  • Returns: DataFrame[timestamp, o, h, l, c, v] │
└─────────┬───────────────────────────────────────┘
          │
          ├──────────────────────────────────────┐
          │                                      │
          ↓                                      ↓
┌───────────────────────┐          ┌───────────────────────┐
│ StrategyEngine        │          │ TechnicalIndicators   │
│  • Spread = p2 - β*p1 │          │  • RSI(prices, 14)    │
│  • Z-score = (s-μ)/σ  │          │  • MACD(prices, ...)  │
│  • Bollinger = μ±2σ   │          │  • Bollinger(...)     │
│  • Signals: long/exit │          └───────────────────────┘
└───────────┬───────────┘
            │
            ↓
┌─────────────────────────────────────────────────┐
│ Backtester                                      │
│  • Simulate trades                              │
│  • Calculate equity curve                       │
│  • Metrics: Sharpe, drawdown, win rate          │
└─────────┬───────────────────────────────────────┘
          │
          ↓
┌─────────────────────────────────────────────────┐
│ Plotly Charts (Streamlit UI)                    │
│  • Spread + Bollinger bands                     │
│  • Z-score with thresholds                      │
│  • Price series                                 │
│  • RSI/MACD subplots                            │
│  • Equity curves                                │
└─────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. No Redis (Simplified Architecture)
- **Before**: FastAPI → Redis → Streamlit (3 processes)
- **After**: Streamlit → In-memory → SQLite (1 process)
- **Benefits**: 
  - Easier deployment (no Redis server)
  - Lower latency (no network hops)
  - Simpler debugging
  - Reduced dependencies

### 2. In-Memory Data Management
- **Storage**: `collections.deque` with `maxlen`
- **Auto-rotation**: Old data automatically discarded
- **Fast access**: O(1) append, O(1) access by index
- **Memory usage**: ~5-10 MB per symbol (controlled by maxlen)

### 3. Background WebSocket Thread
- **Pattern**: Daemon thread with asyncio event loop
- **Non-blocking**: UI remains responsive during data ingestion
- **Reconnection**: Automatic reconnect on connection drop
- **Shutdown**: Daemon threads automatically killed on app exit

### 4. SQLite as Backup
- **Use case**: Persistent storage for historical 1m bars
- **Write strategy**: Async writes on bar completion
- **Read strategy**: Load from SQLite if in-memory cache miss
- **Benefits**: Survives app restarts, queryable history

### 5. Session State Management
- **Streamlit pattern**: Objects stored in `st.session_state`
- **Persistence**: Survives Streamlit reruns (button clicks, slider changes)
- **Initialization**: Created once on first run (`if key not in st.session_state`)
- **Shared state**: All tabs access same manager instances

## Performance Characteristics

### Latency
- **WebSocket → In-memory**: ~1-5 ms
- **In-memory → UI**: ~10-50 ms
- **End-to-end (tick → display)**: ~50-100 ms

### Throughput
- **Ingest rate**: 1000+ ticks/second (13 symbols combined)
- **OHLC aggregation**: ~1 ms per interval
- **UI refresh**: 5-second default (configurable)

### Memory Usage
- **Base app**: ~100 MB (Streamlit + dependencies)
- **Per symbol data**: ~5 MB (10k ticks + OHLC bars)
- **Total (13 symbols)**: ~150-200 MB typical

### Scalability Limits
- **Symbols**: Tested up to 50 (memory limited)
- **Tick retention**: 10,000 per symbol (configurable)
- **Concurrent users**: 1 (single-user deployment)
- **For multi-user**: Need Redis/shared storage layer

## Technology Stack

| Layer          | Technology      | Purpose                          |
|----------------|-----------------|----------------------------------|
| Frontend       | Streamlit       | Web UI framework                 |
| Visualization  | Plotly          | Interactive charts               |
| Data Source    | Binance WS API  | Real-time market data            |
| Ingestion      | websockets lib  | WebSocket client                 |
| In-Memory      | collections.deque| Fast FIFO storage               |
| Persistence    | SQLite          | Historical data backup           |
| Computation    | NumPy/Pandas    | Array operations, time series    |
| Statistics     | Statsmodels     | OLS, ADF, cointegration          |
| Indicators     | Custom (NumPy)  | RSI, MACD, Bollinger, etc.       |
| Threading      | threading module| Background WebSocket             |
| Async IO       | asyncio         | WebSocket event loop             |

## Deployment Model

### Development
```bash
python run.py
# OR
streamlit run streamlit_main.py
```

### Production (Local)
- Same as development (single-user)
- No additional infrastructure needed
- Data persists in SQLite

### Production (Cloud) - Future
- Deploy to Streamlit Cloud / Heroku / AWS
- Need external storage (S3, RDS) for multi-user
- Add authentication if needed

## Security Considerations

- **API Keys**: Binance public WebSocket (no auth needed)
- **Data Privacy**: All data local (no external transmission)
- **Network**: Only outbound to Binance (wss://stream.binance.com)
- **File System**: Writes to local SQLite only

## Monitoring & Debugging

### System Tab
- WebSocket connection status
- Active symbols count
- Database record counts
- Memory usage (via psutil)
- Recent tick data preview

### Logs
- Terminal output (Streamlit logs)
- Error logs (if any): `logs/` directory
- Database: `data/market_data.db` (queryable)

### Debugging Tools
- `check_setup.py`: Verify dependencies
- `tools/format_spread_error.py`: Parse error logs
- Direct SQLite inspection: `sqlite3 data/market_data.db`

---

**Last Updated**: 2024 (v2.0 Architecture)  
**Maintainer**: GEMSCAP Quantitative Trading Team
