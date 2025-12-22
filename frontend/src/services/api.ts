import axios from 'axios'
import { debug, info, error } from '@/types'
import type {
  OHLCBar,
  SpreadAnalysis,
  ADFTestResult,
  CointegrationResult,
  TechnicalIndicators,
  BacktestResult,
  KalmanFilterResult,
  LiquidityProfile,
  MicrostructureMetrics,
  CorrelationMatrix,
  ConnectionStatus,
} from '@/types'

const API_BASE_URL = '/api'

// Debug: Log API client initialization
debug('API', 'Initializing API client', { baseURL: API_BASE_URL })

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for debugging
apiClient.interceptors.request.use(
  (config) => {
    debug('API', `Request: ${config.method?.toUpperCase()} ${config.url}`, {
      params: config.params,
      data: config.data,
    })
    return config
  },
  (err) => {
    error('API', 'Request error', err)
    return Promise.reject(err)
  }
)

// Response interceptor for debugging
apiClient.interceptors.response.use(
  (response) => {
    debug('API', `Response: ${response.config.url}`, {
      status: response.status,
      dataSize: JSON.stringify(response.data).length,
    })
    return response
  },
  (err) => {
    error('API', 'Response error', {
      url: err.config?.url,
      status: err.response?.status,
      message: err.message,
    })
    return Promise.reject(err)
  }
)

