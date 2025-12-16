"""
Technical Indicators - RSI, MACD, Bollinger Bands, etc.
"""

import numpy as np
from typing import List, Dict, Tuple

class TechnicalIndicators:
    """Technical analysis indicators"""
    
    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> List[float]:
        """
        Relative Strength Index
        
        Args:
            prices: Price series
            period: RSI period (default 14)
        
        Returns:
            RSI values (0-100)
        """
        if len(prices) < period + 1:
            return []
        
        prices = np.array(prices)
        deltas = np.diff(prices)
        
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # Calculate average gains and losses
        avg_gain = np.zeros(len(prices))
        avg_loss = np.zeros(len(prices))
        
        # Initial averages
        avg_gain[period] = np.mean(gains[:period])
        avg_loss[period] = np.mean(losses[:period])
        
        # Smoothed averages
        for i in range(period + 1, len(prices)):
            avg_gain[i] = (avg_gain[i-1] * (period - 1) + gains[i-1]) / period
            avg_loss[i] = (avg_loss[i-1] * (period - 1) + losses[i-1]) / period
        
        # Calculate RSI
        rs = avg_gain / (avg_loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi[period:].tolist()
    
    @staticmethod
    def macd(prices: List[float], fast: int = 12, slow: int = 26, 
             signal: int = 9) -> Dict[str, List[float]]:
        """
        Moving Average Convergence Divergence
        
        Args:
            prices: Price series
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period
        
        Returns:
            Dict with 'macd', 'signal', 'histogram'
        """
        if len(prices) < slow + signal:
            return {'macd': [], 'signal': [], 'histogram': []}
        
        prices = np.array(prices)
        
        # Calculate EMAs
        ema_fast = TechnicalIndicators._ema(prices, fast)
        ema_slow = TechnicalIndicators._ema(prices, slow)
        
        # MACD line
        macd_line = ema_fast - ema_slow
        
        # Signal line
        signal_line = TechnicalIndicators._ema(macd_line, signal)
        
        # Histogram
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line.tolist(),
            'signal': signal_line.tolist(),
            'histogram': histogram.tolist()
        }
    
    @staticmethod
    def _ema(prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average"""
        ema = np.zeros(len(prices))
        ema[0] = prices[0]
        
        multiplier = 2 / (period + 1)
        for i in range(1, len(prices)):
            ema[i] = (prices[i] * multiplier) + (ema[i-1] * (1 - multiplier))
        
        return ema
    
    @staticmethod
    def bollinger_bands(prices: List[float], period: int = 20, 
                       std_dev: float = 2.0) -> Dict[str, List[float]]:
        """
        Bollinger Bands
        
        Args:
            prices: Price series
            period: Moving average period
            std_dev: Number of standard deviations
        
        Returns:
            Dict with 'upper', 'middle', 'lower'
        """
        if len(prices) < period:
            return {'upper': [], 'middle': [], 'lower': []}
        
        prices = np.array(prices)
        
        # Calculate rolling mean and std
        middle = np.array([
            np.mean(prices[max(0, i-period):i+1])
            for i in range(len(prices))
        ])
        
        rolling_std = np.array([
            np.std(prices[max(0, i-period):i+1])
            for i in range(len(prices))
        ])
        
        upper = middle + (rolling_std * std_dev)
        lower = middle - (rolling_std * std_dev)
        
        return {
            'upper': upper.tolist(),
            'middle': middle.tolist(),
            'lower': lower.tolist()
        }
    
    @staticmethod
    def stochastic(highs: List[float], lows: List[float], closes: List[float],
                  period: int = 14, smooth_k: int = 3, smooth_d: int = 3) -> Dict[str, List[float]]:
        """
        Stochastic Oscillator
        
        Args:
            highs: High prices
            lows: Low prices
            closes: Close prices
            period: Look-back period
            smooth_k: %K smoothing period
            smooth_d: %D smoothing period
        
        Returns:
            Dict with '%K' and '%D' lines
        """
        if len(closes) < period:
            return {'%K': [], '%D': []}
        
        highs = np.array(highs)
        lows = np.array(lows)
        closes = np.array(closes)
        
        # Calculate %K
        k_values = []
        for i in range(period - 1, len(closes)):
            highest = np.max(highs[i-period+1:i+1])
            lowest = np.min(lows[i-period+1:i+1])
            
            if highest == lowest:
                k = 50
            else:
                k = 100 * (closes[i] - lowest) / (highest - lowest)
            
            k_values.append(k)
        
        k_values = np.array(k_values)
        
        # Smooth %K
        k_smooth = TechnicalIndicators._sma(k_values, smooth_k)
        
        # Calculate %D (SMA of %K)
        d_smooth = TechnicalIndicators._sma(k_smooth, smooth_d)
        
        return {
            '%K': k_smooth.tolist(),
            '%D': d_smooth.tolist()
        }
    
    @staticmethod
    def _sma(prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return prices
        
        sma = np.convolve(prices, np.ones(period)/period, mode='valid')
        # Pad beginning with first values
        pad = np.full(period - 1, sma[0])
        return np.concatenate([pad, sma])
    
    @staticmethod
    def atr(highs: List[float], lows: List[float], closes: List[float],
            period: int = 14) -> List[float]:
        """
        Average True Range
        
        Args:
            highs: High prices
            lows: Low prices
            closes: Close prices
            period: ATR period
        
        Returns:
            ATR values
        """
        if len(closes) < period + 1:
            return []
        
        highs = np.array(highs)
        lows = np.array(lows)
        closes = np.array(closes)
        
        # Calculate True Range
        tr = np.maximum(
            highs[1:] - lows[1:],
            np.maximum(
                np.abs(highs[1:] - closes[:-1]),
                np.abs(lows[1:] - closes[:-1])
            )
        )
        
        # Calculate ATR (EMA of TR)
        atr = np.zeros(len(tr))
        atr[0] = np.mean(tr[:period])
        
        multiplier = 1 / period
        for i in range(1, len(tr)):
            atr[i] = (tr[i] * multiplier) + (atr[i-1] * (1 - multiplier))
        
        return atr[period-1:].tolist()
    
    @staticmethod
    def obv(closes: List[float], volumes: List[float]) -> List[float]:
        """
        On-Balance Volume
        
        Args:
            closes: Close prices
            volumes: Volume data
        
        Returns:
            OBV values
        """
        closes = np.array(closes)
        volumes = np.array(volumes)
        
        obv = np.zeros(len(closes))
        obv[0] = volumes[0]
        
        for i in range(1, len(closes)):
            if closes[i] > closes[i-1]:
                obv[i] = obv[i-1] + volumes[i]
            elif closes[i] < closes[i-1]:
                obv[i] = obv[i-1] - volumes[i]
            else:
                obv[i] = obv[i-1]
        
        return obv.tolist()
    
    @staticmethod
    def vwap(highs: List[float], lows: List[float], closes: List[float],
             volumes: List[float]) -> List[float]:
        """
        Volume Weighted Average Price
        
        Args:
            highs: High prices
            lows: Low prices
            closes: Close prices
            volumes: Volume data
        
        Returns:
            VWAP values
        """
        highs = np.array(highs)
        lows = np.array(lows)
        closes = np.array(closes)
        volumes = np.array(volumes)
        
        typical_price = (highs + lows + closes) / 3
        cumulative_tpv = np.cumsum(typical_price * volumes)
        cumulative_volume = np.cumsum(volumes)
        
        vwap = cumulative_tpv / (cumulative_volume + 1e-10)
        
        return vwap.tolist()
