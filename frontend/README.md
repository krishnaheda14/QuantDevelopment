# GEMSCAP Quant - React Frontend

Professional React + TypeScript frontend for the GEMSCAP Quantitative Trading Analytics Platform.

## Tech Stack

- **React 18** - Modern UI library with hooks
- **TypeScript** - Type safety for financial data
- **Vite** - Ultra-fast build tool and dev server
- **Material-UI (MUI)** - Professional component library
- **Recharts** - Financial charting library
- **TanStack Query** - Data fetching and caching
- **Zustand** - Lightweight state management
- **Socket.IO** - Real-time WebSocket communication
- **React Router** - Client-side routing
- **Framer Motion** - Smooth animations

## Features

- 📊 **Real-time Data Streaming** - Live tick and OHLC data via WebSocket
- 📈 **Interactive Charts** - Professional financial charts with Recharts
- 🎨 **Beautiful Dark Theme** - Optimized for trading dashboards
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile
- 🔍 **Comprehensive Debugging** - Extensive logging for all operations
- ⚡ **Optimized Performance** - Fast rendering with React Query caching
- 🎯 **Type Safety** - Full TypeScript coverage

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── Layout.tsx       # Main layout with sidebar
│   │   ├── ConnectionStatus.tsx
│   │   └── charts/          # Chart components
│   ├── pages/               # Page components (13 pages)
│   │   ├── Dashboard.tsx
│   │   ├── SpreadAnalysis.tsx
│   │   ├── StrategySignals.tsx
│   │   └── ...
│   ├── services/            # API and WebSocket services
│   │   ├── api.ts           # REST API client
│   │   └── websocket.ts     # WebSocket service
│   ├── store/               # Zustand state management
│   │   └── index.ts
│   ├── types/               # TypeScript type definitions
│   │   └── index.ts
│   ├── App.tsx              # Main app component
│   ├── main.tsx             # Entry point
│   └── theme.ts             # MUI theme configuration
├── public/                  # Static assets
├── index.html               # HTML template
├── package.json             # Dependencies
├── tsconfig.json            # TypeScript config
├── vite.config.ts           # Vite config
└── README.md                # This file
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- Python backend running on `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

Opens at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

Outputs to `dist/` folder.

### Preview Production Build

```bash
npm run preview
```

## Pages & Features

### 1. Dashboard (/)
- Overview of system status
- Live connection indicator
- Quick access to all features

### 2. Spread Analysis (/spread)
- OLS regression hedge ratio
- Real-time spread calculation
- Z-score visualization
- Trading signals (LONG/SHORT/NEUTRAL)

### 3. Strategy Signals (/signals)
- RSI indicator with thresholds
- MACD with histogram
- Bollinger Bands
- Visual buy/sell signals

### 4. Statistical Tests (/statistical)
- ADF stationarity tests
- Cointegration analysis
- P-value interpretation
- Critical values display

### 5. Backtesting (/backtest)
- Strategy performance metrics
- Equity curve visualization
- Trade log analysis
- Sharpe ratio, max drawdown, win rate

### 6. Alerts (/alerts)
- Real-time alert notifications
- Custom threshold configuration
- Alert history
- Severity levels (info/warning/error)

### 7. System (/system)
- Connection diagnostics
- Database statistics
- WebSocket status
- Debug logs viewer

### 8. Quick Compare (/compare)
- Side-by-side price charts
- Volume comparison
- Historical data upload

### 9. Kalman & Robust (/kalman)
- Dynamic hedge ratio estimation
- Kalman filter visualization
- Robust regression (Huber, Theil-Sen)
- Outlier detection

### 10. Liquidity (/liquidity)
- Volume profile heatmap
- Point of Control (POC)
- Value area identification
- Support/resistance levels

### 11. Microstructure (/microstructure)
- Order flow imbalance
- VWAP calculation and deviation
- Effective spread analysis
- Trade intensity metrics

### 12. Correlation (/correlation)
- Multi-asset correlation matrix
- Correlation heatmap
- Best/worst correlated pairs
- Pearson coefficient calculations

### 13. Time Series Table (/timeseries)
- Comprehensive data table
- All metrics per timestamp
- CSV/JSON export
- Column selection

## API Integration

### REST API
The frontend connects to the Python backend API at `http://localhost:8000`:

