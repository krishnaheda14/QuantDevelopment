"""Advanced microstructure and liquidity metrics."""
import numpy as np
import pandas as pd
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AdvancedMetrics:
    """
    Creative analytics for microstructure, liquidity, and cross-asset analysis.
    """
    
    @staticmethod
    def liquidity_score(prices: List[float], volumes: List[float], window: int = 20) -> Dict[str, Any]:
        """
        Compute liquidity score based on volume and price stability.
        
        Score = volume / price_volatility
        Higher score = better liquidity
        """
        try:
            df = pd.DataFrame({"price": prices, "volume": volumes})
            
            # Rolling volatility
            price_returns = df["price"].pct_change()
            rolling_vol = price_returns.rolling(window=window).std()
            
            # Rolling average volume
            rolling_volume = df["volume"].rolling(window=window).mean()
            
            # Liquidity score
            liquidity = rolling_volume / (rolling_vol + 1e-8)  # Avoid division by zero
            
            result = {
                "liquidity_scores": liquidity.fillna(0).tolist(),
                "current_liquidity": float(liquidity.iloc[-1]) if len(liquidity) > 0 else 0.0,
                "mean_liquidity": float(liquidity.mean()),
                "window": window
            }
            
            logger.debug(f"Liquidity score: {result['current_liquidity']:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Liquidity score calculation failed: {e}")
            raise
    
    @staticmethod
    def tick_velocity(timestamps: List[int], window_seconds: int = 60) -> Dict[str, Any]:
        """
        Measure tick arrival rate (ticks per second).
        """
        try:
            timestamps = np.array(timestamps) / 1000  # Convert to seconds
            
            # Sort timestamps
            timestamps = np.sort(timestamps)
            
            # Compute tick intervals
            intervals = np.diff(timestamps)
            
            # Ticks per second (inverse of mean interval)
            if len(intervals) > 0:
                tps = 1.0 / np.mean(intervals) if np.mean(intervals) > 0 else 0.0
            else:
                tps = 0.0
            
            result = {
                "ticks_per_second": float(tps),
                "mean_interval_ms": float(np.mean(intervals) * 1000) if len(intervals) > 0 else 0.0,
                "total_ticks": len(timestamps),
                "time_span_seconds": float(timestamps[-1] - timestamps[0]) if len(timestamps) > 1 else 0.0
            }
            
            logger.debug(f"Tick velocity: {result['ticks_per_second']:.2f} ticks/sec")
            
            return result
            
        except Exception as e:
            logger.error(f"Tick velocity calculation failed: {e}")
            raise
    
    @staticmethod
    def order_imbalance(buy_volumes: List[float], sell_volumes: List[float]) -> Dict[str, Any]:
        """
        Compute order flow imbalance.
        
        Imbalance = (buy_volume - sell_volume) / (buy_volume + sell_volume)
        Range: [-1, 1], positive = buy pressure
        """
        try:
            buy = np.array(buy_volumes)
            sell = np.array(sell_volumes)
            
            total = buy + sell
            imbalance = np.where(total > 0, (buy - sell) / total, 0)
            
            result = {
                "imbalance": imbalance.tolist(),
                "current_imbalance": float(imbalance[-1]) if len(imbalance) > 0 else 0.0,
                "mean_imbalance": float(np.mean(imbalance)),
                "total_buy_volume": float(np.sum(buy)),
                "total_sell_volume": float(np.sum(sell))
            }
            
            logger.debug(f"Order imbalance: {result['current_imbalance']:.4f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Order imbalance calculation failed: {e}")
            raise
    
    @staticmethod
    def correlation_matrix(price_data: Dict[str, List[float]]) -> Dict[str, Any]:
        """
        Compute correlation matrix for multiple assets.
        
        Args:
            price_data: Dict of {symbol: prices}
        
        Returns:
            Correlation matrix and heatmap data
        """
        try:
            df = pd.DataFrame(price_data)
            corr_matrix = df.corr()
            
            result = {
                "symbols": list(price_data.keys()),
                "correlation_matrix": corr_matrix.values.tolist(),
                "correlation_dict": corr_matrix.to_dict(),
                "heatmap_data": {
                    "x": list(corr_matrix.columns),
                    "y": list(corr_matrix.index),
                    "z": corr_matrix.values.tolist()
                }
            }
            
            logger.debug(f"Correlation matrix computed for {len(price_data)} assets")
            
            return result
            
        except Exception as e:
            logger.error(f"Correlation matrix calculation failed: {e}")
            raise
    
    @staticmethod
    def price_momentum(prices: List[float], periods: List[int] = [5, 10, 20]) -> Dict[str, Any]:
        """
        Compute price momentum over multiple periods.
        """
        try:
            prices = np.array(prices)
            
            momentum = {}
            for period in periods:
                if len(prices) >= period:
                    mom = (prices[-1] - prices[-period]) / prices[-period]
                    momentum[f"{period}_period"] = float(mom)
                else:
                    momentum[f"{period}_period"] = 0.0
            
            result = {
                "momentum": momentum,
                "periods": periods,
                "current_price": float(prices[-1])
            }
            
            logger.debug(f"Momentum: {momentum}")
            
            return result
            
        except Exception as e:
            logger.error(f"Momentum calculation failed: {e}")
            raise
    
    @staticmethod
    def volatility_metrics(prices: List[float], window: int = 20) -> Dict[str, Any]:
        """
        Compute various volatility measures.
        """
        try:
            df = pd.Series(prices)
            returns = df.pct_change().dropna()
            
            # Historical volatility (annualized)
            hist_vol = returns.std() * np.sqrt(252)  # Assuming daily data
            
            # Parkinson volatility (using high-low range if available)
            rolling_std = returns.rolling(window=window).std()
            
            # EWMA volatility
            ewma_vol = returns.ewm(span=window).std()
            
            result = {
                "historical_volatility": float(hist_vol),
                "rolling_volatility": rolling_std.fillna(0).tolist(),
                "current_rolling_vol": float(rolling_std.iloc[-1]) if len(rolling_std) > 0 else 0.0,
                "ewma_volatility": ewma_vol.fillna(0).tolist(),
                "current_ewma_vol": float(ewma_vol.iloc[-1]) if len(ewma_vol) > 0 else 0.0,
                "window": window
            }
            
            logger.debug(f"Volatility: hist={hist_vol:.4f}, current_rolling={result['current_rolling_vol']:.4f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Volatility metrics calculation failed: {e}")
            raise


