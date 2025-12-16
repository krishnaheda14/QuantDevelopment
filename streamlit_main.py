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
    initial_sidebar_state="expanded"
)

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

# Initialize session state
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = DataManager()
    st.session_state.strategy_engine = StrategyEngine()
    st.session_state.indicators = TechnicalIndicators()
    st.session_state.stats = StatisticalAnalytics()
    st.session_state.backtester = Backtester()
    st.session_state.alerts = []
    st.session_state.start_time = time.time()
    st.session_state.refresh_count = 0

# Check if we should auto-refresh (first 5 minutes or until we have data)
elapsed_time = time.time() - st.session_state.start_time
should_auto_refresh = elapsed_time < 300  # Auto-refresh for first 5 minutes

# Sidebar
with st.sidebar:
    st.title("📊 GEMSCAP Quant")
    
    # Connection Status (Top of sidebar)
    status = st.session_state.data_manager.get_connection_status()
    if status['connected']:
        st.success(f"🟢 Live: {status['symbols']} symbols")
    else:
        st.error("🔴 Disconnected - Reconnecting...")
    
    st.markdown("---")
    
    # Symbol selection
    symbols = st.session_state.data_manager.get_available_symbols()
    print(f"[DEBUG] Available symbols: {len(symbols)} - {symbols[:3]}...")
    
    st.subheader("Pair Selection")
    symbol1 = st.selectbox("Symbol 1", symbols, index=0)
    symbol2 = st.selectbox("Symbol 2", symbols, index=1)
    
    st.markdown("---")
    st.subheader("Time Window")
    lookback = st.slider("Lookback (minutes)", 5, 60, 15)
    
    st.markdown("---")
    st.subheader("Strategy Settings")
    zscore_entry = st.number_input("Z-Score Entry", 1.0, 5.0, 2.0, 0.5)
    zscore_exit = st.number_input("Z-Score Exit", -1.0, 1.0, 0.0, 0.25)
    
    rsi_oversold = st.slider("RSI Oversold", 10, 40, 30)
    rsi_overbought = st.slider("RSI Overbought", 60, 90, 70)
    
    st.markdown("---")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()
    
    if st.button("📥 Export All", use_container_width=True):
        st.session_state.export_trigger = True

# Data accumulation status banner
st.markdown("### 📡 GEMSCAP Real-Time Quantitative Trading System")

# Get quick data check for both symbols
quick_data1 = st.session_state.data_manager.get_ohlc(symbol1, '1m', 1)
quick_data2 = st.session_state.data_manager.get_ohlc(symbol2, '1m', 1)
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

# Main content
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Spread Analysis",
    "🎯 Strategy Signals", 
    "📊 Statistical Tests",
    "🔍 Backtesting",
    "🔔 Alerts",
    "⚙️ System"
])

# Tab 1: Spread Analysis
with tab1:
    st.header(f"Pairs Trading: {symbol1} / {symbol2}")
    
    # Get data with debugging
    print(f"[DEBUG] Fetching OHLC for {symbol1} and {symbol2}, lookback={lookback}min")
    data1 = st.session_state.data_manager.get_ohlc(symbol1, '1m', lookback)
    data2 = st.session_state.data_manager.get_ohlc(symbol2, '1m', lookback)
    
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
        prices1 = [d['close'] for d in data1]
        prices2 = [d['close'] for d in data2]
        timestamps = [d['timestamp'] for d in data1]
        
        # Compute OLS and spread
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
        
        # Price series
        fig.add_trace(go.Scatter(x=timestamps, y=prices1, name=symbol1, 
                                line=dict(color='orange')), row=3, col=1)
        fig.add_trace(go.Scatter(x=timestamps, y=prices2, name=symbol2,
                                line=dict(color='cyan')), row=3, col=1)
        
        fig.update_layout(height=800, showlegend=True, hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)
        
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
        fig.add_trace(go.Scatter(x=timestamps, y=prices, name="Price"), row=1, col=1)
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
        st.plotly_chart(fig, use_container_width=True)
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
                if adf_result['is_stationary']:
                    st.success("✅ Stationary")
                else:
                    st.warning("❌ Non-stationary")
                with st.expander("Details"):
                    st.json(adf_result)
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col2:
        st.subheader(f"ADF Test - {symbol2}")
        if len(data2) > 20:
            try:
                prices = [d['close'] for d in data2]
                adf_result = st.session_state.stats.adf_test(prices)
                st.metric("ADF Statistic", f"{adf_result['adf_statistic']:.4f}")
                st.metric("P-Value", f"{adf_result['p_value']:.4f}")
                if adf_result['is_stationary']:
                    st.success("✅ Stationary")
                else:
                    st.warning("❌ Non-stationary")
                with st.expander("Details"):
                    st.json(adf_result)
            except Exception as e:
                st.error(f"Error: {e}")
    
    st.markdown("---")
    if len(data1) > 20 and len(data2) > 20:
        st.subheader("Cointegration Test")
        try:
            prices1 = [d['close'] for d in data1]
            prices2 = [d['close'] for d in data2]
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
                st.plotly_chart(fig, use_container_width=True)
                
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
    recent_data = st.session_state.data_manager.get_ohlc(symbol1, '1m', 10)
    if recent_data:
        df = pd.DataFrame(recent_data)
        st.dataframe(df, use_container_width=True)
    
    # Export functionality
    if st.session_state.get('export_trigger', False):
        st.subheader("📥 Exporting Data")
        
        # Prepare export package
        export_data = {
            'ohlc_data': {
                symbol1: st.session_state.data_manager.get_ohlc(symbol1, '1m', 1000),
                symbol2: st.session_state.data_manager.get_ohlc(symbol2, '1m', 1000)
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

# Auto-refresh
auto_refresh = st.checkbox("Auto-refresh (5s)", value=should_auto_refresh, 
                          help="Automatically enabled for first 5 minutes to accumulate data")

# Show live data status at bottom
status = st.session_state.data_manager.get_connection_status()
col1, col2, col3 = st.columns(3)
with col1:
    if status['connected']:
        st.success(f"🟢 LIVE: {status['symbols']} symbols streaming")
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
