"""
Backtester - Simple strategy backtesting engine
"""

import numpy as np
from typing import List, Dict, Tuple
from src.analytics.indicators import TechnicalIndicators

class Backtester:
    """Backtest trading strategies"""
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
    
    def run_backtest(self, prices: List[float], strategy: str = 'z_score',
                    capital: float = 10000, **kwargs) -> Dict:
        """
        Run backtest on price series
        
        Args:
            prices: Price series
            strategy: Strategy type ('z_score', 'rsi', 'macd', 'multi_strategy')
            capital: Initial capital
            **kwargs: Strategy-specific parameters
        
        Returns:
            Backtest results with metrics and trades
        """
        if strategy == 'z_score':
            return self._backtest_zscore(prices, capital, **kwargs)
        elif strategy == 'rsi':
            return self._backtest_rsi(prices, capital, **kwargs)
        elif strategy == 'macd':
            return self._backtest_macd(prices, capital, **kwargs)
        elif strategy == 'multi_strategy':
            return self._backtest_multi(prices, capital, **kwargs)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    def _backtest_zscore(self, prices: List[float], capital: float,
                        zscore_threshold: float = 2.0, **kwargs) -> Dict:
        """Backtest z-score mean reversion strategy"""
        prices = np.array(prices)
        
        # Calculate z-score (simplified - using rolling mean/std)
        window = kwargs.get('window', 20)
        rolling_mean = np.array([
            np.mean(prices[max(0, i-window):i+1])
            for i in range(len(prices))
        ])
        rolling_std = np.array([
            np.std(prices[max(0, i-window):i+1])
            for i in range(len(prices))
        ])
        
        zscore = (prices - rolling_mean) / (rolling_std + 1e-8)
        
        # Simulate trades
        position = 0  # 0 = flat, 1 = long, -1 = short
        entry_price = 0
        equity = [capital]
        trades = []
        
        for i in range(window, len(prices)):
            if position == 0:
                # Enter long if oversold
                if zscore[i] < -zscore_threshold:
                    position = 1
                    entry_price = prices[i]
                    trades.append({
                        'index': i,
                        'type': 'LONG',
                        'price': entry_price,
                        'zscore': zscore[i]
                    })
                # Enter short if overbought
                elif zscore[i] > zscore_threshold:
                    position = -1
                    entry_price = prices[i]
                    trades.append({
                        'index': i,
                        'type': 'SHORT',
                        'price': entry_price,
                        'zscore': zscore[i]
                    })
            else:
                # Exit conditions
                exit_signal = False
                if position == 1 and zscore[i] > 0:
                    exit_signal = True
                elif position == -1 and zscore[i] < 0:
                    exit_signal = True
                
                if exit_signal:
                    # Calculate P&L
                    if position == 1:
                        pnl = (prices[i] - entry_price) / entry_price
                    else:
                        pnl = (entry_price - prices[i]) / entry_price
                    
                    capital *= (1 + pnl)
                    
                    trades.append({
                        'index': i,
                        'type': 'EXIT',
                        'price': prices[i],
                        'zscore': zscore[i],
                        'pnl': pnl * 100
                    })
                    
                    position = 0
            
            # Update equity curve
            if position != 0:
                if position == 1:
                    unrealized_pnl = (prices[i] - entry_price) / entry_price
                else:
                    unrealized_pnl = (entry_price - prices[i]) / entry_price
                equity.append(capital * (1 + unrealized_pnl))
            else:
                equity.append(capital)
        
        return self._calculate_metrics(equity, trades, prices)
    
    def _backtest_rsi(self, prices: List[float], capital: float,
                     rsi_levels: Tuple[float, float] = (30, 70), **kwargs) -> Dict:
        """Backtest RSI strategy"""
        rsi_oversold, rsi_overbought = rsi_levels
        
        rsi_values = self.indicators.rsi(prices, period=14)
        if len(rsi_values) == 0:
            return self._empty_results()
        
        prices = np.array(prices)
        offset = len(prices) - len(rsi_values)
        
        position = 0
        entry_price = 0
        equity = [capital] * offset
        trades = []
        
        for i in range(len(rsi_values)):
            price_idx = i + offset
            
            if position == 0:
                if rsi_values[i] < rsi_oversold:
                    position = 1
                    entry_price = prices[price_idx]
                    trades.append({
                        'index': price_idx,
                        'type': 'LONG',
                        'price': entry_price,
                        'rsi': rsi_values[i]
                    })
                elif rsi_values[i] > rsi_overbought:
                    position = -1
                    entry_price = prices[price_idx]
                    trades.append({
                        'index': price_idx,
                        'type': 'SHORT',
                        'price': entry_price,
                        'rsi': rsi_values[i]
                    })
            else:
                exit_signal = False
                if position == 1 and rsi_values[i] > 50:
                    exit_signal = True
                elif position == -1 and rsi_values[i] < 50:
                    exit_signal = True
                
                if exit_signal:
                    if position == 1:
                        pnl = (prices[price_idx] - entry_price) / entry_price
                    else:
                        pnl = (entry_price - prices[price_idx]) / entry_price
                    
                    capital *= (1 + pnl)
                    
                    trades.append({
                        'index': price_idx,
                        'type': 'EXIT',
                        'price': prices[price_idx],
                        'rsi': rsi_values[i],
                        'pnl': pnl * 100
                    })
                    
                    position = 0
            
            if position != 0:
                if position == 1:
                    unrealized_pnl = (prices[price_idx] - entry_price) / entry_price
                else:
                    unrealized_pnl = (entry_price - prices[price_idx]) / entry_price
                equity.append(capital * (1 + unrealized_pnl))
            else:
                equity.append(capital)
        
        return self._calculate_metrics(equity, trades, prices)
    
    def _backtest_macd(self, prices: List[float], capital: float, **kwargs) -> Dict:
        """Backtest MACD strategy"""
        macd_data = self.indicators.macd(prices)
        if len(macd_data['macd']) == 0:
            return self._empty_results()
        
        prices = np.array(prices)
        macd = np.array(macd_data['macd'])
        signal = np.array(macd_data['signal'])
        offset = len(prices) - len(macd)
        
        position = 0
        entry_price = 0
        equity = [capital] * offset
        trades = []
        
        for i in range(1, len(macd)):
            price_idx = i + offset
            
            # Detect crossovers
            bullish_cross = macd[i] > signal[i] and macd[i-1] <= signal[i-1]
            bearish_cross = macd[i] < signal[i] and macd[i-1] >= signal[i-1]
            
            if position == 0:
                if bullish_cross:
                    position = 1
                    entry_price = prices[price_idx]
                    trades.append({
                        'index': price_idx,
                        'type': 'LONG',
                        'price': entry_price,
                        'macd': macd[i]
                    })
                elif bearish_cross:
                    position = -1
                    entry_price = prices[price_idx]
                    trades.append({
                        'index': price_idx,
                        'type': 'SHORT',
                        'price': entry_price,
                        'macd': macd[i]
                    })
            else:
                exit_signal = False
                if position == 1 and bearish_cross:
                    exit_signal = True
                elif position == -1 and bullish_cross:
                    exit_signal = True
                
                if exit_signal:
                    if position == 1:
                        pnl = (prices[price_idx] - entry_price) / entry_price
                    else:
                        pnl = (entry_price - prices[price_idx]) / entry_price
                    
                    capital *= (1 + pnl)
                    
                    trades.append({
                        'index': price_idx,
                        'type': 'EXIT',
                        'price': prices[price_idx],
                        'macd': macd[i],
                        'pnl': pnl * 100
                    })
                    
                    position = 0
            
            if position != 0:
                if position == 1:
                    unrealized_pnl = (prices[price_idx] - entry_price) / entry_price
                else:
                    unrealized_pnl = (entry_price - prices[price_idx]) / entry_price
                equity.append(capital * (1 + unrealized_pnl))
            else:
                equity.append(capital)
        
        return self._calculate_metrics(equity, trades, prices)
    
    def _backtest_multi(self, prices: List[float], capital: float, **kwargs) -> Dict:
        """Backtest multi-strategy combining signals"""
        # Combine RSI, MACD, and mean reversion
        rsi_results = self._backtest_rsi(prices, capital, **kwargs)
        macd_results = self._backtest_macd(prices, capital, **kwargs)
        
        # Simple ensemble: average returns
        combined_return = (rsi_results['total_return'] + macd_results['total_return']) / 2
        combined_sharpe = (rsi_results['sharpe_ratio'] + macd_results['sharpe_ratio']) / 2
        
        return {
            'total_return': combined_return,
            'sharpe_ratio': combined_sharpe,
            'max_drawdown': max(rsi_results['max_drawdown'], macd_results['max_drawdown']),
            'win_rate': (rsi_results['win_rate'] + macd_results['win_rate']) / 2,
            'equity_curve': rsi_results['equity_curve'],  # Use one for display
            'trades': rsi_results['trades'] + macd_results['trades']
        }
    
    def _calculate_metrics(self, equity: List[float], trades: List[Dict],
                          prices: np.ndarray) -> Dict:
        """Calculate performance metrics"""
        equity = np.array(equity)
        
        if len(equity) < 2:
            return self._empty_results()
        
        # Total return
        total_return = ((equity[-1] / equity[0]) - 1) * 100
        
        # Calculate returns
        returns = np.diff(equity) / equity[:-1]
        
        # Sharpe ratio (annualized, assuming daily data)
        if len(returns) > 0 and np.std(returns) > 0:
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)
        else:
            sharpe_ratio = 0
        
        # Max drawdown
        cummax = np.maximum.accumulate(equity)
        drawdown = (equity - cummax) / cummax * 100
        max_drawdown = abs(np.min(drawdown))
        
        # Win rate
        winning_trades = [t for t in trades if 'pnl' in t and t['pnl'] > 0]
        total_closed = len([t for t in trades if 'pnl' in t])
        win_rate = (len(winning_trades) / total_closed * 100) if total_closed > 0 else 0
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'equity_curve': equity.tolist(),
            'trades': trades
        }
    
    def _empty_results(self) -> Dict:
        """Return empty results when backtest fails"""
        return {
            'total_return': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'win_rate': 0,
            'equity_curve': [],
            'trades': []
        }

    def multi_timeframe_backtest(self, data_by_timeframe: Dict[str, List[float]], 
                                   strategy: str = 'z_score',
                                   capital: float = 10000, **kwargs) -> Dict:
        """
        Run backtest across multiple timeframes and aggregate results.
        
        Args:
            data_by_timeframe: Dictionary mapping timeframe (e.g., '1m', '5m', '1h') to price series
            strategy: Strategy to backtest
            capital: Initial capital per timeframe
            **kwargs: Strategy parameters
        
        Returns:
            Aggregated backtest results across all timeframes
        """
        timeframe_results = {}
        
        for tf, prices in data_by_timeframe.items():
            if len(prices) < 50:
                # Skip if insufficient data
                continue
            
            result = self.run_backtest(prices, strategy=strategy, capital=capital, **kwargs)
            timeframe_results[tf] = result
        
        if not timeframe_results:
            return {
                "timeframe_results": {},
                "combined_metrics": self._empty_results(),
                "best_timeframe": None
            }
        
        # Calculate aggregate metrics
        total_returns = [r['total_return'] for r in timeframe_results.values()]
        sharpe_ratios = [r['sharpe_ratio'] for r in timeframe_results.values()]
        max_drawdowns = [r['max_drawdown'] for r in timeframe_results.values()]
        win_rates = [r['win_rate'] for r in timeframe_results.values()]
        
        combined_metrics = {
            "avg_total_return": float(np.mean(total_returns)),
            "avg_sharpe_ratio": float(np.mean(sharpe_ratios)),
            "avg_max_drawdown": float(np.mean(max_drawdowns)),
            "avg_win_rate": float(np.mean(win_rates)),
            "best_return": float(np.max(total_returns)),
            "worst_return": float(np.min(total_returns)),
            "timeframe_count": len(timeframe_results)
        }
        
        # Identify best timeframe
        best_tf = max(timeframe_results.keys(), key=lambda tf: timeframe_results[tf]['total_return'])
        
        return {
            "timeframe_results": timeframe_results,
            "combined_metrics": combined_metrics,
            "best_timeframe": best_tf,
            "best_metrics": timeframe_results[best_tf]
        }
    
    def walk_forward_analysis(self, prices: List[float], 
                               in_sample_pct: float = 0.7,
                               n_folds: int = 3,
                               strategy: str = 'z_score',
                               capital: float = 10000, **kwargs) -> Dict:
        """
        Perform walk-forward analysis (rolling train/test splits).
        
        Args:
            prices: Full price series
            in_sample_pct: Percentage of data for in-sample (training)
            n_folds: Number of walk-forward folds
            strategy: Strategy to test
            capital: Initial capital
            **kwargs: Strategy parameters
        
        Returns:
            Walk-forward test results
        """
        prices_arr = np.array(prices)
        n_total = len(prices_arr)
        
        fold_size = n_total // (n_folds + 1)
        
        fold_results = []
        
        for fold_idx in range(n_folds):
            # Define in-sample and out-of-sample windows
            train_start = fold_idx * fold_size
            train_end = train_start + int(fold_size * in_sample_pct)
            test_start = train_end
            test_end = min(test_start + fold_size, n_total)
            
            if test_end - test_start < 20:
                # Skip if test window too small
                continue
            
            train_prices = prices_arr[train_start:train_end]
            test_prices = prices_arr[test_start:test_end]
            
            # Optimize parameters on training set (simplified: just use provided params)
            # In real implementation, would optimize here
            
            # Test on out-of-sample data
            test_result = self.run_backtest(test_prices.tolist(), strategy=strategy, 
                                             capital=capital, **kwargs)
            
            fold_results.append({
                "fold": fold_idx + 1,
                "train_window": (train_start, train_end),
                "test_window": (test_start, test_end),
                "test_return": test_result['total_return'],
                "test_sharpe": test_result['sharpe_ratio'],
                "test_win_rate": test_result['win_rate']
            })
        
        if not fold_results:
            return {
                "fold_results": [],
                "average_oos_return": 0.0,
                "average_oos_sharpe": 0.0,
                "consistency_score": 0.0
            }
        
        # Calculate aggregate out-of-sample metrics
        oos_returns = [f['test_return'] for f in fold_results]
        oos_sharpes = [f['test_sharpe'] for f in fold_results]
        
        # Consistency score: negative if returns vary wildly
        consistency_score = 1.0 / (1.0 + np.std(oos_returns)) if len(oos_returns) > 1 else 1.0
        
        return {
            "fold_results": fold_results,
            "average_oos_return": float(np.mean(oos_returns)),
            "average_oos_sharpe": float(np.mean(oos_sharpes)),
            "consistency_score": float(consistency_score),
            "n_folds": len(fold_results)
        }

