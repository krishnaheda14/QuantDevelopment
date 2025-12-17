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

    def momentum_strategy(self, prices: List[float], lookback: int = 20, 
                          threshold: float = 0.02) -> Dict:
        """
        Momentum strategy based on rate of change.
        
        Args:
            prices: Price series
            lookback: Lookback period for momentum calculation
            threshold: Threshold for signal generation (e.g., 2% = 0.02)
        
        Returns:
            Dictionary with momentum values, signals, and interpretation
        """
        prices_arr = np.array(prices)
        
        if len(prices_arr) < lookback + 1:
            return {
                "momentum": [],
                "signals": [],
                "current_momentum": 0.0,
                "interpretation": "Insufficient data"
            }
        
        # Calculate rolling momentum (rate of change)
        momentum = []
        for i in range(lookback, len(prices_arr)):
            roc = (prices_arr[i] - prices_arr[i - lookback]) / prices_arr[i - lookback]
            momentum.append(roc)
        
        momentum_arr = np.array(momentum)
        
        # Generate signals
        signals = []
        for i, mom in enumerate(momentum_arr):
            if mom > threshold:
                signals.append({"index": i + lookback, "type": "buy", "momentum": mom})
            elif mom < -threshold:
                signals.append({"index": i + lookback, "type": "sell", "momentum": mom})
        
        current_momentum = float(momentum_arr[-1]) if len(momentum_arr) > 0 else 0.0
        
        # Interpretation
        if current_momentum > threshold:
            interpretation = "Strong upward momentum"
        elif current_momentum < -threshold:
            interpretation = "Strong downward momentum"
        else:
            interpretation = "Weak/neutral momentum"
        
        return {
            "momentum": momentum_arr.tolist(),
            "signals": signals,
            "current_momentum": current_momentum,
            "lookback": lookback,
            "threshold": threshold,
            "interpretation": interpretation
        }
    
    def pairs_rotation_strategy(self, pairs_data: Dict[str, Dict[str, List[float]]], 
                                 rotation_window: int = 30) -> Dict:
        """
        Pairs rotation strategy: select best-performing pair based on multiple criteria.
        
        Args:
            pairs_data: Dictionary mapping pair names to {"prices1": [...], "prices2": [...]}
            rotation_window: Window for performance evaluation
        
        Returns:
            Rankings and recommended pair to trade
        """
        if not pairs_data:
            return {
                "rankings": [],
                "best_pair": None,
                "reason": "No pairs data provided"
            }
        
        pair_scores = []
        
        for pair_name, data in pairs_data.items():
            prices1 = np.array(data.get("prices1", []))
            prices2 = np.array(data.get("prices2", []))
            
            if len(prices1) < rotation_window or len(prices2) < rotation_window:
                continue
            
            # Criteria 1: Correlation strength (want high correlation)
            recent1 = prices1[-rotation_window:]
            recent2 = prices2[-rotation_window:]
            correlation = np.corrcoef(recent1, recent2)[0, 1]
            
            # Criteria 2: Spread stationarity proxy (lower variance is better)
            spread = recent2 - (np.mean(recent2) / np.mean(recent1)) * recent1
            spread_volatility = np.std(spread) / np.mean(np.abs(spread)) if np.mean(np.abs(spread)) > 0 else 1.0
            
            # Criteria 3: Recent mean reversion (spread returning to mean)
            spread_mean = np.mean(spread)
            recent_spread = spread[-5:]  # Last 5 observations
            reversion_score = -np.mean(np.abs(recent_spread - spread_mean))  # Negative distance from mean
            
            # Combined score (higher is better)
            # Normalize and weight criteria
            score = (
                0.4 * correlation +  # High correlation is good
                0.3 * (1.0 / (1.0 + spread_volatility)) +  # Low volatility is good
                0.3 * reversion_score  # Near mean is good
            )
            
            pair_scores.append({
                "pair_name": pair_name,
                "score": float(score),
                "correlation": float(correlation),
                "spread_volatility": float(spread_volatility),
                "reversion_score": float(reversion_score)
            })
        
        # Sort by score descending
        pair_scores.sort(key=lambda x: x["score"], reverse=True)
        
        best_pair = pair_scores[0] if pair_scores else None
        
        return {
            "rankings": pair_scores,
            "best_pair": best_pair["pair_name"] if best_pair else None,
            "best_score": best_pair["score"] if best_pair else 0.0,
            "reason": f"Highest combined score: {best_pair['score']:.3f}" if best_pair else "No valid pairs"
        }
    
    def cross_momentum_pairs(self, prices1: List[float], prices2: List[float], 
                              lookback: int = 20) -> Dict:
        """
        Cross-momentum pairs strategy: trade when one asset has stronger momentum.
        
        Args:
            prices1: Price series for asset 1
            prices2: Price series for asset 2
            lookback: Lookback for momentum calculation
        
        Returns:
            Signals based on momentum divergence
        """
        prices1_arr = np.array(prices1)
        prices2_arr = np.array(prices2)
        
        if len(prices1_arr) < lookback + 1 or len(prices2_arr) < lookback + 1:
            return {
                "signals": [],
                "momentum_spread": [],
                "interpretation": "Insufficient data"
            }
        
        # Calculate momentum for both assets
        mom1 = []
        mom2 = []
        for i in range(lookback, len(prices1_arr)):
            roc1 = (prices1_arr[i] - prices1_arr[i - lookback]) / prices1_arr[i - lookback]
            roc2 = (prices2_arr[i] - prices2_arr[i - lookback]) / prices2_arr[i - lookback]
            mom1.append(roc1)
            mom2.append(roc2)
        
        mom1_arr = np.array(mom1)
        mom2_arr = np.array(mom2)
        
        # Momentum spread (difference)
        mom_spread = mom1_arr - mom2_arr
        
        # Generate signals based on momentum divergence
        signals = []
        threshold = 0.01  # 1% momentum difference
        
        for i, ms in enumerate(mom_spread):
            if ms > threshold:
                # Asset 1 has stronger momentum → Long asset1, short asset2
                signals.append({"index": i + lookback, "type": "long_1_short_2", "mom_spread": ms})
            elif ms < -threshold:
                # Asset 2 has stronger momentum → Long asset2, short asset1
                signals.append({"index": i + lookback, "type": "long_2_short_1", "mom_spread": ms})
        
        current_spread = float(mom_spread[-1]) if len(mom_spread) > 0 else 0.0
        
        return {
            "momentum_spread": mom_spread.tolist(),
            "signals": signals,
            "current_mom_spread": current_spread,
            "interpretation": "Asset 1 stronger" if current_spread > threshold else "Asset 2 stronger" if current_spread < -threshold else "Balanced momentum"
        }

