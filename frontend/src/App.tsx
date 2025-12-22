import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Box } from '@mui/material'
import { info, debug, error } from '@/types'
import Layout from '@/components/Layout'
import { Dashboard } from '@/pages/Dashboard'
import { SpreadAnalysis } from '@/pages/SpreadAnalysis'
import { StrategySignals } from '@/pages/StrategySignals'
import { StatisticalTests } from '@/pages/StatisticalTests'
import { Backtesting } from '@/pages/Backtesting'
import { Alerts } from '@/pages/Alerts'
import { APIDebug } from '@/pages/APIDebug'
import { System, QuickCompare, KalmanRobust, Liquidity, Microstructure, Correlation, TimeSeriesTable } from '@/pages'
import wsService from '@/services/websocket'
import { useStore } from '@/store'

function App() {
  const { setConnected, addBar } = useStore()

  useEffect(() => {
    info('App', 'Application mounting - initializing WebSocket')

    // Connect to WebSocket
    wsService.connect()

    // Subscribe to connection status
    const unsubscribeConnection = wsService.onConnection((connected) => {
      info('App', 'WebSocket connection status changed', { connected })
      setConnected(connected)
    })

    // Subscribe to tick data and buffer before committing to store
    let tickBuffer: any[] = []
    let flushTimer: any = null

    const flush = () => {
      if (tickBuffer.length === 0) return
      try {
        const toFlush = [...tickBuffer]
        tickBuffer = []
        info('App', `Flushing ${toFlush.length} ticks to store`)
        useStore.getState().addTicks(toFlush)
      } catch (e) {
        error('App', 'Error flushing tick buffer', e)
      }
    }

    const unsubscribeTicks = wsService.onTick((tick) => {
      // Buffer incoming tick
      debug('App', 'Tick received', { symbol: tick.symbol, price: tick.price, bufferSize: tickBuffer.length })
      tickBuffer.push(tick)
      
      // Set flush timer if not already set
      if (!flushTimer) {
        flushTimer = setTimeout(() => {
          flush()
          clearTimeout(flushTimer)
          flushTimer = null
        }, 250)
      }
    })

    // Subscribe to OHLC bars
    const unsubscribeBars = wsService.onOHLC((bar) => {
      info('App', 'OHLC bar received in App', {
        symbol: bar.symbol,
        close: bar.close,
      })
      addBar(bar)
    })

    info('App', 'WebSocket subscriptions established')

    // Cleanup on unmount
    return () => {
      info('App', 'Application unmounting - cleaning up WebSocket')
      unsubscribeConnection()
      unsubscribeTicks()
      // flush any remaining ticks
      try { flush() } catch {}
      unsubscribeBars()
      wsService.disconnect()
    }
  }, [setConnected, addBar])

  debug('App', 'Rendering application routes')

  return (
    <Box sx={{ minHeight: '100vh', backgroundColor: 'background.default' }}>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="spread" element={<SpreadAnalysis />} />
          <Route path="signals" element={<StrategySignals />} />
          <Route path="statistical" element={<StatisticalTests />} />
          <Route path="backtest" element={<Backtesting />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="apidebug" element={<APIDebug />} />
          <Route path="compare" element={<QuickCompare />} />
          <Route path="kalman" element={<KalmanRobust />} />
          <Route path="liquidity" element={<Liquidity />} />
          <Route path="microstructure" element={<Microstructure />} />
          <Route path="correlation" element={<Correlation />} />
          <Route path="timeseries" element={<TimeSeriesTable />} />
        </Route>
      </Routes>
    </Box>
  )
}

export default App
