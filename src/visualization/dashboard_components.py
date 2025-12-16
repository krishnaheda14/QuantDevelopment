"""Streamlit dashboard components."""
import streamlit as st
import pandas as pd
from typing import Dict, Any, List


def render_header(title: str, subtitle: str = ""):
    """Render dashboard header."""
    st.title(title)
    if subtitle:
        st.markdown(f"*{subtitle}*")
    st.divider()


def render_metrics_row(metrics: Dict[str, Any]):
    """Render a row of metric cards."""
    cols = st.columns(len(metrics))
    
    for i, (label, value) in enumerate(metrics.items()):
        with cols[i]:
            if isinstance(value, dict):
                st.metric(label, value.get("value"), value.get("delta"))
            else:
                st.metric(label, value)


def render_data_table(data: List[Dict], title: str = "Data Table"):
    """Render data as table."""
    st.subheader(title)
    
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No data available")


def render_alert_panel(alerts: List[Dict]):
    """Render alert notifications."""
    st.subheader("🚨 Recent Alerts")
    
    if not alerts:
        st.success("No recent alerts")
        return
    
    for alert in alerts[:10]:  # Show last 10
        with st.expander(f"{alert['rule_name']} - {alert.get('symbol', 'N/A')}"):
            st.write(f"**Message:** {alert['message']}")
            st.write(f"**Time:** {pd.to_datetime(alert['timestamp'], unit='ms')}")
            st.write(f"**Value:** {alert.get('triggered_value', 'N/A'):.4f}")


def render_symbol_selector(symbols: List[str], key: str = "symbol"):
    """Render symbol selection dropdown."""
    return st.selectbox("Select Symbol", symbols, key=key)


def render_interval_selector(intervals: List[str] = ["1s", "1m", "5m"], key: str = "interval"):
    """Render interval selection."""
    return st.radio("Interval", intervals, horizontal=True, key=key)


def render_debug_panel(components: Dict[str, Any]):
    """Render system debug information."""
    st.subheader("🔧 System Debug")
    
    for component, status in components.items():
        if isinstance(status, dict):
            with st.expander(f"{component.title()}"):
                st.json(status)
        else:
            st.write(f"**{component}:** {status}")