def test_advanced_metrics():
    """Test advanced metrics."""
    np.random.seed(42)
    
    # Generate test data
    n = 200
    prices = np.cumsum(np.random.randn(n)) + 100
    volumes = np.random.uniform(0.1, 2.0, n)
    timestamps = np.arange(n) * 1000  # milliseconds
    
    metrics = AdvancedMetrics()
    
    # Test liquidity score
    print("=== Liquidity Score ===")
    liq = metrics.liquidity_score(prices.tolist(), volumes.tolist())
    print(f"Current: {liq['current_liquidity']:.2f}")
    
    # Test tick velocity
    print("\n=== Tick Velocity ===")
    velocity = metrics.tick_velocity(timestamps.tolist())
    print(f"Ticks/sec: {velocity['ticks_per_second']:.2f}")
    
    # Test correlation matrix
    print("\n=== Correlation Matrix ===")
    price_data = {
        "Asset1": prices.tolist(),
        "Asset2": (prices * 2 + np.random.randn(n) * 5).tolist(),
        "Asset3": (prices * 0.5 + np.random.randn(n) * 10).tolist()
    }
    corr = metrics.correlation_matrix(price_data)
    print(f"Symbols: {corr['symbols']}")
    
    # Test momentum
    print("\n=== Price Momentum ===")
    mom = metrics.price_momentum(prices.tolist())
    print(f"Momentum: {mom['momentum']}")
    
    # Test volatility
    print("\n=== Volatility Metrics ===")
    vol = metrics.volatility_metrics(prices.tolist())
    print(f"Historical volatility: {vol['historical_volatility']:.4f}")
    print(f"Current rolling vol: {vol['current_rolling_vol']:.4f}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_advanced_metrics()
