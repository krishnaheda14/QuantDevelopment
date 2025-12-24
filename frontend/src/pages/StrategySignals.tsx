import React from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
  Alert,
  CircularProgress,
  Paper,
  Stack,
  Autocomplete,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Button,
} from '@mui/material';
import { TrendingUp, TrendingDown, ShowChart } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, Bar, ComposedChart } from 'recharts';
import { useStore } from '@/store';
import api from '@/services/api';
import { debug, info } from '@/types';

const COMPONENT_NAME = 'StrategySignals';

export const StrategySignals: React.FC = () => {
  const { selectedSymbol1, selectedSymbol2, settings, availableSymbols, setAvailableSymbols, setAggregationInterval } = useStore();

  debug(COMPONENT_NAME, 'Rendering strategy signals', {
    symbol1: selectedSymbol1,
    symbol2: selectedSymbol2,
  });

  // Local UI state: typed symbol input and explicit applied override (Apply button)
  const [inputSymbol, setInputSymbol] = React.useState<string | null>(null)
  const [appliedSymbol, setAppliedSymbol] = React.useState<string | null>(null)

  // Timeframe selector uses global store setter so other pages stay in sync
  const timeframe = settings.aggregationInterval || '1m'

  // Ensure available symbols are populated (query and store)
  const { data: symbols } = useQuery({
    queryKey: ['symbols'],
    queryFn: () => api.getSymbols(),
    staleTime: 1000 * 60 * 5,
    onSuccess: (s) => {
      if (Array.isArray(s) && s.length > 0) setAvailableSymbols(s)
    },
  })

  // Use the applied override (only changes when user clicks Apply). If none, use pair selection from Spread Analysis.
  const symbol1 = appliedSymbol || selectedSymbol1
  const symbol2 = appliedSymbol ? undefined : selectedSymbol2

  // Fetch technical indicators
  const { data: indicators, isLoading, error } = useQuery({
    queryKey: ['indicators', symbol1, symbol2, settings.lookbackPeriod, timeframe],
    queryFn: () => {
      if (!symbol1) return Promise.resolve(null as any)
      if (symbol2) return api.getIndicators(symbol1!, symbol2!, settings.lookbackPeriod, timeframe)
      return api.getIndicators(symbol1!, settings.lookbackPeriod, undefined, timeframe)
    },
    enabled: !!symbol1,
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  React.useEffect(() => {
    if (indicators) {
      info(COMPONENT_NAME, 'Indicators received', indicators);
    }
  }, [indicators]);

  // Client-side RSI alerting: create an alert when RSI crosses lenient thresholds (uses store settings)
  React.useEffect(() => {
    try {
      if (!indicators || !Array.isArray(indicators.rsi) || indicators.rsi.length === 0) return
      const store = useStore.getState()
      const last = Number(indicators.rsi[indicators.rsi.length - 1])
      if (!Number.isFinite(last)) return

      const over = store.settings.rsiOverbought ?? store.rsiOverbought ?? 70
      const under = store.settings.rsiOversold ?? store.rsiOversold ?? 30

      const recent = store.alerts.find(a => a.type === 'RSI' && a.symbol === (symbol1 || '') && (Date.now() - a.timestamp) < 60000)
      if (recent) return // suppress duplicates within 60s

      if (last >= over) {
        store.addAlert({
          id: `rsi-over-${symbol1 || 'unknown'}-${Date.now()}`,
          timestamp: Date.now(),
          symbol: symbol1 || '',
          type: 'RSI',
          message: `RSI ${last.toFixed(0)} >= ${over} (overbought)`,
          severity: 'warning',
          triggered: true,
          value: last,
        })
      } else if (last <= under) {
        store.addAlert({
          id: `rsi-under-${symbol1 || 'unknown'}-${Date.now()}`,
          timestamp: Date.now(),
          symbol: symbol1 || '',
          type: 'RSI',
          message: `RSI ${last.toFixed(0)} <= ${under} (oversold)`,
          severity: 'warning',
          triggered: true,
          value: last,
        })
      }
    } catch (e) {
      debug(COMPONENT_NAME, 'RSI alert generation failed', e)
    }
  }, [indicators, symbol1])

  // Normalize indicator shapes to provide a consistent API for the UI
  const macdArray = indicators
    ? Array.isArray(indicators.macd)
      ? indicators.macd
      : indicators.macd?.macd || []
    : []
  const macdSignal = indicators?.macd_signal || (indicators && !Array.isArray(indicators.macd) ? indicators.macd?.signal || [] : [])
  const macdHistogram = indicators?.macd_histogram || (indicators && !Array.isArray(indicators.macd) ? indicators.macd?.histogram || [] : [])
  const bollUpper = indicators?.bollinger_upper || indicators?.bollinger_bands?.upper || []
  const bollMiddle = indicators?.bollinger_middle || indicators?.bollinger_bands?.middle || []
  const bollLower = indicators?.bollinger_lower || indicators?.bollinger_bands?.lower || []
  const prices = indicators?.prices || []

  // Prepare chart data
  const prepareChartData = () => {
    if (!indicators || !indicators.rsi || indicators.rsi.length === 0) {
      return [];
    }

    return indicators.rsi.map((rsi, index) => ({
      index,
      rsi: rsi,
      macd: macdArray[index],
      signal: macdSignal[index],
      histogram: macdHistogram[index],
      bb_upper: bollUpper[index],
      bb_middle: bollMiddle[index],
      bb_lower: bollLower[index],
      price: prices[index],
    }));
  };

  const chartData = prepareChartData();

  // Get current signals
  const getCurrentSignals = () => {
    if (!indicators || !indicators.rsi || indicators.rsi.length === 0) {
      return { rsi: null, macd: null, bb: null };
    }

    const lastIndex = indicators.rsi.length - 1;
    const currentRSI = indicators.rsi[lastIndex];
    const currentMACD = macdArray[lastIndex];
    const currentSignal = macdSignal[lastIndex];
    const currentPrice = prices[lastIndex];
    const currentBBUpper = bollUpper[lastIndex];
    const currentBBLower = bollLower[lastIndex];

    return {
      rsi: {
        value: currentRSI,
        signal: currentRSI > 70 ? 'OVERBOUGHT' : currentRSI < 30 ? 'OVERSOLD' : 'NEUTRAL',
      },
      macd: {
        value: currentMACD,
        signalLine: currentSignal,
        histogram: macdHistogram[lastIndex],
        signal: currentMACD > currentSignal ? 'BULLISH' : 'BEARISH',
      },
      bb: {
        price: currentPrice,
        upper: currentBBUpper,
        lower: currentBBLower,
        signal: currentPrice > currentBBUpper ? 'OVERBOUGHT' : currentPrice < currentBBLower ? 'OVERSOLD' : 'NEUTRAL',
      },
    };
  };

  const signals = getCurrentSignals();

  const fmt = (v: number | null | undefined, d: number) => (v !== null && v !== undefined && !Number.isNaN(Number(v)) ? Number(v).toFixed(d) : 'N/A')

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Strategy Signals - Technical Indicators
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Technical analysis using RSI, MACD, and Bollinger Bands to identify trading opportunities.
      </Typography>

      {/* Controls: typed symbol input, Apply button, and timeframe */}
      <Box mb={2}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6} lg={5}>
            <Autocomplete
              freeSolo
              options={availableSymbols && availableSymbols.length ? availableSymbols : []}
              value={inputSymbol}
              onChange={(e, v) => setInputSymbol(v as string | null)}
              onInputChange={(e, v) => setInputSymbol(v === '' ? null : v)}
              renderInput={(params) => <TextField {...params} label="Symbol (leave empty to use pair from Spread Analysis)" />}
            />
          </Grid>
          <Grid item xs={6} md={2} lg={2}>
            <Button
              fullWidth
              variant="contained"
              onClick={() => setAppliedSymbol(inputSymbol)}
            >
              Apply
            </Button>
          </Grid>
          <Grid item xs={6} md={3} lg={2}>
            <FormControl fullWidth>
              <InputLabel id="timeframe-label">Timeframe</InputLabel>
              <Select
                labelId="timeframe-label"
                value={timeframe}
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
          <Grid item xs={6} md={2} lg={1}>
            <FormControlLabel
              control={<Switch checked={!!appliedSymbol} onChange={(e) => {
                if (e.target.checked) {
                  // enable single-symbol mode: apply either current appliedSymbol, typed input, or the currently selected primary symbol
                  const useSym = appliedSymbol || inputSymbol || selectedSymbol1
                  setAppliedSymbol(useSym || null)
                  setInputSymbol(useSym || null)
                } else {
                  // disable override
                  setAppliedSymbol(null)
                }
              }} />}
              label="Single"
            />
          </Grid>
        </Grid>
      </Box>

      <Grid container spacing={3}>
        {/* No symbols selected */}
        {(!symbol1) && (
          <Grid item xs={12}>
            <Alert severity="info">
              Please select a symbol (or leave empty to use the pair selected in Spread Analysis) to view technical indicators.
            </Alert>
          </Grid>
        )}

        {/* Error */}
        {error && (
          <Grid item xs={12}>
            <Alert severity="error">
              Failed to fetch indicators: {error instanceof Error ? error.message : 'Unknown error'}
            </Alert>
          </Grid>
        )}

        {/* Loading */}
        {isLoading && (
          <Grid item xs={12}>
            <Box display="flex" alignItems="center" justifyContent="center" py={5}>
              <CircularProgress />
              <Typography variant="body1" ml={2}>
                Calculating indicators...
              </Typography>
            </Box>
          </Grid>
        )}

        {/* Indicator Cards */}
        {indicators && signals && (
          <>
            {/* RSI Card */}
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Stack spacing={2}>
                    <Box display="flex" alignItems="center" justifyContent="space-between">
                      <Typography variant="h6">RSI</Typography>
                      <ShowChart color="primary" />
                    </Box>
                    {signals.rsi && (
                      <>
                        <Typography variant="h3" fontWeight="bold" color="primary.main">
                          {fmt(signals.rsi?.value, 2)}
                        </Typography>
                        <Chip
                          label={signals.rsi.signal}
                          color={
                            signals.rsi.signal === 'OVERBOUGHT'
                              ? 'error'
                              : signals.rsi.signal === 'OVERSOLD'
                              ? 'success'
                              : 'default'
                          }
                          size="medium"
                        />
                        <Typography variant="body2" color="text.secondary">
                          {signals.rsi.signal === 'OVERBOUGHT' && 'Consider selling - market may be overheated'}
                          {signals.rsi.signal === 'OVERSOLD' && 'Consider buying - market may be oversold'}
                          {signals.rsi.signal === 'NEUTRAL' && 'No clear signal - market in equilibrium'}
                        </Typography>
                      </>
                    )}
                  </Stack>
                </CardContent>
              </Card>
            </Grid>

            {/* MACD Card */}
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Stack spacing={2}>
                    <Box display="flex" alignItems="center" justifyContent="space-between">
                      <Typography variant="h6">MACD</Typography>
                      <TrendingUp color="success" />
                    </Box>
                    {signals.macd && (
                      <>
                        <Typography variant="h3" fontWeight="bold" color="info.main">
                          {fmt(signals.macd?.value, 4)}
                        </Typography>
                        <Chip
                          label={signals.macd.signal}
                          color={signals.macd.signal === 'BULLISH' ? 'success' : 'error'}
                          icon={signals.macd.signal === 'BULLISH' ? <TrendingUp /> : <TrendingDown />}
                          size="medium"
                        />
                        <Paper sx={{ p: 1 }}>
                          <Typography variant="caption" color="text.secondary">
                            Signal Line: {fmt(signals.macd?.signalLine, 4)}
                            <br />
                            Histogram: {fmt(signals.macd?.histogram, 4)}
                          </Typography>
                        </Paper>
                      </>
                    )}
                  </Stack>
                </CardContent>
              </Card>
            </Grid>

            {/* Bollinger Bands Card */}
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Stack spacing={2}>
                    <Box display="flex" alignItems="center" justifyContent="space-between">
                      <Typography variant="h6">Bollinger Bands</Typography>
                      <ShowChart color="warning" />
                    </Box>
                    {signals.bb && (
                      <>
                        <Typography variant="h3" fontWeight="bold" color="warning.main">
                          ${fmt(signals.bb?.price, 2)}
                        </Typography>
                        <Chip
                          label={signals.bb.signal}
                          color={
                            signals.bb.signal === 'OVERBOUGHT'
                              ? 'error'
                              : signals.bb.signal === 'OVERSOLD'
                              ? 'success'
                              : 'default'
                          }
                          size="medium"
                        />
                        <Paper sx={{ p: 1 }}>
                          <Typography variant="caption" color="text.secondary">
                            Upper: ${fmt(signals.bb?.upper, 2)}
                            <br />
                            Lower: ${fmt(signals.bb?.lower, 2)}
                          </Typography>
                        </Paper>
                      </>
                    )}
                  </Stack>
                </CardContent>
              </Card>
            </Grid>

            {/* RSI Chart */}
            <Grid item xs={12} lg={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    RSI (Relative Strength Index)
                  </Typography>
                  <Box sx={{ width: '100%', height: 300 }}>
                    <ResponsiveContainer>
                      <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                        <XAxis dataKey="index" stroke="#888" />
                        <YAxis 
                          stroke="#888"
                          domain={[(dataMin: number) => Math.floor(dataMin * 0.995), (dataMax: number) => Math.ceil(dataMax * 1.005)]}
                          tickFormatter={(value) => value.toFixed(2)}
                        />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#1a1a2e',
                            border: '1px solid #333',
                            borderRadius: '8px',
                          }}
                        />
                        <Legend />
                        <ReferenceLine y={70} stroke="#ff4444" strokeDasharray="3 3" label="Overbought" />
                        <ReferenceLine y={30} stroke="#00ff88" strokeDasharray="3 3" label="Oversold" />
                        <Line
                          type="monotone"
                          dataKey="rsi"
                          stroke="#00bfff"
                          strokeWidth={2}
                          dot={false}
                          name="RSI"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* MACD Chart */}
            <Grid item xs={12} lg={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    MACD (Moving Average Convergence Divergence)
                  </Typography>
                  <Box sx={{ width: '100%', height: 300 }}>
                    <ResponsiveContainer>
                      <ComposedChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                        <XAxis dataKey="index" stroke="#888" />
                        <YAxis 
                          stroke="#888"
                          domain={['auto', 'auto']}
                          tickFormatter={(value) => value.toFixed(3)}
                        />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#1a1a2e',
                            border: '1px solid #333',
                            borderRadius: '8px',
                          }}
                        />
                        <Legend />
                        <Bar dataKey="histogram" fill="#888" name="Histogram" />
                        <Line
                          type="monotone"
                          dataKey="macd"
                          stroke="#00ff88"
                          strokeWidth={2}
                          dot={false}
                          name="MACD"
                        />
                        <Line
                          type="monotone"
                          dataKey="signal"
                          stroke="#ff4444"
                          strokeWidth={2}
                          dot={false}
                          name="Signal"
                        />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* Bollinger Bands Chart */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Price with Bollinger Bands
                  </Typography>
                  <Box sx={{ width: '100%', height: 350 }}>
                    <ResponsiveContainer>
                      <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                        <XAxis dataKey="index" stroke="#888" />
                        <YAxis 
                          stroke="#888"
                          domain={[(dataMin: number) => Math.floor(dataMin * 0.995), (dataMax: number) => Math.ceil(dataMax * 1.005)]}
                          tickFormatter={(value) => value.toFixed(2)}
                        />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#1a1a2e',
                            border: '1px solid #333',
                            borderRadius: '8px',
                          }}
                        />
                        <Legend />
                        <Line
                          type="monotone"
                          dataKey="bb_upper"
                          stroke="#ff4444"
                          strokeWidth={1}
                          strokeDasharray="5 5"
                          dot={false}
                          name="Upper Band"
                        />
                        <Line
                          type="monotone"
                          dataKey="bb_middle"
                          stroke="#888"
                          strokeWidth={1}
                          strokeDasharray="3 3"
                          dot={false}
                          name="Middle (SMA)"
                        />
                        <Line
                          type="monotone"
                          dataKey="bb_lower"
                          stroke="#00ff88"
                          strokeWidth={1}
                          strokeDasharray="5 5"
                          dot={false}
                          name="Lower Band"
                        />
                        <Line
                          type="monotone"
                          dataKey="price"
                          stroke="#00bfff"
                          strokeWidth={2}
                          dot={false}
                          name="Price"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </Box>
                  <Alert severity="info" sx={{ mt: 2 }}>
                    <strong>Interpretation:</strong> Price touching the upper band suggests overbought conditions.
                    Price touching the lower band suggests oversold conditions. Bands expand during volatility and contract during consolidation.
                  </Alert>
                </CardContent>
              </Card>
            </Grid>
          </>
        )}
      </Grid>
    </Box>
  );
};
