import { io, Socket } from 'socket.io-client'
import { debug, info, warn, error } from '@/types'
import type { TickData, OHLCBar, ConnectionStatus } from '@/types'
import { useStore } from '@/store'
import api from '@/services/api'

class WebSocketService {
  private socket: Socket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 2000
  private isIntentionalDisconnect = false

  // Event handlers
  private tickHandlers: Array<(tick: TickData) => void> = []
  private ohlcHandlers: Array<(bar: OHLCBar) => void> = []
  private connectionHandlers: Array<(connected: boolean) => void> = []

  constructor() {
    debug('WebSocket', 'WebSocket service initialized')
  }

  connect(): void {
    if (this.socket?.connected) {
      warn('WebSocket', 'Already connected')
      return
    }

    info('WebSocket', 'Attempting to connect to WebSocket server')

    // Use HTTP origin to let Socket.IO negotiate transport; CORS is handled server-side
    this.socket = io('http://localhost:8000', {
      path: '/socket.io',
      transports: ['websocket'],
      reconnection: false, // We'll handle reconnection manually
    })

    this.setupEventListeners()
  }

  private setupEventListeners(): void {
    if (!this.socket) return

    this.socket.on('connect', () => {
      info('WebSocket', 'Connected successfully', { socketId: this.socket?.id })
      this.reconnectAttempts = 0
      this.isIntentionalDisconnect = false
      this.notifyConnectionHandlers(true)

      // Update global store connection flags
      try {
        useStore.getState().setConnected(true)
      } catch (e) {
        debug('WebSocket', 'Failed to update store connected flag', e)
      }

      // Fetch health and set a basic connection status so UI reflects backend state
      api.getHealth()
        .then((h) => {
          const cs: ConnectionStatus = {
            connected: true,
            active_symbols: h?.active_symbols ?? 0,
            symbols: h?.active_symbols ?? 0,
            total_ticks: h?.ticks_stored ?? 0,
            uptime: 0,
          }
          try {
            useStore.getState().setConnectionStatus(cs)
          } catch (e) {
            debug('WebSocket', 'Failed to set connection status from health', e)
          }
        })
        .catch((e) => debug('WebSocket', 'Health fetch failed on connect', e))
    })

    this.socket.on('disconnect', (reason) => {
      warn('WebSocket', 'Disconnected', { reason })
      this.notifyConnectionHandlers(false)

      // Non-intentional disconnect -> surface an alert in UI so user can verify Alerts tab
      try {
        if (!this.isIntentionalDisconnect) {
          const alert = {
            id: `ws-disconnect-${Date.now()}`,
            timestamp: Date.now(),
            symbol: '',
            type: 'CUSTOM' as const,
            message: `WebSocket disconnected (${reason})`,
            severity: 'error' as const,
            triggered: true,
          }
          useStore.getState().addAlert(alert)
        }
      } catch (e) {
        debug('WebSocket', 'Failed to add disconnect alert', e)
      }

      if (!this.isIntentionalDisconnect) {
        this.attemptReconnect()
      }
    })

    this.socket.on('connect_error', (err) => {
      error('WebSocket', 'Connection error', {
        message: err.message,
        attempts: this.reconnectAttempts,
      })
      this.attemptReconnect()
    })

    // Unified data events from backend (channel + data)
    this.socket.on('data', (msg: any) => {
      const rawChannel = msg?.channel
      const channel = typeof rawChannel === 'string' ? rawChannel : String(rawChannel)
      const payload = msg?.data

      if (!channel || payload === undefined) {
        debug('WebSocket', 'Empty data event - ignoring', { rawChannel, payload })
        return
      }

      info('WebSocket', `Data received on channel: ${channel}`, { 
        payloadType: Array.isArray(payload) ? 'array' : typeof payload, 
        length: Array.isArray(payload) ? payload.length : undefined,
        sample: Array.isArray(payload) ? payload[0] : payload
      })

      if (channel === 'market_data') {
        let ticksProcessed = 0
        if (Array.isArray(payload)) {
          payload.forEach((p) => {
            if (p && p.symbol && (p.price !== undefined || p.lastPrice !== undefined)) {
              if (p.price === undefined && p.lastPrice !== undefined) p.price = Number(p.lastPrice)
              this.notifyTickHandlers(p)
              ticksProcessed++
              // Lightweight client-side price jump alert (lenient): 1% move between last stored tick and this tick
              try {
                const store = useStore.getState()
                const symbol = p.symbol
                const prevTicks = store.ticks.get(symbol) || []
                const prev = prevTicks[prevTicks.length - 1]
                if (prev && typeof prev.price === 'number' && typeof p.price === 'number') {
                  const pct = Math.abs((Number(p.price) - Number(prev.price)) / Number(prev.price))
                  if (pct >= 0.01) {
                    // Suppress duplicate alerts for same symbol within 60s
                    const recent = store.alerts.find(a => a.symbol === symbol && a.type === 'PRICE' && (Date.now() - a.timestamp) < 60000)
                    if (!recent) {
                      const alert = {
                        id: `price-${symbol}-${Date.now()}`,
                        timestamp: Date.now(),
                        symbol,
                        type: 'PRICE' as const,
                        message: `Price moved ${(pct * 100).toFixed(2)}% since last tick`,
                        severity: 'warning' as const,
                        triggered: true,
                        value: Number(p.price),
                      }
                      store.addAlert(alert)
                    }
                  }
                }
              } catch (e) {
                debug('WebSocket', 'Price-alert generation failed', e)
              }
            }
          })
          info('WebSocket', `Processed ${ticksProcessed} ticks from market_data array`)
        } else if (payload && payload.symbol && (payload.price !== undefined || payload.lastPrice !== undefined)) {
          if (payload.price === undefined && payload.lastPrice !== undefined) payload.price = Number(payload.lastPrice)
          this.notifyTickHandlers(payload as TickData)
          info('WebSocket', `Processed 1 tick: ${payload.symbol} @ ${payload.price}`)
        } else {
          warn('WebSocket', 'market_data payload has no valid ticks', payload)
        }
      } else if (channel === 'ohlc') {
        let barsProcessed = 0
        if (Array.isArray(payload)) {
          payload.forEach((b) => {
            if (b && b.symbol && (b.close !== undefined || b.c !== undefined)) {
              if (b.close === undefined && b.c !== undefined) b.close = Number(b.c)
              this.notifyOHLCHandlers(b)
              barsProcessed++
              // Lightweight volume spike alert: if volume >> recent average (3x)
              try {
                const store = useStore.getState()
                const symbol = b.symbol
                const bars = store.ohlcBars.get(symbol) || []
                const lookback = 10
                const recent = bars.slice(-lookback)
                const avg = recent.length ? recent.reduce((s, x) => s + (x.volume || 0), 0) / recent.length : 0
                const vol = Number(b.volume || b.v || 0)
                if (vol > 0 && (avg === 0 ? vol > 100 : vol >= Math.max(100, avg * 3))) {
                  const recentAlert = store.alerts.find(a => a.symbol === symbol && a.type === 'VOLUME' && (Date.now() - a.timestamp) < 60000)
                  if (!recentAlert) {
                    const alert = {
                      id: `volume-${symbol}-${Date.now()}`,
                      timestamp: Date.now(),
                      symbol,
                      type: 'VOLUME' as const,
                      message: `Volume spike: ${vol} (avg ${avg.toFixed(1)})`,
                      severity: 'warning' as const,
                      triggered: true,
                      value: vol,
                    }
                    store.addAlert(alert)
                  }
                }
              } catch (e) {
                debug('WebSocket', 'Volume-alert generation failed', e)
              }
            }
          })
          info('WebSocket', `Processed ${barsProcessed} OHLC bars`)
        } else if (payload && payload.symbol && (payload.close !== undefined || payload.c !== undefined)) {
          if (payload.close === undefined && payload.c !== undefined) payload.close = Number(payload.c)
          this.notifyOHLCHandlers(payload as OHLCBar)
          info('WebSocket', `Processed 1 OHLC bar: ${payload.symbol}`)
        }
      } else if (channel === 'alerts') {
        // Backend-originated alerts -> add to frontend store so Alerts tab shows them
        try {
          const store = useStore.getState()
          if (Array.isArray(payload)) {
            payload.forEach((a: any) => {
              // Basic shape normalization
              const alert = {
                id: a.id ?? `srv-${a.type ?? 'alert'}-${Date.now()}`,
                timestamp: a.timestamp ?? Date.now(),
                symbol: a.symbol ?? '',
                type: a.type ?? 'CUSTOM',
                message: a.message ?? JSON.stringify(a),
                severity: a.severity ?? 'info',
                triggered: true,
                value: a.value,
              }
              store.addAlert(alert)
            })
          } else if (payload && typeof payload === 'object') {
            const a = payload
            const alert = {
              id: a.id ?? `srv-${a.type ?? 'alert'}-${Date.now()}`,
              timestamp: a.timestamp ?? Date.now(),
              symbol: a.symbol ?? '',
              type: a.type ?? 'CUSTOM',
              message: a.message ?? JSON.stringify(a),
              severity: a.severity ?? 'info',
              triggered: true,
              value: a.value,
            }
            store.addAlert(alert)
          }
        } catch (e) {
          debug('WebSocket', 'Failed to apply backend alerts to store', e)
        }
      } else if (channel === 'analytics' || channel === 'status') {
        try {
          // If analytics payload contains connection info, apply it
          if (payload && payload.connected !== undefined) {
            const cs: ConnectionStatus = {
              connected: !!payload.connected,
              active_symbols: payload.active_symbols ?? 0,
              symbols: payload.symbols ?? payload.active_symbols ?? 0,
              total_ticks: payload.tick_count ?? payload.total_ticks ?? 0,
              uptime: payload.uptime ?? 0,
            }
            info('WebSocket', `Status update applied: uptime=${cs.uptime}s, ticks=${cs.total_ticks}`)
            useStore.getState().setConnectionStatus(cs)
          }

          // Analytics-based lenient trading alerts (client-side only)
          if (payload && typeof payload === 'object') {
            const store = useStore.getState()

            // Z-score / spread alerts
            try {
              const zscores = payload.z_scores || payload.zscore || payload.z || []
              const spreadMean = payload.spread_mean ?? payload.spreadMean ?? null
              const spreadStd = payload.spread_std ?? payload.spreadStd ?? null
              if (Array.isArray(zscores) && zscores.length) {
                const lastZ = Number(zscores[zscores.length - 1])
                if (Number.isFinite(lastZ) && Math.abs(lastZ) >= 1.0) {
                  const recent = store.alerts.find(a => a.type === 'ZSCORE' && (Date.now() - a.timestamp) < 60000)
                  if (!recent) {
                    store.addAlert({
                      id: `zscore-${Date.now()}`,
                      timestamp: Date.now(),
                      symbol: payload.symbol ?? '',
                      type: 'ZSCORE',
                      message: `Z-score ${lastZ.toFixed(2)} (lenient threshold 1.0)` ,
                      severity: 'warning',
                      triggered: true,
                      value: lastZ,
                    })
                  }
                }
              }

              // Spread divergence using mean/std if available
              if (spreadMean !== null && spreadStd !== null && Array.isArray(payload.spread || payload.spread_values)) {
                const spreadArr = payload.spread || payload.spread_values || []
                const lastSpread = Number(spreadArr[spreadArr.length - 1])
                if (Number.isFinite(lastSpread)) {
                  const threshold = Math.abs(spreadMean) + (spreadStd || 0)
                  if (Math.abs(lastSpread) >= threshold) {
                    const recent = store.alerts.find(a => a.type === 'ZSCORE' && (Date.now() - a.timestamp) < 60000)
                    if (!recent) {
                      store.addAlert({
                        id: `spread-${Date.now()}`,
                        timestamp: Date.now(),
                        symbol: payload.symbol ?? '',
                        type: 'CUSTOM',
                        message: `Spread divergence: ${lastSpread.toFixed(4)} (mean ${Number(spreadMean).toFixed(4)})`,
                        severity: 'warning',
                        triggered: true,
                        value: lastSpread,
                      })
                    }
                  }
                }
              }
            } catch (e) {
              debug('WebSocket', 'Analytics zscore/spread alert generation failed', e)
            }

            // RSI alerts
            try {
              const rsi = payload.rsi || (payload.indicator_series && payload.indicator_series.rsi) || []
              if (Array.isArray(rsi) && rsi.length) {
                const last = Number(rsi[rsi.length - 1])
                if (Number.isFinite(last) && (last <= 25 || last >= 75)) {
                  const recent = store.alerts.find(a => a.type === 'CUSTOM' && a.message.includes('RSI') && (Date.now() - a.timestamp) < 60000)
                  if (!recent) {
                    store.addAlert({
                      id: `rsi-${Date.now()}`,
                      timestamp: Date.now(),
                      symbol: payload.symbol ?? '',
                      type: 'CUSTOM',
                      message: `RSI ${last.toFixed(0)} (lenient 25/75)`,
                      severity: 'info',
                      triggered: true,
                      value: last,
                    })
                  }
                }
              }
            } catch (e) {
              debug('WebSocket', 'Analytics RSI alert generation failed', e)
            }

            // MACD crossover (lenient): detect sign change in MACD histogram
            try {
              const macdHist = (payload.macd_histogram) || (payload.indicator_series && payload.indicator_series.macd_histogram) || []
              if (Array.isArray(macdHist) && macdHist.length >= 2) {
                const a = Number(macdHist[macdHist.length - 2])
                const b = Number(macdHist[macdHist.length - 1])
                if (Number.isFinite(a) && Number.isFinite(b) && (a <= 0 && b > 0 || a >= 0 && b < 0)) {
                  const recent = store.alerts.find(a => a.type === 'CUSTOM' && a.message.includes('MACD') && (Date.now() - a.timestamp) < 60000)
                  if (!recent) {
                    store.addAlert({
                      id: `macd-${Date.now()}`,
                      timestamp: Date.now(),
                      symbol: payload.symbol ?? '',
                      type: 'CUSTOM',
                      message: `MACD histogram crossover detected`,
                      severity: 'info',
                      triggered: true,
                    })
                  }
                }
              }
            } catch (e) {
              debug('WebSocket', 'Analytics MACD alert generation failed', e)
            }
          }
        } catch (e) {
          error('WebSocket', 'Failed to apply status payload', e)
        }
      } else {
        debug('WebSocket', `Unhandled channel: ${channel}`)
      }
    })

    this.socket.on('status', (data: any) => {
      debug('WebSocket', 'Status update received', data)
      try {
        if (data && data.connected !== undefined) {
          useStore.getState().setConnectionStatus(data as ConnectionStatus)
        }
      } catch (e) {
        debug('WebSocket', 'Failed to set status from status event', e)
      }
    })

    info('WebSocket', 'Event listeners set up successfully')
  }

