# System Fixes & Diagnostics Update

## Issues Fixed

### 1. WebSocket Connection Error
**Error**: `'ClientConnection' object has no attribute 'closed'`

**Root Cause**: Different versions of the `websockets` library use different attributes:
- Older versions: `websocket.closed` (boolean)
- Newer versions: `websocket.state` (State enum)

**Fix Applied**:
- Updated `get_stats()` method to safely check both attributes
- Added exception handling for connection state checks
- Modified the `run()` loop to handle both connection state mechanisms

**Location**: `src/ingestion/websocket_client.py`

### 2. Missing Data in Tabs
**Problem**: No data loading in Spread Analysis, Statistics, Alerts, and Debug tabs

**Root Cause**: Multiple issues:
- Insufficient data in Redis/Database for analytics
- No visibility into data flow from WebSocket → Redis → Analytics
- Missing diagnostics to identify bottlenecks

**Fix Applied**:
- Added comprehensive `/debug/diagnostics` endpoint
- Shows sample data from Redis with actual tick counts
- Displays database table row counts
- Real-time WebSocket statistics including per-symbol tick counts

**Location**: `app.py`, `streamlit_app.py`

## New Features Added

### 1. Enhanced Diagnostics Endpoint
**Endpoint**: `GET /debug/diagnostics`

**Returns**:
- WebSocket connection status and tick counts per symbol
- Redis health with memory usage and sample data (2 ticks per symbol)
- Database health with row counts for all tables
- Data processor statistics (ticks processed, errors, buffered)

### 2. System Status Tab
**Location**: New 7th tab in Streamlit dashboard

**Features**:
- **Backend Status**: API health check, response time, available symbols
- **WebSocket Connection**: Mode, connection status, total ticks, per-symbol counts
- **Redis Status**: Connection, memory usage, total keys, sample data per symbol
- **Database Status**: Connection, table row counts for ticks/ohlc/analytics/alerts
- **Data Processor**: Ticks processed, error count, buffer status
- **Quick Tests**: One-click buttons to test /ohlc, /ticks, and /analytics/spread endpoints

### 3. Auto-Pause Enhancement
The auto-refresh now pauses on both Debug and System Status tabs to allow proper inspection.

## How to Use

### 1. Restart Backend
```powershell
.\venv\Scripts\Activate.ps1
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Restart Frontend
```powershell
streamlit run streamlit_app.py
```

### 3. Check System Status Tab
1. Open dashboard at http://localhost:8501
2. Navigate to "🖥️ System Status" tab
3. Check each section:
   - ✅ API Health should show "API is healthy"
   - ✅ WebSocket should show "Connected: Yes"
   - ✅ Tick Counts should show increasing numbers per symbol
   - ✅ Redis sample data should show actual tick data
   - ✅ Database tables should show row counts

### 4. Diagnose Issues

**If WebSocket shows "Connected: No"**:
- Check if Binance URL is correct in `config.py`
- Verify network connectivity
- Check server logs for connection errors

**If Tick Counts are 0**:
- WebSocket is connected but no data flowing
- Check server logs for parsing errors
- Verify symbols are valid (BTCUSDT, ETHUSDT, etc.)

**If Redis shows "No sample data available"**:
- Ticks are being received but not stored in Redis
- Check DataProcessor logs for Redis errors
- Verify Redis is running (should be on localhost:6379)

**If Database tables show 0 rows**:
- Data is in Redis but not being sampled to DB
- Check DataSampler logs
- Verify 1s/1m/5m sampling jobs are running

**If Analytics endpoints return 404**:
- Not enough OHLC data (need minimum 10-50 samples)
- Wait for sampler to accumulate data (1-2 minutes)
- Check System Status tab → Database → Table Counts

## Troubleshooting Commands

### Check if Redis is running
```powershell
redis-cli ping
# Should return: PONG
```

### Check Redis keys
```powershell
redis-cli keys "*"
# Should show: ticks:BTCUSDT, ohlc:BTCUSDT:1s, etc.
```

### Get Redis tick count
```powershell
redis-cli zcard ticks:BTCUSDT
# Returns number of ticks stored
```

### Query database
```powershell
python -c "import sqlite3; conn = sqlite3.connect('data/tick_data.db'); print(conn.execute('SELECT COUNT(*) FROM ohlc_1s').fetchone()[0])"
```

## Expected Behavior

After 1-2 minutes of running:
- WebSocket: 100-1000+ ticks per symbol
- Redis: Sample data shows recent ticks
- Database: ohlc_1s table has 60-120 rows, ohlc_1m has 1-2 rows
- Analytics endpoints: Start returning data once minimum samples available

## Debug Workflow

1. **System Status Tab** → Check all components are green
2. **WebSocket section** → Verify ticks are increasing
3. **Redis section** → Verify sample data exists
4. **Database section** → Verify table row counts are increasing
5. **Quick Tests** → Test individual endpoints
6. **Analytics tabs** → Should now show data

## API Endpoints Summary

| Endpoint | Purpose | Min Data Required |
|----------|---------|-------------------|
| `/health` | API health check | None |
| `/symbols` | List available symbols | None |
| `/ohlc/{symbol}` | Get OHLC data | 1+ OHLC samples |
| `/ticks/{symbol}` | Get recent ticks | 1+ ticks in Redis |
| `/analytics/spread` | Spread analysis | 50+ OHLC samples |
| `/analytics/correlation` | Rolling correlation | 50+ OHLC samples |
| `/analytics/adf` | Stationarity test | 10+ OHLC samples |
| `/debug/system` | Component status | None |
| `/debug/diagnostics` | Detailed diagnostics | None |
