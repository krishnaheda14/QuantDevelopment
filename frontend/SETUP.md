# GEMSCAP Quant - Quick Start Guide

## Prerequisites

1. **Backend Running**: Ensure Python backend is running on `http://localhost:8000`
   ```bash
   cd F:\Gemscap_Quant_Project
   python run.py
   ```

2. **Node.js**: Version 18+ required
   - Download from [nodejs.org](https://nodejs.org/)
   - Verify installation: `node --version`

## Installation Steps

### Step 1: Navigate to Frontend Directory
```bash
cd F:\Gemscap_Quant_Project\frontend
```

### Step 2: Install Dependencies
```bash
npm install
```

This will install:
- React 18 + TypeScript
- Material-UI components
- Recharts for visualization
- Socket.IO for WebSocket
- TanStack Query for data fetching
- Zustand for state management
- And more...

### Step 3: Start Development Server
```bash
npm run dev
```

The application will open at `http://localhost:3000`

## Development Commands

```bash
# Start dev server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type check
npm run type-check

# Lint code
npm run lint
```

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable components
│   │   ├── Layout.tsx       # Sidebar navigation
│   │   └── ConnectionStatus.tsx
│   ├── pages/               # Page components
│   │   ├── Dashboard.tsx
│   │   ├── SpreadAnalysis.tsx
│   │   ├── StrategySignals.tsx
│   │   ├── StatisticalTests.tsx
│   │   ├── Backtesting.tsx
│   │   ├── Alerts.tsx
│   │   └── index.tsx        # Stub pages
│   ├── services/            # API & WebSocket
│   │   ├── api.ts
│   │   └── websocket.ts
│   ├── store/               # State management
│   │   └── index.ts
│   ├── types/               # TypeScript types
│   │   └── index.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── theme.ts
├── public/
├── package.json
├── vite.config.ts
└── README.md
```

## Features Implemented

### ✅ Complete Pages:
1. **Dashboard** - Overview with connection status, metrics, alerts
2. **Spread Analysis** - OLS regression, spread charts, z-score, signals
3. **Strategy Signals** - RSI, MACD, Bollinger Bands with charts
4. **Statistical Tests** - ADF test, cointegration analysis
5. **Backtesting** - Performance metrics, equity curve, trade statistics
6. **Alerts** - Real-time notifications with severity levels

### ⏳ Stub Pages (To Be Expanded):
7. **System** - System diagnostics and debug logs
8. **Quick Compare** - Side-by-side comparison
9. **Kalman & Robust** - Dynamic hedge ratio estimation
10. **Liquidity** - Volume profile analysis
11. **Microstructure** - Order flow metrics
12. **Correlation** - Multi-asset correlation matrix
13. **Time Series Table** - Data export capabilities

## API Integration

### Backend Endpoints Used:
- `GET /health` - System health
- `GET /symbols` - Available symbols
- `GET /ohlc/{symbol}` - OHLC data
- `GET /analytics/spread` - Spread analysis
- `GET /analytics/adf` - ADF test
- `GET /analytics/cointegration` - Cointegration test
- `GET /analytics/indicators` - Technical indicators
- `POST /backtest` - Run backtest

### WebSocket Events:
- `tick` - Real-time tick data
- `ohlc` - OHLC bar updates
- `connection` - Connection status

## Debugging

All components have extensive debug logging. Check browser console for:

```
[DEBUG][Component] Message
[INFO][Component] Message
[WARN][Component] Message
[ERROR][Component] Message
```

## Troubleshooting

### Issue: WebSocket not connecting
**Solution**: Ensure backend is running on port 8000
```bash
cd F:\Gemscap_Quant_Project
python run.py
```

### Issue: npm install fails
**Solution**: Clear cache and retry
```bash
npm cache clean --force
npm install
```

### Issue: Port 3000 already in use
**Solution**: Kill process or use different port
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Or specify different port
npm run dev -- --port 3001
```

### Issue: TypeScript errors
**Solution**: Check tsconfig.json and restart VS Code

### Issue: Blank page / white screen
**Solution**: Check browser console for errors, verify backend is running

## Next Steps

1. ✅ **Completed**: Core infrastructure, main pages, real-time data
2. 🚀 **TODO**: Expand stub pages with full functionality
3. 🚀 **TODO**: Add error boundaries for better error handling
4. 🚀 **TODO**: Implement chart zoom and interactivity
5. 🚀 **TODO**: Add data export functionality
6. 🚀 **TODO**: Optimize performance for large datasets

## Architecture Highlights

### State Management (Zustand)
- Lightweight and performant
- No boilerplate
- TypeScript support
- Middleware for logging

### Data Fetching (TanStack Query)
- Automatic caching
- Background refetching
- Loading/error states
- Request deduplication

### UI Library (Material-UI)
- Professional components
- Dark theme optimized for trading
- Responsive design
- Accessibility built-in

### Charts (Recharts)
- Declarative API
- Interactive tooltips
- Responsive containers
- Multiple chart types

## Browser Support

- Chrome (recommended)
- Firefox
- Edge
- Safari

## Performance Tips

1. **Reduce Refetch Intervals**: Adjust `refetchInterval` in queries for less frequent updates
2. **Limit Data Points**: Use pagination or windowing for large datasets
3. **Disable Dev Tools**: Production builds are faster
4. **Use Code Splitting**: Lazy load heavy components

## Contributing

When adding new features:
1. Add TypeScript types in `types/index.ts`
2. Create service methods in `services/api.ts`
3. Update Zustand store in `store/index.ts`
4. Build page component with Material-UI
5. Add route in `App.tsx`
6. Update navigation in `Layout.tsx`

## Environment Variables

Create `.env` file for custom configuration:
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_DEBUG=true
```

## License

MIT - Part of GEMSCAP Quant Project