  private attemptReconnect(): void {
    if (this.isIntentionalDisconnect) return

    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      error('WebSocket', 'Max reconnect attempts reached', {
        attempts: this.reconnectAttempts,
      })
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * this.reconnectAttempts

    info('WebSocket', `Attempting reconnect ${this.reconnectAttempts}/${this.maxReconnectAttempts}`, {
      delayMs: delay,
    })

    setTimeout(() => {
      this.connect()
    }, delay)
  }

  disconnect(): void {
    info('WebSocket', 'Disconnecting intentionally')
    this.isIntentionalDisconnect = true
    this.socket?.disconnect()
    this.socket = null
  }

  // Subscribe to ticks
  onTick(handler: (tick: TickData) => void): () => void {
    debug('WebSocket', 'Tick handler registered')
    this.tickHandlers.push(handler)
    return () => {
      debug('WebSocket', 'Tick handler unregistered')
      this.tickHandlers = this.tickHandlers.filter((h) => h !== handler)
    }
  }

  // Subscribe to OHLC bars
  onOHLC(handler: (bar: OHLCBar) => void): () => void {
    debug('WebSocket', 'OHLC handler registered')
    this.ohlcHandlers.push(handler)
    return () => {
      debug('WebSocket', 'OHLC handler unregistered')
      this.ohlcHandlers = this.ohlcHandlers.filter((h) => h !== handler)
    }
  }

