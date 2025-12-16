# GEMSCAP Quantitative Trading System - Quick Start Guide

## 🚀 Launch in 3 Steps

### Step 1: Verify Setup
```bash
cd F:\Gemscap_Quant_Project
python check_setup.py
```

Expected output: `✓ ALL CHECKS PASSED - Ready to run!`

### Step 2: Launch Application
```bash
python run.py
```

Or directly with Streamlit:
```bash
streamlit run streamlit_main.py
```

### Step 3: Open Browser
Navigate to: **http://localhost:8501**

---

## 📊 First Use Walkthrough

### 1. Wait for Data (30-60 seconds)
- App starts → WebSocket connects → Data accumulates
- Check **System** tab (Tab 6) for connection status
- Wait until you see "✓ Connected" and record counts > 0

### 2. Explore Spread Analysis (Tab 1)
1. **Select Symbols**: Use sidebar dropdowns
   - Example: Symbol 1 = BTCUSDT, Symbol 2 = ETHUSDT
2. **View Metrics**: See hedge ratio, R², z-score, correlation, signal
3. **Interactive Chart**: Zoom, pan, hover for details
   - Top subplot: Spread with Bollinger bands + entry/exit markers
   - Middle subplot: Z-score with threshold lines
   - Bottom subplot: Both symbol prices
4. **What-If Sliders**: Test scenarios
   - "Correlation change %" → See impact on z-score
   - "Volatility multiplier" → Adjust Bollinger bands
   - "Hedge ratio adjustment %" → Modify hedge ratio

### 3. Check Strategy Signals (Tab 2)
- **RSI**: Oversold (<30) = long signal, Overbought (>70) = short signal
- **MACD**: Bullish cross = long, Bearish cross = short
- **Bollinger**: Price position relative to bands
- **Combined Chart**: All indicators visualized together

### 4. Run Statistical Tests (Tab 3)
- **ADF Tests**: Check if symbols are stationary (p-value < 0.05)
- **Cointegration**: Johansen test for pair relationship
- Side-by-side display for easy comparison

### 5. Backtest Strategies (Tab 4)
1. **Select Strategy**: Z-Score / RSI / MACD / Multi-Strategy
2. **Set Capital**: Initial capital (default $100,000)
3. **Click "Run Backtest"**
4. **View Results**:
   - Total Return %
   - Sharpe Ratio
   - Max Drawdown %
   - Win Rate %
   - Equity Curve Chart
   - Trade History Table

### 6. Monitor Alerts (Tab 5)
- **Enable Alerts**: Check boxes for desired alert types
- **View Active Alerts**: Color-coded by severity
  - 🔴 High (red)
  - 🟡 Medium (yellow)
  - 🔵 Low (blue)
- **Clear Alerts**: Remove old/resolved alerts

### 7. System Status (Tab 6)
- **Connection**: WebSocket health check
- **Database**: Record counts per symbol
- **Memory**: CPU and RAM usage
- **Recent Data**: Latest tick data preview
- **Export**: Download data and analytics

---

## 🎯 Common Workflows

### Workflow 1: Find Cointegrated Pairs
1. Go to **Tab 1** (Spread Analysis)
2. Try different symbol combinations in sidebar
3. Look for:
   - Correlation > 0.7
   - R² > 0.6
   - ADF test p-value < 0.05 (Tab 3)
4. Good pairs: BTC/ETH, ETH/BNB, SOL/AVAX

### Workflow 2: Backtest a Strategy
1. Go to **Tab 4** (Backtesting)
2. Select strategy (try "Z-Score" first)
3. Use sidebar to adjust parameters:
   - Entry threshold: 2.0
   - Exit threshold: 0.5
4. Click "Run Backtest"
5. Analyze results:
   - Sharpe > 1.0 = good
   - Max drawdown < 20% = acceptable
   - Win rate > 50% = positive edge

### Workflow 3: Set Up Alerts
1. Go to **Tab 5** (Alerts)
2. Enable desired alerts:
   - Z-Score > 2.0
   - RSI Extremes
   - MACD Crossovers
3. Monitor throughout trading session
4. Clear alerts after reviewing

### Workflow 4: Export Data
1. Go to **System** tab
2. Click "Export Data" button in sidebar
3. Files downloaded:
   - Raw OHLC: CSV format
   - Full analytics: JSON format
4. Use for:
   - External analysis
   - Record keeping
   - Sharing with team

---

## ⚙️ Configuration Tips

