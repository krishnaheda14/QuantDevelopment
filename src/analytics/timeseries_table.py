"""Time-series statistics table generator for export and analysis."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class TimeSeriesStatsTable:
    """
    Generate comprehensive time-series statistics tables with all analytics features.
    """
    
    @staticmethod
    def generate_stats_table(
        data1: List[Dict],
        data2: List[Dict],
        symbol1: str,
        symbol2: str,
        hedge_ratio: float,
        include_indicators: bool = True
    ) -> pd.DataFrame:
        """
        Generate comprehensive time-series statistics table.
        
        Args:
            data1: OHLC data for symbol 1
            data2: OHLC data for symbol 2
            symbol1: Name of symbol 1
            symbol2: Name of symbol 2
            hedge_ratio: Hedge ratio for spread calculation
            include_indicators: Whether to compute technical indicators
        
        Returns:
            DataFrame with time-series statistics
        """
        try:
            # Align data by timestamp
            map1 = {int(d['timestamp']): d for d in data1}
            map2 = {int(d['timestamp']): d for d in data2}
            common_ts = sorted(set(map1.keys()) & set(map2.keys()))
            
            if len(common_ts) < 2:
                raise ValueError("Insufficient aligned data for stats table")
            
            # Build base DataFrame
            rows = []
            for ts in common_ts:
                row = {
                    'timestamp': ts,
                    'datetime': pd.to_datetime(ts, unit='ms'),
                    f'{symbol1}_open': map1[ts]['open'],
                    f'{symbol1}_high': map1[ts]['high'],
                    f'{symbol1}_low': map1[ts]['low'],
                    f'{symbol1}_close': map1[ts]['close'],
                    f'{symbol1}_volume': map1[ts]['volume'],
                    f'{symbol2}_open': map2[ts]['open'],
                    f'{symbol2}_high': map2[ts]['high'],
                    f'{symbol2}_low': map2[ts]['low'],
                    f'{symbol2}_close': map2[ts]['close'],
                    f'{symbol2}_volume': map2[ts]['volume'],
                }
                rows.append(row)
            
            df = pd.DataFrame(rows)
            
            # Calculate spread and z-score
            df['spread'] = df[f'{symbol2}_close'] - hedge_ratio * df[f'{symbol1}_close']
            df['spread_ma_20'] = df['spread'].rolling(window=20, min_periods=1).mean()
            df['spread_std_20'] = df['spread'].rolling(window=20, min_periods=1).std()
            df['zscore'] = (df['spread'] - df['spread_ma_20']) / (df['spread_std_20'] + 1e-8)
            
            # Price returns
            df[f'{symbol1}_return'] = df[f'{symbol1}_close'].pct_change()
            df[f'{symbol2}_return'] = df[f'{symbol2}_close'].pct_change()
            
            # Rolling correlation
            df['rolling_corr_20'] = df[f'{symbol1}_close'].rolling(window=20).corr(df[f'{symbol2}_close'])
            
            # Volume ratio
            df['volume_ratio'] = df[f'{symbol1}_volume'] / (df[f'{symbol2}_volume'] + 1e-8)
            
            if include_indicators and len(df) >= 50:
                # Add technical indicators
                from src.analytics.indicators import TechnicalIndicators
                indicators = TechnicalIndicators()
                
                # RSI for both symbols
                try:
                    rsi1 = indicators.rsi(df[f'{symbol1}_close'].tolist(), period=14)
                    if len(rsi1) > 0:
                        df[f'{symbol1}_rsi'] = [np.nan] * (len(df) - len(rsi1)) + rsi1
                except Exception:
                    pass
                
                try:
                    rsi2 = indicators.rsi(df[f'{symbol2}_close'].tolist(), period=14)
                    if len(rsi2) > 0:
                        df[f'{symbol2}_rsi'] = [np.nan] * (len(df) - len(rsi2)) + rsi2
                except Exception:
                    pass
                
                # Bollinger Bands for spread
                try:
                    bb = indicators.bollinger_bands(df['spread'].tolist(), period=20, std_dev=2)
                    if len(bb['upper']) > 0:
                        offset = len(df) - len(bb['upper'])
                        df['spread_bb_upper'] = [np.nan] * offset + bb['upper']
                        df['spread_bb_lower'] = [np.nan] * offset + bb['lower']
                        df['spread_bb_pct'] = ((df['spread'] - df['spread_bb_lower']) / 
                                               (df['spread_bb_upper'] - df['spread_bb_lower'] + 1e-8))
                except Exception:
                    pass
            
            # Trading signals
            df['signal'] = 'NEUTRAL'
            df.loc[df['zscore'] > 2.0, 'signal'] = 'SHORT_SPREAD'
            df.loc[df['zscore'] < -2.0, 'signal'] = 'LONG_SPREAD'
            df.loc[df['zscore'].abs() < 0.5, 'signal'] = 'EXIT'
            
            # Add metadata columns
            df['hedge_ratio'] = hedge_ratio
            df['pair'] = f"{symbol1}/{symbol2}"
            
            return df
            
        except Exception:
            logger.exception("Time-series stats table generation failed")
            raise
    
    @staticmethod
    def generate_summary_stats(df: pd.DataFrame, symbol1: str, symbol2: str) -> Dict[str, Any]:
        """
        Generate summary statistics from time-series DataFrame.
        
        Args:
            df: Time-series DataFrame
            symbol1: Symbol 1 name
            symbol2: Symbol 2 name
        
        Returns:
            Dictionary of summary statistics
        """
        try:
            summary = {
                'time_period': {
                    'start': str(df['datetime'].min()),
                    'end': str(df['datetime'].max()),
                    'duration_minutes': float((df['datetime'].max() - df['datetime'].min()).total_seconds() / 60),
                    'observations': len(df)
                },
                'prices': {
                    f'{symbol1}_mean': float(df[f'{symbol1}_close'].mean()),
                    f'{symbol1}_std': float(df[f'{symbol1}_close'].std()),
                    f'{symbol1}_min': float(df[f'{symbol1}_close'].min()),
                    f'{symbol1}_max': float(df[f'{symbol1}_close'].max()),
                    f'{symbol2}_mean': float(df[f'{symbol2}_close'].mean()),
                    f'{symbol2}_std': float(df[f'{symbol2}_close'].std()),
                    f'{symbol2}_min': float(df[f'{symbol2}_close'].min()),
                    f'{symbol2}_max': float(df[f'{symbol2}_close'].max()),
                },
                'spread': {
                    'mean': float(df['spread'].mean()),
                    'std': float(df['spread'].std()),
                    'min': float(df['spread'].min()),
                    'max': float(df['spread'].max()),
                    'current': float(df['spread'].iloc[-1])
                },
                'zscore': {
                    'mean': float(df['zscore'].mean()),
                    'std': float(df['zscore'].std()),
                    'min': float(df['zscore'].min()),
                    'max': float(df['zscore'].max()),
                    'current': float(df['zscore'].iloc[-1])
                },
                'correlation': {
                    'overall': float(df[f'{symbol1}_close'].corr(df[f'{symbol2}_close'])),
                    'mean_rolling': float(df['rolling_corr_20'].mean()),
                    'current_rolling': float(df['rolling_corr_20'].iloc[-1])
                },
                'signals': {
                    'long_spread_count': int((df['signal'] == 'LONG_SPREAD').sum()),
                    'short_spread_count': int((df['signal'] == 'SHORT_SPREAD').sum()),
                    'exit_count': int((df['signal'] == 'EXIT').sum()),
                    'neutral_count': int((df['signal'] == 'NEUTRAL').sum())
                }
            }
            
            return summary
            
        except Exception:
            logger.exception("Summary stats generation failed")
            raise
    
    @staticmethod
    def export_to_csv(df: pd.DataFrame, filename: Optional[str] = None) -> str:
        """
        Export DataFrame to CSV string.
        
        Args:
            df: DataFrame to export
            filename: Optional filename hint
        
        Returns:
            CSV string
        """
        try:
            # Round numeric columns for cleaner export
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df_export = df.copy()
            df_export[numeric_cols] = df_export[numeric_cols].round(6)
            
            return df_export.to_csv(index=False)
            
        except Exception:
            logger.exception("CSV export failed")
            raise


def test_timeseries_table():
    """Test time-series table generation."""
    import logging as _logging
    _logging.basicConfig(level=_logging.DEBUG)
    
    np.random.seed(42)
    
    # Generate synthetic OHLC data
    n = 100
    base_time = int(datetime.now().timestamp() * 1000)
    
    data1 = []
    data2 = []
    
    for i in range(n):
        price1 = 50000 + np.cumsum(np.random.randn(1))[0] * 100
        price2 = 0.035 * price1 + np.random.randn() * 5
        
        data1.append({
            'timestamp': base_time + i * 60000,  # 1 minute intervals
            'open': price1,
            'high': price1 * 1.001,
            'low': price1 * 0.999,
            'close': price1,
            'volume': abs(np.random.randn() * 10)
        })
        
        data2.append({
            'timestamp': base_time + i * 60000,
            'open': price2,
            'high': price2 * 1.001,
            'low': price2 * 0.999,
            'close': price2,
            'volume': abs(np.random.randn() * 100)
        })
    
    table_gen = TimeSeriesStatsTable()
    
    print("=== Generating Stats Table ===")
    df = table_gen.generate_stats_table(data1, data2, "BTCUSDT", "ETHUSDT", hedge_ratio=0.035)
    print(f"Table shape: {df.shape}")
    print(f"\nColumns: {list(df.columns)}")
    print(f"\nFirst 5 rows:")
    print(df.head())
    
    print("\n=== Summary Statistics ===")
    summary = table_gen.generate_summary_stats(df, "BTCUSDT", "ETHUSDT")
    print(f"Time period: {summary['time_period']['duration_minutes']:.1f} minutes")
    print(f"Z-score current: {summary['zscore']['current']:.3f}")
    print(f"Signals: {summary['signals']}")
    
    print("\n=== CSV Export Sample ===")
    csv_str = table_gen.export_to_csv(df)
    print(csv_str[:500] + "...")


if __name__ == "__main__":
    test_timeseries_table()
