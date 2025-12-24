// Core data types matching Python backend

export interface TickData {
  symbol: string
  timestamp: number
  price: number
  quantity: number
  isBuyerMaker: boolean
}

export interface OHLCBar {
  symbol: string
  timestamp: number
  open: number
  high: number
  low: number
  close: number
  volume: number
  tick_count: number
}

export interface SpreadAnalysis {
  hedge_ratio: number
  alpha: number
  r_squared: number
  correlation: number
  spread: number[]
  zscore: number[]
  timestamps: number[]
  current_zscore: number
  signal: 'LONG' | 'SHORT' | 'NEUTRAL' | 'EXIT'
  // Backwards-compatible aliases used across the UI
  z_score?: number
  z_scores?: number[]
  spread_values?: number[]
  intercept?: number
  spread_mean?: number
  spread_std?: number
}

export interface ADFTestResult {
  adf_statistic: number
  p_value: number
  critical_values: Record<string, number>
  is_stationary: boolean
  interpretation: string
  observations: number
  // Rolling window fields (optional)
  stationary_pct?: number | null
  is_stationary_by_threshold?: boolean | null
}

export interface CointegrationResult {
  hedge_ratio?: number
  spread_adf_stat?: number
  spread_p_value?: number
  is_cointegrated: boolean
  interpretation?: string
  // Compatibility aliases
  cointegration_statistic?: number | null
  p_value?: number
  r_squared?: number | null
  observations?: number
  timestamp?: string
  critical_values?: any
}

export interface TechnicalIndicators {
  rsi: number[]
  macd: {
    macd: number[]
    signal: number[]
    histogram: number[]
  }
  bollinger_bands: {
    upper: number[]
    middle: number[]
    lower: number[]
  }
  timestamps: number[]
  // Flat aliases used in UI
  macd_signal?: number[]
  macd_histogram?: number[]
  // Bollinger bands: nested and flat aliases
  bollinger_upper?: number[]
  bollinger_middle?: number[]
  bollinger_lower?: number[]
  // Price series if provided
  prices?: number[]
}

export interface BacktestResult {
  equity_curve: number[]
  trades: Trade[]
  sharpe_ratio: number
  max_drawdown: number
  win_rate: number
  total_return: number
  num_trades: number
  // Compatibility fields expected by some UI components
  winning_trades?: number
  losing_trades?: number
  avg_trade_return?: number
}

export interface Trade {
  entry_time: number
  exit_time: number
  entry_price: number
  exit_price: number
  pnl: number
  side: 'LONG' | 'SHORT'
}

export interface KalmanFilterResult {
  hedge_ratio: number[]
  hedge_ratio_std: number[]
  predicted_spread: number[]
  timestamps: number[]
  current_hedge_ratio: number
  // (no extra aliases here)
}

export interface LiquidityProfile {
  price_levels: number[]
  volumes: number[]
  poc: number
  value_area_high: number
  value_area_low: number
}

export interface MicrostructureMetrics {
  order_flow_imbalance: number[]
  vwap: number[]
  vwap_deviation: number[]
  effective_spread: number[]
  timestamps: number[]
}

export interface CorrelationMatrix {
  symbols: string[]
  matrix: number[][]
  best_correlated: { symbol1: string; symbol2: string; correlation: number }
  worst_correlated: { symbol1: string; symbol2: string; correlation: number }
  pairs: Array<{ symbol1: string; symbol2: string; correlation: number }>
}

export interface ConnectionStatus {
  connected: boolean
  active_symbols: number
  symbols: number
  total_ticks: number
  uptime: number
}

export interface Alert {
  id: string
  timestamp: number
  symbol: string
  type: 'ZSCORE' | 'PRICE' | 'VOLUME' | 'CUSTOM'
  message: string
  severity: 'info' | 'warning' | 'error'
  triggered: boolean
  value?: number
}

// Debug logging interface
export interface DebugLog {
  timestamp: number
  level: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR'
  component: string
  message: string
  data?: any
}

// Debug logger utility
export class DebugLogger {
  private static logs: DebugLog[] = []
  private static maxLogs = 1000

  static log(level: DebugLog['level'], component: string, message: string, data?: any) {
    const logEntry: DebugLog = {
      timestamp: Date.now(),
      level,
      component,
      message,
      data,
    }

    this.logs.push(logEntry)
    if (this.logs.length > this.maxLogs) {
      this.logs.shift()
    }

    const prefix = `[${level}][${component}]`
    const fullMessage = data ? `${message} - Data:` : message

    switch (level) {
      case 'DEBUG':
        console.debug(prefix, fullMessage, data || '')
        break
      case 'INFO':
        console.info(prefix, fullMessage, data || '')
        break
      case 'WARN':
        console.warn(prefix, fullMessage, data || '')
        break
      case 'ERROR':
        console.error(prefix, fullMessage, data || '')
        break
    }
  }

  static getLogs() {
    return [...this.logs]
  }

  static clearLogs() {
    this.logs = []
  }
}

// Export convenience methods
export const debug = (component: string, message: string, data?: any) =>
  DebugLogger.log('DEBUG', component, message, data)
export const info = (component: string, message: string, data?: any) =>
  DebugLogger.log('INFO', component, message, data)
export const warn = (component: string, message: string, data?: any) =>
  DebugLogger.log('WARN', component, message, data)
export const error = (component: string, message: string, data?: any) =>
  DebugLogger.log('ERROR', component, message, data)
