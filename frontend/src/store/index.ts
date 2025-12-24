import { create } from 'zustand'
import { debug, info } from '@/types'
import type {
  TickData,
  OHLCBar,
  SpreadAnalysis,
  ConnectionStatus,
  Alert,
} from '@/types'

interface AppState {
  // Connection
  isConnected: boolean
  connectionStatus: ConnectionStatus | null
  setConnected: (connected: boolean) => void
  setConnectionStatus: (status: ConnectionStatus) => void

  // Symbols
  selectedSymbol1: string
  selectedSymbol2: string
  availableSymbols: string[]
  setSelectedSymbol1: (symbol: string) => void
  setSelectedSymbol2: (symbol: string) => void
  setAvailableSymbols: (symbols: string[]) => void

  // Settings
  lookbackMinutes: number
  aggregationInterval: string
  zscoreEntry: number
  zscoreExit: number
  rsiOversold: number
  rsiOverbought: number
  setLookbackMinutes: (minutes: number) => void
  setAggregationInterval: (interval: string) => void
  setZscoreEntry: (value: number) => void
  setZscoreExit: (value: number) => void
  setRsiOversold: (value: number) => void
  setRsiOverbought: (value: number) => void

  // Real-time data
  latestTicks: Map<string, TickData[]>
  latestBars: Map<string, OHLCBar[]>
  // Backward-compatible aliases used across pages
  ticks: Map<string, TickData[]>
  ohlcBars: Map<string, OHLCBar[]>
  addTick: (tick: TickData) => void
  addBar: (bar: OHLCBar) => void
  addTicks: (ticks: TickData[]) => void

  // Derived settings object expected by many pages
  settings: {
    lookbackPeriod: number
    aggregationInterval: string
    zScoreThreshold: number
    zScoreExit: number
    rsiOversold: number
    rsiOverbought: number
  }

  // Analytics
  spreadAnalysis: SpreadAnalysis | null
  setSpreadAnalysis: (analysis: SpreadAnalysis) => void

  // Alerts
  alerts: Alert[]
  addAlert: (alert: Alert) => void
  clearAlert: (id: string) => void
  clearAllAlerts: () => void

  // UI state
  autoRefresh: boolean
  setAutoRefresh: (value: boolean) => void
}

debug('Store', 'Creating Zustand store')

