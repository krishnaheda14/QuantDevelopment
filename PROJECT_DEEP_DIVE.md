# GEMSCAP Quant Project: Comprehensive Technical Deep Dive

## Table of Contents
1. [Introduction](#introduction)
2. [Technology Stack & Architecture Decisions](#technology-stack--architecture-decisions)
3. [Data Flow & Ingestion Pipeline](#data-flow--ingestion-pipeline)
4. [Tab-by-Tab Analysis](#tab-by-tab-analysis)
5. [Mathematical Foundations & Statistical Methods](#mathematical-foundations--statistical-methods)
6. [Interview Questions & Answers](#interview-questions--answers)

---

## Introduction

The GEMSCAP Quant Project is a real-time quantitative trading analytics platform focused on cryptocurrency pairs trading. Built in approximately one day, it demonstrates end-to-end capabilities from live data ingestion to advanced statistical analysis and interactive visualization. The system processes live tick data from Binance WebSocket, aggregates it into OHLC bars, and applies sophisticated quantitative methods to identify trading opportunities.

**Core Philosophy**: Pairs trading exploits mean-reversion in correlated assets. If two assets typically move together but temporarily diverge, we can profit by betting on convergence.

---

## Technology Stack & Architecture Decisions

### Why Python?
- **Why Python**: Dominant in quantitative finance and data science. Rich ecosystem of libraries (pandas, numpy, statsmodels, scikit-learn). Excellent for rapid prototyping and algorithmic trading.
- **Why not Java/C++**: Python's simplicity and library ecosystem outweighs performance concerns for this real-time but not ultra-low-latency application. Java would add unnecessary complexity for a prototype.
- **Why not R**: While R excels in statistical analysis, Python's general-purpose nature and web framework integration (Streamlit) make it superior for full-stack applications.

### Frontend: Streamlit
- **Why Streamlit**: Rapid UI development for data science apps. No HTML/CSS/JS required. Perfect for dashboards with plots and controls. Hot-reload during development.
- **Why not Dash/Flask**: Streamlit is more declarative and data-focused. Dash requires more web development knowledge; Flask would need separate frontend work.
- **Why not React/Vue**: Overkill for a quantitative dashboard. Streamlit handles the heavy lifting of data visualization and interactivity.

### Backend: SQLite + In-Memory Structures
- **Why SQLite**: Lightweight, file-based database. No server setup required. ACID compliance for data integrity. Perfect for local development and deployment.
- **Why not PostgreSQL/MySQL**: Too heavy for a single-user application. SQLite scales sufficiently for this use case.
- **Why not Redis**: While Redis excels at high-frequency data, SQLite provides persistence and relational querying capabilities needed for OHLC aggregation.

### Data Processing: Pandas + NumPy
- **Why Pandas**: Time-series data manipulation, resampling, and analysis. Industry standard for quantitative work.
- **Why NumPy**: Efficient numerical computations, especially for statistical calculations.
- **Why not Pure NumPy**: Pandas provides higher-level abstractions for time-series operations.

### Statistical Libraries
- **Statsmodels**: Comprehensive statistical modeling (OLS, ADF tests, cointegration).
- **SciPy**: Optimization and additional statistical functions.
- **Scikit-learn**: Machine learning algorithms (robust regression).
- **PyKalman**: Specialized Kalman filtering for dynamic hedge ratios.

### WebSocket: websocket-client
- **Why websocket-client**: Simple, synchronous WebSocket library. Easy integration with asyncio for concurrent operations.
- **Why not aiohttp**: websocket-client is more straightforward for this use case.

### Why This Architecture?
- **Modular Design**: Separates concerns (ingestion, storage, analytics, UI) for maintainability.
- **Real-time Processing**: WebSocket → In-memory deques → SQLite persistence → Analytics → UI.
- **Scalability**: Can be extended to multiple data sources, more symbols, or distributed processing.
- **Cost-Effective**: No cloud dependencies; runs locally.

---

## Data Flow & Ingestion Pipeline

### WebSocket Data Source
**What Data Comes In?**
- **Source**: Binance WebSocket API (wss://stream.binance.com:9443/ws)
- **Data Format**: JSON messages containing trade ticks
- **Sample Message**:
```json
{
  "e": "trade",           // Event type
  "E": 1672515782136,     // Event time
  "s": "BTCUSDT",         // Symbol
  "t": 12345,             // Trade ID
  "p": "87654.32",        // Price
  "q": "0.001",           // Quantity
  "b": 88,                // Buyer order ID
  "a": 50,                // Seller order ID
  "T": 1672515782136,     // Trade time
  "m": true,              // Is buyer market maker
  "M": true               // Ignore
}
```

**Key Fields Extracted**:
- `timestamp`: Trade time (milliseconds since epoch)
- `price`: Trade price as float
- `quantity`: Trade volume as float
- `symbol`: Trading pair (e.g., "BTCUSDT")

### Ingestion Flow
1. **WebSocket Connection**: Connects to Binance streams for configured symbols (BTCUSDT, ETHUSDT, etc.)
2. **Raw Tick Storage**: Each tick stored in in-memory deque (DataManager.ticks[symbol])
3. **OHLC Aggregation**: 
   - 1-second bars: Resample ticks using pandas
   - 1-minute bars: Aggregate from 1s bars
   - 5-minute bars: Aggregate from 1m bars
4. **Persistence**: OHLC bars written to SQLite tables (ohlc_1m, ohlc_5m)
5. **Analytics Pipeline**: Bars fed to statistical modules for real-time analysis

**Why This Flow?**
- **Real-time**: Immediate processing of live market data
- **Efficient**: In-memory for speed, SQLite for persistence
- **Scalable**: Deques limit memory usage; can be extended to Redis for distributed setups

---

## Tab-by-Tab Analysis

### Tab 1: Spread Analysis
**What It Shows**: OLS regression hedge ratio, spread calculation, z-score, and trading signals.

**Mathematics**:
- **OLS Regression**: `price2 = α + β × price1`
  - β (hedge ratio): How much of asset2 to hold per unit of asset1
  - R²: Goodness of fit (0-1)
- **Spread**: `spread = price2 - (α + β × price1)`
- **Z-Score**: `z = (spread - mean) / std_dev`
- **Signal Logic**: 
  - Z > 2.0: Short spread (price2 overvalued)
  - Z < -2.0: Long spread (price2 undervalued)

**How to Use**: Identifies mean-reversion opportunities. Example: BTC and ETH typically correlate. If BTC rises 5% but ETH only 2%, z-score increases → short BTC, long ETH.

**Analogy**: Like a rubber band between two correlated stocks. When stretched too far, it snaps back.

### Tab 2: Strategy Signals
**What It Shows**: Technical indicators (RSI, MACD, Bollinger Bands) with visual signals.

**Mathematics**:
- **RSI**: `RSI = 100 - (100 / (1 + RS))` where `RS = Average Gain / Average Loss`
- **MACD**: `MACD = EMA12 - EMA26`, Signal = EMA9 of MACD
- **Bollinger Bands**: `Upper = SMA + 2×STD`, `Lower = SMA - 2×STD`

**How to Use**: Confirms momentum or reversal signals. Example: RSI > 70 indicates overbought (sell signal).

**Analogy**: Technical indicators are like gauges on a car's dashboard, showing engine performance.

### Tab 3: Statistical Tests
**What It Shows**: ADF stationarity tests and cointegration analysis.

**Mathematics**:
- **ADF Test**: Tests for unit root in time series. Null: non-stationary.
  - p-value < 0.05: Stationary (mean-reverting)
- **Cointegration**: Tests if spread between assets is stationary.
  - Engle-Granger: OLS on assets, then ADF on residuals.

**How to Use**: Validates pairs trading assumptions. Non-stationary assets can't be traded as pairs.

**Analogy**: Like checking if two dancers are in sync. Cointegration means they return to formation.

### Tab 4: Backtesting
**What It Shows**: Historical performance of trading strategies.

**Mathematics**:
- **Sharpe Ratio**: `(Return - Risk-free) / Volatility`
- **Max Drawdown**: Peak-to-trough decline
- **Win Rate**: Percentage of profitable trades

**How to Use**: Evaluates strategy effectiveness. Example: Z-score strategy with 60% win rate and 1.5 Sharpe ratio.

**Analogy**: Like reviewing game footage to improve strategy.

### Tab 5: Alerts
**What It Shows**: Customizable alert system for trading signals.

**Logic**: User-defined thresholds trigger notifications.

**How to Use**: Real-time monitoring without constant watching.

### Tab 6: System Status
**What It Shows**: Connection status, data diagnostics, database stats.

**How to Use**: Monitors system health and data flow.

### Tab 7: Quick Compare
**What It Shows**: Side-by-side price/volume charts with OHLC upload.

**How to Use**: Visual comparison of assets and historical data import.

### Tab 8: Kalman & Robust Regression
**What It Shows**: Dynamic hedge ratios and outlier-resistant regression.

**Mathematics**:
- **Kalman Filter**: State-space model for time-varying parameters.
- **Huber Regression**: Minimizes sum of ρ(r) where ρ is less sensitive to outliers.

**How to Use**: Adapts to changing market conditions.

**Analogy**: Kalman filter is like GPS correcting for noise.

### Tab 9: Liquidity & Heatmap
**What It Shows**: Volume profiles and 2D price-volume heatmaps.

**Mathematics**:
- **POC (Point of Control)**: Price level with maximum volume.
- **Value Area**: 70% of volume around POC.

**How to Use**: Identifies support/resistance levels.

**Analogy**: Like finding the busiest highway lanes.

### Tab 10: Microstructure
**What It Shows**: Order flow analysis and market impact metrics.

**Mathematics**:
- **Order Flow Imbalance**: `(Buy Volume - Sell Volume) / Total Volume`
- **VWAP Deviation**: `(Price - VWAP) / VWAP`

**How to Use**: Detects market manipulation or institutional activity.

### Tab 11: Correlation Matrix
**What It Shows**: Multi-asset correlation heatmap.

**Mathematics**: Pearson correlation coefficient.

**How to Use**: Finds correlated pairs for trading.

### Tab 12: Time-Series Stats Table
**What It Shows**: Comprehensive table with all metrics per timestamp.

**How to Use**: Detailed analysis and CSV export.

---

## Mathematical Foundations & Statistical Methods

### Time Series Analysis
- **Stationarity**: Constant mean, variance, autocovariance.
- **Unit Root Tests**: ADF tests for trend-stationarity.
- **Cointegration**: Long-run relationship between non-stationary series.

### Regression Techniques
- **OLS**: Minimizes sum of squared residuals.
- **Robust Regression**: Resistant to outliers (Huber, Theil-Sen).
- **Kalman Filtering**: Optimal estimation in noisy environments.

### Risk Metrics
- **Sharpe Ratio**: Risk-adjusted returns.
- **Value at Risk (VaR)**: Potential loss over time horizon.

### Trading Strategy Logic
- **Mean Reversion**: Assumes prices return to mean.
- **Momentum**: Assumes trends persist.
- **Pairs Trading**: Exploits relative mispricing.

---

## Interview Questions & Answers

### Q1: Why did you choose this tech stack?
A: Python for its quantitative libraries, Streamlit for rapid dashboard development, SQLite for lightweight persistence. This combination allows quick prototyping while maintaining production-quality code.

### Q2: Explain the data flow from WebSocket to UI.
A: WebSocket receives JSON trade ticks → parsed and stored in memory deques → aggregated into OHLC bars → persisted to SQLite → fed to analytics modules → displayed in Streamlit UI with real-time updates.

### Q3: What is pairs trading and why use it?
A: Pairs trading exploits mean-reversion in correlated assets. When two assets diverge unusually, bet on convergence. It's market-neutral, reducing directional risk.

### Q4: Explain OLS regression in pairs trading.
A: OLS finds the hedge ratio β where price2 = α + β × price1. The spread is price2 - (α + β × price1). We trade when spread deviates significantly from its mean.

### Q5: What is stationarity and why does it matter?
A: Stationarity means constant statistical properties over time. Non-stationary series can't be reliably predicted. Pairs trading requires the spread to be stationary for mean-reversion.

### Q6: How does Kalman filtering improve hedge ratios?
A: Kalman filter adapts hedge ratios in real-time, accounting for changing correlations. Unlike static OLS, it handles time-varying relationships.

### Q7: What challenges did you face in real-time data processing?
A: Handling high-frequency ticks, ensuring timestamp alignment, managing memory with deques, and maintaining UI responsiveness during live updates.

### Q8: How would you scale this system?
A: Add Redis for distributed caching, use async processing for multiple symbols, implement database sharding, and add load balancing for multiple users.

### Q9: Explain the difference between correlation and cointegration.
A: Correlation measures short-term linear relationship. Cointegration measures long-term equilibrium. Two assets can be correlated but not cointegrated, or vice versa.

### Q10: What would you improve if you had more time?
A: Add more assets, implement machine learning for signal prediction, create a trading execution layer, add comprehensive backtesting with transaction costs, and improve UI with more interactive charts.

---

This comprehensive guide covers the entire GEMSCAP Quant Project, from architecture decisions to mathematical foundations, designed to explain the system thoroughly for technical interviews and deep understanding.