export const api = {
  // System endpoints
  async getHealth(): Promise<any> {
    info('API', 'Fetching system health')
    const { data } = await apiClient.get('/health')
    return data
  },

  // Debug endpoints
  async getDebugSystemStatus(): Promise<any> {
    debug('API', 'Fetching debug system status')
    const { data } = await apiClient.get('/debug/system/status')
    return data
  },

  async getDebugRedisStatus(): Promise<any> {
    debug('API', 'Fetching debug redis status')
    const { data } = await apiClient.get('/debug/redis/status')
    return data
  },

  async getDebugServicesStatus(): Promise<any> {
    debug('API', 'Fetching debug services status')
    const { data } = await apiClient.get('/debug/services/status')
    return data
  },

  async getConnectionStatus(): Promise<ConnectionStatus> {
    debug('API', 'Fetching connection status')
    const { data } = await apiClient.get('/status')
    return data
  },

  async getSymbols(): Promise<string[]> {
    info('API', 'Fetching available symbols')
    const { data } = await apiClient.get('/symbols')
    debug('API', 'Symbols received', { count: data.length, symbols: data })
    return data
  },

  // Data endpoints
  async getOHLC(symbol: string, interval: string = '1m', limit: number = 100): Promise<OHLCBar[]> {
    debug('API', 'Fetching OHLC data', { symbol, interval, limit })
    const { data } = await apiClient.get(`/ohlc/${symbol}`, {
      params: { interval, limit },
    })
    info('API', `OHLC data received for ${symbol}`, { bars: data.length })
    return data
  },

  async getTicks(symbol: string, limit: number = 100): Promise<any[]> {
    debug('API', 'Fetching tick data', { symbol, limit })
    const { data } = await apiClient.get(`/ticks/${symbol}`, {
      params: { limit },
    })
    info('API', `Tick data received for ${symbol}`, { ticks: data.length })
    return data
  },

  // Analytics endpoints
  async getSpreadAnalysis(
    symbol1: string,
    symbol2: string,
    lookback: number = 100
  ): Promise<SpreadAnalysis> {
    debug('API', 'Fetching spread analysis', { symbol1, symbol2, lookback })
    const { data } = await apiClient.get('/analytics/spread', {
      params: { symbol1, symbol2, lookback },
    })
    info('API', 'Spread analysis received', {
      hedgeRatio: data.hedge_ratio,
      currentZScore: data.current_zscore,
      signal: data.signal,
    })
    return data
  },

  async getADFTest(symbol1: string, symbol2?: string, lookback: number = 100): Promise<ADFTestResult> {
    debug('API', 'Fetching ADF test', { symbol1, symbol2, lookback })
    const params: any = { symbol: symbol1, lookback }
    if (symbol2) params.symbol2 = symbol2
    const { data } = await apiClient.get('/analytics/adf', {
      params,
    })
    info('API', 'ADF test result received', {
      isStationary: data.is_stationary,
      pValue: data.p_value,
    })
    return data
  },

  async getCointegration(symbol1: string, symbol2: string, lookback?: number): Promise<CointegrationResult> {
    debug('API', 'Fetching cointegration test', { symbol1, symbol2, lookback })
    const params: any = { symbol1, symbol2 }
    if (lookback) params.lookback = lookback
    const { data } = await apiClient.get('/analytics/cointegration', {
      params,
    })
    info('API', 'Cointegration result received', {
      isCointegrated: data.is_cointegrated,
      pValue: data.spread_p_value,
    })
    return data
  },

  async getIndicators(symbol1: string, arg2?: string | number, arg3?: number): Promise<TechnicalIndicators> {
    // Flexible signature: (symbol), (symbol, lookback), (symbol1, symbol2, lookback)
    let symbol2: string | undefined
    let lookback = 100
    if (typeof arg2 === 'string') {
      symbol2 = arg2
      if (typeof arg3 === 'number') lookback = arg3
    } else if (typeof arg2 === 'number') {
      lookback = arg2
    }

    debug('API', 'Fetching technical indicators', { symbol1, symbol2, lookback })
    const params: any = { symbol: symbol1, lookback }
    if (symbol2) params.symbol2 = symbol2
    const { data } = await apiClient.get('/analytics/indicators', {
      params,
    })
    info('API', 'Technical indicators received', {
      rsiLength: data.rsi?.length || 0,
      // handle both shapes
      macdLength: Array.isArray(data.macd) ? data.macd.length : data.macd?.macd?.length || 0,
    })
    return data
  },

  async runBacktest(
    symbol1: string,
    symbol2: string,
    // support calling convention used by Backtesting page: (symbol1, symbol2, entryThreshold, exitThreshold, stopLoss, lookback)
    arg3: any,
    arg4?: any,
    arg5?: any,
    arg6?: any,
    arg7?: any
  ): Promise<BacktestResult> {
    // Normalize payload
    let payload: any = { symbol1, symbol2 }

    if (typeof arg3 === 'string') {
      // legacy: (symbol1, symbol2, strategy, params)
      payload.strategy = arg3
      payload.params = arg4 || {}
    } else {
      // numeric thresholds: (entryThreshold, exitThreshold, stopLoss)
      payload.params = {
        entry_threshold: arg3,
        exit_threshold: arg4,
        stop_loss: arg5,
      }
    }

    debug('API', 'Running backtest', payload)
    if (typeof arg6 === 'number') payload.lookback = arg6
    // optional extra options (strategy, params, trade_size, commission, etc.)
    if (arg7 && typeof arg7 === 'object') {
      // merge top-level keys
      Object.assign(payload, arg7)
    }
    const { data } = await apiClient.post('/analytics/backtest', payload)
    info('API', 'Backtest completed', {
      numTrades: data.num_trades,
      sharpeRatio: data.sharpe_ratio,
      winRate: data.win_rate,
    })
    return data
  },

  async getKalmanFilter(symbol1: string, symbol2: string): Promise<KalmanFilterResult> {
    debug('API', 'Fetching Kalman filter results', { symbol1, symbol2 })
    const { data } = await apiClient.get('/analytics/kalman', {
      params: { symbol1, symbol2 },
    })
    info('API', 'Kalman filter results received', {
      currentHedgeRatio: data.current_hedge_ratio,
    })
    return data
  },

  async getLiquidityProfile(symbol: string, lookback: number = 100): Promise<LiquidityProfile> {
    debug('API', 'Fetching liquidity profile', { symbol, lookback })
    const { data } = await apiClient.get('/analytics/liquidity', {
      params: { symbol, lookback },
    })
    info('API', 'Liquidity profile received', {
      poc: data.poc,
      price_levels_count: data.price_levels?.length || 0,
    })
    return data
  },

  async getMicrostructure(symbol: string, lookback: number = 100): Promise<MicrostructureMetrics> {
    debug('API', 'Fetching microstructure metrics', { symbol, lookback })
    const { data } = await apiClient.get('/analytics/microstructure', {
      params: { symbol, lookback },
    })
    info('API', 'Microstructure metrics received')
    return data
  },

  async getCorrelationMatrix(symbols: string[]): Promise<CorrelationMatrix> {
    debug('API', 'Fetching correlation matrix', { symbols })
    const { data } = await apiClient.post('/analytics/correlation', { symbols })
    info('API', 'Correlation matrix received', {
      symbolCount: data.symbols?.length || 0,
    })
    return data
  },

  // Export endpoints
  async exportCSV(symbol: string, interval: string = '1m'): Promise<Blob> {
    debug('API', 'Exporting CSV', { symbol, interval })
    const { data } = await apiClient.get(`/export/csv`, {
      params: { symbol, interval },
      responseType: 'blob',
    })
    info('API', 'CSV exported successfully')
    return data
  },
}

export default api
