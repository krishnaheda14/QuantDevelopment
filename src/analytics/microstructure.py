"""Microstructure analytics: order flow, trade classification, and tape reading."""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
import logging
from collections import deque

logger = logging.getLogger(__name__)


class MicrostructureAnalyzer:
    """
    Analyze market microstructure: order flow, trade aggression, and price formation.
    """
    
    @staticmethod
    def classify_trades_tick_rule(prices: List[float]) -> Dict[str, Any]:
        """
        Classify trades as buyer-initiated or seller-initiated using tick rule.
        
        Tick Rule:
        - If price > previous price: buyer-initiated
        - If price < previous price: seller-initiated
        - If price == previous price: use last different price
        
        Args:
            prices: Sequential trade prices
        
        Returns:
            Trade classification counts and imbalance metrics
        """
        try:
            if len(prices) < 2:
                raise ValueError("Need at least 2 prices for tick rule")
            
            prices_arr = np.array(prices)
            
            # Calculate price changes
            price_diff = np.diff(prices_arr)
            
            # Classify trades
            buyer_initiated = np.sum(price_diff > 0)
            seller_initiated = np.sum(price_diff < 0)
            neutral = np.sum(price_diff == 0)
            
            total = len(price_diff)
            buyer_pct = 100.0 * buyer_initiated / total if total > 0 else 0.0
            seller_pct = 100.0 * seller_initiated / total if total > 0 else 0.0
            
            # Order flow imbalance
            ofi = (buyer_initiated - seller_initiated) / total if total > 0 else 0.0
            
            return {
                "buyer_initiated": int(buyer_initiated),
                "seller_initiated": int(seller_initiated),
                "neutral": int(neutral),
                "buyer_pct": float(buyer_pct),
                "seller_pct": float(seller_pct),
                "order_flow_imbalance": float(ofi),
                "total_trades": total,
                "interpretation": "Buy pressure" if ofi > 0.1 else "Sell pressure" if ofi < -0.1 else "Balanced"
            }
            
        except Exception:
            logger.exception("Tick rule classification failed")
            raise
    
    @staticmethod
    def rolling_order_flow(prices: List[float], volumes: List[float], 
                           window: int = 20) -> Dict[str, Any]:
        """
        Calculate rolling order flow imbalance with volume weighting.
        
        Args:
            prices: Trade prices
            volumes: Trade volumes
            window: Rolling window size
        
        Returns:
            Rolling OFI time series and summary statistics
        """
        try:
            if len(prices) < window:
                raise ValueError(f"Need at least {window} observations for rolling OFI")
            
            prices_arr = np.array(prices)
            volumes_arr = np.array(volumes)
            
            # Calculate price changes
            price_diff = np.diff(prices_arr)
            
            # Volume-weighted order flow
            buy_volume = np.zeros(len(price_diff))
            sell_volume = np.zeros(len(price_diff))
            
            buy_volume[price_diff > 0] = volumes_arr[1:][price_diff > 0]
            sell_volume[price_diff < 0] = volumes_arr[1:][price_diff < 0]
            
            # Rolling calculation
            rolling_ofi = []
            for i in range(window - 1, len(buy_volume)):
                window_buy = np.sum(buy_volume[i - window + 1:i + 1])
                window_sell = np.sum(sell_volume[i - window + 1:i + 1])
                total_vol = window_buy + window_sell
                ofi = (window_buy - window_sell) / total_vol if total_vol > 0 else 0.0
                rolling_ofi.append(ofi)
            
            rolling_ofi_arr = np.array(rolling_ofi)
            
            return {
                "rolling_ofi": rolling_ofi_arr.tolist(),
                "current_ofi": float(rolling_ofi_arr[-1]) if len(rolling_ofi_arr) > 0 else 0.0,
                "mean_ofi": float(np.mean(rolling_ofi_arr)),
                "std_ofi": float(np.std(rolling_ofi_arr)),
                "max_ofi": float(np.max(rolling_ofi_arr)),
                "min_ofi": float(np.min(rolling_ofi_arr)),
                "window": window
            }
            
        except Exception:
            logger.exception("Rolling order flow calculation failed")
            raise
    
    @staticmethod
    def trade_intensity(timestamps: List[int], window_ms: int = 60000) -> Dict[str, Any]:
        """
        Calculate trade arrival intensity (trades per time window).
        
        Args:
            timestamps: Trade timestamps in milliseconds
            window_ms: Time window in milliseconds (default 1 minute)
        
        Returns:
            Trade intensity metrics
        """
        try:
            if len(timestamps) == 0:
                raise ValueError("Empty timestamp list")
            
            ts_arr = np.array(timestamps)
            
            # Calculate inter-arrival times
            inter_arrival = np.diff(ts_arr)
            
            # Trades per window
            time_span_ms = ts_arr[-1] - ts_arr[0]
            if time_span_ms == 0:
                trades_per_window = 0.0
            else:
                n_windows = time_span_ms / window_ms
                trades_per_window = len(timestamps) / n_windows if n_windows > 0 else 0.0
            
            return {
                "trades_per_window": float(trades_per_window),
                "window_ms": window_ms,
                "mean_inter_arrival_ms": float(np.mean(inter_arrival)) if len(inter_arrival) > 0 else 0.0,
                "std_inter_arrival_ms": float(np.std(inter_arrival)) if len(inter_arrival) > 0 else 0.0,
                "total_trades": len(timestamps),
                "time_span_ms": float(time_span_ms)
            }
            
        except Exception:
            logger.exception("Trade intensity calculation failed")
            raise
    
    @staticmethod
    def vwap_deviation(prices: List[float], volumes: List[float]) -> Dict[str, Any]:
        """
        Calculate Volume-Weighted Average Price and current deviation.
        
        Args:
            prices: Trade prices
            volumes: Trade volumes
        
        Returns:
            VWAP and deviation metrics
        """
        try:
            prices_arr = np.array(prices)
            volumes_arr = np.array(volumes)
            
            if len(prices_arr) == 0 or len(volumes_arr) == 0:
                raise ValueError("Empty price or volume data")
            
            # Calculate VWAP
            total_value = np.sum(prices_arr * volumes_arr)
            total_volume = np.sum(volumes_arr)
            
            vwap = total_value / total_volume if total_volume > 0 else 0.0
            
            # Current price deviation from VWAP
            current_price = float(prices_arr[-1])
            deviation = current_price - vwap
            deviation_pct = 100.0 * deviation / vwap if vwap > 0 else 0.0
            
            return {
                "vwap": float(vwap),
                "current_price": current_price,
                "deviation": float(deviation),
                "deviation_pct": float(deviation_pct),
                "interpretation": "Above VWAP" if deviation > 0 else "Below VWAP" if deviation < 0 else "At VWAP"
            }
            
        except Exception:
            logger.exception("VWAP calculation failed")
            raise
    
    @staticmethod
    def effective_spread(prices: List[float], mid_prices: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Estimate effective spread (twice the distance from trade price to mid-price).
        
        Args:
            prices: Trade prices
            mid_prices: Mid prices (if None, use rolling mean as proxy)
        
        Returns:
            Effective spread metrics
        """
        try:
            prices_arr = np.array(prices)
            
            if mid_prices is None:
                # Use rolling mean as mid-price proxy
                window = min(10, len(prices_arr) // 2)
                if window < 2:
                    window = 2
                mid_prices_arr = pd.Series(prices_arr).rolling(window=window, center=True).mean().values
                mid_prices_arr = np.nan_to_num(mid_prices_arr, nan=np.nanmean(prices_arr))
            else:
                mid_prices_arr = np.array(mid_prices)
            
            # Effective spread = 2 * |trade_price - mid_price|
            spreads = 2 * np.abs(prices_arr - mid_prices_arr)
            
            # Express as percentage
            spread_pct = 100.0 * spreads / mid_prices_arr
            spread_pct = spread_pct[np.isfinite(spread_pct)]
            
            return {
                "mean_spread": float(np.mean(spreads)),
                "mean_spread_pct": float(np.mean(spread_pct)) if len(spread_pct) > 0 else 0.0,
                "median_spread": float(np.median(spreads)),
                "std_spread": float(np.std(spreads)),
                "max_spread": float(np.max(spreads)),
                "observations": len(prices_arr)
            }
            
        except Exception:
            logger.exception("Effective spread calculation failed")
            raise


def test_microstructure_analysis():
    """Test microstructure analysis functions."""
    import logging as _logging
    _logging.basicConfig(level=_logging.DEBUG)
    
    np.random.seed(42)
    
    # Generate synthetic trade data
    n = 200
    base_price = 50000.0
    prices = base_price + np.cumsum(np.random.randn(n) * 5)
    volumes = np.abs(np.random.randn(n) * 0.5 + 1.0)
    timestamps = np.cumsum(np.random.exponential(scale=100, size=n)).astype(int)
    
    analyzer = MicrostructureAnalyzer()
    
    print("=== Trade Classification (Tick Rule) ===")
    tc = analyzer.classify_trades_tick_rule(prices.tolist())
    print(f"Buyer-initiated: {tc['buyer_initiated']} ({tc['buyer_pct']:.1f}%)")
    print(f"Seller-initiated: {tc['seller_initiated']} ({tc['seller_pct']:.1f}%)")
    print(f"OFI: {tc['order_flow_imbalance']:.3f} - {tc['interpretation']}")
    
    print("\n=== Rolling Order Flow ===")
    rofi = analyzer.rolling_order_flow(prices.tolist(), volumes.tolist(), window=20)
    print(f"Current OFI: {rofi['current_ofi']:.3f}")
    print(f"Mean OFI: {rofi['mean_ofi']:.3f} ± {rofi['std_ofi']:.3f}")
    
    print("\n=== Trade Intensity ===")
    ti = analyzer.trade_intensity(timestamps.tolist(), window_ms=60000)
    print(f"Trades per minute: {ti['trades_per_window']:.2f}")
    print(f"Mean inter-arrival: {ti['mean_inter_arrival_ms']:.2f} ms")
    
    print("\n=== VWAP Deviation ===")
    vwap = analyzer.vwap_deviation(prices.tolist(), volumes.tolist())
    print(f"VWAP: ${vwap['vwap']:.2f}")
    print(f"Current: ${vwap['current_price']:.2f} ({vwap['deviation_pct']:+.2f}%)")
    
    print("\n=== Effective Spread ===")
    es = analyzer.effective_spread(prices.tolist())
    print(f"Mean spread: ${es['mean_spread']:.2f} ({es['mean_spread_pct']:.3f}%)")


if __name__ == "__main__":
    test_microstructure_analysis()
