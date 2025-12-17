"""Liquidity analysis and heatmap visualization for order book depth and trade flow."""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class LiquidityAnalyzer:
    """
    Analyze liquidity characteristics from trade data and order book snapshots.
    """
    
    @staticmethod
    def compute_volume_profile(prices: List[float], volumes: List[float], 
                               n_bins: int = 50) -> Dict[str, Any]:
        """
        Compute volume profile (volume traded at each price level).
        
        Args:
            prices: Trade prices
            volumes: Trade volumes
            n_bins: Number of price bins for histogram
        
        Returns:
            Dictionary with price bins and volume distribution
        """
        try:
            prices_arr = np.array(prices)
            volumes_arr = np.array(volumes)
            
            if len(prices_arr) == 0 or len(volumes_arr) == 0:
                raise ValueError("Empty price or volume data")
            
            # Create price bins
            price_min, price_max = prices_arr.min(), prices_arr.max()
            bins = np.linspace(price_min, price_max, n_bins + 1)
            
            # Digitize prices into bins
            bin_indices = np.digitize(prices_arr, bins) - 1
            bin_indices = np.clip(bin_indices, 0, n_bins - 1)
            
            # Aggregate volume by bin
            volume_by_bin = np.zeros(n_bins)
            for idx, vol in zip(bin_indices, volumes_arr):
                volume_by_bin[idx] += vol
            
            # Calculate bin centers
            bin_centers = (bins[:-1] + bins[1:]) / 2
            
            # Find point of control (POC) - price level with highest volume
            poc_idx = np.argmax(volume_by_bin)
            poc_price = float(bin_centers[poc_idx])
            poc_volume = float(volume_by_bin[poc_idx])
            
            # Value area (70% of volume)
            sorted_indices = np.argsort(volume_by_bin)[::-1]
            total_volume = volume_by_bin.sum()
            cumulative_volume = 0
            value_area_indices = []
            for idx in sorted_indices:
                value_area_indices.append(idx)
                cumulative_volume += volume_by_bin[idx]
                if cumulative_volume >= 0.7 * total_volume:
                    break
            
            value_area_low = float(bin_centers[min(value_area_indices)])
            value_area_high = float(bin_centers[max(value_area_indices)])
            
            return {
                "bin_centers": bin_centers.tolist(),
                "volume_by_bin": volume_by_bin.tolist(),
                "poc_price": poc_price,
                "poc_volume": poc_volume,
                "value_area_low": value_area_low,
                "value_area_high": value_area_high,
                "total_volume": float(total_volume),
                "n_bins": n_bins
            }
            
        except Exception:
            logger.exception("Volume profile computation failed")
            raise
    
    @staticmethod
    def liquidity_heatmap_data(timestamps: List[int], prices: List[float], 
                                volumes: List[float], 
                                time_bins: int = 50, price_bins: int = 30) -> Dict[str, Any]:
        """
        Generate 2D heatmap data (time vs price) with volume intensity.
        
        Args:
            timestamps: Trade timestamps (milliseconds)
            prices: Trade prices
            volumes: Trade volumes
            time_bins: Number of time buckets
            price_bins: Number of price levels
        
        Returns:
            Dictionary with heatmap matrix and axis labels
        """
        try:
            ts_arr = np.array(timestamps)
            prices_arr = np.array(prices)
            volumes_arr = np.array(volumes)
            
            if len(ts_arr) == 0:
                raise ValueError("Empty timestamp data")
            
            # Create time bins
            time_min, time_max = ts_arr.min(), ts_arr.max()
            time_edges = np.linspace(time_min, time_max, time_bins + 1)
            time_centers = (time_edges[:-1] + time_edges[1:]) / 2
            
            # Create price bins
            price_min, price_max = prices_arr.min(), prices_arr.max()
            price_edges = np.linspace(price_min, price_max, price_bins + 1)
            price_centers = (price_edges[:-1] + price_edges[1:]) / 2
            
            # Create 2D histogram
            heatmap_matrix = np.zeros((price_bins, time_bins))
            
            # Digitize data
            time_indices = np.digitize(ts_arr, time_edges) - 1
            price_indices = np.digitize(prices_arr, price_edges) - 1
            
            time_indices = np.clip(time_indices, 0, time_bins - 1)
            price_indices = np.clip(price_indices, 0, price_bins - 1)
            
            # Accumulate volume
            for t_idx, p_idx, vol in zip(time_indices, price_indices, volumes_arr):
                heatmap_matrix[p_idx, t_idx] += vol
            
            return {
                "heatmap_matrix": heatmap_matrix.tolist(),  # Shape: (price_bins, time_bins)
                "time_labels": time_centers.tolist(),
                "price_labels": price_centers.tolist(),
                "time_bins": time_bins,
                "price_bins": price_bins,
                "max_volume": float(heatmap_matrix.max()),
                "total_volume": float(volumes_arr.sum())
            }
            
        except Exception:
            logger.exception("Liquidity heatmap generation failed")
            raise
    
    @staticmethod
    def bid_ask_imbalance(bid_volumes: List[float], ask_volumes: List[float]) -> Dict[str, Any]:
        """
        Calculate order book imbalance metrics.
        
        Args:
            bid_volumes: Volumes at bid levels
            ask_volumes: Volumes at ask levels
        
        Returns:
            Imbalance ratio and pressure metrics
        """
        try:
            total_bid = sum(bid_volumes) if bid_volumes else 0.0
            total_ask = sum(ask_volumes) if ask_volumes else 0.0
            
            if total_bid + total_ask == 0:
                imbalance_ratio = 0.0
            else:
                imbalance_ratio = (total_bid - total_ask) / (total_bid + total_ask)
            
            return {
                "imbalance_ratio": float(imbalance_ratio),
                "total_bid_volume": float(total_bid),
                "total_ask_volume": float(total_ask),
                "interpretation": "Buy pressure" if imbalance_ratio > 0.1 else "Sell pressure" if imbalance_ratio < -0.1 else "Balanced"
            }
            
        except Exception:
            logger.exception("Bid-ask imbalance calculation failed")
            raise


