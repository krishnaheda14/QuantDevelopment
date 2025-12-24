import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  TextField,
  MenuItem,
  Button,
  Chip,
  Paper,
  Divider,
  Alert,
  CircularProgress,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Collapse,
} from '@mui/material';
import { ShowChart, TrendingUp, TrendingDown, Remove, InfoOutlined, ExpandLess, ExpandMore } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import { useStore } from '@/store';
import { useSymbols } from '@/hooks/useSymbols';
import api from '@/services/api';
import { debug, info, warn } from '@/types';

const COMPONENT_NAME = 'SpreadAnalysis';

export const SpreadAnalysis: React.FC = () => {
  const {
    selectedSymbol1,
    selectedSymbol2,
    setSelectedSymbol1,
    setSelectedSymbol2,
    settings,
    ohlcBars,
  } = useStore();
  const { setAggregationInterval } = useStore();

  const [availableSymbols, setAvailableSymbols] = useState<string[]>([]);
  const [infoOpen, setInfoOpen] = useState(false);
  const [debugCollapsed, setDebugCollapsed] = useState(false);
  const [fallbackSeries1, setFallbackSeries1] = useState<Array<{ timestamp: string; price: number }>>([])
  const [fallbackSeries2, setFallbackSeries2] = useState<Array<{ timestamp: string; price: number }>>([])
  const [metricInfo, setMetricInfo] = useState<{ open: boolean; metric?: string }>({ open: false })

  debug(COMPONENT_NAME, 'Rendering spread analysis', {
    symbol1: selectedSymbol1,
    symbol2: selectedSymbol2,
    lookback: settings.lookbackPeriod,
  });

  // Fetch available symbols
  const { symbols: symbolsData, isLoading: symbolsLoading } = useSymbols();

  useEffect(() => {
    if (symbolsData) {
      debug(COMPONENT_NAME, 'Symbols received', symbolsData);
      // API may return either an array or an object with `symbols` key
      if (Array.isArray(symbolsData)) {
        setAvailableSymbols(symbolsData as string[])
      } else if ((symbolsData as any).symbols) {
        setAvailableSymbols((symbolsData as any).symbols)
      } else {
        setAvailableSymbols([])
      }
    }
  }, [symbolsData]);

  // Fetch spread analysis
  const {
    data: spreadData,
    isLoading: spreadLoading,
    error: spreadError,
    refetch: refetchSpread,
  } = useQuery({
    queryKey: ['spread', selectedSymbol1, selectedSymbol2, settings.lookbackPeriod, settings.aggregationInterval],
    queryFn: () => api.getSpreadAnalysis(selectedSymbol1!, selectedSymbol2!, settings.lookbackPeriod, settings.aggregationInterval),
    enabled: !!selectedSymbol1 && !!selectedSymbol2,
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  useEffect(() => {
    if (spreadData) {
      // Normalize spread data fields for compatibility with different API shapes
      const spreadValues = spreadData.spread_values || spreadData.spread || []
      const currentZ = spreadData.z_score ?? spreadData.current_zscore ?? 0

      info(COMPONENT_NAME, 'Spread analysis received', {
        hedgeRatio: spreadData.hedge_ratio,
        rSquared: spreadData.r_squared,
        signal: spreadData.signal,
        zScore: currentZ,
        points: spreadValues.length,
      })
    }
  }, [spreadData]);

  // If no live OHLC bars are present, fetch recent OHLC from API as a fallback so charts show
  useEffect(() => {
    let mounted = true
    const fetchFallback = async (symbol: string, setter: (s: Array<{ timestamp: string; price: number }>) => void) => {
      try {
        if (!symbol) return
        const bars = await api.getOHLC(symbol, settings.aggregationInterval || '1m', settings.lookbackPeriod)
        if (!mounted) return
        const series = bars.map((b: any) => ({ timestamp: b.timestamp ? new Date(b.timestamp).toLocaleTimeString() : new Date(b.t || Date.now()).toLocaleTimeString(), price: Number(b.close) }))
        setter(series)
        debug(COMPONENT_NAME, 'Fallback OHLC loaded', { symbol, points: series.length })
      } catch (e) {
        warn(COMPONENT_NAME, 'Failed to fetch fallback OHLC', { symbol, error: e })
      }
    }

    const bars1 = selectedSymbol1 ? (ohlcBars.get(selectedSymbol1) || []) : []
    const bars2 = selectedSymbol2 ? (ohlcBars.get(selectedSymbol2) || []) : []

    if (selectedSymbol1 && bars1.length === 0) fetchFallback(selectedSymbol1, setFallbackSeries1)
    if (selectedSymbol2 && bars2.length === 0) fetchFallback(selectedSymbol2, setFallbackSeries2)

    return () => { mounted = false }
  }, [selectedSymbol1, selectedSymbol2, ohlcBars, settings.lookbackPeriod])

  useEffect(() => {
    if (spreadError) {
      warn(COMPONENT_NAME, 'Error fetching spread data', spreadError);
    }
  }, [spreadError]);

  // Handle symbol selection
  const handleSymbol1Change = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    debug(COMPONENT_NAME, 'Symbol 1 changed', value);
    setSelectedSymbol1(value);
  };

  const handleSymbol2Change = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    debug(COMPONENT_NAME, 'Symbol 2 changed', value);
    setSelectedSymbol2(value);
  };

  const handleRefresh = () => {
    info(COMPONENT_NAME, 'Manual refresh triggered');
    refetchSpread();
  };

  const openInfo = () => setInfoOpen(true);
  const closeInfo = () => setInfoOpen(false);

  // Prepare chart data for spread
  const prepareChartData = () => {
    const spreadValues = spreadData?.spread_values || spreadData?.spread || []
    if (!spreadData || spreadValues.length === 0) {
      debug(COMPONENT_NAME, 'No spread data available for chart')
      return []
    }

    const chartData = spreadValues.map((value, index) => {
      const timestamp = spreadData.timestamps?.[index] || new Date(Date.now() - (spreadValues.length - index) * 60000).toISOString()
      return {
        timestamp: new Date(timestamp).toLocaleTimeString(),
        spread: value,
        zScore: (spreadData.z_scores || spreadData.zscore || [])[index] || 0,
        upperThreshold: settings.zScoreThreshold,
        lowerThreshold: -settings.zScoreThreshold,
      }
    })

    debug(COMPONENT_NAME, 'Chart data prepared', { points: chartData.length });
    return chartData;
  };

  // Prepare price chart data
  const preparePriceChartData = () => {
    if (!selectedSymbol1 || !selectedSymbol2) {
      return [];
    }

    const bars1 = ohlcBars.get(selectedSymbol1) || [];
    const bars2 = ohlcBars.get(selectedSymbol2) || [];

    const maxLength = Math.max(bars1.length, bars2.length);
    const chartData = [];

    for (let i = Math.max(0, maxLength - settings.lookbackPeriod); i < maxLength; i++) {
      const bar1 = bars1[i];
      const bar2 = bars2[i];

      chartData.push({
        timestamp: bar1?.timestamp ? new Date(bar1.timestamp).toLocaleTimeString() : bar2?.timestamp ? new Date(bar2.timestamp).toLocaleTimeString() : '',
        symbol1: bar1?.close,
        symbol2: bar2?.close,
      });
    }

    debug(COMPONENT_NAME, 'Price chart data prepared', { points: chartData.length });
    return chartData;
  };

  // Prepare separate series for each symbol so we can plot on independent axes
  const preparePriceSeries = (symbol: string) => {
    const bars = ohlcBars.get(symbol) || [];
    const series: Array<{ timestamp: string; price: number | null }> = [];
    const start = Math.max(0, bars.length - settings.lookbackPeriod);
    for (let i = start; i < bars.length; i++) {
      const b = bars[i];
      // Only include points that have numeric close prices
      const ts = b?.timestamp ? new Date(b.timestamp).toLocaleTimeString() : '';
      const price = typeof b?.close === 'number' ? b.close : (b?.close ? Number(b.close) : null);
      if (price === null || Number.isNaN(price)) continue;
      series.push({ timestamp: ts, price });
    }
    return series;
  };

  const priceSeries1 = preparePriceSeries(selectedSymbol1 || '');
  const priceSeries2 = preparePriceSeries(selectedSymbol2 || '');
  const visiblePriceSeries1 = priceSeries1.length ? priceSeries1 : fallbackSeries1
  const visiblePriceSeries2 = priceSeries2.length ? priceSeries2 : fallbackSeries2

  const formatPriceTick = (value: number) => {
    if (!isFinite(Number(value))) return 'N/A';
    const v = Number(value);
    if (Math.abs(v) >= 1000) return `$${Math.round(v).toLocaleString()}`;
    return `$${v.toFixed(2)}`;
  };

  const chartData = prepareChartData();
  const priceChartData = preparePriceChartData();

  // Precompute metric values to avoid complex inline JSX expressions
  const metricValues = (() => {
    const hedge = spreadData && typeof spreadData.hedge_ratio === 'number' ? spreadData.hedge_ratio : null
    const intercept = spreadData && typeof spreadData.intercept === 'number' ? spreadData.intercept : null
    const r2 = spreadData && typeof spreadData.r_squared === 'number' ? spreadData.r_squared : null
    let current_z: number | null = null
    if (spreadData) {
      if (typeof spreadData.current_zscore === 'number') current_z = spreadData.current_zscore
      else if (Array.isArray(spreadData.z_scores) && spreadData.z_scores.length) current_z = spreadData.z_scores[spreadData.z_scores.length - 1]
    }
    const observations = spreadData ? (spreadData.observations ?? ((spreadData.spread_values || spreadData.spread || []).length)) : 0
    return { hedge, intercept, r2, current_z, observations }
  })()

  return (
    <Box>
      <Box display="flex" alignItems="center" justifyContent="space-between">
        <Typography variant="h4" gutterBottom>
          Spread Analysis - OLS Regression
        </Typography>
        <IconButton onClick={openInfo} size="large" aria-label="info">
          <InfoOutlined />
        </IconButton>
      </Box>
      <Typography variant="body2" color="text.secondary" paragraph>
        Analyze the statistical relationship between two trading pairs using ordinary least squares regression.
        The spread is calculated as: Spread = Symbol2 - (hedge_ratio × Symbol1)
      </Typography>

      <Grid container spacing={3}>
        {/* Symbol Selection */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Symbol Selection
              </Typography>
              <Grid container spacing={2} mt={1}>
                <Grid item xs={12} sm={6} md={4}>
                  <TextField
                    select
                    fullWidth
                    label="Symbol 1"
                    value={selectedSymbol1 || ''}
                    onChange={handleSymbol1Change}
                    disabled={symbolsLoading}
                    helperText="First trading pair"
                  >
                    <MenuItem value="">
                      <em>Select Symbol 1</em>
                    </MenuItem>
                    {availableSymbols.map((symbol) => (
                      <MenuItem key={symbol} value={symbol}>
                        {symbol}
                      </MenuItem>
                    ))}
                  </TextField>
                </Grid>

                <Grid item xs={12} sm={6} md={4}>
                  <TextField
                    select
                    fullWidth
                    label="Symbol 2"
                    value={selectedSymbol2 || ''}
                    onChange={handleSymbol2Change}
                    disabled={symbolsLoading}
                    helperText="Second trading pair"
                  >
                    <MenuItem value="">
                      <em>Select Symbol 2</em>
                    </MenuItem>
                    {availableSymbols.map((symbol) => (
                      <MenuItem key={symbol} value={symbol}>
                        {symbol}
                      </MenuItem>
                    ))}
                  </TextField>
                </Grid>

                <Grid item xs={12} sm={12} md={4} display="flex" alignItems="center">
                  <Button
                    variant="contained"
                    fullWidth
                    onClick={handleRefresh}
                    disabled={!selectedSymbol1 || !selectedSymbol2 || spreadLoading}
                    startIcon={spreadLoading ? <CircularProgress size={20} /> : <ShowChart />}
                  >
                    {spreadLoading ? 'Analyzing...' : 'Refresh Analysis'}
                  </Button>
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                  <TextField
                    select
                    fullWidth
                    label="Timeframe"
                    value={settings.aggregationInterval}
                    onChange={(e) => {
                      setAggregationInterval(e.target.value)
                    }}
                    helperText="OHLC aggregation interval used for metrics"
                  >
                    <MenuItem value="1m">1m</MenuItem>
                    <MenuItem value="5m">5m</MenuItem>
                    <MenuItem value="15m">15m</MenuItem>
                    <MenuItem value="1h">1h</MenuItem>
                    <MenuItem value="4h">4h</MenuItem>
                    <MenuItem value="1d">1d</MenuItem>
                  </TextField>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Error Display */}
        {spreadError && (
          <Grid item xs={12}>
            <Alert severity="error">
              Failed to fetch spread analysis: {spreadError instanceof Error ? spreadError.message : 'Unknown error'}
            </Alert>
          </Grid>
        )}
        {/* Loading State */}
        {spreadLoading && !spreadData && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="center" py={5}>
                  <CircularProgress />
                  <Typography variant="body1" ml={2}>
                    Analyzing spread...
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Regression Results */}
        {spreadData && (
          <>
            {/* Key Metrics */}
            <Grid item xs={12} md={6} lg={3}>
              <Card>
                <CardContent>
                  <Typography variant="caption" color="text.secondary">
                    Hedge Ratio
                  </Typography>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="h4" fontWeight="bold" color="primary.main">
                      {typeof spreadData.hedge_ratio === 'number' ? spreadData.hedge_ratio.toFixed(4) : 'N/A'}
                    </Typography>
                    <IconButton size="small" onClick={() => setMetricInfo({ open: true, metric: 'hedge' })}>
                      <InfoOutlined fontSize="small" />
                    </IconButton>
                  </Box>
                  <Typography variant="body2" color="text.secondary" mt={1}>
                    OLS regression slope
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6} lg={3}>
              <Card>
                <CardContent>
                  <Typography variant="caption" color="text.secondary">
                    R-Squared
                  </Typography>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="h4" fontWeight="bold" color="info.main">
                      {typeof spreadData.r_squared === 'number' ? spreadData.r_squared.toFixed(4) : 'N/A'}
                    </Typography>
                    <IconButton size="small" onClick={() => setMetricInfo({ open: true, metric: 'r2' })}>
                      <InfoOutlined fontSize="small" />
                    </IconButton>
                  </Box>
                  <Typography variant="body2" color="text.secondary" mt={1}>
                    Goodness of fit ({metricValues.r2 !== null ? (metricValues.r2 * 100).toFixed(2) + '%' : 'N/A'})
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6} lg={3}>
              <Card>
                <CardContent>
                  <Typography variant="caption" color="text.secondary">
                    Z-Score
                  </Typography>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography
                    variant="h4"
                    fontWeight="bold"
                    color={
                      Math.abs(spreadData.z_score ?? spreadData.current_zscore ?? 0) > settings.zScoreThreshold
                        ? 'warning.main'
                        : 'success.main'
                    }
                    >
                      {typeof (spreadData.z_score ?? spreadData.current_zscore) === 'number' ? (spreadData.z_score ?? spreadData.current_zscore ?? 0).toFixed(2) : 'N/A'}
                    </Typography>
                    <IconButton size="small" onClick={() => setMetricInfo({ open: true, metric: 'z' })}>
                      <InfoOutlined fontSize="small" />
                    </IconButton>
                  </Box>
                  <Typography variant="body2" color="text.secondary" mt={1}>
                    Current deviation
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6} lg={3}>
              <Card>
                <CardContent>
                  <Typography variant="caption" color="text.secondary">
                    Trading Signal
                  </Typography>
                  <Box mt={1}>
                    <Chip
                      label={spreadData.signal}
                      color={
                        spreadData.signal === 'LONG'
                          ? 'success'
                          : spreadData.signal === 'SHORT'
                          ? 'error'
                          : 'default'
                      }
                      icon={
                        spreadData.signal === 'LONG' ? (
                          <TrendingUp />
                        ) : spreadData.signal === 'SHORT' ? (
                          <TrendingDown />
                        ) : (
                          <Remove />
                        )
                      }
                      sx={{ fontSize: '1.1rem', py: 2.5, width: '100%' }}
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary" mt={1}>
                    {spreadData.signal === 'LONG' && 'Buy spread (long Symbol1, short Symbol2)'}
                    {spreadData.signal === 'SHORT' && 'Sell spread (short Symbol1, long Symbol2)'}
                    {spreadData.signal === 'NEUTRAL' && 'No trading signal'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            {/* Price Charts - two separate charts side-by-side with independent scales */}
            <Grid item xs={12} lg={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Price Comparison
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <Paper sx={{ p: 1, height: 300 }}>
                        <Box display="flex" alignItems="center" justifyContent="space-between">
                          <Typography variant="subtitle2">{selectedSymbol1}</Typography>
                          <IconButton size="small" onClick={() => setMetricInfo({ open: true, metric: 'price1' })}>
                            <InfoOutlined fontSize="small" />
                          </IconButton>
                        </Box>
                        <Box sx={{ width: '100%', height: 230 }}>
                          <ResponsiveContainer>
                            <LineChart data={visiblePriceSeries1}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                              <XAxis dataKey="timestamp" stroke="#888" tick={{ fontSize: 11 }} />
                              <YAxis
                                stroke="#888"
                                tickFormatter={(v) => formatPriceTick(Number(v))}
                                domain={['dataMin', 'dataMax']}
                              />
                              <Tooltip contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333', borderRadius: '8px' }} />
                              <Line type="monotone" dataKey="price" stroke="#00ff88" strokeWidth={2} dot={false} isAnimationActive={false} />
                            </LineChart>
                          </ResponsiveContainer>
                        </Box>
                      </Paper>
                    </Grid>

                    <Grid item xs={12} sm={6}>
                      <Paper sx={{ p: 1, height: 300 }}>
                        <Box display="flex" alignItems="center" justifyContent="space-between">
                          <Typography variant="subtitle2">{selectedSymbol2}</Typography>
                          <IconButton size="small" onClick={() => setMetricInfo({ open: true, metric: 'price2' })}>
                            <InfoOutlined fontSize="small" />
                          </IconButton>
                        </Box>
                        <Box sx={{ width: '100%', height: 230 }}>
                          <ResponsiveContainer>
                            <LineChart data={visiblePriceSeries2}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                              <XAxis dataKey="timestamp" stroke="#888" tick={{ fontSize: 11 }} />
                              <YAxis
                                stroke="#888"
                                tickFormatter={(v) => formatPriceTick(Number(v))}
                                domain={['dataMin', 'dataMax']}
                              />
                              <Tooltip contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333', borderRadius: '8px' }} />
                              <Line type="monotone" dataKey="price" stroke="#ff4444" strokeWidth={2} dot={false} isAnimationActive={false} />
                            </LineChart>
                          </ResponsiveContainer>
                        </Box>
                      </Paper>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>

            {/* Spread Chart */}
            <Grid item xs={12} lg={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Spread Value
                  </Typography>
                  <Box sx={{ width: '100%', height: 300 }}>
                    <ResponsiveContainer>
                      <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                        <XAxis
                          dataKey="timestamp"
                          stroke="#888"
                          style={{ fontSize: '12px' }}
                        />
                        <YAxis 
                          stroke="#888" 
                          style={{ fontSize: '12px' }}
                          domain={['auto', 'auto']}
                          tickFormatter={(value) => {
                            const n = Number(value);
                            return Number.isFinite(n) ? n.toFixed(3) : 'N/A';
                          }}
                        />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#1a1a2e',
                            border: '1px solid #333',
                            borderRadius: '8px',
                          }}
                        />
                        <Legend />
                        <ReferenceLine y={0} stroke="#888" strokeDasharray="3 3" />
                        <Line
                          type="monotone"
                          dataKey="spread"
                          stroke="#00bfff"
                          strokeWidth={2}
                          dot={false}
                          name="Spread"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* Debug / Explainability Panel */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" justifyContent="space-between">
                    <Box>
                      <Typography variant="h6" gutterBottom>
                        Debug — Raw Values & Explainability
                      </Typography>
                      <Typography variant="caption" color="text.secondary">Quick diagnostics to help understand why metrics may be zero or missing</Typography>
                    </Box>
                    <IconButton size="small" onClick={() => setDebugCollapsed((s) => !s)} aria-label={debugCollapsed ? 'Expand' : 'Collapse'}>
                      {debugCollapsed ? <ExpandMore /> : <ExpandLess />}
                    </IconButton>
                  </Box>
                  <Divider sx={{ my: 2 }} />
                  <Collapse in={!debugCollapsed} timeout="auto" unmountOnExit>
                    <Grid container spacing={2}>
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2 }}>
                        <Typography variant="caption" color="text.secondary">Hedge Ratio</Typography>
                        <Typography variant="h6">{spreadData && typeof spreadData.hedge_ratio === 'number' ? spreadData.hedge_ratio.toFixed(6) : 'N/A'}</Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2 }}>
                        <Typography variant="caption" color="text.secondary">Intercept (OLS α)</Typography>
                        <Typography variant="h6">{spreadData && typeof spreadData.intercept === 'number' ? spreadData.intercept.toFixed(6) : 'N/A'}</Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2 }}>
                        <Typography variant="caption" color="text.secondary">R-Squared</Typography>
                        <Typography variant="h6">{spreadData && typeof spreadData.r_squared === 'number' ? spreadData.r_squared.toFixed(6) : 'N/A'}</Typography>
                        <Typography variant="caption" color="text.secondary">{spreadData && typeof spreadData.r_squared === 'number' ? (spreadData.r_squared * 100).toFixed(2) + '%' : ''}</Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2 }}>
                        <Typography variant="caption" color="text.secondary">Observations</Typography>
                        <Typography variant="h6">{spreadData ? (spreadData.observations ?? ((spreadData.spread_values || spreadData.spread || []).length)) : 'N/A'}</Typography>
                      </Paper>
                    </Grid>

                    <Grid item xs={12}>
                      <Paper sx={{ p: 2, maxHeight: 220, overflow: 'auto', backgroundColor: '#0f1115' }}>
                        <Typography variant="caption" color="text.secondary">Raw API payload (truncated)</Typography>
                        <pre style={{ color: '#ddd', fontSize: 12, whiteSpace: 'pre-wrap' }}>{spreadData ? JSON.stringify(spreadData, null, 2).slice(0, 8000) : 'No data'}</pre>
                      </Paper>
                    </Grid>
                  </Grid>
                </Collapse>
              </CardContent>
            </Card>
            </Grid>

            {/* Z-Score Chart */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Z-Score (Standardized Spread)
                  </Typography>
                  <Box sx={{ width: '100%', height: 350 }}>
                    <ResponsiveContainer>
                      <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                        <XAxis
                          dataKey="timestamp"
                          stroke="#888"
                          style={{ fontSize: '12px' }}
                        />
                        <YAxis 
                          stroke="#888" 
                          style={{ fontSize: '12px' }}
                          domain={['auto', 'auto']}
                          tickFormatter={(value) => {
                            const n = Number(value);
                            return Number.isFinite(n) ? n.toFixed(2) : 'N/A';
                          }}
                        />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#1a1a2e',
                            border: '1px solid #333',
                            borderRadius: '8px',
                          }}
                        />
                        <Legend />
                        <ReferenceLine y={0} stroke="#888" strokeDasharray="3 3" />
                        <ReferenceLine
                          y={settings.zScoreThreshold}
                          stroke="#00ff88"
                          strokeDasharray="5 5"
                          label="Upper Threshold"
                        />
                        <ReferenceLine
                          y={-settings.zScoreThreshold}
                          stroke="#ff4444"
                          strokeDasharray="5 5"
                          label="Lower Threshold"
                        />
                        <Line
                          type="monotone"
                          dataKey="zScore"
                          stroke="#ffd700"
                          strokeWidth={3}
                          dot={false}
                          name="Z-Score"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </Box>
                  <Box mt={2}>
                    <Alert severity="info">
                      <strong>Interpretation:</strong> Z-score above {settings.zScoreThreshold} suggests the spread is overvalued (SHORT signal).
                      Z-score below {-settings.zScoreThreshold} suggests the spread is undervalued (LONG signal).
                    </Alert>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* Statistical Details */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Statistical Details
                  </Typography>
                  <Divider sx={{ my: 2 }} />
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2 }}>
                        <Typography variant="caption" color="text.secondary">
                          Intercept
                        </Typography>
                        <Typography variant="h6">{(spreadData.intercept ?? 0).toFixed(4)}</Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2 }}>
                        <Typography variant="caption" color="text.secondary">
                          Spread Mean
                        </Typography>
                        <Typography variant="h6">{(spreadData.spread_mean ?? 0).toFixed(4)}</Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2 }}>
                        <Typography variant="caption" color="text.secondary">
                          Spread Std Dev
                        </Typography>
                        <Typography variant="h6">{(spreadData.spread_std ?? 0).toFixed(4)}</Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2 }}>
                        <Typography variant="caption" color="text.secondary">
                          Data Points
                        </Typography>
                        <Typography variant="h6">{(spreadData.spread_values || spreadData.spread || []).length}</Typography>
                      </Paper>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </>
        )}

        {/* Instructions */}
        {!selectedSymbol1 || !selectedSymbol2 ? (
          <Grid item xs={12}>
            <Card sx={{ bgcolor: 'primary.dark', color: 'primary.contrastText' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Getting Started
                </Typography>
                <Typography variant="body2">
                  1. Select two trading symbols from the dropdowns above
                  <br />
                  2. The system will automatically calculate the OLS regression and spread
                  <br />
                  3. Monitor the Z-score to identify trading opportunities
                  <br />
                  4. LONG signal: Spread is undervalued, buy Symbol1 and sell Symbol2
                  <br />
                  5. SHORT signal: Spread is overvalued, sell Symbol1 and buy Symbol2
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ) : null}
      </Grid>

      {/* Info dialog explaining metrics and current calculations */}
      <Dialog open={infoOpen} onClose={closeInfo} maxWidth="sm" fullWidth>
        <DialogTitle>Spread Metrics — Explanation & Current Calculations</DialogTitle>
        <DialogContent dividers>
          <DialogContentText component="div">
            <Typography variant="subtitle1" gutterBottom><strong>What these metrics mean</strong></Typography>
            <Typography variant="body2" paragraph>
              <strong>Hedge Ratio:</strong> The OLS regression slope (Symbol2 ~ alpha + hedge_ratio × Symbol1). It determines how many units of Symbol1 to hold against Symbol2 when constructing the spread.
            </Typography>
            <Typography variant="body2" paragraph>
              <strong>R-Squared:</strong> Goodness-of-fit of the OLS regression; fraction of variance in Symbol2 explained by the linear relationship with Symbol1. Higher is better for pairs trading.
            </Typography>
            <Typography variant="body2" paragraph>
              <strong>Z-Score:</strong> Standardized spread: (spread - mean) / std. Shows how many standard deviations the current spread is from its mean. Thresholds determine trading signals.
            </Typography>

            <Typography variant="subtitle1" gutterBottom><strong>Current calculations</strong></Typography>
            <Typography variant="body2">
              Hedge Ratio: <strong>{spreadData ? (spreadData.hedge_ratio ?? 'N/A') : 'N/A'}</strong>
            </Typography>
            <Typography variant="body2">
              R-Squared: <strong>{spreadData ? (spreadData.r_squared ?? 'N/A') : 'N/A'}</strong>
            </Typography>
            <Typography variant="body2">
              Z-Score: <strong>{spreadData ? ((spreadData.z_score ?? spreadData.current_zscore ?? 0).toFixed(4)) : 'N/A'}</strong>
            </Typography>
            <Typography variant="body2" paragraph>
              Data points: <strong>{spreadData ? ((spreadData.spread_values || spreadData.spread || []).length) : 0}</strong>
            </Typography>

            <Typography variant="subtitle1" gutterBottom><strong>Are these dynamic?</strong></Typography>
            <Typography variant="body2" paragraph>
              Yes — the backend recomputes analytics from recent OHLC data and the frontend requests updates periodically. This page requests new analysis every <strong>5 seconds</strong> (when symbols are selected). The analytics are computed over the most recent <strong>{settings.lookbackPeriod} minutes</strong> unless changed in settings.
            </Typography>

            <Typography variant="subtitle1" gutterBottom><strong>Formulas / How they are computed</strong></Typography>
            <Typography variant="body2" paragraph>
              • OLS: Fit Symbol2 = alpha + hedge_ratio × Symbol1 using ordinary least squares on aligned close prices; hedge_ratio is the slope.
              <br />• R²: coefficient of determination from the OLS model.
              <br />• Spread: spread_t = price_symbol2_t - hedge_ratio × price_symbol1_t.
              <br />• Z-score: (spread_t - mean(spread_window)) / std(spread_window).
            </Typography>

            <Typography variant="body2" color="text.secondary">
              Timestamps: {spreadData && spreadData.timestamps && spreadData.timestamps.length ? (
                <>
                  <strong>{new Date(spreadData.timestamps[0]).toLocaleString()}</strong> → <strong>{new Date(spreadData.timestamps[spreadData.timestamps.length - 1]).toLocaleString()}</strong>
                </>
              ) : 'N/A'}
            </Typography>
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeInfo}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Per-metric info dialog */}
      <Dialog open={metricInfo.open} onClose={() => setMetricInfo({ open: false })} maxWidth="sm" fullWidth>
        <DialogTitle>Metric Details</DialogTitle>
        <DialogContent dividers>
          <DialogContentText component="div">
            {metricInfo.metric === 'hedge' && (
              <>
                <Typography variant="subtitle1"><strong>Hedge Ratio</strong></Typography>
                <Typography variant="body2" paragraph>
                  Value used: <strong>{spreadData && typeof spreadData.hedge_ratio === 'number' ? spreadData.hedge_ratio : 'N/A'}</strong>
                </Typography>
                <Typography variant="body2" paragraph>
                  What it depicts: Number of units of Symbol1 to hold per unit of Symbol2 when constructing the market-neutral spread.
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Analogy: If hedge ratio = 2, think of holding 2 apples to offset 1 orange when balancing a fruit crate.
                </Typography>
              </>
            )}

            {metricInfo.metric === 'r2' && (
              <>
                <Typography variant="subtitle1"><strong>R-Squared</strong></Typography>
                <Typography variant="body2" paragraph>
                  Value used: <strong>{spreadData && typeof spreadData.r_squared === 'number' ? spreadData.r_squared : 'N/A'}</strong>
                </Typography>
                <Typography variant="body2" paragraph>
                  What it depicts: Fraction of variance in Symbol2 explained by the linear model with Symbol1. Higher → better explanatory power.
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Analogy: R²=0.8 means 80% of the movement in oranges is explained by apples in our crate analogy.
                </Typography>
              </>
            )}

            {metricInfo.metric === 'z' && (
              <>
                <Typography variant="subtitle1"><strong>Z-Score</strong></Typography>
                <Typography variant="body2" paragraph>
                  Value used: <strong>{metricValues.current_z !== null ? metricValues.current_z : 'N/A'}</strong>
                </Typography>
                <Typography variant="body2" paragraph>
                  What it depicts: How many standard deviations the current spread is from its historical mean.
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Analogy: Z-score=2 means the spread is unusually high — like seeing two standard deviations more apples than usual in a crate.
                </Typography>
              </>
            )}

            {metricInfo.metric === 'price1' && (
              <>
                <Typography variant="subtitle1"><strong>{selectedSymbol1} — Price Series</strong></Typography>
                <Typography variant="body2" paragraph>
                  Showing most recent {visiblePriceSeries1.length} points used to draw the chart.
                </Typography>
              </>
            )}

            {metricInfo.metric === 'price2' && (
              <>
                <Typography variant="subtitle1"><strong>{selectedSymbol2} — Price Series</strong></Typography>
                <Typography variant="body2" paragraph>
                  Showing most recent {visiblePriceSeries2.length} points used to draw the chart.
                </Typography>
              </>
            )}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMetricInfo({ open: false })}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SpreadAnalysis;
