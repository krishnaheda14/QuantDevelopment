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
