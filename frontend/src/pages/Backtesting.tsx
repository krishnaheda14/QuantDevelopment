import React, { useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Alert,
  CircularProgress,
  Paper,
  Stack,
  Divider,
} from '@mui/material';
import { FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import { PlayArrow, TrendingUp, TrendingDown, AttachMoney } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useStore } from '@/store';
import api from '@/services/api';
import { debug, info } from '@/types';

const COMPONENT_NAME = 'Backtesting';

export const Backtesting: React.FC = () => {
  const { selectedSymbol1, selectedSymbol2, settings, setAggregationInterval } = useStore();
  const [entryThreshold, setEntryThreshold] = useState(2.0);
  const [exitThreshold, setExitThreshold] = useState(0.5);
  const [stopLoss, setStopLoss] = useState(3.0);
  const [lookback, setLookback] = useState(500);
  const [runBacktest, setRunBacktest] = useState(false);
  const [lastRequestPayload, setLastRequestPayload] = useState<any>(null);
  const [lastRawResponse, setLastRawResponse] = useState<any>(null);
  const [strategy, setStrategy] = useState<string>('zscore');
  const [rsiBuy, setRsiBuy] = useState<number>(30);
  const [rsiSell, setRsiSell] = useState<number>(50);
  const [tradeSize, setTradeSize] = useState<number>(1);
  const [commission, setCommission] = useState<number>(0);

  debug(COMPONENT_NAME, 'Rendering backtesting', {
    symbol1: selectedSymbol1,
    symbol2: selectedSymbol2,
    entryThreshold,
    exitThreshold,
    stopLoss,
  });

  // Fetch backtest results
  const { data: backtestData, isLoading, error, refetch } = useQuery({
    queryKey: ['backtest', selectedSymbol1, selectedSymbol2, entryThreshold, exitThreshold, stopLoss, lookback, settings.aggregationInterval],
    queryFn: () => api.runBacktest(selectedSymbol1!, selectedSymbol2!, entryThreshold, exitThreshold, stopLoss, lookback),
    enabled: runBacktest && !!selectedSymbol1 && !!selectedSymbol2,
  });

  React.useEffect(() => {
    if (backtestData) {
      info(COMPONENT_NAME, 'Backtest results received', backtestData);
      setRunBacktest(false);
    }
  }, [backtestData]);

  // keep raw response for debug panel
  React.useEffect(() => {
    if (backtestData) setLastRawResponse(backtestData);
  }, [backtestData]);

  const handleRunBacktest = () => {
    info(COMPONENT_NAME, 'Running backtest', { entryThreshold, exitThreshold, stopLoss, strategy });
    setRunBacktest(true);
    const options: any = {
      strategy,
      trade_size: tradeSize,
      commission,
      slippage: 0.0,
      initial_capital: 100000.0,
      params: {},
    };
    // include timeframe so backend calculates using requested OHLC interval
    const { settings } = useStore.getState()
    options.interval = settings.aggregationInterval || '1m'
    if (strategy === 'rsi') {
      options.params.rsi_buy = rsiBuy;
      options.params.rsi_sell = rsiSell;
    }

    // store last request payload for debug panel
    const payload = { symbol1: selectedSymbol1, symbol2: selectedSymbol2, entry_z: entryThreshold, exit_z: exitThreshold, stoploss_z: stopLoss, lookback, ...options };
    setLastRequestPayload(payload);
    setLastRawResponse(null);
    // call api with lookback and options merged as arg7
    api.runBacktest(selectedSymbol1!, selectedSymbol2!, entryThreshold, exitThreshold, stopLoss, lookback, options).then(() => setRunBacktest(false)).catch(() => setRunBacktest(false));
    refetch();
  };

  // Prepare equity curve data
  const prepareEquityCurveData = () => {
    if (!backtestData) return [];

    // Use server-provided equity_curve when available
    if (Array.isArray(backtestData.equity_curve) && backtestData.equity_curve.length > 0) {
      return backtestData.equity_curve.map((equity: any, index: number) => ({
        index,
        equity: typeof equity === 'number' && isFinite(equity) ? equity : 0,
      }));
    }

    // Fallback: build equity curve from trades and z/spread length
    const zlen = Array.isArray(backtestData?.z_scores) ? backtestData.z_scores.length : (Array.isArray(backtestData?.spread) ? backtestData.spread.length : 0);
    if (zlen === 0) return [];

    const eq: number[] = new Array(zlen).fill(0);
    let cum = 0;
    // apply PnL at exit indices
    for (const t of (backtestData.trades || [])) {
      const exit = Number(t.exit_index ?? t.exit_index);
      const pnl = Number(t.pnl ?? 0);
      if (!Number.isFinite(exit) || exit < 0 || exit >= zlen) continue;
      eq[exit] = (eq[exit] || 0) + pnl;
    }
    for (let i = 0; i < zlen; i++) {
      cum += (eq[i] || 0);
      eq[i] = cum;
    }

    return eq.map((e, i) => ({ index: i, equity: e }));
  };

  const equityCurveData = prepareEquityCurveData();

  // Decide whether to show absolute equity or percent change
  const percentSeries: number[] | null = Array.isArray(backtestData?.equity_pct) ? backtestData.equity_pct : null;
  const pctMin = percentSeries && percentSeries.length ? Math.min(...percentSeries) : 0;
  const pctMax = percentSeries && percentSeries.length ? Math.max(...percentSeries) : 0;
  const showPercent = !!percentSeries && (pctMax - pctMin) >= 0.1; // show percent view when >0.1% movement

  const chartData = showPercent
    ? (percentSeries || []).map((p: number, i: number) => ({ index: i, equity_pct: p }))
    : equityCurveData;

  // API debug states are declared earlier to be available to handlers

  // Normalize backtest payload: some backend responses nest values under `summary`
  const summary = backtestData ? (backtestData.summary ?? backtestData) : null;
  const trades = backtestData?.trades ?? [];
  const totalTrades = summary?.num_trades ?? backtestData?.num_trades ?? trades.length ?? 0;
  const winningTrades = typeof summary?.winning_trades === 'number' ? summary.winning_trades : trades.filter((t: any) => (t.pnl ?? 0) > 0).length;
  const losingTrades = typeof summary?.losing_trades === 'number' ? summary.losing_trades : trades.filter((t: any) => (t.pnl ?? 0) <= 0).length;
  const displayTotalReturn = typeof summary?.total_return === 'number' ? summary.total_return : (typeof summary?.total_pnl === 'number' ? summary.total_pnl : null);
  const displayAvgTradeReturn = typeof summary?.avg_trade_return === 'number' ? summary.avg_trade_return : (typeof summary?.avg_pnl === 'number' ? summary.avg_pnl : null);
  const displaySharpe = typeof summary?.sharpe_ratio === 'number' ? summary.sharpe_ratio : (typeof backtestData?.sharpe_ratio === 'number' ? backtestData.sharpe_ratio : null);
  const displayMaxDD = typeof summary?.max_drawdown === 'number' ? summary.max_drawdown : (typeof backtestData?.max_drawdown === 'number' ? backtestData.max_drawdown : null);
  const displayWinRate = typeof summary?.win_rate === 'number' ? summary.win_rate : (typeof backtestData?.win_rate === 'number' ? backtestData.win_rate : null);

  // Live / running metrics (backend may optionally stream these during a long backtest)
  const live = backtestData?.live ?? backtestData?.running ?? null;
  const runningEquity = equityCurveData.length > 0 ? equityCurveData[equityCurveData.length - 1].equity : null;
  const runningPnlDisplay = typeof runningEquity === 'number' ? runningEquity : null;
  const runningZ = typeof live?.zscore === 'number' ? live.zscore : null;
  const runningHedge = typeof live?.hedge_ratio === 'number' ? live.hedge_ratio : (typeof summary?.hedge_ratio === 'number' ? summary.hedge_ratio : null);
  const openTrades = typeof backtestData?.open_trades === 'number' ? backtestData.open_trades : (Array.isArray(backtestData?.trades) ? backtestData.trades.filter((t: any) => !t.closed).length : 0);

  // Compute Sharpe and Max Drawdown locally if backend did not provide
  let computedSharpe: number | null = null;
  let computedMaxDD: number | null = null;
  if ((!displaySharpe || !isFinite(displaySharpe)) && equityCurveData.length > 1) {
    const returns: number[] = [];
    for (let i = 1; i < equityCurveData.length; i++) {
      returns.push(equityCurveData[i].equity - equityCurveData[i - 1].equity);
    }
    const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
    const std = Math.sqrt(returns.map(r => (r - mean) ** 2).reduce((a, b) => a + b, 0) / returns.length) || 0;
    if (std > 0) computedSharpe = (mean / std) * Math.sqrt(252);
  }

  if ((!displayMaxDD || !isFinite(displayMaxDD)) && equityCurveData.length > 0) {
    let peak = -Infinity;
    let maxdd = 0;
    for (const p of equityCurveData.map(d => d.equity)) {
      if (p > peak) peak = p;
      const dd = peak - p;
      if (peak > 0) maxdd = Math.max(maxdd, dd / Math.max(1e-9, peak));
    }
    computedMaxDD = isFinite(maxdd) ? maxdd : null;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Backtesting - Strategy Performance
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Test your pairs trading strategy against historical data to evaluate performance metrics.
      </Typography>

      <Grid container spacing={3}>
        {/* No symbols selected */}
        {(!selectedSymbol1 || !selectedSymbol2) && (
          <Grid item xs={12}>
            <Alert severity="info">
              Please select symbols in the Spread Analysis tab to run backtests.
            </Alert>
          </Grid>
        )}

        {/* Parameter Configuration */}
        {selectedSymbol1 && selectedSymbol2 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Strategy Parameters
                </Typography>
                <Grid container spacing={2} mt={1}>
                  <Grid item xs={12} sm={4}>
                    <TextField
                      select
                      fullWidth
                      label="Strategy"
                      value={strategy}
                      onChange={(e) => setStrategy(e.target.value)}
                      SelectProps={{ native: true }}
                    >
                      <option value="zscore">Z-Score Pairs</option>
                      <option value="rsi">RSI (symbol1)</option>
                      <option value="macd">MACD (symbol1)</option>
                    </TextField>
                  </Grid>
                  {strategy === 'rsi' && (
                    <Grid item xs={12} sm={4}>
                      <TextField
                        fullWidth
                        type="number"
                        label="RSI Buy Threshold"
                        value={rsiBuy}
                        onChange={(e) => setRsiBuy(parseInt(e.target.value || '30'))}
                        inputProps={{ step: 1 }}
                      />
                    </Grid>
                  )}
                  {strategy === 'rsi' && (
                    <Grid item xs={12} sm={4}>
                      <TextField
                        fullWidth
                        type="number"
                        label="RSI Sell Threshold"
                        value={rsiSell}
                        onChange={(e) => setRsiSell(parseInt(e.target.value || '50'))}
                        inputProps={{ step: 1 }}
                      />
                    </Grid>
                  )}
                  <Grid item xs={12} sm={4}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Entry Threshold (Z-Score)"
                      value={entryThreshold}
                      onChange={(e) => setEntryThreshold(parseFloat(e.target.value))}
                      disabled={strategy !== 'zscore'}
                      inputProps={{ step: 0.1, min: 0 }}
                      helperText="Enter trade when |z-score| > this value"
                    />
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <FormControl fullWidth>
                      <InputLabel id="bt-timeframe-label">Timeframe</InputLabel>
                      <Select
                        labelId="bt-timeframe-label"
                        value={settings.aggregationInterval}
                        label="Timeframe"
                        onChange={(e) => setAggregationInterval(e.target.value as string)}
                      >
                        <MenuItem value="1m">1m</MenuItem>
                        <MenuItem value="5m">5m</MenuItem>
                        <MenuItem value="15m">15m</MenuItem>
                        <MenuItem value="1h">1h</MenuItem>
                        <MenuItem value="4h">4h</MenuItem>
                        <MenuItem value="1d">1d</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Lookback (bars)"
                      value={lookback}
                      onChange={(e) => setLookback(parseInt(e.target.value || '0'))}
                      inputProps={{ step: 10, min: 10 }}
                      helperText="Number of bars used for spread/ADF calculations (1m bars)"
                    />
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Exit Threshold (Z-Score)"
                      value={exitThreshold}
                      onChange={(e) => setExitThreshold(parseFloat(e.target.value))}
                      disabled={strategy !== 'zscore'}
                      inputProps={{ step: 0.1, min: 0 }}
                      helperText="Exit trade when |z-score| < this value"
                    />
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Stop Loss (Z-Score)"
                      value={stopLoss}
                      onChange={(e) => setStopLoss(parseFloat(e.target.value))}
                      disabled={strategy !== 'zscore'}
                      inputProps={{ step: 0.1, min: 0 }}
                      helperText="Cut losses when |z-score| > this value"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <Button
                      variant="contained"
                      size="large"
                      fullWidth
                      onClick={handleRunBacktest}
                      disabled={isLoading}
                      startIcon={isLoading ? <CircularProgress size={20} /> : <PlayArrow />}
                    >
                      {isLoading ? 'Running Backtest...' : 'Run Backtest'}
                    </Button>
                  </Grid>
                  <Grid item xs={12}>
                    <Typography variant="caption" color="text.secondary">
                      Backtest timeframe: last {lookback} 1m bars (~{Math.round(lookback/60)} hours or {lookback} minutes)
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Error Display */}
        {error && (
          <Grid item xs={12}>
            <Alert severity="error">
              Failed to run backtest: {error instanceof Error ? error.message : 'Unknown error'}
            </Alert>
          </Grid>
        )}

        {/* Backtest Results */}
        {backtestData && (
          <>
            {/* Live calculations panel */}
            {(isLoading || runBacktest || live) && (
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Live Calculations
                    </Typography>
                    <Stack direction="row" spacing={2}>
                      <Box>
                        <Typography variant="caption" color="text.secondary">Running P&L</Typography>
                        <Typography variant="h5" fontWeight="bold">
                          {runningPnlDisplay !== null ? `$${runningPnlDisplay.toFixed(2)}` : 'N/A'}
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary">Current Z-Score</Typography>
                        <Typography variant="h5" fontWeight="bold">
                          {runningZ !== null ? runningZ.toFixed(3) : 'N/A'}
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary">Hedge Ratio</Typography>
                        <Typography variant="h5" fontWeight="bold">
                          {runningHedge !== null ? runningHedge.toFixed(4) : 'N/A'}
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary">Open Trades</Typography>
                        <Typography variant="h5" fontWeight="bold">{openTrades}</Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            )}
            {/* Performance Metrics */}
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Stack spacing={1}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <AttachMoney color="primary" />
                      <Typography variant="caption" color="text.secondary">
                        Total Return
                      </Typography>
                    </Box>
                    <Typography
                      variant="h4"
                      fontWeight="bold"
                      color={typeof displayTotalReturn === 'number' && displayTotalReturn >= 0 ? 'success.main' : 'error.main'}
                    >
                      {typeof displayTotalReturn === 'number'
                        ? (summary?.total_return !== undefined
                            ? `${(displayTotalReturn * 100).toFixed(2)}%`
                            : `${displayTotalReturn.toFixed(2)}`)
                        : 'N/A'}
                    </Typography>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Stack spacing={1}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <TrendingUp color="success" />
                      <Typography variant="caption" color="text.secondary">
                        Sharpe Ratio
                      </Typography>
                    </Box>
                    <Typography variant="h4" fontWeight="bold" color="info.main">
                      {typeof displaySharpe === 'number'
                        ? displaySharpe.toFixed(2)
                        : (computedSharpe !== null ? computedSharpe.toFixed(2) : 'N/A')}
                    </Typography>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Stack spacing={1}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <TrendingDown color="error" />
                      <Typography variant="caption" color="text.secondary">
                        Max Drawdown
                      </Typography>
                    </Box>
                    <Typography variant="h4" fontWeight="bold" color="error.main">
                      {typeof displayMaxDD === 'number'
                        ? `${(displayMaxDD * 100).toFixed(2)}%`
                        : (computedMaxDD !== null ? `${(computedMaxDD * 100).toFixed(2)}%` : 'N/A')}
                    </Typography>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Stack spacing={1}>
                    <Typography variant="caption" color="text.secondary">
                      Win Rate
                    </Typography>
                    <Typography variant="h4" fontWeight="bold" color="success.main">
                      {typeof displayWinRate === 'number' ? `${(displayWinRate * 100).toFixed(1)}%` : 'N/A'}
                    </Typography>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>

            {/* Equity Curve */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Equity Curve
                  </Typography>
                  <Box sx={{ width: '100%', height: 400 }}>
                    <ResponsiveContainer>
                      <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                        <XAxis dataKey="index" stroke="#888" />
                        <YAxis
                          stroke="#888"
                          // pad axis to make small moves visible
                          domain={showPercent ? ['dataMin', 'dataMax'] : [(dataMin: number) => dataMin * 0.999, (dataMax: number) => dataMax * 1.001]}
                          tickFormatter={(v) => (showPercent ? `${Number(v).toFixed(2)}%` : `$${Number(v).toFixed(0)}`)}
                        />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#1a1a2e',
                            border: '1px solid #333',
                            borderRadius: '8px',
                          }}
                          formatter={(value: any, name: any) => {
                            if (showPercent) return [`${Number(value).toFixed(2)}%`, 'Equity %'];
                            return [`$${Number(value).toFixed(2)}`, 'Portfolio Value'];
                          }}
                        />
                        <Legend />
                        <Line
                          type="monotone"
                          dataKey={showPercent ? 'equity_pct' : 'equity'}
                          stroke="#00ff88"
                          strokeWidth={2}
                          dot={false}
                          name={showPercent ? 'Portfolio %' : 'Portfolio Value'}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* Trade Statistics */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Trade Statistics
                  </Typography>
                  <Divider sx={{ my: 2 }} />
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="caption" color="text.secondary">
                          Total Trades
                        </Typography>
                        <Typography variant="h5" fontWeight="bold">
                          {totalTrades}
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="caption" color="text.secondary">
                          Winning Trades
                        </Typography>
                          <Typography variant="h5" fontWeight="bold" color="success.main">
                          {winningTrades}
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="caption" color="text.secondary">
                          Losing Trades
                        </Typography>
                        <Typography variant="h5" fontWeight="bold" color="error.main">
                          {losingTrades}
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="caption" color="text.secondary">
                          Avg Trade Return
                        </Typography>
                        <Typography variant="h5" fontWeight="bold">
                          {typeof displayAvgTradeReturn === 'number'
                            ? (summary && typeof summary.avg_trade_return === 'number'
                                ? `${(displayAvgTradeReturn * 100).toFixed(2)}%`
                                : `$${displayAvgTradeReturn.toFixed(2)}`)
                            : 'N/A'}
                        </Typography>
                      </Paper>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
            {/* API Debug Panel */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    API Debug
                  </Typography>
                  <Typography variant="caption" color="text.secondary">Request Payload</Typography>
                  <pre style={{ maxHeight: 200, overflow: 'auto', background: '#0f1724', color: '#dbeafe', padding: 12 }}>
                    {lastRequestPayload ? JSON.stringify(lastRequestPayload, null, 2) : 'No request yet'}
                  </pre>
                  <Typography variant="caption" color="text.secondary">Raw Response</Typography>
                  <pre style={{ maxHeight: 400, overflow: 'auto', background: '#0f1724', color: '#dbeafe', padding: 12 }}>
                    {lastRawResponse ? JSON.stringify(lastRawResponse, null, 2) : 'No response yet'}
                  </pre>
                </CardContent>
              </Card>
            </Grid>
          </>
        )}
      </Grid>
    </Box>
  );
};
