"""Plotly chart building utilities."""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Dict, Any


def candlestick_chart(ohlc_data: List[Dict], title: str = "OHLC Chart"):
    """Create candlestick chart."""
    df = pd.DataFrame(ohlc_data)
    
    if "timestamp" in df.columns:
        df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")
    
    fig = go.Figure(data=[go.Candlestick(
        x=df["datetime"] if "datetime" in df.columns else df.index,
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name="OHLC"
    )])
    
    fig.update_layout(
        title=title,
        xaxis_title="Time",
        yaxis_title="Price",
        template="plotly_white",
        height=500
    )
    
    return fig


def line_chart(x: List, y: List, name: str = "Series", title: str = "Line Chart"):
    """Create line chart."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name=name))
    
    fig.update_layout(
        title=title,
        xaxis_title="X",
        yaxis_title="Y",
        template="plotly_white",
        height=400
    )
    
    return fig


def spread_chart(spread_data: Dict[str, Any], title: str = "Spread Analysis"):
    """Create spread chart with z-score overlay."""
    spread = spread_data["spread"]
    zscore = spread_data["zscore"]["zscore"]
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        subplot_titles=("Spread", "Z-Score"),
        vertical_spacing=0.1
    )
    
    # Spread
    fig.add_trace(
        go.Scatter(y=spread, mode="lines", name="Spread", line=dict(color="blue")),
        row=1, col=1
    )
    
    # Z-score
    fig.add_trace(
        go.Scatter(y=zscore, mode="lines", name="Z-Score", line=dict(color="orange")),
        row=2, col=1
    )
    
    # Threshold lines
    fig.add_hline(y=2.0, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=-2.0, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=0, line_dash="dot", line_color="gray", row=2, col=1)
    
    fig.update_layout(
        title=title,
        height=600,
        template="plotly_white",
        showlegend=True
    )
    
    return fig


def correlation_heatmap(corr_matrix: List[List[float]], symbols: List[str], 
                        title: str = "Correlation Matrix"):
    """Create correlation heatmap."""
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix,
        x=symbols,
        y=symbols,
        colorscale="RdBu",
        zmid=0,
        text=[[f"{val:.2f}" for val in row] for row in corr_matrix],
        texttemplate="%{text}",
        textfont={"size": 10}
    ))
    
    fig.update_layout(
        title=title,
        height=500,
        template="plotly_white"
    )
    
    return fig


def volume_chart(ohlc_data: List[Dict], title: str = "Volume"):
    """Create volume bar chart."""
    df = pd.DataFrame(ohlc_data)
    
    if "timestamp" in df.columns:
        df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")
    
    fig = go.Figure(data=[go.Bar(
        x=df["datetime"] if "datetime" in df.columns else df.index,
        y=df["volume"],
        name="Volume",
        marker_color="lightblue"
    )])
    
    fig.update_layout(
        title=title,
        xaxis_title="Time",
        yaxis_title="Volume",
        template="plotly_white",
        height=300
    )
    
    return fig
