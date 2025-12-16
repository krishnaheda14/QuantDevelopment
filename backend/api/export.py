"""
Export API Endpoints
Data export in various formats (CSV, JSON, Parquet)
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, Response
from typing import List, Optional
import io
import json
import pandas as pd
from datetime import datetime

router = APIRouter()


@router.get("/csv/ohlc/{symbol}")
async def export_ohlc_csv(
    symbol: str,
    interval: str = Query("1m", regex="^(1s|1m|5m|15m|1h)$"),
    limit: int = Query(1000, ge=1, le=10000)
):
    """
    Export OHLC data as CSV
    Returns streaming CSV response
    """
    from ..services.data_ingestion import data_service
    
    try:
        # Get OHLC data
        data = await data_service.get_ohlc(symbol, interval, limit)
        
        if not data:
            raise HTTPException(status_code=404, detail="No data available")
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Convert timestamp to datetime
        if 'timestamp' in df.columns:
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Generate CSV
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={symbol}_{interval}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/csv/spread/{symbol1}/{symbol2}")
async def export_spread_csv(
    symbol1: str,
    symbol2: str,
    lookback: int = Query(60, ge=20, le=1440)
):
    """
    Export spread analysis as CSV
    Includes spread, z-score, Bollinger bands
    """
    from ..services.analytics_service import analytics_service
    
    try:
        # Compute spread
        spread_data = await analytics_service.compute_spread(
            symbol1, symbol2, lookback
        )
        
        # Create DataFrame
        df = pd.DataFrame({
            'timestamp': spread_data['timestamps'],
            'spread': spread_data['spread'],
            'zscore': spread_data['zscore'],
            'bollinger_upper': spread_data['bollinger_upper'],
            'bollinger_lower': spread_data['bollinger_lower'],
            'bollinger_ma': spread_data['bollinger_ma']
        })
        
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Generate CSV
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=spread_{symbol1}_{symbol2}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/json/analytics")
async def export_analytics_json(
    symbol1: str,
    symbol2: str,
    lookback: int = Query(60, ge=20, le=1440)
):
    """
    Export comprehensive analytics as JSON
    Includes OLS, spread, ADF, cointegration, indicators
    """
    from ..services.analytics_service import analytics_service
    
    try:
        # Gather all analytics
        ols = await analytics_service.compute_ols(symbol1, symbol2, lookback)
        spread = await analytics_service.compute_spread(symbol1, symbol2, lookback)
        adf1 = await analytics_service.adf_test(symbol1, lookback)
        adf2 = await analytics_service.adf_test(symbol2, lookback)
        cointegration = await analytics_service.cointegration_test(symbol1, symbol2, lookback)
        indicators1 = await analytics_service.compute_indicators(symbol1, ["rsi", "macd"], lookback)
        indicators2 = await analytics_service.compute_indicators(symbol2, ["rsi", "macd"], lookback)
        
        # Build export package
        export_package = {
            "metadata": {
                "symbol1": symbol1,
                "symbol2": symbol2,
                "lookback_minutes": lookback,
                "export_timestamp": datetime.now().isoformat()
            },
            "ols_regression": ols,
            "spread_analysis": spread,
            "adf_tests": {
                symbol1: adf1,
                symbol2: adf2
            },
            "cointegration": cointegration,
            "technical_indicators": {
                symbol1: indicators1,
                symbol2: indicators2
            }
        }
        
        return Response(
            content=json.dumps(export_package, indent=2, default=str),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=analytics_{symbol1}_{symbol2}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/json/alerts")
async def export_alerts_json(limit: int = Query(1000, ge=1, le=10000)):
    """
    Export alert history as JSON
    """
    from ..services.alert_engine import alert_engine
    
    try:
        alerts = await alert_engine.get_alert_history(limit)
        
        export_package = {
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "total_alerts": len(alerts)
            },
            "alerts": alerts
        }
        
        return Response(
            content=json.dumps(export_package, indent=2, default=str),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
