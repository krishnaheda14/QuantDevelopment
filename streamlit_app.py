"""Streamlit dashboard for GEMSCAP Quant Project."""
import streamlit as st
import requests
import pandas as pd
import time
from src.visualization.chart_builder import (
    candlestick_chart, line_chart, spread_chart, 
    correlation_heatmap, volume_chart
)
from src.visualization.dashboard_components import (
    render_header, render_metrics_row, render_data_table,
    render_alert_panel, render_symbol_selector, render_interval_selector,
    render_debug_panel
)

# Page config
st.set_page_config(
    page_title="GEMSCAP Quant Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API base URL
API_URL = "http://localhost:8000"

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/150x50?text=GEMSCAP", use_container_width=True)
    st.title("Controls")
    
    # Get symbols from API
    try:
        response = requests.get(f"{API_URL}/symbols", timeout=2)
        symbols = response.json().get("symbols", ["BTCUSDT", "ETHUSDT"])
    except:
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
    
    # Symbol selectors
    symbol1 = st.selectbox("Symbol 1", symbols, key="sym1")
    symbol2 = st.selectbox("Symbol 2", [s for s in symbols if s != symbol1], key="sym2")
    
    # Interval selector
    interval = st.radio("Interval", ["1s", "1m", "5m"], horizontal=True)
    
    # Window parameters
    st.subheader("Analytics Parameters")
    rolling_window = st.slider("Rolling Window", 10, 200, 50)
    zscore_threshold = st.slider("Z-Score Threshold", 1.0, 3.0, 2.0, 0.1)
    
    # Auto-refresh
    auto_refresh = st.checkbox("Auto-refresh", value=True)
    if auto_refresh:
        refresh_rate = st.slider("Refresh Rate (sec)", 1, 30, 5)
    # Pause auto-refresh when Debug tab is active
    pause_on_debug = st.checkbox("Pause auto-refresh when Debug tab active", value=True)

# Main content
render_header("GEMSCAP Quant Dashboard", "Real-time Quantitative Analytics")

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Price Charts", 
    "📈 Spread Analysis", 
    "🔗 Correlation", 
    "📉 Statistics",
    "🚨 Alerts",
    "🔧 Debug",
    "🖥️ System Status"
])