- `GET /health` - System health check
- `GET /symbols` - Available trading symbols
- `GET /ohlc/{symbol}` - OHLC data
- `GET /analytics/spread` - Spread analysis
- `GET /analytics/adf` - ADF test
- And more...

### WebSocket
Real-time data streaming via Socket.IO:

```typescript
// Automatic connection on app mount
wsService.connect()

// Subscribe to ticks
wsService.onTick((tick) => {
  console.log('Tick:', tick)
})

// Subscribe to OHLC bars
wsService.onOHLC((bar) => {
  console.log('Bar:', bar)
})
```

## State Management

### Zustand Store

Global state managed with Zustand for simplicity and performance:

```typescript
import { useStore } from '@/store'

function Component() {
  const { selectedSymbol1, setSelectedSymbol1 } = useStore()
  
  return (
    <select onChange={(e) => setSelectedSymbol1(e.target.value)}>
      {/* options */}
    </select>
  )
}
```

### React Query

Data fetching with automatic caching and background refetching:

```typescript
import { useQuery } from '@tanstack/react-query'
import api from '@/services/api'

function Component() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['spread', symbol1, symbol2],
    queryFn: () => api.getSpreadAnalysis(symbol1, symbol2),
    refetchInterval: 5000, // Refresh every 5s
  })
}
```

## Debugging

Extensive debugging built-in:

```typescript
import { debug, info, warn, error } from '@/types'

// Log messages with component context
debug('Component', 'Debug message', { data })
info('Component', 'Info message')
warn('Component', 'Warning message')
error('Component', 'Error message', err)

// View all logs
import { DebugLogger } from '@/types'
const logs = DebugLogger.getLogs()
```

Check browser console for detailed logs of:
- API requests/responses
- WebSocket events
- State changes
- Component renders
- Data transformations

## Styling

### Custom Theme

Dark trading theme optimized for financial data:

```typescript
// Primary: Green (#00ff88) - Bullish signals
// Secondary: Red (#ff4444) - Bearish signals
// Background: Dark blue-gray (#0a0e1a)
```

### Responsive Breakpoints

```typescript
// xs: 0px
// sm: 600px
// md: 900px  (Mobile drawer toggle)
// lg: 1200px
// xl: 1536px
```

## Performance Optimization

- **Code Splitting** - Automatic route-based splitting
- **Lazy Loading** - Components loaded on demand
- **Memoization** - React.memo for expensive components
- **Virtual Scrolling** - For large data tables
- **Debouncing** - Input handlers optimized
- **Query Caching** - TanStack Query reduces API calls

## Best Practices

1. **Type Safety** - All data strictly typed
2. **Error Handling** - Try-catch blocks everywhere
3. **Loading States** - Skeleton screens for better UX
4. **Accessibility** - ARIA labels and keyboard navigation
5. **Debug Logging** - Comprehensive logging for troubleshooting
6. **Clean Code** - ESLint + Prettier formatting

## Troubleshooting

### WebSocket not connecting
- Ensure Python backend is running on `http://localhost:8000`
- Check browser console for connection errors
- Verify firewall/proxy settings

### API requests failing
- Verify backend server is accessible
- Check CORS configuration
- Inspect Network tab in browser DevTools

### Charts not rendering
- Check data format matches TypeScript types
- Verify data is not empty/undefined
- Look for console errors

### State not updating
- Check Zustand store actions are being called
- Verify React Query cache isn't stale
- Use React DevTools to inspect state

## Development Tips

### Hot Module Replacement
Vite provides instant HMR - changes reflect immediately without full reload.

### TypeScript Strict Mode
All code uses strict TypeScript for maximum type safety.

### Component Development
Use React DevTools extension to inspect component hierarchy and props.

### API Testing
Use browser Network tab or tools like Postman to test API endpoints.

## Deployment

### Production Build

```bash
npm run build
npm run preview  # Test production build locally
```

### Serve Static Files

Serve the `dist/` folder with any static file server:

```bash
# Using Python
python -m http.server 3000 --directory dist

# Using Node.js http-server
npx http-server dist -p 3000
```

### Environment Variables

Create `.env` file for environment-specific config:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

Access in code:
```typescript
const apiUrl = import.meta.env.VITE_API_URL
```

## License

MIT License - Part of GEMSCAP Quant Project

## Credits

Built with modern web technologies for quantitative trading analytics.
