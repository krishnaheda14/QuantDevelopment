"""
Strategy Engine - Implements trading strategies and signal generation
"""

import numpy as np
from typing import List, Dict, Tuple

class StrategyEngine:
    """Multi-strategy engine for pairs trading"""
    
    def compute_spread(self, prices1: List[float], prices2: List[float], 
                      hedge_ratio: float, window: int = 20,
                      volatility_mult: float = 1.0) -> Dict:
        """
        Compute spread, z-score, and Bollinger Bands
        
        Args:
            prices1: Price series for asset 1
            prices2: Price series for asset 2
            hedge_ratio: Hedge ratio from OLS
            window: Rolling window for statistics
            volatility_mult: Multiplier for volatility (for what-if analysis)
        """
        prices1 = np.array(prices1)
        prices2 = np.array(prices2)
        
        # Compute spread
        spread = prices2 - hedge_ratio * prices1
        
        # Rolling mean and std
        if len(spread) >= window:
            rolling_mean = np.array([
                np.mean(spread[max(0, i-window):i+1]) 
                for i in range(len(spread))
            ])
            rolling_std = np.array([
                np.std(spread[max(0, i-window):i+1]) * volatility_mult
                for i in range(len(spread))
            ])
        else:
            rolling_mean = np.full(len(spread), np.mean(spread))
            rolling_std = np.full(len(spread), np.std(spread) * volatility_mult)
        
        # Z-score
        zscore = (spread - rolling_mean) / (rolling_std + 1e-8)
        
        # Bollinger Bands (2 std)
        bollinger_upper = rolling_mean + 2 * rolling_std
        bollinger_lower = rolling_mean - 2 * rolling_std
        
        return {
            'spread': spread.tolist(),
            'zscore': zscore.tolist(),
            'bollinger_ma': rolling_mean.tolist(),
            'bollinger_upper': bollinger_upper.tolist(),
            'bollinger_lower': bollinger_lower.tolist(),
            'rolling_std': rolling_std.tolist()
        }
    
    def generate_signals(self, zscore: List[float], 
                        entry_threshold: float = 2.0,
                        exit_threshold: float = 0.0) -> List[Dict]:
        """
        Generate trading signals based on z-score
        
        Returns list of signal events: {'index': int, 'type': 'long'|'short'|'exit', 'zscore': float}
        """
        signals = []
        position = None  # 'long', 'short', or None
        
        for i, z in enumerate(zscore):
            if position is None:
                if z < -entry_threshold:
                    signals.append({'index': i, 'type': 'long', 'zscore': z})
                    position = 'long'
                elif z > entry_threshold:
                    signals.append({'index': i, 'type': 'short', 'zscore': z})
                    position = 'short'
            else:
                # Exit conditions
                if position == 'long' and z > exit_threshold:
                    signals.append({'index': i, 'type': 'exit_long', 'zscore': z})
                    position = None
                elif position == 'short' and z < exit_threshold:
                    signals.append({'index': i, 'type': 'exit_short', 'zscore': z})
                    position = None
        
        return signals
    
    def check_alerts(self, zscore: float, rsi: float, macd_histogram: float,
                    zscore_threshold: float = 2.0,
                    rsi_oversold: float = 30,
                    rsi_overbought: float = 70) -> List[Dict]:
        """
        Check for alert conditions
        
        Returns list of alerts with severity and message
        """
        alerts = []
        
        # Z-score alerts
        if abs(zscore) > zscore_threshold:
            alerts.append({
                'type': 'zscore',
                'severity': 'high' if abs(zscore) > 3 else 'medium',
                'message': f"Z-Score extreme: {zscore:.2f}",
                'value': zscore
            })
        
        # RSI alerts
        if rsi < rsi_oversold:
            alerts.append({
                'type': 'rsi',
                'severity': 'medium',
                'message': f"RSI oversold: {rsi:.1f}",
                'value': rsi
            })
        elif rsi > rsi_overbought:
            alerts.append({
                'type': 'rsi',
                'severity': 'medium',
                'message': f"RSI overbought: {rsi:.1f}",
                'value': rsi
            })
        
        # MACD crossover alerts
        if abs(macd_histogram) > 0 and abs(macd_histogram) < 0.5:
            direction = "bullish" if macd_histogram > 0 else "bearish"
            alerts.append({
                'type': 'macd',
                'severity': 'low',
                'message': f"MACD {direction} crossover approaching",
                'value': macd_histogram
            })
        
        return alerts
    
    def calculate_position_size(self, capital: float, price1: float, price2: float,
                               hedge_ratio: float, risk_pct: float = 0.02) -> Tuple[float, float]:
        """
        Calculate position sizes for pairs trade
        
        Args:
            capital: Available capital
            price1: Current price of asset 1
            price2: Current price of asset 2
            hedge_ratio: Hedge ratio
            risk_pct: Risk percentage of capital per trade
        
        Returns:
            (quantity1, quantity2) positions
        """
        # Allocate risk capital
        risk_capital = capital * risk_pct
        
        # Calculate notional values maintaining hedge ratio
        # We want: qty2 * price2 = hedge_ratio * qty1 * price1
        # And: qty1 * price1 + qty2 * price2 = risk_capital
        
        # Solve: qty1 * price1 * (1 + hedge_ratio) = risk_capital
        qty1 = risk_capital / (price1 * (1 + hedge_ratio))
        qty2 = hedge_ratio * qty1
        
        return qty1, qty2
    
    def optimize_hedge_ratio(self, prices1: List[float], prices2: List[float],
                            method: str = 'ols') -> float:
        """
        Optimize hedge ratio using various methods
        
        Args:
            prices1: Price series 1
            prices2: Price series 2
            method: 'ols', 'total_least_squares', or 'correlation'
        
        Returns:
            Optimal hedge ratio
        """
        prices1 = np.array(prices1)
        prices2 = np.array(prices2)
        
        if method == 'ols':
            # Standard OLS
            X = np.column_stack([prices1, np.ones(len(prices1))])
            beta, _ = np.linalg.lstsq(X, prices2, rcond=None)[:2]
            return float(beta[0])
        
        elif method == 'total_least_squares':
            # Total Least Squares (orthogonal regression)
            A = np.column_stack([prices1, -prices2])
            _, _, V = np.linalg.svd(A)
            return float(V[-1, 0] / V[-1, 1])
        
        elif method == 'correlation':
            # Correlation-based
            corr = np.corrcoef(prices1, prices2)[0, 1]
            std_ratio = np.std(prices2) / np.std(prices1)
            return float(corr * std_ratio)
        
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def dynamic_hedge_ratio(self, prices1: List[float], prices2: List[float],
                           lookback: int = 50) -> List[float]:
        """
        Calculate rolling hedge ratio
        
        Returns time series of hedge ratios
        """
        prices1 = np.array(prices1)
        prices2 = np.array(prices2)
        
        hedge_ratios = []
        for i in range(lookback, len(prices1)):
            window1 = prices1[i-lookback:i]
            window2 = prices2[i-lookback:i]
            
            X = np.column_stack([window1, np.ones(len(window1))])
            beta, _ = np.linalg.lstsq(X, window2, rcond=None)[:2]
            hedge_ratios.append(float(beta[0]))
        
        return hedge_ratios