export const useStore = create<AppState>((set, get) => {
  info('Store', 'Store initialized with default values')

  return {
    // Connection
    isConnected: false,
    connectionStatus: null,
    setConnected: (connected) => {
      debug('Store', 'Connection status updated', { connected })
      set({ isConnected: connected })
    },
    setConnectionStatus: (status) => {
      debug('Store', 'Connection status details updated', status)
      set({ connectionStatus: status })
    },

    // Symbols
    selectedSymbol1: 'BTCUSDT',
    selectedSymbol2: 'ETHUSDT',
    availableSymbols: [],
    setSelectedSymbol1: (symbol) => {
      info('Store', 'Symbol 1 changed', { from: get().selectedSymbol1, to: symbol })
      set({ selectedSymbol1: symbol })
    },
    setSelectedSymbol2: (symbol) => {
      info('Store', 'Symbol 2 changed', { from: get().selectedSymbol2, to: symbol })
      set({ selectedSymbol2: symbol })
    },
    setAvailableSymbols: (symbols) => {
      info('Store', 'Available symbols updated', { count: symbols.length, symbols })
      set({ availableSymbols: symbols })
    },

    // Settings
    lookbackMinutes: 500,
    aggregationInterval: '1m',
    apiInterval: '1s',
    zscoreEntry: 2.0,
    zscoreExit: 0.0,
    rsiOversold: 30,
    rsiOverbought: 70,
    setLookbackMinutes: (minutes) => {
      debug('Store', 'Lookback minutes changed', { minutes })
      set((state) => ({ lookbackMinutes: minutes, settings: { ...state.settings, lookbackPeriod: minutes } }))
    },
    setAggregationInterval: (interval) => {
      debug('Store', 'Aggregation interval changed', { interval })
      set((state) => ({ aggregationInterval: interval, settings: { ...state.settings, aggregationInterval: interval } }))
    },
    setApiInterval: (interval: string) => {
      debug('Store', 'API interval changed', { interval })
      set((state) => ({ apiInterval: interval, settings: { ...state.settings, apiInterval: interval } }))
    },
    setZscoreEntry: (value) => {
      debug('Store', 'Z-score entry threshold changed', { value })
      set((state) => ({ zscoreEntry: value, settings: { ...state.settings, zScoreThreshold: value } }))
    },
    setZscoreExit: (value) => {
      debug('Store', 'Z-score exit threshold changed', { value })
      set((state) => ({ zscoreExit: value, settings: { ...state.settings, zScoreExit: value } }))
    },
    setRsiOversold: (value) => {
      debug('Store', 'RSI oversold level changed', { value })
      set((state) => ({ rsiOversold: value, settings: { ...state.settings, rsiOversold: value } }))
    },
    setRsiOverbought: (value) => {
      debug('Store', 'RSI overbought level changed', { value })
      set((state) => ({ rsiOverbought: value, settings: { ...state.settings, rsiOverbought: value } }))
    },

    // Derived settings object for pages expecting a settings structure
    settings: {
      lookbackPeriod: 500,
      aggregationInterval: '1m',
      apiInterval: '1s',
      zScoreThreshold: 2.0,
      zScoreExit: 0.0,
      rsiOversold: 30,
      rsiOverbought: 70,
    },

    // Real-time data
    latestTicks: new Map(),
    latestBars: new Map(),
    // Legacy aliases used by pages: keep both keys in sync
    ticks: new Map(),
    ohlcBars: new Map(),
    addTick: (tick) => {
      const ticks = get().latestTicks
      const symbolTicks = ticks.get(tick.symbol) || []
      
      // Keep last 1000 ticks per symbol
      const updated = [...symbolTicks, tick].slice(-1000)
      ticks.set(tick.symbol, updated)
      
      debug('Store', 'Tick added', {
        symbol: tick.symbol,
        price: tick.price,
        totalTicks: updated.length,
      })
      
      // Update both latestTicks and ticks (alias) for backward compatibility
      set({ latestTicks: new Map(ticks), ticks: new Map(ticks) })
    },
    addTicks: (tickArray) => {
      if (!tickArray || tickArray.length === 0) {
        debug('Store', 'addTicks called with empty array')
        return
      }

      const ticksMap = get().latestTicks
      let totalAdded = 0

      for (const tick of tickArray) {
        const symbolTicks = ticksMap.get(tick.symbol) || []
        const updated = [...symbolTicks, tick].slice(-1000)
        ticksMap.set(tick.symbol, updated)
        totalAdded++
      }

      info('Store', `Batched ${totalAdded} ticks added`, { 
        symbols: Array.from(ticksMap.keys()),
        totalTicksInStore: Array.from(ticksMap.values()).reduce((sum, arr) => sum + arr.length, 0)
      })

      // Single set to update state once
      set({ latestTicks: new Map(ticksMap), ticks: new Map(ticksMap) })
    },
    addBar: (bar) => {
      const bars = get().latestBars
      const symbolBars = bars.get(bar.symbol) || []
      
      // Keep last 500 bars per symbol
      // If incoming bar has same timestamp as last bar, replace last bar (snapshot update). Otherwise append.
      const updated = [...symbolBars]
      const last = updated[updated.length - 1]
      if (last && last.timestamp === bar.timestamp) {
        updated[updated.length - 1] = bar
      } else {
        updated.push(bar)
      }
      const sliced = updated.slice(-500)
      bars.set(bar.symbol, sliced)
      
      debug('Store', 'OHLC bar added', {
        symbol: bar.symbol,
        close: bar.close,
        totalBars: updated.length,
      })
      
      // Update both latestBars and ohlcBars (alias) for backward compatibility
      set({ latestBars: new Map(bars), ohlcBars: new Map(bars) })
    },

    // Analytics
    spreadAnalysis: null,
    setSpreadAnalysis: (analysis) => {
      info('Store', 'Spread analysis updated', {
        hedgeRatio: analysis.hedge_ratio,
        currentZScore: analysis.current_zscore,
        signal: analysis.signal,
      })
      set({ spreadAnalysis: analysis })
    },

    // Alerts
    alerts: [],
    addAlert: (alert) => {
      info('Store', 'Alert added', {
        type: alert.type,
        symbol: alert.symbol,
        message: alert.message,
      })
      set({ alerts: [...get().alerts, alert] })
    },
    clearAlert: (id) => {
      debug('Store', 'Alert cleared', { id })
      set({ alerts: get().alerts.filter((a) => a.id !== id) })
    },
    clearAllAlerts: () => {
      info('Store', 'All alerts cleared')
      set({ alerts: [] })
    },

    // UI state
    autoRefresh: true,
    setAutoRefresh: (value) => {
      debug('Store', 'Auto-refresh toggled', { value })
      set({ autoRefresh: value })
    },
  }
})

info('Store', 'Zustand store exported successfully')
