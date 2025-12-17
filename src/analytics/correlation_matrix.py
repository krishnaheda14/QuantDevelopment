"""Cross-product correlation matrix for multiple asset pairs."""

import numpy as np
import pandas as pd
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class CorrelationMatrix:
    """
    Compute and visualize correlation matrices for multiple assets.
    """
    
    @staticmethod
    def compute_correlation_matrix(price_series: Dict[str, List[float]], 
                                     method: str = 'pearson') -> Dict[str, Any]:
        """
        Compute correlation matrix for multiple price series.
        
        Args:
            price_series: Dictionary mapping symbol names to price lists
            method: 'pearson', 'spearman', or 'kendall'
        
        Returns:
            Correlation matrix and related metrics
        """
        try:
            if len(price_series) < 2:
                raise ValueError("Need at least 2 price series for correlation matrix")
            
            # Align series to common length
            min_len = min(len(v) for v in price_series.values())
            aligned_data = {k: v[-min_len:] for k, v in price_series.items()}
            
            # Create DataFrame
            df = pd.DataFrame(aligned_data)
            
            # Compute correlation matrix
            if method == 'pearson':
                corr_matrix = df.corr(method='pearson')
            elif method == 'spearman':
                corr_matrix = df.corr(method='spearman')
            elif method == 'kendall':
                corr_matrix = df.corr(method='kendall')
            else:
                raise ValueError(f"Unknown correlation method: {method}")
            
            # Extract upper triangle (excluding diagonal)
            symbols = list(price_series.keys())
            n = len(symbols)
            
            pairs = []
            for i in range(n):
                for j in range(i + 1, n):
                    pairs.append({
                        "symbol1": symbols[i],
                        "symbol2": symbols[j],
                        "correlation": float(corr_matrix.iloc[i, j])
                    })
            
            # Sort by absolute correlation (descending)
            pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)
            
            # Find best and worst correlated pairs
            best_pair = pairs[0] if pairs else None
            worst_pair = min(pairs, key=lambda x: abs(x["correlation"])) if pairs else None
            
            return {
                "correlation_matrix": corr_matrix.to_dict(),
                "symbols": symbols,
                "pairs": pairs,
                "best_correlated": best_pair,
                "worst_correlated": worst_pair,
                "method": method,
                "observations": min_len
            }
            
        except Exception:
            logger.exception("Correlation matrix computation failed")
            raise
    
    @staticmethod
    def rolling_correlation_matrix(price_series: Dict[str, List[float]], 
                                     window: int = 50) -> Dict[str, Any]:
        """
        Compute rolling correlation matrices over time.
        
        Args:
            price_series: Dictionary mapping symbol names to price lists
            window: Rolling window size
        
        Returns:
            Time series of correlation matrices
        """
        try:
            if len(price_series) < 2:
                raise ValueError("Need at least 2 price series")
            
            # Align series
            min_len = min(len(v) for v in price_series.values())
            aligned_data = {k: v[-min_len:] for k, v in price_series.items()}
            
            df = pd.DataFrame(aligned_data)
            symbols = list(price_series.keys())
            
            # Calculate rolling correlations for each pair
            rolling_corrs = {}
            for i, sym1 in enumerate(symbols):
                for j, sym2 in enumerate(symbols):
                    if i < j:  # Only upper triangle
                        pair_key = f"{sym1}_{sym2}"
                        rolling_corrs[pair_key] = df[sym1].rolling(window=window).corr(df[sym2]).dropna().tolist()
            
            # Current correlation matrix (last window)
            current_corr = df.tail(window).corr()
            
            return {
                "rolling_correlations": rolling_corrs,
                "current_matrix": current_corr.to_dict(),
                "symbols": symbols,
                "window": window
            }
            
        except Exception:
            logger.exception("Rolling correlation matrix failed")
            raise
    
    @staticmethod
    def correlation_heatmap_data(correlation_matrix_dict: Dict[str, Dict[str, float]], 
                                  symbols: List[str]) -> Dict[str, Any]:
        """
        Prepare correlation matrix data for heatmap visualization.
        
        Args:
            correlation_matrix_dict: Nested dict from DataFrame.to_dict()
            symbols: List of symbol names
        
        Returns:
            Formatted data for heatmap plotting
        """
        try:
            n = len(symbols)
            matrix_array = np.zeros((n, n))
            
            for i, sym1 in enumerate(symbols):
                for j, sym2 in enumerate(symbols):
                    matrix_array[i, j] = correlation_matrix_dict.get(sym1, {}).get(sym2, 0.0)
            
            return {
                "matrix": matrix_array.tolist(),
                "x_labels": symbols,
                "y_labels": symbols,
                "title": "Asset Correlation Matrix"
            }
            
        except Exception:
            logger.exception("Heatmap data preparation failed")
            raise


def test_correlation_matrix():
    """Test correlation matrix functions."""
    import logging as _logging
    _logging.basicConfig(level=_logging.DEBUG)
    
    np.random.seed(42)
    
    # Generate synthetic correlated price series
    n = 200
    base = np.cumsum(np.random.randn(n)) + 100
    
    price_series = {
        "BTC": base + np.random.randn(n) * 5,
        "ETH": 0.8 * base + np.random.randn(n) * 3,
        "BNB": 0.5 * base + np.random.randn(n) * 7,
        "SOL": 0.3 * base + np.cumsum(np.random.randn(n)) * 2
    }
    
    cm = CorrelationMatrix()
    
    print("=== Correlation Matrix ===")
    result = cm.compute_correlation_matrix(price_series)
    print(f"Symbols: {result['symbols']}")
    print(f"\nBest correlated: {result['best_correlated']['symbol1']} - {result['best_correlated']['symbol2']}: {result['best_correlated']['correlation']:.3f}")
    print(f"Worst correlated: {result['worst_correlated']['symbol1']} - {result['worst_correlated']['symbol2']}: {result['worst_correlated']['correlation']:.3f}")
    
    print("\n=== Top Pairs ===")
    for pair in result['pairs'][:5]:
        print(f"{pair['symbol1']}-{pair['symbol2']}: {pair['correlation']:.3f}")
    
    print("\n=== Rolling Correlation ===")
    rolling = cm.rolling_correlation_matrix(price_series, window=50)
    for pair_key, corrs in rolling['rolling_correlations'].items():
        print(f"{pair_key}: current={corrs[-1]:.3f}, mean={np.mean(corrs):.3f}")


if __name__ == "__main__":
    test_correlation_matrix()