# Tab 1: Price Charts
with tab1:
    st.session_state['active_tab'] = 'price'
    st.header(f"Price Charts - {symbol1}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            response = requests.get(
                f"{API_URL}/ohlc/{symbol1}",
                params={"interval": interval, "limit": 100},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()["data"]
                
                if data:
                    # Metrics
                    latest = data[0]
                    render_metrics_row({
                        "Current Price": f"${latest['close']:,.2f}",
                        "24h High": f"${latest['high']:,.2f}",
                        "24h Low": f"${latest['low']:,.2f}",
                        "Volume": f"{latest['volume']:.4f}"
                    })
                    
                    # Candlestick chart
                    fig = candlestick_chart(data, f"{symbol1} - {interval}")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Volume chart
                    fig_vol = volume_chart(data, f"{symbol1} Volume")
                    st.plotly_chart(fig_vol, use_container_width=True)
                else:
                    st.warning("No data available yet. WebSocket is collecting data...")
                    # Debug
                    st.write("Debug: Price API response empty or missing fields")
            else:
                st.error(f"API Error: {response.status_code}")
                # Show debug details
                try:
                    st.write(response.text)
                except Exception:
                    pass
                
        except Exception as e:
            st.error(f"Failed to fetch data: {e}")
    
    with col2:
        # Same for symbol2
        try:
            response = requests.get(
                f"{API_URL}/ohlc/{symbol2}",
                params={"interval": interval, "limit": 100},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()["data"]
                
                if data:
                    latest = data[0]
                    render_metrics_row({
                        "Current Price": f"${latest['close']:,.2f}",
                        "Volume": f"{latest['volume']:.4f}"
                    })
                    
                    fig = candlestick_chart(data, f"{symbol2} - {interval}")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No data available yet")
                    st.write("Debug: Symbol2 OHLC empty")
            else:
                st.error(f"API Error: {response.status_code}")
                try:
                    st.write(response.text)
                except Exception:
                    pass
                
        except Exception as e:
            st.error(f"Failed to fetch data: {e}")

# Tab 2: Spread Analysis
with tab2:
    st.session_state['active_tab'] = 'spread'
    st.header(f"Spread Analysis: {symbol1} vs {symbol2}")
    
    try:
        response = requests.get(
            f"{API_URL}/analytics/spread",
            params={
                "symbol1": symbol1,
                "symbol2": symbol2,
                "interval": interval,
                "limit": 200
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()["data"]
            
            ols = result["ols"]
            spread = result["spread"]
            
            # Metrics
            render_metrics_row({
                "Hedge Ratio": f"{ols['hedge_ratio']:.4f}",
                "R-Squared": f"{ols['r_squared']:.4f}",
                "Current Z-Score": f"{spread['zscore']['current_zscore']:.4f}",
                "Current Spread": f"{spread['current_spread']:.4f}"
            })
            
            # Spread chart
            st.subheader("Spread & Z-Score")
            fig_spread = spread_chart(spread, f"{symbol1} vs {symbol2}")
            st.plotly_chart(fig_spread, use_container_width=True)
            
            # Trading signal
            zscore_val = spread['zscore']['current_zscore']
            
            if zscore_val > zscore_threshold:
                st.error(f"🔴 SHORT Signal: Z-score {zscore_val:.2f} > {zscore_threshold}")
            elif zscore_val < -zscore_threshold:
                st.success(f"🟢 LONG Signal: Z-score {zscore_val:.2f} < -{zscore_threshold}")
            elif abs(zscore_val) < 0.5:
                st.warning(f"🟡 EXIT Signal: Z-score near mean ({zscore_val:.2f})")
            else:
                st.info("⚪ HOLD: No clear signal")
            
            # Statistical summary
            with st.expander("📊 Statistical Details"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**OLS Regression**")
                    st.json(ols)
                
                with col2:
                    st.write("**Spread Statistics**")
                    st.write(f"Mean: {spread['spread_mean']:.4f}")
                    st.write(f"Std Dev: {spread['spread_std']:.4f}")
        else:
            st.error(f"API Error: {response.status_code}")
            # show server error details
            try:
                st.json(response.json())
            except Exception:
                st.write(response.text)
            
    except Exception as e:
        st.error(f"Spread analysis failed: {e}")
        st.exception(e)

# Tab 3: Correlation
with tab3:
    st.session_state['active_tab'] = 'correlation'
    st.header("Correlation Analysis")
    
    try:
        response = requests.get(
            f"{API_URL}/analytics/correlation",
            params={
                "symbol1": symbol1,
                "symbol2": symbol2,
                "interval": interval,
                "window": rolling_window
            },
            timeout=10
        )
        
        if response.status_code == 200:
            corr_result = response.json()["data"]
            
            # Current correlation
            st.metric("Current Correlation", f"{corr_result['current_correlation']:.4f}")
            
            # Rolling correlation chart
            rolling_corr = corr_result.get("rolling_values", [])
            if rolling_corr:
                fig = line_chart(
                    list(range(len(rolling_corr))),
                    rolling_corr,
                    "Rolling Correlation",
                    f"Rolling Correlation ({rolling_window} periods)"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Correlation stats
            with st.expander("Correlation Statistics"):
                st.json(corr_result)
        else:
            st.error(f"API Error: {response.status_code}")
            try:
                st.json(response.json())
            except Exception:
                st.write(response.text)
            
    except Exception as e:
        st.error(f"Correlation analysis failed: {e}")
        st.exception(e)

# Tab 4: Statistics
with tab4:
    st.session_state['active_tab'] = 'statistics'
    st.header("Statistical Tests")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"ADF Test - {symbol1}")
        try:
            response = requests.get(
                f"{API_URL}/analytics/adf",
                params={"symbol": symbol1, "interval": interval},
                timeout=10
            )
            
            if response.status_code == 200:
                adf_result = response.json()["data"]
                
                is_stationary = adf_result["is_stationary"]
                
                if is_stationary:
                    st.success(f"✅ Stationary (p-value: {adf_result['p_value']:.4f})")
                else:
                    st.warning(f"❌ Non-stationary (p-value: {adf_result['p_value']:.4f})")
                
                st.json(adf_result)
            else:
                st.error(f"API Error: {response.status_code}")
                try:
                    st.json(response.json())
                except Exception:
                    st.write(response.text)
                
        except Exception as e:
            st.error(f"ADF test failed: {e}")
            st.exception(e)
    
    with col2:
        st.subheader(f"ADF Test - {symbol2}")
        try:
            response = requests.get(
                f"{API_URL}/analytics/adf",
                params={"symbol": symbol2, "interval": interval},
                timeout=10
            )
            
            if response.status_code == 200:
                adf_result = response.json()["data"]
                
                is_stationary = adf_result["is_stationary"]
                
                if is_stationary:
                    st.success(f"✅ Stationary (p-value: {adf_result['p_value']:.4f})")
                else:
                    st.warning(f"❌ Non-stationary (p-value: {adf_result['p_value']:.4f})")
                
                st.json(adf_result)
            else:
                st.error(f"API Error: {response.status_code}")
                try:
                    st.json(response.json())
                except Exception:
                    st.write(response.text)
                
        except Exception as e:
            st.error(f"ADF test failed: {e}")
            st.exception(e)

# Tab 5: Alerts
with tab5:
    st.session_state['active_tab'] = 'alerts'
    st.header("Alert Management")
    
    try:
        response = requests.get(f"{API_URL}/debug/system", timeout=5)
        
        if response.status_code == 200:
            system_data = response.json()
            
            if "components" in system_data and "alert_manager" in system_data["components"]:
                alert_stats = system_data["components"]["alert_manager"]
                
                render_metrics_row({
                    "Active Rules": alert_stats.get("active_rules", 0),
                    "Checks Performed": alert_stats.get("checks_performed", 0),
                    "Recent Alerts": alert_stats.get("recent_alerts_count", 0)
                })
                
                st.write("**Active Rules:**", ", ".join(alert_stats.get("rule_names", [])))
            
            # Note: Would need to add alert history endpoint to show actual alerts
            st.info("Alert history display requires additional API endpoint implementation")
            
        else:
            st.error("Failed to fetch alert data")
            try:
                st.write(response.text)
            except Exception:
                pass
            
    except Exception as e:
        st.error(f"Alert fetch failed: {e}")

# Tab 6: Debug
with tab6:
    st.session_state['active_tab'] = 'debug'
    st.header("System Debug")
    
    try:
        response = requests.get(f"{API_URL}/debug/system", timeout=5)
        
        if response.status_code == 200:
            system_data = response.json()
            
            st.subheader("System Status")
            st.json(system_data["config"])
            
            st.subheader("Component Health")
            components = system_data.get("components", {})
            
            for component, data in components.items():
                with st.expander(f"📦 {component.replace('_', ' ').title()}"):
                    st.json(data)
            
            # Test API endpoints
            st.subheader("API Endpoint Tests")
            
            if st.button("Test Health Endpoint"):
                try:
                    resp = requests.get(f"{API_URL}/health", timeout=2)
                    st.json(resp.json())
                except Exception as e:
                    st.error(f"Health check failed: {e}")
            
            if st.button("Test Symbols Endpoint"):
                try:
                    resp = requests.get(f"{API_URL}/symbols", timeout=2)
                    st.json(resp.json())
                except Exception as e:
                    st.error(f"Symbols fetch failed: {e}")
            
        else:
            st.error(f"Debug data unavailable: {response.status_code}")
            try:
                st.write(response.text)
            except Exception:
                pass
            
    except Exception as e:
        st.error(f"Debug panel error: {e}")

# Tab 7: System Status
with tab7:
    st.session_state['active_tab'] = 'system_status'
    st.header("🖥️ System Status - Backend & Frontend")
    
    # Backend Status
    st.subheader("Backend Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**API Health Check**")
        try:
            response = requests.get(f"{API_URL}/health", timeout=2)
            if response.status_code == 200:
                health = response.json()
                st.success("✅ API is healthy")
                st.metric("Response Time", f"{health.get('response_time_ms', 0):.2f} ms")
            else:
                st.error(f"❌ API returned {response.status_code}")
        except Exception as e:
            st.error(f"❌ API unreachable: {e}")
    
    with col2:
        st.write("**Symbols Available**")
        try:
            response = requests.get(f"{API_URL}/symbols", timeout=2)
            if response.status_code == 200:
                syms = response.json().get("symbols", [])
                st.success(f"✅ {len(syms)} symbols")
                st.write(", ".join(syms))
            else:
                st.error("Failed to fetch symbols")
        except Exception as e:
            st.error(f"Error: {e}")
    
    st.divider()
    
    # Comprehensive Diagnostics
    st.subheader("Detailed Diagnostics")
    
    try:
        response = requests.get(f"{API_URL}/debug/diagnostics", timeout=5)
        
        if response.status_code == 200:
            diag = response.json()
            
            # WebSocket Status
            st.write("**🌐 WebSocket Connection**")
            ws_diag = diag.get("websocket", {})
            if "error" in ws_diag:
                st.error(f"WebSocket Error: {ws_diag['error']}")
            else:
                ws_col1, ws_col2, ws_col3 = st.columns(3)
                with ws_col1:
                    st.metric("Mode", ws_diag.get("mode", "N/A"))
                with ws_col2:
                    connected = ws_diag.get("connected", False)
                    st.metric("Connected", "✅ Yes" if connected else "❌ No")
                with ws_col3:
                    st.metric("Total Ticks", ws_diag.get("total_ticks", 0))
                
                # Per-symbol tick counts
                st.write("**Tick Counts per Symbol:**")
                tick_counts = ws_diag.get("tick_counts", {})
                if tick_counts:
                    tick_df = pd.DataFrame(list(tick_counts.items()), columns=["Symbol", "Ticks"])
                    st.dataframe(tick_df, use_container_width=True)
                else:
                    st.warning("No ticks received yet")
            
            st.divider()
            
            # Redis Status
            st.write("**📡 Redis Status**")
            redis_diag = diag.get("redis", {})
            if "error" in redis_diag:
                st.error(f"Redis Error: {redis_diag['error']}")
            else:
                redis_col1, redis_col2, redis_col3 = st.columns(3)
                with redis_col1:
                    st.metric("Status", "✅ Connected" if redis_diag.get("connected") else "❌ Disconnected")
                with redis_col2:
                    memory = redis_diag.get("memory", {})
                    st.metric("Memory Used", memory.get("used_memory", "N/A"))
                with redis_col3:
                    st.metric("Total Keys", memory.get("total_keys", 0))
                
                # Sample data from Redis
                st.write("**Sample Data in Redis:**")
                sample_data = redis_diag.get("sample_data", {})
                if sample_data:
                    for sym, data in sample_data.items():
                        with st.expander(f"📊 {sym}"):
                            if "error" in data:
                                st.error(data["error"])
                            else:
                                st.write(f"Count: {data.get('count', 0)}")
                                if data.get("sample"):
                                    st.json(data["sample"])
                                else:
                                    st.info("No sample data available")
                else:
                    st.warning("No sample data available")
            
            st.divider()
            
            # Database Status
            st.write("**💾 Database Status**")
            db_diag = diag.get("database", {})
            if "error" in db_diag:
                st.error(f"Database Error: {db_diag['error']}")
            else:
                db_col1, db_col2 = st.columns(2)
                with db_col1:
                    st.metric("Status", "✅ Connected" if db_diag.get("connected") else "❌ Disconnected")
                with db_col2:
                    st.metric("Database", db_diag.get("database", "N/A"))
                
                # Table counts
                table_counts = db_diag.get("table_counts", {})
                if table_counts:
                    st.write("**Table Row Counts:**")
                    tables_df = pd.DataFrame(list(table_counts.items()), columns=["Table", "Rows"])
                    st.dataframe(tables_df, use_container_width=True)
            
            st.divider()
            
            # Data Processor Status
            st.write("**⚙️ Data Processor**")
            dp_diag = diag.get("data_processor", {})
            if "error" in dp_diag:
                st.error(f"Data Processor Error: {dp_diag['error']}")
            else:
                dp_col1, dp_col2, dp_col3 = st.columns(3)
                with dp_col1:
                    st.metric("Ticks Processed", dp_diag.get("ticks_processed", 0))
                with dp_col2:
                    st.metric("Errors", dp_diag.get("errors", 0))
                with dp_col3:
                    st.metric("Total Buffered", dp_diag.get("total_buffered", 0))
        else:
            st.error(f"Diagnostics unavailable: {response.status_code}")
            try:
                st.write(response.text)
            except Exception:
                pass
                
    except Exception as e:
        st.error(f"Failed to fetch diagnostics: {e}")
        st.exception(e)
    
    # Quick Actions
    st.divider()
    st.subheader("Quick Tests")
    
    test_col1, test_col2, test_col3 = st.columns(3)
    
    with test_col1:
        if st.button("Test /ohlc/BTCUSDT"):
            try:
                resp = requests.get(f"{API_URL}/ohlc/BTCUSDT?interval=1s&limit=10", timeout=3)
                st.write(f"Status: {resp.status_code}")
                if resp.status_code == 200:
                    data = resp.json()
                    st.write(f"Rows: {len(data.get('data', []))}")
                    if data.get('data'):
                        st.json(data['data'][0])
                else:
                    st.write(resp.text)
            except Exception as e:
                st.error(str(e))
    
    with test_col2:
        if st.button("Test /ticks/BTCUSDT"):
            try:
                resp = requests.get(f"{API_URL}/ticks/BTCUSDT?limit=5", timeout=3)
                st.write(f"Status: {resp.status_code}")
                if resp.status_code == 200:
                    data = resp.json()
                    st.write(f"Ticks: {len(data.get('data', []))}")
                    if data.get('data'):
                        st.json(data['data'][0])
                else:
                    st.write(resp.text)
            except Exception as e:
                st.error(str(e))
    
    with test_col3:
        if st.button("Test /analytics/spread"):
            try:
                resp = requests.get(
                    f"{API_URL}/analytics/spread?symbol1=BTCUSDT&symbol2=ETHUSDT&interval=1s&limit=50",
                    timeout=5
                )
                st.write(f"Status: {resp.status_code}")
                if resp.status_code == 200:
                    st.success("✅ Spread endpoint working")
                else:
                    st.write(resp.text)
            except Exception as e:
                st.error(str(e))

# Footer
st.divider()
st.caption(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")

# Auto-refresh
if auto_refresh:
    # Only auto-refresh when not paused for Debug tab
    active = st.session_state.get('active_tab', None)
    if not (pause_on_debug and active in ['debug', 'system_status']):
        time.sleep(refresh_rate)
        st.rerun()
