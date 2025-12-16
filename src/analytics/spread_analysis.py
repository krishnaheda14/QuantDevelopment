"""Spread analysis and z-score calculations."""
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SpreadAnalysis:
    """
    Compute spread, z-score, and Bollinger Bands for pairs trading.
    """
    
    @staticmethod
    def compute_spread(price1: List[float], price2: List[float], hedge_ratio: float, alpha: float = 0.0) -> np.ndarray:
        """
        Compute spread: spread = price2 - (alpha + hedge_ratio * price1)
        """
        p1 = np.array(price1)
        p2 = np.array(price2)
        
        spread = p2 - (alpha + hedge_ratio * p1)
        return spread
    
    @staticmethod
    def compute_zscore(series: List[float], window: Optional[int] = None) -> Dict[str, Any]:
        """
        Compute z-score of a series.
        
        If window is provided, compute rolling z-score.
        Otherwise, compute global z-score.
        """
        series = np.array(series)
        
        if window and window < len(series):
            # Rolling z-score
            df = pd.Series(series)
            rolling_mean = df.rolling(window=window).mean()
            rolling_std = df.rolling(window=window).std()
            
            zscore = (df - rolling_mean) / rolling_std
            zscore = zscore.fillna(0).values
            
            result = {
                "zscore": zscore.tolist(),
                "current_zscore": float(zscore[-1]),
                "mean_zscore": float(np.nanmean(zscore)),
                "std_zscore": float(np.nanstd(zscore)),
                "window": window,
                "type": "rolling"
            }
        else:
            # Global z-score
            mean = np.mean(series)
            std = np.std(series)
            
            if std == 0:
                zscore = np.zeros_like(series)
            else:
                zscore = (series - mean) / std
            
            result = {
                "zscore": zscore.tolist(),
                "current_zscore": float(zscore[-1]),
                "mean": float(mean),
                "std": float(std),
                "type": "global"
            }
        
        logger.debug(f"Z-score: current={result['current_zscore']:.4f}")
        
        return result
    
    @staticmethod
    def bollinger_bands(series: List[float], window: int = 20, num_std: float = 2.0) -> Dict[str, Any]:
        """
        Compute Bollinger Bands for a series.
        """
        df = pd.Series(series)
        
        rolling_mean = df.rolling(window=window).mean()
        rolling_std = df.rolling(window=window).std()
        
        upper_band = rolling_mean + (rolling_std * num_std)
        lower_band = rolling_mean - (rolling_std * num_std)
        
        # Current values
        current_price = series[-1]
        current_upper = upper_band.iloc[-1]
        current_lower = lower_band.iloc[-1]
        current_middle = rolling_mean.iloc[-1]
        
        # Position within bands (0-1 scale)
        if not np.isnan(current_upper) and not np.isnan(current_lower):
            band_width = current_upper - current_lower
            if band_width > 0:
                position = (current_price - current_lower) / band_width
            else:
                position = 0.5
        else:
            position = 0.5
        
        result = {
            "middle_band": rolling_mean.tolist(),
            "upper_band": upper_band.tolist(),
            "lower_band": lower_band.tolist(),
            "current_price": float(current_price),
            "current_upper": float(current_upper) if not np.isnan(current_upper) else None,
            "current_lower": float(current_lower) if not np.isnan(current_lower) else None,
            "current_middle": float(current_middle) if not np.isnan(current_middle) else None,
            "position_in_band": float(position),
            "window": window,
            "num_std": num_std
        }
        
        logger.debug(f"Bollinger: pos={position:.2%}, price={current_price:.2f}")
        
        return result
    
    @staticmethod
    def analyze_spread(price1: List[float], price2: List[float], hedge_ratio: float, 
                       window: int = 50, alpha: float = 0.0) -> Dict[str, Any]:
        """
        Complete spread analysis including spread, z-score, and Bollinger Bands.
        """
        try:
            logger.debug(f"[SPREAD_ANALYSIS] Input: len(price1)={len(price1)}, len(price2)={len(price2)}")
            logger.debug(f"[SPREAD_ANALYSIS] hedge_ratio={hedge_ratio:.4f}, alpha={alpha:.4f}, window={window}")
            
            # Compute spread
            logger.debug(f"[SPREAD_ANALYSIS] Step 1: Computing spread...")
            spread = SpreadAnalysis.compute_spread(price1, price2, hedge_ratio, alpha)
            logger.debug(f"[SPREAD_ANALYSIS] Spread computed: len={len(spread)}, type={type(spread)}")
            logger.debug(f"[SPREAD_ANALYSIS] Spread range: [{spread.min():.4f}, {spread.max():.4f}], mean={spread.mean():.4f}")
            
            # Compute z-score
            logger.debug(f"[SPREAD_ANALYSIS] Step 2: Computing z-score with window={window}...")
            zscore_result = SpreadAnalysis.compute_zscore(spread.tolist(), window=window)
            logger.debug(f"[SPREAD_ANALYSIS] Z-score computed: current={zscore_result.get('current_zscore', 'N/A')}")
            
            # Compute Bollinger Bands
            logger.debug(f"[SPREAD_ANALYSIS] Step 3: Computing Bollinger Bands...")
            bollinger_result = SpreadAnalysis.bollinger_bands(spread.tolist(), window=window)
            logger.debug(f"[SPREAD_ANALYSIS] Bollinger computed: position={bollinger_result.get('position_in_band', 'N/A')}")
            
            # Additional metrics
            current_spread = float(spread[-1])
            spread_mean = float(np.mean(spread))
            spread_std = float(np.std(spread))
            
            logger.debug(f"[SPREAD_ANALYSIS] Final metrics: current={current_spread:.4f}, mean={spread_mean:.4f}, std={spread_std:.4f}")
            
            result = {
                "spread": spread.tolist(),
                "current_spread": current_spread,
                "spread_mean": spread_mean,
                "spread_std": spread_std,
                "hedge_ratio": hedge_ratio,
                "alpha": alpha,
                "zscore": zscore_result,
                "bollinger_bands": bollinger_result,
                "window": window
            }
            
            logger.info(
                f"[SPREAD_ANALYSIS] Complete: current={current_spread:.4f}, "
                f"z-score={zscore_result['current_zscore']:.4f}, "
                f"bollinger_pos={bollinger_result['position_in_band']:.2%}"
            )
            
            return result
            
        except Exception as e:
            logger.exception(f"[SPREAD_ANALYSIS] Analysis failed")
            raise
    
    @staticmethod
    def mean_reversion_signal(zscore: float, entry_threshold: float = 2.0, 
                              exit_threshold: float = 0.5) -> Dict[str, Any]:
        """
        Generate mean reversion trading signal based on z-score.
        
        Returns:
            signal: 'long', 'short', 'exit', or 'hold'
        """
        signal = "hold"
        reason = ""
        
        if zscore > entry_threshold:
            signal = "short"
            reason = f"Z-score {zscore:.2f} > {entry_threshold} (overvalued)"
        elif zscore < -entry_threshold:
            signal = "long"
            reason = f"Z-score {zscore:.2f} < -{entry_threshold} (undervalued)"
        elif abs(zscore) < exit_threshold:
            signal = "exit"
            reason = f"Z-score {zscore:.2f} near mean (mean reversion)"
        
        return {
            "signal": signal,
            "zscore": zscore,
            "reason": reason,
            "entry_threshold": entry_threshold,
            "exit_threshold": exit_threshold
        }


def test_spread_analysis():
    """Test spread analysis."""
    np.random.seed(42)
    
    # Generate correlated prices
    price1 = np.cumsum(np.random.randn(200)) + 100
    price2 = 2 * price1 + 5 + np.random.randn(200) * 2
    
    hedge_ratio = 2.0
    
    # Analyze spread
    print("=== Spread Analysis ===")
    result = SpreadAnalysis.analyze_spread(
        price1.tolist(), price2.tolist(), hedge_ratio, window=50
    )
    
    print(f"Current spread: {result['current_spread']:.4f}")
    print(f"Current z-score: {result['zscore']['current_zscore']:.4f}")
    print(f"Bollinger position: {result['bollinger_bands']['position_in_band']:.2%}")
    
    # Generate trading signal
    print("\n=== Trading Signal ===")
    signal = SpreadAnalysis.mean_reversion_signal(
        result['zscore']['current_zscore'], 
        entry_threshold=2.0
    )
    print(f"Signal: {signal['signal']}")
    print(f"Reason: {signal['reason']}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_spread_analysis()
