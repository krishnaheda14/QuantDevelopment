"""
GEMSCAP QUANT - Unified Streamlit Application
Real-time crypto pairs trading analytics with advanced strategies
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import asyncio
import time
from datetime import datetime, timedelta
from collections import deque
import json
import io
import threading

# Page config
st.set_page_config(
    page_title="GEMSCAP Quant Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/gemscap/quant',
        'Report a bug': None,
        'About': "GEMSCAP Quant Analytics v1.0 - Real-time crypto pairs trading system"
    }
)

# Compatibility helper: safe rerun across Streamlit versions
def safe_rerun():
    rerun_fn = getattr(st, "experimental_rerun", None)
    if callable(rerun_fn):
        return rerun_fn()
    try:
        from streamlit.runtime.scriptrunner.script_runner import RerunException
        raise RerunException()
    except Exception:
        st.session_state['_applied_toggle'] = not st.session_state.get('_applied_toggle', False)
        try:
            st.experimental_set_query_params(_applied=int(time.time()))
        except Exception:
            st.stop()

# Custom CSS for trader-friendly UI
st.markdown("""
<style>
    .metric-card { padding: 1rem; background: #0e1117; border-radius: 5px; border: 1px solid #262730; }
    .positive { color: #00ff88; font-weight: bold; }
    .negative { color: #ff4444; font-weight: bold; }
    .neutral { color: #888888; }
    .signal-long { background: #00332200; border: 2px solid #00ff88; padding: 0.5rem; border-radius: 5px; }
    .signal-short { background: #33000000; border: 2px solid #ff4444; padding: 0.5rem; border-radius: 5px; }
    .signal-neutral { background: #33333300; border: 2px solid #888888; padding: 0.5rem; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# Import our modules
from src.core.data_manager import DataManager
from src.core.strategy_engine import StrategyEngine
from src.analytics.indicators import TechnicalIndicators
from src.analytics.statistical import StatisticalAnalytics
from src.analytics.backtester import Backtester
from src.analytics.kalman_filter import KalmanHedgeRatio
from src.analytics.liquidity_analysis import LiquidityAnalyzer
from src.analytics.microstructure import MicrostructureAnalyzer
from src.analytics.correlation_matrix import CorrelationMatrix
from src.analytics.timeseries_table import TimeSeriesStatsTable

# Initialize session state
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = DataManager()
    st.session_state.strategy_engine = StrategyEngine()
    st.session_state.indicators = TechnicalIndicators()
    st.session_state.stats = StatisticalAnalytics()
    st.session_state.backtester = Backtester()
    st.session_state.kalman = KalmanHedgeRatio()
    st.session_state.liquidity = LiquidityAnalyzer()
    st.session_state.microstructure = MicrostructureAnalyzer()
    st.session_state.corr_matrix = CorrelationMatrix()
    st.session_state.timeseries_table = TimeSeriesStatsTable()
    st.session_state.alerts = []
    st.session_state.start_time = time.time()
    st.session_state.refresh_count = 0
    st.session_state.adf_results = {}

# Check if we should auto-refresh (first 5 minutes or until we have data)
elapsed_time = time.time() - st.session_state.start_time
should_auto_refresh = elapsed_time < 300  # Auto-refresh for first 5 minutes

# Sidebar
with st.sidebar:
    st.title("📊 GEMSCAP Quant")
    
    # Connection Status (Top of sidebar)
    status = st.session_state.data_manager.get_connection_status()
    # Consider feed live if websocket connected OR we have any ticks/active symbols
    is_live = bool(status.get('connected')) or int(status.get('total_ticks', 0)) > 0 or int(status.get('active_symbols', 0)) > 0
    if is_live:
        st.success(f"🟢 Live: {status.get('active_symbols', 0)} active / {status.get('symbols', 0)} configured symbols (ticks: {status.get('total_ticks', 0)})")
    else:
        st.error("🔴 Disconnected - Reconnecting...")
    
    st.markdown("---")
    
    # Symbol selection
    symbols = st.session_state.data_manager.get_available_symbols()
    print(f"[DEBUG] Available symbols: {len(symbols)} - {symbols[:3]}...")
    
    st.subheader("Pair Selection")
    symbol1 = st.selectbox("Symbol 1", symbols, index=0)
    symbol2 = st.selectbox("Symbol 2", symbols, index=1)
    
    # Show ADF status for selected symbols in sidebar (after selection)
    adf_results = st.session_state.get('adf_results', {})
    if symbol1 in adf_results:
        res = adf_results[symbol1]
        if res.get('is_stationary'):
            st.success(f"{symbol1} ADF: ✅ Stationary (p={res.get('p_value'):.4f})")
        else:
            st.warning(f"{symbol1} ADF: ❌ Non-stationary (p={res.get('p_value'):.4f})")
    if symbol2 in adf_results:
        res = adf_results[symbol2]
        if res.get('is_stationary'):
            st.success(f"{symbol2} ADF: ✅ Stationary (p={res.get('p_value'):.4f})")
        else:
            st.warning(f"{symbol2} ADF: ❌ Non-stationary (p={res.get('p_value'):.4f})")
    
    st.markdown("---")
    st.subheader("Time Window")
    if 'pending_lookback' not in st.session_state:
        st.session_state.pending_lookback = 15
    lookback = st.slider("Lookback (minutes)", 1, 60, st.session_state.pending_lookback, key='pending_lookback')

    # Aggregation interval (allow seconds and minutes)
    interval_options = ['1s', '5s', '10s', '1m', '5m']
    if 'applied_config' not in st.session_state:
        st.session_state.applied_config = {'interval': '1s', 'zscore_entry': 2.0, 'zscore_exit': 0.0, 'lookback': lookback}
    default_interval = st.session_state.applied_config.get('interval', '1m')
    idx = interval_options.index(default_interval) if default_interval in interval_options else 0
    st.selectbox("Aggregation Interval", interval_options, index=idx, key='pending_interval')
    
    st.markdown("---")
    st.subheader("Strategy Settings")
    if 'pending_zscore_entry' not in st.session_state:
        st.session_state.pending_zscore_entry = st.session_state.applied_config.get('zscore_entry', 2.0)
    if 'pending_zscore_exit' not in st.session_state:
        st.session_state.pending_zscore_exit = st.session_state.applied_config.get('zscore_exit', 0.0)

    st.number_input("Z-Score Entry", 0.5, 10.0, st.session_state.pending_zscore_entry, 0.1, key='pending_zscore_entry')
    st.number_input("Z-Score Exit", -5.0, 5.0, st.session_state.pending_zscore_exit, 0.1, key='pending_zscore_exit')
    st.markdown("""
    **What changing Z-Score does:**
    - Higher entry threshold → fewer signals (only large deviations trigger trades).
    - Lower entry threshold → more frequent signals (more sensitive to spread moves).
    - Exit threshold controls when to close the position (closer to 0 means quicker exits).
    """, unsafe_allow_html=True)
    
    rsi_oversold = st.slider("RSI Oversold", 10, 40, 30)
    rsi_overbought = st.slider("RSI Overbought", 60, 90, 70)
    
    st.markdown("---")
    # Apply changes button: only commit pending settings when user clicks
    if st.button("Apply Changes", width='stretch'):
        st.session_state.applied_config = {
            'interval': st.session_state.get('pending_interval', st.session_state.applied_config.get('interval', '1m')),
            'zscore_entry': st.session_state.get('pending_zscore_entry', st.session_state.applied_config.get('zscore_entry', 2.0)),
            'zscore_exit': st.session_state.get('pending_zscore_exit', st.session_state.applied_config.get('zscore_exit', 0.0)),
            'lookback': st.session_state.get('pending_lookback', st.session_state.applied_config.get('lookback', 15))
        }
        st.success("✅ Applied configuration")
        # Use safe rerun helper to support multiple Streamlit versions
        safe_rerun()

    if st.button("🔄 Refresh Data", width='stretch'):
        safe_rerun()

    if st.button("📥 Export All", width='stretch'):
        st.session_state.export_trigger = True

# Data accumulation status banner
st.markdown("### 📡 GEMSCAP Real-Time Quantitative Trading System")

# Helper: fetch bars for requested interval (supports seconds via resampling 1s bars)
def fetch_bars(dm, symbol, interval, lookback_min):
    # lookback_min expressed in minutes
    if interval.endswith('s'):
        # Build continuous 1-second bars from raw ticks, then resample to requested seconds
        sec = int(interval[:-1])
        # collect recent ticks (deque) from DataManager
        lookback_secs = max(1, lookback_min * 60)
        cutoff_ms = int((time.time() - lookback_secs) * 1000)
        raw_ticks = list(dm.ticks.get(symbol, []))
        recent = [t for t in raw_ticks if t['timestamp'] >= cutoff_ms]
        if not recent:
            return []
        df = pd.DataFrame(recent)
        if df.empty:
            return []
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.set_index('datetime').sort_index()

        # Create 1s OHLC with forward-fill for seconds with no trades
        price_ohlc = df['price'].resample('1s').agg(['first', 'max', 'min', 'last'])
        vol = df['quantity'].resample('1s').sum().fillna(0)
        price_ohlc = price_ohlc.ffill()
        price_ohlc = price_ohlc.fillna(0)
        price_ohlc.columns = ['open', 'high', 'low', 'close']
        price_ohlc['volume'] = vol
        price_ohlc = price_ohlc.reset_index()

        # If requested >1s, further aggregate
        if sec > 1:
            agg = price_ohlc.set_index('datetime').resample(f"{sec}s").agg({
                'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
            }).dropna().reset_index()
        else:
            agg = price_ohlc

        if agg.empty:
            return []
        agg['timestamp'] = (agg['datetime'].astype('int64') // 1_000_000).astype(int)
        return agg.to_dict('records')
    else:
        # minutes-based intervals supported directly
        return dm.get_ohlc(symbol, interval, max(1, lookback_min if interval == '1m' else (lookback_min // (int(interval[:-1]) if interval.endswith('m') else 1)) ))


def get_bars(dm, symbol, interval, lookback_min):
    """Unified accessor: return bars for seconds intervals via fetch_bars, otherwise use DataManager.get_ohlc."""
    if interval.endswith('s'):
        return fetch_bars(dm, symbol, interval, lookback_min)
    # minutes-based - compute limit conservatively (lookback_min bars)
    if interval == '1m':
        limit = max(1, lookback_min)
    else:
        # e.g., '5m' -> number of 5m bars in lookback_min
        try:
            m = int(interval[:-1]) if interval.endswith('m') else 1
            limit = max(1, lookback_min // m)
        except Exception:
            limit = max(1, lookback_min)
    return dm.get_ohlc(symbol, interval, limit)

# Determine applied config
applied = st.session_state.get('applied_config', {'interval':'1m','lookback': lookback, 'zscore_entry':2.0, 'zscore_exit':0.0})
agg_interval = applied.get('interval', '1m')
agg_lookback = applied.get('lookback', lookback)
zscore_entry = applied.get('zscore_entry', 2.0)
zscore_exit = applied.get('zscore_exit', 0.0)

# Get quick data check for both symbols using applied interval
quick_data1 = fetch_bars(st.session_state.data_manager, symbol1, agg_interval, agg_lookback)
quick_data2 = fetch_bars(st.session_state.data_manager, symbol2, agg_interval, agg_lookback)
data_ready = len(quick_data1) > 0 and len(quick_data2) > 0

if data_ready:
    st.success(f"✅ Live data streaming: {symbol1} ${quick_data1[-1]['close']:.2f} | {symbol2} ${quick_data2[-1]['close']:.2f}")
else:
    progress_text = f"🔄 Collecting initial data... ({int(elapsed_time)}s elapsed)"
    st.warning(progress_text)
    with st.expander("ℹ️ What's happening?", expanded=True):
        st.markdown("""
        **First-time setup:**
        1. ✅ WebSocket connected to Binance
        2. 🔄 Receiving live tick data (check bottom of page for tick count)
        3. ⏳ Building 1-minute OHLC bars (takes 1-2 minutes)
        4. ✅ Auto-refresh is ON - page updates every 5 seconds
        
        **Current progress:**
        - Ticks received: {:,}
        - Bars for {}: {}
        - Bars for {}: {}
        
        **Tip:** Check the 'System' tab for detailed connection status.
        """.format(
            st.session_state.data_manager.tick_count,
            symbol1, len(st.session_state.data_manager.ohlc_1m[symbol1]),
            symbol2, len(st.session_state.data_manager.ohlc_1m[symbol2])
        ))

st.markdown("---")

# Navigation Helper
with st.expander("📚 Navigation Guide - Click to expand", expanded=False):
    nav_col1, nav_col2, nav_col3 = st.columns(3)
    
    with nav_col1:
        st.markdown("**📊 Core Analysis**")
        st.markdown("- 📈 Spread Analysis")
        st.markdown("- 🎯 Strategy Signals")
        st.markdown("- 📊 Statistical Tests")
        st.markdown("- 🔍 Backtesting")
    
    with nav_col2:
        st.markdown("**🔬 Advanced Analytics**")
        st.markdown("- 🧮 Kalman & Robust Regression")
        st.markdown("- 💧 Liquidity & Heatmap")
        st.markdown("- 🔬 Microstructure")
        st.markdown("- 🔗 Correlation Matrix")
    
    with nav_col3:
        st.markdown("**⚙️ System & Export**")
        st.markdown("- 🔔 Alerts")
        st.markdown("- ⚙️ System Status")
        st.markdown("- 🔎 Quick Compare")
        st.markdown("- 📋 Time-Series Table (CSV Export)")

# Main content
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12 = st.tabs([
    "📈 Spread Analysis",
    "🎯 Strategy Signals", 
    "📊 Statistical Tests",
    "🔍 Backtesting",
    "🔔 Alerts",
    "⚙️ System",
    "🔎 Quick Compare",
    "🧮 Kalman & Robust Regression",
    "💧 Liquidity & Heatmap",
    "🔬 Microstructure",
    "🔗 Correlation Matrix",
    "📋 Time-Series Stats Table"
])

# Tab 1: Spread Analysis
with tab1:
    st.header(f"Pairs Trading: {symbol1} / {symbol2}")
    
    # Get data with debugging
    print(f"[DEBUG] Fetching OHLC for {symbol1} and {symbol2}, lookback={lookback}min (agg={agg_interval})")
    data1 = get_bars(st.session_state.data_manager, symbol1, agg_interval, agg_lookback)
    data2 = get_bars(st.session_state.data_manager, symbol2, agg_interval, agg_lookback)
    
    print(f"[DEBUG] Data received: {symbol1}={len(data1)} bars, {symbol2}={len(data2)} bars")
    
    # Data diagnostics panel
    with st.expander("🔍 Data Diagnostics", expanded=False):
        diag_col1, diag_col2, diag_col3 = st.columns(3)
        with diag_col1:
            st.metric(f"{symbol1} Bars", len(data1))
            if data1:
                st.caption(f"Latest: ${data1[-1]['close']:.2f}")
        with diag_col2:
            st.metric(f"{symbol2} Bars", len(data2))
            if data2:
                st.caption(f"Latest: ${data2[-1]['close']:.2f}")
        with diag_col3:
            db_stats = st.session_state.data_manager.get_db_stats()
            st.metric("Total DB Records", db_stats['total_records'])
            st.caption(f"Ticks: {st.session_state.data_manager.tick_count}")
    
    if len(data1) > 20 and len(data2) > 20:
        print(f"[DEBUG] Sufficient data - computing spread analysis")
        # Align bars by timestamp to ensure equal-length series for OLS
        map1 = {int(d['timestamp']): d['close'] for d in data1}
        map2 = {int(d['timestamp']): d['close'] for d in data2}
        common_ts = sorted(set(map1.keys()) & set(map2.keys()))
        if len(common_ts) < 20:
            st.warning(f"Not enough aligned bars for analysis (need 20+, have {len(common_ts)}).")
        prices1 = [map1[t] for t in common_ts]
        prices2 = [map2[t] for t in common_ts]
        timestamps = common_ts
        
        # Ensure arrays are equal-length (defensive trim if necessary)
        if len(prices1) != len(prices2):
            min_len = min(len(prices1), len(prices2))
            prices1 = prices1[-min_len:]
            prices2 = prices2[-min_len:]
            timestamps = timestamps[-min_len:]
            print(f"[WARN] Trimmed aligned series to min length={min_len}")

        # Compute OLS and spread (now with aligned arrays)
        ols_result = st.session_state.stats.ols_regression(prices1, prices2)
        spread_data = st.session_state.strategy_engine.compute_spread(
            prices1, prices2, ols_result['hedge_ratio']
        )
        
        # Metrics row with color coding
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("⚖️ Hedge Ratio", f"{ols_result['hedge_ratio']:.4f}")
            st.caption(f"α: {ols_result['alpha']:.4f}")
        with col2:
            r2_color = "🟢" if ols_result['r_squared'] > 0.7 else "🟡" if ols_result['r_squared'] > 0.5 else "🔴"
            st.metric(f"{r2_color} R²", f"{ols_result['r_squared']:.4f}")
            st.caption(f"Fit: {'Excellent' if ols_result['r_squared'] > 0.7 else 'Good' if ols_result['r_squared'] > 0.5 else 'Poor'}")
        with col3:
            z_current = spread_data['zscore'][-1]
            z_color = "🔴" if abs(z_current) > zscore_entry else "🟡" if abs(z_current) > zscore_entry*0.5 else "🟢"
            st.metric(f"{z_color} Z-Score", f"{z_current:.2f}")
            st.caption(f"Std Dev: {abs(z_current):.2f}σ")
        with col4:
            corr = ols_result.get('correlation', np.corrcoef(prices1, prices2)[0,1])
            corr_color = "🟢" if corr > 0.7 else "🟡" if corr > 0.5 else "🔴"
            st.metric(f"{corr_color} Correlation", f"{corr:.3f}")
            st.caption(f"Strength: {'Strong' if corr > 0.7 else 'Moderate' if corr > 0.5 else 'Weak'}")
        with col5:
            if spread_data['zscore'][-1] < -zscore_entry:
                signal_text = "🟢 LONG"
                signal_class = "signal-long"
                action = "BUY SPREAD"
            elif spread_data['zscore'][-1] > zscore_entry:
                signal_text = "🔴 SHORT"
                signal_class = "signal-short"
                action = "SELL SPREAD"
            else:
                signal_text = "⚪ NEUTRAL"
                signal_class = "signal-neutral"
                action = "WAIT"
            st.metric("🎯 Signal", signal_text)
            st.caption(f"Action: {action}")
        
        # Create comprehensive chart
        fig = make_subplots(
            rows=3, cols=1,
            row_heights=[0.5, 0.25, 0.25],
            subplot_titles=("Spread & Bollinger Bands", "Z-Score", "Price Series"),
            vertical_spacing=0.08
        )
        
        # Spread with Bollinger Bands
        fig.add_trace(go.Scatter(x=timestamps, y=spread_data['spread'], 
                                name="Spread", line=dict(color='blue')), row=1, col=1)
        fig.add_trace(go.Scatter(x=timestamps, y=spread_data['bollinger_upper'],
                                name="Upper Band", line=dict(dash='dash', color='red')), row=1, col=1)
        fig.add_trace(go.Scatter(x=timestamps, y=spread_data['bollinger_lower'],
                                name="Lower Band", line=dict(dash='dash', color='green')), row=1, col=1)
        fig.add_trace(go.Scatter(x=timestamps, y=spread_data['bollinger_ma'],
                                name="MA", line=dict(dash='dot', color='gray')), row=1, col=1)
        
        # Add entry/exit markers
        entry_long = [i for i, z in enumerate(spread_data['zscore']) if z < -zscore_entry]
        entry_short = [i for i, z in enumerate(spread_data['zscore']) if z > zscore_entry]
        if entry_long:
            fig.add_trace(go.Scatter(x=[timestamps[i] for i in entry_long],
                                    y=[spread_data['spread'][i] for i in entry_long],
                                    mode='markers', name='Long Entry', 
                                    marker=dict(color='green', size=10, symbol='triangle-up')), row=1, col=1)
        if entry_short:
            fig.add_trace(go.Scatter(x=[timestamps[i] for i in entry_short],
                                    y=[spread_data['spread'][i] for i in entry_short],
                                    mode='markers', name='Short Entry',
                                    marker=dict(color='red', size=10, symbol='triangle-down')), row=1, col=1)
        
        # Z-Score
        fig.add_trace(go.Scatter(x=timestamps, y=spread_data['zscore'],
                                name="Z-Score", line=dict(color='purple')), row=2, col=1)
        fig.add_hline(y=zscore_entry, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=-zscore_entry, line_dash="dash", line_color="green", row=2, col=1)
        fig.add_hline(y=0, line_dash="dot", line_color="gray", row=2, col=1)
        
        # Price series - normalize both to a common starting point for comparable scale
        try:
            base1 = prices1[0] if prices1 and prices1[0] != 0 else 1.0
            base2 = prices2[0] if prices2 and prices2[0] != 0 else 1.0
            norm1 = [p / base1 * 100.0 for p in prices1]
            norm2 = [p / base2 * 100.0 for p in prices2]
        except Exception:
            norm1 = prices1
            norm2 = prices2

        fig.add_trace(go.Scatter(x=timestamps, y=norm1, name=f"{symbol1} (norm)", 
                                line=dict(color='orange')), row=3, col=1)
        fig.add_trace(go.Scatter(x=timestamps, y=norm2, name=f"{symbol2} (norm)",
                                line=dict(color='cyan')), row=3, col=1)
        
        fig.update_layout(height=800, showlegend=True, hovermode='x unified')
        st.plotly_chart(fig, width='stretch')
        
        # What-if Analysis
        st.subheader("🔬 What-If Analysis")
        col1, col2, col3 = st.columns(3)
        with col1:
            corr_change = st.slider("Correlation Change (%)", -50, 50, 0)
        with col2:
            vol_multiplier = st.slider("Volatility Multiplier", 0.5, 3.0, 1.0, 0.1)
        with col3:
            hedge_adjust = st.slider("Hedge Ratio Adjustment (%)", -20, 20, 0)
        
        if corr_change != 0 or vol_multiplier != 1.0 or hedge_adjust != 0:
            adjusted_hedge = ols_result['hedge_ratio'] * (1 + hedge_adjust/100)
            adjusted_spread = st.session_state.strategy_engine.compute_spread(
                prices1, prices2, adjusted_hedge, volatility_mult=vol_multiplier
            )
            st.info(f"Adjusted Z-Score: {adjusted_spread['zscore'][-1]:.2f} (vs original {spread_data['zscore'][-1]:.2f})")
    
    else:
        st.warning(f"⏳ Collecting data... Please wait")
        st.info(f"📊 Current data: {symbol1}={len(data1)} bars, {symbol2}={len(data2)} bars (need 20+ each)")
        st.markdown("""
        **Waiting for data...**
        - Check connection status in sidebar (should be 🟢 Live)
        - Data accumulates every minute from Binance WebSocket
        - Typically takes 1-2 minutes for sufficient data
        - Check 'System' tab for detailed connection info
        """)
        
        # Show what we do have
        if data1 or data2:
            st.subheader("🔍 Current Data Preview")
            col1, col2 = st.columns(2)
            with col1:
                if data1:
                    st.write(f"**{symbol1}** - {len(data1)} bars")
                    st.write(f"Latest price: ${data1[-1]['close']:.2f}")
                else:
                    st.write(f"**{symbol1}** - No data yet")
            with col2:
                if data2:
                    st.write(f"**{symbol2}** - {len(data2)} bars")
                    st.write(f"Latest price: ${data2[-1]['close']:.2f}")
                else:
                    st.write(f"**{symbol2}** - No data yet")

# Tab 2: Strategy Signals
with tab2:
    st.header("Multi-Strategy Signals")
    
    print(f"[DEBUG] Tab 2 - Data length: {len(data1)} bars (need 50+)")
    
    if len(data1) > 50:
        prices = [d['close'] for d in data1]
        
        # Compute indicators
        rsi = st.session_state.indicators.rsi(prices, period=14)
        macd_data = st.session_state.indicators.macd(prices)
        bb_data = st.session_state.indicators.bollinger_bands(prices)
        
        # Display signals
        col1, col2, col3 = st.columns(3)
        with col1:
            st.subheader("RSI")
            current_rsi = rsi[-1] if len(rsi) > 0 else 50
            st.metric("Current RSI", f"{current_rsi:.1f}")
            if current_rsi < rsi_oversold:
                st.success("🟢 Oversold - Buy Signal")
            elif current_rsi > rsi_overbought:
                st.error("🔴 Overbought - Sell Signal")
            else:
                st.info("⚪ Neutral")
        
        with col2:
            st.subheader("MACD")
            if len(macd_data['macd']) > 0:
                macd_val = macd_data['macd'][-1]
                signal_val = macd_data['signal'][-1]
                st.metric("MACD", f"{macd_val:.2f}")
                st.metric("Signal", f"{signal_val:.2f}")
                if macd_val > signal_val:
                    st.success("🟢 Bullish Cross")
                else:
                    st.error("🔴 Bearish Cross")
        
        with col3:
            st.subheader("Bollinger")
            price = prices[-1]
            upper = bb_data['upper'][-1]
            lower = bb_data['lower'][-1]
            st.metric("Price Position", f"{((price-lower)/(upper-lower)*100):.1f}%")
            if price > upper:
                st.error("🔴 Overbought")
            elif price < lower:
                st.success("🟢 Oversold")
            else:
                st.info("⚪ Normal")
        
        # Combined chart
        fig = make_subplots(rows=3, cols=1, row_heights=[0.5, 0.25, 0.25],
                           subplot_titles=("Price & Bollinger", "RSI", "MACD"))
        
        timestamps = [d['timestamp'] for d in data1]
        # Normalize price series so indicators and visual comparison share a common scale
        try:
            base_price = prices[0] if prices and prices[0] != 0 else 1.0
            norm_prices = [p / base_price * 100.0 for p in prices]
        except Exception:
            norm_prices = prices

        fig.add_trace(go.Scatter(x=timestamps, y=norm_prices, name="Price (norm)"), row=1, col=1)
        fig.add_trace(go.Scatter(x=timestamps, y=bb_data['upper'], name="BB Upper", line=dict(dash='dash')), row=1, col=1)
        fig.add_trace(go.Scatter(x=timestamps, y=bb_data['lower'], name="BB Lower", line=dict(dash='dash')), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=timestamps[-len(rsi):], y=rsi, name="RSI"), row=2, col=1)
        fig.add_hline(y=rsi_overbought, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=rsi_oversold, line_dash="dash", line_color="green", row=2, col=1)
        
        if len(macd_data['macd']) > 0:
            fig.add_trace(go.Scatter(x=timestamps[-len(macd_data['macd']):], y=macd_data['macd'], name="MACD"), row=3, col=1)
            fig.add_trace(go.Scatter(x=timestamps[-len(macd_data['signal']):], y=macd_data['signal'], name="Signal"), row=3, col=1)
            fig.add_trace(go.Bar(x=timestamps[-len(macd_data['histogram']):], y=macd_data['histogram'], name="Histogram"), row=3, col=1)
        
        fig.update_layout(height=800, showlegend=True)
        st.plotly_chart(fig, width='stretch')
    else:
        st.warning(f"⏳ Need at least 50 bars for indicator analysis (currently: {len(data1)} bars)")
        st.info("This tab shows RSI, MACD, and Bollinger Band indicators. Collecting more data...")

# Tab 3: Statistical Tests
with tab3:
    st.header("Statistical Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"ADF Test - {symbol1}")
        if len(data1) > 20:
            try:
                prices = [d['close'] for d in data1]
                adf_result = st.session_state.stats.adf_test(prices)
                st.metric("ADF Statistic", f"{adf_result['adf_statistic']:.4f}")
                st.metric("P-Value", f"{adf_result['p_value']:.4f}")
                # Store ADF result in session state and avoid printing status here
                st.session_state.adf_results[symbol1] = adf_result
                with st.expander("Details"):
                    st.json(adf_result)
            except Exception as e:
                st.error(f"Error: {e}")
    
# Tab 7: Quick Compare - price + volume for both symbols (fallback to ticks)
with tab7:
    st.header(f"Quick Compare: {symbol1} vs {symbol2}")

    def _build_df_from_ohlc(ohlc_list):
        if not ohlc_list:
            return pd.DataFrame()
        df = pd.DataFrame(ohlc_list)
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df.sort_values('datetime')

    def _build_df_from_ticks(tick_deque, max_points=500):
        ticks = list(tick_deque)[-max_points:]
        if not ticks:
            return pd.DataFrame()
        df = pd.DataFrame([{
            'price': t['price'],
            'volume': t['quantity'],
            'timestamp': t['timestamp']
        } for t in ticks])
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df.sort_values('datetime')

    dm = st.session_state.data_manager

    # Uploader: allow user to import historical OHLC CSV and persist to DB
    with st.expander("📁 Upload OHLC CSV (optional)", expanded=False):
        st.markdown("Upload a CSV with columns: timestamp, open, high, low, close, volume.\nTimestamp may be epoch ms or ISO datetime.")
        upload_symbol = st.selectbox("Target Symbol for Upload", options=symbols, index=0)
        upload_interval = st.selectbox("Target Interval", options=['1m', '5m'], index=0)
        timestamp_format = st.selectbox("Timestamp format", options=['epoch_ms', 'iso'], index=0)
        uploaded_file = st.file_uploader("Choose OHLC CSV file", type=['csv'])

        if uploaded_file is not None:
            try:
                uploaded_bytes = uploaded_file.read()
                uploaded_file.seek(0)
                df_upload = pd.read_csv(io.BytesIO(uploaded_bytes))

                # Validate required columns
                required = {'timestamp', 'open', 'high', 'low', 'close', 'volume'}
                if not required.issubset(set(df_upload.columns.str.lower())):
                    st.error(f"Missing required columns. Required: {sorted(required)}")
                else:
                    # Normalize column names
                    df_upload.columns = [c.lower() for c in df_upload.columns]

                    # Parse timestamp
                    if timestamp_format == 'epoch_ms':
                        df_upload['timestamp'] = df_upload['timestamp'].astype('int64')
                    else:
                        df_upload['timestamp'] = pd.to_datetime(df_upload['timestamp']).astype('int64') // 1_000_000

                    # Keep only required columns and drop duplicates
                    df_upload = df_upload[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
                    df_upload = df_upload.drop_duplicates(subset=['timestamp'])

                    # Convert numeric types
                    for col in ['open','high','low','close','volume']:
                        df_upload[col] = pd.to_numeric(df_upload[col], errors='coerce')

                    # Ensure timestamps are integers
                    df_upload = df_upload.dropna()
                    df_upload['timestamp'] = df_upload['timestamp'].astype(int)

                    # Persist to SQLite (1m table exists; 5m table created in DataManager)
                    import sqlite3
                    conn = sqlite3.connect(st.session_state.data_manager.db_path)
                    cursor = conn.cursor()

                    inserted = 0
                    for _, row in df_upload.iterrows():
                        try:
                            if upload_interval == '1m':
                                cursor.execute('''INSERT OR REPLACE INTO ohlc_1m (symbol, timestamp, open, high, low, close, volume, tick_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                                               (upload_symbol, int(row['timestamp']), float(row['open']), float(row['high']), float(row['low']), float(row['close']), float(row['volume']), 0))
                                # update in-memory deque for quick access
                                bar = {'symbol': upload_symbol, 'timestamp': int(row['timestamp']), 'open': float(row['open']), 'high': float(row['high']), 'low': float(row['low']), 'close': float(row['close']), 'volume': float(row['volume']), 'tick_count': 0}
                                try:
                                    st.session_state.data_manager.ohlc_1m[upload_symbol].append(bar)
                                except Exception:
                                    pass
                            else:
                                cursor.execute('''INSERT OR REPLACE INTO ohlc_5m (symbol, timestamp, open, high, low, close, volume, tick_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                                               (upload_symbol, int(row['timestamp']), float(row['open']), float(row['high']), float(row['low']), float(row['close']), float(row['volume']), 0))
                                bar = {'symbol': upload_symbol, 'timestamp': int(row['timestamp']), 'open': float(row['open']), 'high': float(row['high']), 'low': float(row['low']), 'close': float(row['close']), 'volume': float(row['volume']), 'tick_count': 0}
                                try:
                                    st.session_state.data_manager.ohlc_5m[upload_symbol].append(bar)
                                except Exception:
                                    pass
                            inserted += 1
                        except Exception as e:
                            print(f"[Upload] row insert error: {e}")
                    conn.commit()
                    conn.close()

                    st.success(f"Imported {inserted} OHLC rows into {upload_symbol} ({upload_interval})")
                    st.write(df_upload.head(10))
            except Exception as e:
                st.error(f"Failed to parse uploaded CSV: {e}")

    # Try OHLC first, otherwise fall back to ticks
    df1 = _build_df_from_ohlc(get_bars(dm, symbol1, agg_interval, agg_lookback))
    if df1.empty:
        df1 = _build_df_from_ticks(dm.ticks[symbol1])

    df2 = _build_df_from_ohlc(get_bars(dm, symbol2, agg_interval, agg_lookback))
    if df2.empty:
        df2 = _build_df_from_ticks(dm.ticks[symbol2])

    if df1.empty and df2.empty:
        st.warning("No data available yet for either symbol. Waiting for ticks or bars...")
    else:
        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader(symbol1)
            if not df1.empty:
                fig1 = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
                fig1.add_trace(go.Scatter(x=df1['datetime'], y=df1['close'] if 'close' in df1.columns else df1['price'],
                                          name='Price', line=dict(color='orange')), row=1, col=1)
                vol_y = df1['volume'] if 'volume' in df1.columns else df1['quantity'] if 'quantity' in df1.columns else df1.get('volume', None)
                if vol_y is not None:
                    fig1.add_trace(go.Bar(x=df1['datetime'], y=vol_y, name='Volume', marker_color='lightblue'), row=2, col=1)
                fig1.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig1, width='stretch')
            else:
                st.info("No 1m bars; showing recent ticks (if any)")
                st.write(df1.tail(50))

        with col_b:
            st.subheader(symbol2)
            if not df2.empty:
                fig2 = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
                fig2.add_trace(go.Scatter(x=df2['datetime'], y=df2['close'] if 'close' in df2.columns else df2['price'],
                                          name='Price', line=dict(color='cyan')), row=1, col=1)
                vol_y2 = df2['volume'] if 'volume' in df2.columns else df2['quantity'] if 'quantity' in df2.columns else df2.get('volume', None)
                if vol_y2 is not None:
                    fig2.add_trace(go.Bar(x=df2['datetime'], y=vol_y2, name='Volume', marker_color='lightgreen'), row=2, col=1)
                fig2.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig2, width='stretch')
            else:
                st.info("No 1m bars; showing recent ticks (if any)")
                st.write(df2.tail(50))

        # Combined small metrics
        mcol1, mcol2, mcol3 = st.columns(3)
        with mcol1:
            if not df1.empty:
                st.metric(f"{symbol1} Latest", f"${(df1['close'] if 'close' in df1.columns else df1['price']).iloc[-1]:.2f}")
            else:
                st.metric(f"{symbol1} Latest", "n/a")
        with mcol2:
            if not df2.empty:
                st.metric(f"{symbol2} Latest", f"${(df2['close'] if 'close' in df2.columns else df2['price']).iloc[-1]:.2f}")
            else:
                st.metric(f"{symbol2} Latest", "n/a")
        with mcol3:
            total_ticks = dm.tick_count
            st.metric("Ticks Received", f"{total_ticks}")

    with col2:
        st.subheader(f"ADF Test - {symbol2}")
        if len(data2) > 20:
            try:
                prices = [d['close'] for d in data2]
                adf_result = st.session_state.stats.adf_test(prices)
                st.metric("ADF Statistic", f"{adf_result['adf_statistic']:.4f}")
                st.metric("P-Value", f"{adf_result['p_value']:.4f}")
                # Store ADF result in session state and avoid printing status here
                st.session_state.adf_results[symbol2] = adf_result
                with st.expander("Details"):
                    st.json(adf_result)
            except Exception as e:
                st.error(f"Error: {e}")
    
    st.markdown("---")
    if len(data1) > 20 and len(data2) > 20:
        st.subheader("Cointegration Test")
        try:
            # Align by timestamp to ensure equal-length series
            map1 = {int(d['timestamp']): d['close'] for d in data1}
            map2 = {int(d['timestamp']): d['close'] for d in data2}
            common_ts = sorted(set(map1.keys()) & set(map2.keys()))
            if len(common_ts) < 20:
                st.warning(f"Not enough aligned bars for cointegration test (need 20+, have {len(common_ts)}).")
                raise ValueError("Insufficient aligned data")
            prices1 = [map1[t] for t in common_ts]
            prices2 = [map2[t] for t in common_ts]
            coint_result = st.session_state.stats.cointegration_test(prices1, prices2)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Hedge Ratio", f"{coint_result['hedge_ratio']:.4f}")
            with col2:
                st.metric("Spread ADF", f"{coint_result['spread_adf_stat']:.4f}")
            with col3:
                if coint_result['is_cointegrated']:
                    st.success("✅ Cointegrated")
                else:
                    st.warning("❌ Not Cointegrated")
        except Exception as e:
            st.error(f"Error: {e}")

# Tab 4: Backtesting
with tab4:
    st.header("Strategy Backtesting")
    
    col1, col2 = st.columns(2)
    with col1:
        strategy_type = st.selectbox("Strategy", ["Z-Score", "RSI", "MACD", "Multi-Strategy"])
    with col2:
        capital = st.number_input("Initial Capital ($)", 1000, 1000000, 10000)
    
    if st.button("🚀 Run Backtest"):
        with st.spinner("Running backtest..."):
            if len(data1) > 50:
                prices = [d['close'] for d in data1]
                timestamps = [d['timestamp'] for d in data1]
                
                results = st.session_state.backtester.run_backtest(
                    prices, 
                    strategy=strategy_type.lower().replace("-", "_"),
                    capital=capital,
                    zscore_threshold=zscore_entry,
                    rsi_levels=(rsi_oversold, rsi_overbought)
                )
                
                # Display results
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Return", f"{results['total_return']:.2f}%")
                with col2:
                    st.metric("Sharpe Ratio", f"{results['sharpe_ratio']:.2f}")
                with col3:
                    st.metric("Max Drawdown", f"{results['max_drawdown']:.2f}%")
                with col4:
                    st.metric("Win Rate", f"{results['win_rate']:.1f}%")
                
                # Equity curve
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=timestamps, y=results['equity_curve'], 
                                        name="Portfolio Value", fill='tozeroy'))
                fig.update_layout(title="Equity Curve", height=400)
                st.plotly_chart(fig, width='stretch')
                
                # Trade log
                st.subheader("Trade History")
                st.dataframe(pd.DataFrame(results['trades']))

# Tab 5: Alerts
with tab5:
    st.header("Alert System")
    
    # Alert settings
    col1, col2 = st.columns(2)
    with col1:
        enable_zscore_alerts = st.checkbox("Z-Score Alerts", value=True)
        enable_rsi_alerts = st.checkbox("RSI Alerts", value=True)
    with col2:
        enable_macd_alerts = st.checkbox("MACD Alerts", value=True)
        enable_cointegration_alerts = st.checkbox("Cointegration Break Alerts", value=False)
    
    # Active alerts
    st.subheader("Active Alerts")
    if st.session_state.alerts:
        for alert in reversed(st.session_state.alerts[-50:]):
            if alert['severity'] == 'high':
                st.error(f"🔴 {alert['timestamp']} - {alert['message']}")
            elif alert['severity'] == 'medium':
                st.warning(f"🟡 {alert['timestamp']} - {alert['message']}")
            else:
                st.info(f"🔵 {alert['timestamp']} - {alert['message']}")
    else:
        st.info("No alerts yet")
    
    if st.button("Clear All Alerts"):
        st.session_state.alerts = []
        st.rerun()

# Tab 6: System
with tab6:
    st.header("System Status")
    
    # Connection status
    col1, col2, col3 = st.columns(3)
    with col1:
        ws_status = st.session_state.data_manager.get_connection_status()
        if ws_status['connected']:
            st.success("🟢 WebSocket Connected")
        else:
            st.error("🔴 WebSocket Disconnected")
        st.metric("Symbols", ws_status['active_symbols'])
    
    with col2:
        db_stats = st.session_state.data_manager.get_db_stats()
        st.success("🟢 Database Active")
        st.metric("Total Records", db_stats['total_records'])
    
    with col3:
        st.metric("Memory Usage", f"{db_stats['memory_mb']:.1f} MB")
        st.metric("Uptime", db_stats['uptime'])
    
    # Data table
    st.subheader("Recent Data")
    recent_data = get_bars(st.session_state.data_manager, symbol1, agg_interval, max(1, agg_lookback))
    if recent_data:
        # show most recent 10 bars
        df = pd.DataFrame(recent_data[-10:])
        st.dataframe(df, width='stretch')
    
    # Export functionality
    if st.session_state.get('export_trigger', False):
        st.subheader("📥 Exporting Data")
        
        # Prepare export package
        export_data = {
                'ohlc_data': {
                symbol1: get_bars(st.session_state.data_manager, symbol1, agg_interval, 1000),
                symbol2: get_bars(st.session_state.data_manager, symbol2, agg_interval, 1000)
            },
            'analytics': {
                'ols': ols_result if 'ols_result' in locals() else None,
                'spread': spread_data if 'spread_data' in locals() else None
            },
            'alerts': st.session_state.alerts,
            'config': {
                'zscore_entry': zscore_entry,
                'zscore_exit': zscore_exit,
                'rsi_levels': (rsi_oversold, rsi_overbought)
            }
        }
        
        json_str = json.dumps(export_data, indent=2, default=str)
        st.download_button(
            label="Download JSON",
            data=json_str,
            file_name=f"gemscap_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        
        st.session_state.export_trigger = False

# Tab 8: Kalman Filter & Robust Regression
with tab8:
    st.header("Advanced Regression Methods")
    
    if len(data1) > 50 and len(data2) > 50:
        # Align data first
        map1 = {int(d['timestamp']): d['close'] for d in data1}
        map2 = {int(d['timestamp']): d['close'] for d in data2}
        common_ts = sorted(set(map1.keys()) & set(map2.keys()))
        
        if len(common_ts) >= 50:
            prices1 = [map1[t] for t in common_ts]
            prices2 = [map2[t] for t in common_ts]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🧮 Kalman Filter (Dynamic Hedge)")
                try:
                    kalman_result = st.session_state.kalman.estimate(prices1, prices2)
                    st.metric("Current Hedge Ratio", f"{kalman_result['current_hedge_ratio']:.4f}")
                    st.metric("Std Dev", f"±{kalman_result['current_std']:.4f}")
                    
                    # Plot dynamic hedge ratio
                    fig = go.Figure()
                    hedge_timestamps = common_ts[-len(kalman_result['hedge_ratios']):]
                    fig.add_trace(go.Scatter(x=hedge_timestamps, y=kalman_result['hedge_ratios'], 
                                            name='Kalman Hedge', line=dict(color='purple')))
                    fig.update_layout(title="Dynamic Hedge Ratio (Kalman Filter)", height=300)
                    st.plotly_chart(fig, width='stretch')
                    
                    with st.expander("Kalman Details"):
                        st.json(kalman_result)
                except Exception as e:
                    st.error(f"Kalman filter error: {e}")
            
            with col2:
                st.subheader("🛡️ Robust Regression")
                try:
                    # Compute OLS, Huber, and Theil-Sen
                    ols_res = st.session_state.stats.ols_regression(prices1, prices2)
                    huber_res = st.session_state.stats.robust_regression_huber(prices1, prices2)
                    theil_res = st.session_state.stats.robust_regression_theil_sen(prices1, prices2)
                    
                    # Comparison table
                    comparison = pd.DataFrame({
                        "Method": ["OLS", "Huber", "Theil-Sen"],
                        "Hedge Ratio": [ols_res['hedge_ratio'], huber_res['hedge_ratio'], theil_res['hedge_ratio']],
                        "Alpha": [ols_res['alpha'], huber_res['alpha'], theil_res['alpha']],
                        "R²": [ols_res['r_squared'], huber_res['r_squared'], theil_res['r_squared']]
                    })
                    st.dataframe(comparison, width='stretch')
                    
                    if huber_res.get('outliers_detected', 0) > 0:
                        st.warning(f"⚠️ Huber detected {huber_res['outliers_detected']} outliers ({huber_res['outlier_percentage']:.1f}%)")
                    else:
                        st.success("✅ No significant outliers detected")
                    
                    st.info("**Tip:** Use Huber or Theil-Sen when data has outliers or fat tails.")
                except Exception as e:
                    st.error(f"Robust regression error: {e}")
        else:
            st.warning(f"Need at least 50 aligned bars (have {len(common_ts)})")
    else:
        st.warning("Collecting data for Kalman filter and robust regression...")

# Tab 9: Liquidity & Heatmap
with tab9:
    st.header("Liquidity Analysis & Heatmap")
    
    dm = st.session_state.data_manager
    
    # Get recent ticks for liquidity analysis
    ticks1 = list(dm.ticks.get(symbol1, []))[-1000:]
    ticks2 = list(dm.ticks.get(symbol2, []))[-1000:]
    
    if len(ticks1) > 50:
        st.subheader(f"💧 {symbol1} Liquidity")
        
        try:
            prices = [t['price'] for t in ticks1]
            volumes = [t['quantity'] for t in ticks1]
            timestamps = [t['timestamp'] for t in ticks1]
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Volume profile
                vp = st.session_state.liquidity.compute_volume_profile(prices, volumes, n_bins=30)
                st.metric("POC (Point of Control)", f"${vp['poc_price']:.2f}")
                st.metric("Value Area", f"${vp['value_area_low']:.2f} - ${vp['value_area_high']:.2f}")
                
                # Plot volume profile
                fig = go.Figure()
                fig.add_trace(go.Bar(y=vp['bin_centers'], x=vp['volume_by_bin'], 
                                    orientation='h', name='Volume'))
                fig.add_hline(y=vp['poc_price'], line_dash='dash', line_color='red', 
                             annotation_text='POC')
                fig.update_layout(title="Volume Profile", height=400, 
                                 yaxis_title="Price", xaxis_title="Volume")
                st.plotly_chart(fig, width='stretch')
            
            with col2:
                # Liquidity heatmap
                hm = st.session_state.liquidity.liquidity_heatmap_data(
                    timestamps, prices, volumes, time_bins=30, price_bins=25
                )
                
                fig = go.Figure(data=go.Heatmap(
                    z=hm['heatmap_matrix'],
                    x=hm['time_labels'],
                    y=hm['price_labels'],
                    colorscale='Viridis'
                ))
                fig.update_layout(title="Liquidity Heatmap (Volume Intensity)", height=400,
                                 xaxis_title="Time (ms)", yaxis_title="Price")
                st.plotly_chart(fig, width='stretch')
        
        except Exception as e:
            st.error(f"Liquidity analysis error: {e}")
    else:
        st.info(f"Collecting tick data for liquidity analysis... (have {len(ticks1)} ticks)")

# Tab 10: Microstructure Analytics
with tab10:
    st.header("🔬 Market Microstructure")
    
    ticks1 = list(dm.ticks.get(symbol1, []))[-500:]
    
    if len(ticks1) > 50:
        try:
            prices = [t['price'] for t in ticks1]
            volumes = [t['quantity'] for t in ticks1]
            timestamps = [t['timestamp'] for t in ticks1]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Order Flow (Tick Rule)")
                tc = st.session_state.microstructure.classify_trades_tick_rule(prices)
                
                st.metric("Order Flow Imbalance", f"{tc['order_flow_imbalance']:.3f}")
                st.caption(tc['interpretation'])
                
                # Pie chart
                fig = go.Figure(data=[go.Pie(
                    labels=['Buyer-initiated', 'Seller-initiated', 'Neutral'],
                    values=[tc['buyer_initiated'], tc['seller_initiated'], tc['neutral']],
                    marker_colors=['green', 'red', 'gray']
                )])
                fig.update_layout(title="Trade Classification", height=300)
                st.plotly_chart(fig, width='stretch')
                
                # Rolling OFI
                if len(prices) >= 20:
                    rofi = st.session_state.microstructure.rolling_order_flow(prices, volumes, window=20)
                    fig2 = go.Figure()
                    fig2.add_trace(go.Scatter(y=rofi['rolling_ofi'], name='Rolling OFI', 
                                             line=dict(color='blue')))
                    fig2.add_hline(y=0, line_dash='dash', line_color='gray')
                    fig2.update_layout(title="Rolling Order Flow Imbalance", height=250)
                    st.plotly_chart(fig2, width='stretch')
            
            with col2:
                st.subheader("Trade Intensity & VWAP")
                
                # Trade intensity
                ti = st.session_state.microstructure.trade_intensity(timestamps, window_ms=60000)
                st.metric("Trades per Minute", f"{ti['trades_per_window']:.1f}")
                st.metric("Mean Inter-arrival", f"{ti['mean_inter_arrival_ms']:.1f} ms")
                
                # VWAP
                vwap = st.session_state.microstructure.vwap_deviation(prices, volumes)
                st.metric("VWAP", f"${vwap['vwap']:.2f}")
                st.metric("Current vs VWAP", f"{vwap['deviation_pct']:+.2f}%", 
                         delta=vwap['interpretation'])
                
                # Effective spread
                es = st.session_state.microstructure.effective_spread(prices)
                st.metric("Mean Effective Spread", f"{es['mean_spread_pct']:.3f}%")
                
                st.info("**Microstructure insights:** Low spreads and high trade intensity indicate good liquidity.")
        
        except Exception as e:
            st.error(f"Microstructure analysis error: {e}")
    else:
        st.info(f"Collecting tick data... (have {len(ticks1)} ticks, need 50+)")

# Tab 11: Correlation Matrix
with tab11:
    st.header("🔗 Cross-Product Correlation Matrix")
    
    # Get all available symbols
    all_symbols = st.session_state.data_manager.get_available_symbols()
    
    # Let user select symbols for matrix
    selected_symbols = st.multiselect(
        "Select symbols for correlation matrix (3-10 recommended)",
        all_symbols,
        default=all_symbols[:min(5, len(all_symbols))]
    )
    
    if len(selected_symbols) >= 2:
        # Fetch data for selected symbols
        price_series = {}
        for sym in selected_symbols:
            bars = get_bars(dm, sym, agg_interval, agg_lookback)
            if len(bars) > 20:
                price_series[sym] = [d['close'] for d in bars]
        
        if len(price_series) >= 2:
            try:
                # Compute correlation matrix
                corr_result = st.session_state.corr_matrix.compute_correlation_matrix(
                    price_series, method='pearson'
                )
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Heatmap
                    hm_data = st.session_state.corr_matrix.correlation_heatmap_data(
                        corr_result['correlation_matrix'],
                        corr_result['symbols']
                    )
                    
                    fig = go.Figure(data=go.Heatmap(
                        z=hm_data['matrix'],
                        x=hm_data['x_labels'],
                        y=hm_data['y_labels'],
                        colorscale='RdBu',
                        zmid=0,
                        text=np.round(hm_data['matrix'], 2),
                        texttemplate='%{text}',
                        textfont={"size":10}
                    ))
                    fig.update_layout(title="Correlation Matrix", height=500)
                    st.plotly_chart(fig, width='stretch')
                
                with col2:
                    st.subheader("Top Pairs")
                    
                    best = corr_result['best_correlated']
                    st.success(f"**Highest:** {best['symbol1']}-{best['symbol2']}: {best['correlation']:.3f}")
                    
                    worst = corr_result['worst_correlated']
                    st.error(f"**Lowest:** {worst['symbol1']}-{worst['symbol2']}: {worst['correlation']:.3f}")
                    
                    st.markdown("---")
                    st.subheader("All Pairs (by correlation)")
                    pairs_df = pd.DataFrame(corr_result['pairs'][:15])  # Top 15
                    st.dataframe(pairs_df, width='stretch')
            
            except Exception as e:
                st.error(f"Correlation matrix error: {e}")
        else:
            st.warning("Not enough data for selected symbols")
    else:
        st.info("Select at least 2 symbols to compute correlation matrix")

# Tab 12: Time-Series Stats Table
with tab12:
    st.header("📋 Time-Series Statistics Table")
    
    st.markdown("""
    Comprehensive time-series table with all analytics features at each timestamp.
    Includes prices, spread, z-score, returns, correlation, volume, indicators, and trading signals.
    """)
    
    if len(data1) > 20 and len(data2) > 20:
        try:
            # Generate stats table
            with st.spinner("Generating time-series table..."):
                stats_df = st.session_state.timeseries_table.generate_stats_table(
                    data1, data2, symbol1, symbol2, 
                    hedge_ratio=ols_result['hedge_ratio'] if 'ols_result' in locals() else 1.0,
                    include_indicators=len(data1) >= 50
                )
            
            # Summary metrics at top
            summary = st.session_state.timeseries_table.generate_summary_stats(stats_df, symbol1, symbol2)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Observations", summary['time_period']['observations'])
                st.metric("Duration (min)", f"{summary['time_period']['duration_minutes']:.1f}")
            with col2:
                st.metric("Current Z-Score", f"{summary['zscore']['current']:.3f}")
                st.metric("Spread Mean", f"{summary['spread']['mean']:.4f}")
            with col3:
                st.metric("Overall Correlation", f"{summary['correlation']['overall']:.3f}")
                st.metric("Current Rolling Corr", f"{summary['correlation']['current_rolling']:.3f}")
            with col4:
                st.metric("Long Signals", summary['signals']['long_spread_count'])
                st.metric("Short Signals", summary['signals']['short_spread_count'])
            
            st.markdown("---")
            
            # Interactive table controls
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                show_rows = st.selectbox("Show rows", [10, 25, 50, 100, "All"], index=1)
            
            with col_b:
                sort_by = st.selectbox("Sort by", 
                    ['datetime', 'zscore', 'spread', f'{symbol1}_close', f'{symbol2}_close', 'rolling_corr_20'])
            
            with col_c:
                sort_order = st.radio("Order", ['Descending', 'Ascending'], horizontal=True)
            
            # Apply sorting
            ascending = (sort_order == 'Ascending')
            stats_df_sorted = stats_df.sort_values(by=sort_by, ascending=ascending)
            
            # Display table
            if show_rows == "All":
                display_df = stats_df_sorted
            else:
                display_df = stats_df_sorted.head(int(show_rows))
            
            st.dataframe(
                display_df.style.format({
                    col: "{:.6f}" for col in display_df.select_dtypes(include=[np.number]).columns
                }),
                width='stretch',
                height=400
            )
            
            # Column selector for export
            st.markdown("### 📥 Export Options")
            
            col_export_1, col_export_2 = st.columns(2)
            
            with col_export_1:
                export_cols = st.multiselect(
                    "Select columns to export (leave empty for all)",
                    options=list(stats_df.columns),
                    default=[]
                )
            
            with col_export_2:
                export_format = st.radio("Export format", ['CSV', 'JSON'], horizontal=True)
            
            # Export buttons
            export_df = stats_df[export_cols] if export_cols else stats_df
            # Ensure CSV data available regardless of selected export format (prevents undefined variable)
            try:
                csv_data = export_df.to_csv(index=False)
            except Exception:
                # Fallback: convert to CSV with simple str() representation
                csv_data = str(export_df)
            
            col_btn_1, col_btn_2, col_btn_3 = st.columns(3)
            
            with col_btn_1:
                if export_format == 'CSV':
                    csv_data = st.session_state.timeseries_table.export_to_csv(export_df)
                    st.download_button(
                        label="📥 Download Full Table (CSV)",
                        data=csv_data,
                        file_name=f"timeseries_stats_{symbol1}_{symbol2}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    json_data = export_df.to_json(orient='records', indent=2, date_format='iso')
                    st.download_button(
                        label="📥 Download Full Table (JSON)",
                        data=json_data,
                        file_name=f"timeseries_stats_{symbol1}_{symbol2}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
            
            with col_btn_2:
                # Summary stats export
                summary_json = json.dumps(summary, indent=2)
                st.download_button(
                    label="📊 Download Summary Stats",
                    data=summary_json,
                    file_name=f"summary_stats_{symbol1}_{symbol2}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            with col_btn_3:
                # Quick copy to clipboard (as CSV)
                st.code(csv_data[:500] + "\n... (truncated, use download button for full data)", language="text")
            
            # Additional insights
            with st.expander("📊 Additional Insights"):
                insight_col1, insight_col2 = st.columns(2)
                
                with insight_col1:
                    st.markdown("**Spread Statistics**")
                    st.write(f"- Mean: {summary['spread']['mean']:.4f}")
                    st.write(f"- Std Dev: {summary['spread']['std']:.4f}")
                    st.write(f"- Range: [{summary['spread']['min']:.4f}, {summary['spread']['max']:.4f}]")
                
                with insight_col2:
                    st.markdown("**Trading Signals Distribution**")
                    total_signals = sum(summary['signals'].values())
                    if total_signals > 0:
                        st.write(f"- Long: {summary['signals']['long_spread_count']} ({100*summary['signals']['long_spread_count']/total_signals:.1f}%)")
                        st.write(f"- Short: {summary['signals']['short_spread_count']} ({100*summary['signals']['short_spread_count']/total_signals:.1f}%)")
                        st.write(f"- Exit: {summary['signals']['exit_count']} ({100*summary['signals']['exit_count']/total_signals:.1f}%)")
                        st.write(f"- Neutral: {summary['signals']['neutral_count']} ({100*summary['signals']['neutral_count']/total_signals:.1f}%)")
            
            st.success("✅ Time-series table generated successfully!")
            
        except Exception as e:
            st.error(f"Error generating time-series table: {e}")
            import traceback
            with st.expander("Error details"):
                st.code(traceback.format_exc())
    else:
        st.warning(f"⏳ Need at least 20 bars for time-series table (currently: {symbol1}={len(data1)}, {symbol2}={len(data2)})")
        st.info("The table will include: timestamps, OHLC, spread, z-score, returns, correlation, volume, RSI, Bollinger Bands, and trading signals.")

# Auto-refresh
auto_refresh = st.checkbox("Auto-refresh (5s)", value=should_auto_refresh, 
                          help="Automatically enabled for first 5 minutes to accumulate data")

# Show live data status at bottom
status = st.session_state.data_manager.get_connection_status()
col1, col2, col3 = st.columns(3)
with col1:
    is_live = bool(status.get('connected')) or int(status.get('total_ticks', 0)) > 0 or int(status.get('active_symbols', 0)) > 0
    if is_live:
        st.success(f"🟢 LIVE: {status.get('active_symbols', 0)} active / {status.get('symbols', 0)} configured symbols streaming (ticks: {status.get('total_ticks', 0)})")
    else:
        st.error("🔴 Disconnected - Reconnecting...")
with col2:
    st.info(f"⏱️ Uptime: {int(elapsed_time//60)}m {int(elapsed_time%60)}s")
with col3:
    tick_count = st.session_state.data_manager.tick_count
    st.info(f"📊 Total ticks received: {tick_count:,}")

if auto_refresh:
    st.session_state.refresh_count += 1
    time.sleep(5)
    st.rerun()