  // Subscribe to connection status
  onConnection(handler: (connected: boolean) => void): () => void {
    debug('WebSocket', 'Connection handler registered')
    this.connectionHandlers.push(handler)
    return () => {
      debug('WebSocket', 'Connection handler unregistered')
      this.connectionHandlers = this.connectionHandlers.filter((h) => h !== handler)
    }
  }

  // Emit custom events
  emit(event: string, data: any): void {
    if (!this.socket?.connected) {
      warn('WebSocket', 'Cannot emit - not connected', { event })
      return
    }

    debug('WebSocket', `Emitting event: ${event}`, data)
    this.socket.emit(event, data)
  }

  // Subscribe to specific symbols
  subscribeToSymbols(symbols: string[]): void {
    info('WebSocket', 'Subscribing to symbols', { symbols })
    this.emit('subscribe', { symbols })
  }

  // Unsubscribe from symbols
  unsubscribeFromSymbols(symbols: string[]): void {
    info('WebSocket', 'Unsubscribing from symbols', { symbols })
    this.emit('unsubscribe', { symbols })
  }

  // Notify handlers
  private notifyTickHandlers(tick: TickData): void {
    this.tickHandlers.forEach((handler) => {
      try {
        handler(tick)
      } catch (err) {
        error('WebSocket', 'Error in tick handler', err)
      }
    })
  }

  private notifyOHLCHandlers(bar: OHLCBar): void {
    this.ohlcHandlers.forEach((handler) => {
      try {
        handler(bar)
      } catch (err) {
        error('WebSocket', 'Error in OHLC handler', err)
      }
    })
  }

  private notifyConnectionHandlers(connected: boolean): void {
    this.connectionHandlers.forEach((handler) => {
      try {
        handler(connected)
      } catch (err) {
        error('WebSocket', 'Error in connection handler', err)
      }
    })
  }

  // Get connection status
  isConnected(): boolean {
    return this.socket?.connected || false
  }

  // Get socket ID
  getSocketId(): string | undefined {
    return this.socket?.id
  }
}

// Singleton instance
const wsService = new WebSocketService()

export default wsService