def test_liquidity_analysis():
    """Test liquidity analysis functions."""
    import logging as _logging
    _logging.basicConfig(level=_logging.DEBUG)
    
    np.random.seed(42)
    
    # Generate synthetic trade data
    n = 1000
    base_price = 50000.0
    prices = base_price + np.cumsum(np.random.randn(n) * 10)
    volumes = np.abs(np.random.randn(n) * 0.5 + 1.0)
    timestamps = np.arange(n) * 1000  # milliseconds
    
    analyzer = LiquidityAnalyzer()
    
    print("=== Volume Profile ===")
    vp = analyzer.compute_volume_profile(prices.tolist(), volumes.tolist(), n_bins=20)
    print(f"POC Price: ${vp['poc_price']:.2f}")
    print(f"Value Area: ${vp['value_area_low']:.2f} - ${vp['value_area_high']:.2f}")
    
    print("\n=== Liquidity Heatmap ===")
    hm = analyzer.liquidity_heatmap_data(
        timestamps.tolist(),
        prices.tolist(),
        volumes.tolist(),
        time_bins=10,
        price_bins=10
    )
    print(f"Heatmap shape: {len(hm['price_labels'])} x {len(hm['time_labels'])}")
    print(f"Max volume in cell: {hm['max_volume']:.4f}")
    
    print("\n=== Bid-Ask Imbalance ===")
    bid_vols = np.random.rand(10) * 100
    ask_vols = np.random.rand(10) * 80
    imb = analyzer.bid_ask_imbalance(bid_vols.tolist(), ask_vols.tolist())
    print(f"Imbalance: {imb['imbalance_ratio']:.3f} ({imb['interpretation']})")


if __name__ == "__main__":
    test_liquidity_analysis()
