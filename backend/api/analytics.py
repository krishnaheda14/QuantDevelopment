"""
Analytics API Endpoints
Real-time statistical analysis, spread calculation, OLS, ADF, correlation
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
import numpy as np

from ..services.analytics_service import AnalyticsService

router = APIRouter()
analytics_service = AnalyticsService()


class OLSRequest(BaseModel):
    symbol1: str
    symbol2: str
    lookback: int = 30  # minutes


class OLSResponse(BaseModel):
    hedge_ratio: float
    alpha: float
    r_squared: float
    adj_r_squared: float
    p_value: float
    std_err: float
    correlation: float
    observations: int
    timestamp: str


class SpreadRequest(BaseModel):
    symbol1: str
    symbol2: str
    lookback: int = 30
    hedge_ratio: Optional[float] = None  # If None, will compute OLS first


class SpreadResponse(BaseModel):
    spread: List[float]
    zscore: List[float]
    bollinger_upper: List[float]
    bollinger_lower: List[float]
    bollinger_ma: List[float]
    timestamps: List[int]
    current_zscore: float
    signal: str  # "LONG", "SHORT", "NEUTRAL"


class ADFRequest(BaseModel):
    symbol: str
    lookback: int = 60


class ADFResponse(BaseModel):
    adf_statistic: float
    p_value: float
    critical_values: dict
    is_stationary: bool
    observations: int


@router.post("/ols", response_model=OLSResponse)
async def compute_ols(request: OLSRequest):
    """
    Compute OLS regression for pairs trading
    Returns hedge ratio, R², correlation, etc.
    """
    try:
        result = await analytics_service.compute_ols(
            request.symbol1,
            request.symbol2,
            request.lookback
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/spread", response_model=SpreadResponse)
async def compute_spread(request: SpreadRequest):
    """
    Compute spread, z-score, and Bollinger Bands
    Generates trading signals based on z-score thresholds
    """
    try:
        result = await analytics_service.compute_spread(
            request.symbol1,
            request.symbol2,
            request.lookback,
            request.hedge_ratio
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/adf", response_model=ADFResponse)
async def adf_test(request: ADFRequest):
    """
    Augmented Dickey-Fuller test for stationarity
    Tests if a time series has a unit root
    """
    try:
        result = await analytics_service.adf_test(
            request.symbol,
            request.lookback
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cointegration/{symbol1}/{symbol2}")
async def cointegration_test(
    symbol1: str,
    symbol2: str,
    lookback: int = Query(60, ge=20, le=1440)
):
    """
    Johansen cointegration test
    Tests if two time series are cointegrated
    """
    try:
        result = await analytics_service.cointegration_test(
            symbol1,
            symbol2,
            lookback
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/correlation/{symbol1}/{symbol2}")
async def rolling_correlation(
    symbol1: str,
    symbol2: str,
    window: int = Query(30, ge=10, le=120),
    lookback: int = Query(60, ge=20, le=1440)
):
    """
    Rolling correlation between two symbols
    Returns time series of correlation values
    """
    try:
        result = await analytics_service.rolling_correlation(
            symbol1,
            symbol2,
            window,
            lookback
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indicators/{symbol}")
async def technical_indicators(
    symbol: str,
    indicators: List[str] = Query(["rsi", "macd", "bollinger"]),
    lookback: int = Query(60, ge=20, le=1440)
):
    """
    Compute technical indicators (RSI, MACD, Bollinger, etc.)
    Returns requested indicators for the symbol
    """
    try:
        result = await analytics_service.compute_indicators(
            symbol,
            indicators,
            lookback
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