### Optimal Settings for Day Trading
```
Sidebar Settings:
  Lookback Window: 15 minutes
  Z-Score Entry: 2.0
  Z-Score Exit: 0.5
  RSI Oversold: 30
  RSI Overbought: 70
```

### Optimal Settings for Swing Trading
```
Sidebar Settings:
  Lookback Window: 60 minutes
  Z-Score Entry: 2.5
  Z-Score Exit: 1.0
  RSI Oversold: 25
  RSI Overbought: 75
```

### Performance Optimization
- **Disable Auto-Refresh**: Uncheck box at bottom when not monitoring
- **Reduce Lookback Window**: 5-15 min for faster calculations
- **Limit Symbols**: Focus on 2-3 pairs at a time

---

## 🐛 Troubleshooting

### Problem: "WebSocket not connected"
**Solutions:**
1. Check internet connection
2. Wait 10-20 seconds for initial connection
3. Restart app: Ctrl+C in terminal, then `python run.py`
4. Check if Binance API is accessible (no VPN blocking)

### Problem: "No data showing in charts"
**Solutions:**
1. Wait 30-60 seconds for data accumulation
2. Check System tab → should show records > 0
3. Try different symbol combinations
4. Increase lookback window in sidebar

### Problem: "Backtest fails / no results"
**Solutions:**
1. Ensure sufficient data (need 100-200 bars minimum)
2. Wait longer for data accumulation (2-3 minutes)
3. Try different strategy (Z-Score most robust)
4. Check data quality in System tab

### Problem: "Import errors on startup"
**Solutions:**
1. Run `python check_setup.py` to verify setup
2. Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`
3. Check Python version: `python --version` (need 3.9+)
4. Activate virtual environment: `.venv\Scripts\activate`

### Problem: "Charts not interactive"
**Solutions:**
1. Click on chart area to activate
2. Use mouse wheel to zoom
3. Click and drag to pan
4. Hover over data points for tooltips
5. Check Plotly is installed: `pip list | findstr plotly`

---

## 📈 Understanding the Metrics

### Spread Analysis Metrics
- **Hedge Ratio**: Optimal β in `spread = y - β*x`
- **R²**: Goodness of fit (0-1, higher = better)
- **Z-Score**: Standard deviations from mean spread
- **Correlation**: Linear relationship (-1 to 1)
- **Signal**: Current trading recommendation

### Backtest Metrics
- **Total Return**: Cumulative % gain/loss
- **Sharpe Ratio**: Risk-adjusted return (>1 good, >2 excellent)
- **Max Drawdown**: Largest peak-to-trough decline
- **Win Rate**: % of profitable trades (>50% = edge)

### Indicator Interpretations
- **RSI < 30**: Oversold (potential buy)
- **RSI > 70**: Overbought (potential sell)
- **MACD Bullish Cross**: MACD line crosses above signal (long)
- **MACD Bearish Cross**: MACD line crosses below signal (short)
- **Price < Lower Bollinger**: Potentially oversold
- **Price > Upper Bollinger**: Potentially overbought

---

## 💡 Pro Tips

1. **Let Data Accumulate**: Don't trade on first 2-3 minutes of data
2. **Check Cointegration**: Use Tab 3 before committing to a pair
3. **Compare Strategies**: Run multiple backtests in Tab 4
4. **Monitor Correlation**: If correlation breaks down, exit pair
5. **Use What-If Sliders**: Stress-test your assumptions
6. **Export Regularly**: Save data for post-session analysis
7. **Watch Liquidity**: Focus on high-volume pairs (BTC, ETH, BNB)
8. **Check Spread Stability**: Stable spread = better mean reversion

---

## 📚 Next Steps

### Learn More
1. Read [README_v2.md](README_v2.md) for full feature list
2. Review [ARCHITECTURE.md](ARCHITECTURE.md) for system design
3. Check [requirements.txt](requirements.txt) for dependencies

### Customize
1. Edit `src/core/data_manager.py` to add/remove symbols
2. Modify `src/core/strategy_engine.py` for custom strategies
3. Add indicators in `src/analytics/indicators.py`

### Advanced Usage
1. Implement Kalman filter for dynamic hedge ratios
2. Add robust regression options (Huber, Theil-Sen)
3. Create liquidity heatmap visualization
4. Build cross-product correlation matrix
5. Integrate order execution (paper trading first!)

---

## 🆘 Support

If you encounter issues:
1. Check terminal output for error messages
2. Run `python check_setup.py` to verify installation
3. Review logs in `logs/` directory (if any)
4. Check System tab for connection/data status
5. Restart app as last resort

---

**Ready to start trading?** Run `python run.py` and happy analyzing! 🚀📊
