import React, { useState } from 'react';
import { Box, Typography, Alert, Grid, Card, CardContent, TextField, MenuItem, Button, Stack, Divider } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useStore } from '@/store';
import { useSymbols } from '@/hooks/useSymbols';
import { debug, info } from '@/types';
import SystemPage from './System'

export const System: React.FC = () => <SystemPage />

export const QuickCompare: React.FC = () => {
  const { ticks } = useStore();
  const [symbol1, setSymbol1] = useState('BTCUSDT');
  const [symbol2, setSymbol2] = useState('ETHUSDT');

  const { symbols: availableSymbols } = useSymbols();

  // Get ticks for selected symbols
  const ticks1 = ticks.get(symbol1) || [];
  const ticks2 = ticks.get(symbol2) || [];

  // Prepare chart data
  const chartData = [];
  const maxLength = Math.max(ticks1.length, ticks2.length);
  for (let i = 0; i < maxLength; i++) {
    const tick1 = ticks1[i];
    const tick2 = ticks2[i];
    chartData.push({
      index: i,
      [symbol1]: tick1?.price,
      [symbol2]: tick2?.price,
      time: tick1?.timestamp || tick2?.timestamp,
    });
  }

  const latestTick1 = ticks1[ticks1.length - 1];
  const latestTick2 = ticks2[ticks2.length - 1];

  debug('QuickCompare', 'Rendering comparison', {
    symbol1,
    symbol2,
    ticks1: ticks1.length,
    ticks2: ticks2.length,
  });

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Quick Compare</Typography>
      <Alert severity="info" sx={{ mb: 3 }}>
        Side-by-side price comparison and real-time charting.
      </Alert>

      {/* Symbol Selection */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <TextField
            select
            fullWidth
            label="Symbol 1"
            value={symbol1}
            onChange={(e) => setSymbol1(e.target.value)}
          >
            {availableSymbols.map((sym) => (
              <MenuItem key={sym} value={sym}>{sym}</MenuItem>
            ))}
          </TextField>
        </Grid>
        <Grid item xs={12} md={6}>
          <TextField
            select
            fullWidth
            label="Symbol 2"
            value={symbol2}
            onChange={(e) => setSymbol2(e.target.value)}
          >
            {availableSymbols.map((sym) => (
              <MenuItem key={sym} value={sym}>{sym}</MenuItem>
            ))}
          </TextField>
        </Grid>
      </Grid>

      {/* Side-by-side prices */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>{symbol1}</Typography>
              <Divider sx={{ mb: 2 }} />
              <Stack spacing={1}>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">Price:</Typography>
                  <Typography variant="h5" fontWeight="bold" color="primary">
                    ${latestTick1?.price?.toFixed(2) || 'N/A'}
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">Quantity:</Typography>
                  <Typography variant="body2">{latestTick1?.quantity?.toFixed(4) || 'N/A'}</Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">Ticks Received:</Typography>
                  <Typography variant="body2">{ticks1.length}</Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">Last Update:</Typography>
                  <Typography variant="caption">
                    {latestTick1?.timestamp ? new Date(latestTick1.timestamp).toLocaleTimeString() : 'N/A'}
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>{symbol2}</Typography>
              <Divider sx={{ mb: 2 }} />
              <Stack spacing={1}>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">Price:</Typography>
                  <Typography variant="h5" fontWeight="bold" color="secondary">
                    ${latestTick2?.price?.toFixed(2) || 'N/A'}
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">Quantity:</Typography>
                  <Typography variant="body2">{latestTick2?.quantity?.toFixed(4) || 'N/A'}</Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">Ticks Received:</Typography>
                  <Typography variant="body2">{ticks2.length}</Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">Last Update:</Typography>
                  <Typography variant="caption">
                    {latestTick2?.timestamp ? new Date(latestTick2.timestamp).toLocaleTimeString() : 'N/A'}
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Separate Charts for each symbol */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>{symbol1} Price Chart</Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData.slice(-500)}>
                  <XAxis dataKey="index" />
                  <YAxis 
                    domain={[
                      (dataMin: number) => (typeof dataMin === 'number' && isFinite(dataMin) ? Math.floor(dataMin * 0.999) : 0),
                      (dataMax: number) => (typeof dataMax === 'number' && isFinite(dataMax) ? Math.ceil(dataMax * 1.001) : 1),
                    ]}
                    tickFormatter={(value: any) => (typeof value === 'number' ? value.toFixed(2) : '')}
                  />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey={symbol1}
                    stroke="#1976d2"
                    dot={false}
                    strokeWidth={2}
                    name={`${symbol1} Price`}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>{symbol2} Price Chart</Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData.slice(-500)}>
                  <XAxis dataKey="index" />
                  <YAxis 
                    domain={[
                      (dataMin: number) => (typeof dataMin === 'number' && isFinite(dataMin) ? Math.floor(dataMin * 0.999) : 0),
                      (dataMax: number) => (typeof dataMax === 'number' && isFinite(dataMax) ? Math.ceil(dataMax * 1.001) : 1),
                    ]}
                    tickFormatter={(value: any) => (typeof value === 'number' ? value.toFixed(2) : '')}
                  />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey={symbol2}
                    stroke="#9c27b0"
                    dot={false}
                    strokeWidth={2}
                    name={`${symbol2} Price`}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export const KalmanRobust: React.FC = () => {
  const { ticks } = useStore();
  const [symbol1, setSymbol1] = useState('BTCUSDT');
  const [symbol2, setSymbol2] = useState('ETHUSDT');

  const { symbols: availableSymbols } = useSymbols();

  // Get recent ticks
  const ticks1 = ticks.get(symbol1) || [];
  const ticks2 = ticks.get(symbol2) || [];

  // Simple Kalman filter simulation (hedge ratio estimation)
  const hedgeRatios = [];
  const minLength = Math.min(ticks1.length, ticks2.length, 200);
  
  let kalmanState = 1.0; // Initial hedge ratio estimate
  let kalmanVariance = 0.1;
  const processVariance = 0.001;
  const measurementVariance = 0.01;

  for (let i = 0; i < minLength; i++) {
    const price1 = ticks1[i]?.price || 0;
    const price2 = ticks2[i]?.price || 0;
    
    if (price2 !== 0) {
      // Kalman prediction
      const predictedState = kalmanState;
      const predictedVariance = kalmanVariance + processVariance;
      
      // Measurement (observed hedge ratio)
      const measurement = price1 / price2;
      
      // Kalman update
      const kalmanGain = predictedVariance / (predictedVariance + measurementVariance);
      kalmanState = predictedState + kalmanGain * (measurement - predictedState);
      kalmanVariance = (1 - kalmanGain) * predictedVariance;
      
      hedgeRatios.push({
        index: i,
        hedgeRatio: kalmanState,
        time: ticks1[i]?.timestamp,
      });
    }
  }

  // Regression scatter data
  const scatterData = [];
  for (let i = 0; i < minLength; i++) {
    scatterData.push({
      x: ticks2[i]?.price || 0,
      y: ticks1[i]?.price || 0,
    });
  }

  const currentHedgeRatio = hedgeRatios.length > 0 ? hedgeRatios[hedgeRatios.length - 1].hedgeRatio : 1.0;

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Kalman Filter & Robust Regression</Typography>
      <Alert severity="info" sx={{ mb: 3 }}>
        Dynamic hedge ratio estimation using Kalman filters. Current hedge ratio: <strong>{currentHedgeRatio.toFixed(4)}</strong>
      </Alert>

      {/* Symbol Selection */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <TextField
            select
            fullWidth
            label="Symbol 1 (Y-axis)"
            value={symbol1}
            onChange={(e) => setSymbol1(e.target.value)}
          >
            {availableSymbols.map((sym) => (
              <MenuItem key={sym} value={sym}>{sym}</MenuItem>
            ))}
          </TextField>
        </Grid>
        <Grid item xs={12} md={6}>
          <TextField
            select
            fullWidth
            label="Symbol 2 (X-axis)"
            value={symbol2}
            onChange={(e) => setSymbol2(e.target.value)}
          >
            {availableSymbols.map((sym) => (
              <MenuItem key={sym} value={sym}>{sym}</MenuItem>
            ))}
          </TextField>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Hedge Ratio Time Series */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Dynamic Hedge Ratio (Kalman Filter)</Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={hedgeRatios}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="index" />
                  <YAxis 
                    domain={[(dataMin: number) => (dataMin * 0.995).toFixed(4), (dataMax: number) => (dataMax * 1.005).toFixed(4)]}
                    tickFormatter={(value) => value.toFixed(4)}
                  />
                  <Tooltip />
                  <Line type="monotone" dataKey="hedgeRatio" stroke="#8884d8" dot={false} strokeWidth={2} name="Hedge Ratio" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Regression Scatter */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Regression Scatter: {symbol1} vs {symbol2}</Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Each point represents a simultaneous price observation. The slope of the best-fit line is the <strong>hedge ratio</strong> ({currentHedgeRatio.toFixed(4)}). Tighter clustering indicates higher R² (stronger relationship). Use longer timeframes (200+ points) for robust regression analysis.
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={scatterData.slice(-100)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="x" 
                    label={{ value: symbol2, position: 'insideBottom', offset: -5 }}
                    domain={[(dataMin: number) => Math.floor(dataMin * 0.999), (dataMax: number) => Math.ceil(dataMax * 1.001)]}
                  />
                  <YAxis 
                    label={{ value: symbol1, angle: -90, position: 'insideLeft' }}
                    domain={[(dataMin: number) => Math.floor(dataMin * 0.999), (dataMax: number) => Math.ceil(dataMax * 1.001)]}
                  />
                  <Tooltip />
                  <Line type="monotone" dataKey="y" stroke="#82ca9d" dot={{ r: 3 }} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export const Liquidity: React.FC = () => {
  const { ticks } = useStore();
  const [symbol, setSymbol] = useState('BTCUSDT');

  const { symbols: availableSymbols } = useSymbols();

  const symbolTicks = ticks.get(symbol) || [];

  // Build volume profile: group by price level
  const volumeProfile: { [price: string]: number } = {};
  let totalVolume = 0;
  const currentPrice = symbolTicks.length > 0 ? symbolTicks[symbolTicks.length - 1].price : 0;
  
  // Use finer granularity: $1 bins for better price resolution
  for (const tick of symbolTicks) {
    const priceLevel = Math.round(tick.price); // Round to nearest $1
    const key = priceLevel.toString();
    volumeProfile[key] = (volumeProfile[key] || 0) + tick.quantity;
    totalVolume += tick.quantity;
  }
  
  // Filter to prices within ±2% of current price for focused view
  const priceRange = currentPrice * 0.02;
  const filteredProfile: { [price: string]: number } = {};
  for (const [price, volume] of Object.entries(volumeProfile)) {
    const p = parseFloat(price);
    if (Math.abs(p - currentPrice) <= priceRange) {
      filteredProfile[price] = volume;
    }
  }

  const profileData = Object.entries(filteredProfile).map(([price, volume]) => ({
    price: parseFloat(price),
    volume,
  })).sort((a, b) => a.price - b.price);

  // Find POC (Point of Control) within the visible range
  const poc = profileData.reduce((max, item) => (item.volume > max.volume ? item : max), { price: currentPrice, volume: 0 });

  // Calculate value area (70% of volume)
  const valueAreaThreshold = totalVolume * 0.7;
  let accumulatedVolume = 0;
  const valueArea = [];
  for (const item of profileData.sort((a, b) => b.volume - a.volume)) {
    if (accumulatedVolume < valueAreaThreshold) {
      valueArea.push(item.price);
      accumulatedVolume += item.volume;
    }
  }

  const valueAreaHigh = Math.max(...valueArea);
  const valueAreaLow = Math.min(...valueArea);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Liquidity Profile</Typography>
      <Alert severity="info" sx={{ mb: 3 }}>
        Volume profile showing liquidity within ±2% of current price (${currentPrice.toFixed(2)}). POC: <strong>${poc.price.toFixed(2)}</strong>, Value Area: <strong>${valueAreaLow.toFixed(2)} - ${valueAreaHigh.toFixed(2)}</strong>
      </Alert>

      {/* Symbol Selection */}
      <TextField
        select
        fullWidth
        label="Symbol"
        value={symbol}
        onChange={(e) => setSymbol(e.target.value)}
        sx={{ mb: 3, maxWidth: 300 }}
      >
        {availableSymbols.map((sym) => (
          <MenuItem key={sym} value={sym}>{sym}</MenuItem>
        ))}
      </TextField>

      <Grid container spacing={3}>
        {/* Metrics */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">Point of Control (POC)</Typography>
              <Typography variant="h5">${poc.price.toFixed(2)}</Typography>
              <Typography variant="caption">Volume: {poc.volume.toFixed(4)}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">Value Area High</Typography>
              <Typography variant="h5">${valueAreaHigh.toFixed(2)}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">Value Area Low</Typography>
              <Typography variant="h5">${valueAreaLow.toFixed(2)}</Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Volume Profile Chart */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Volume Profile (±2% Range)</Typography>
              <Typography variant="caption" color="text.secondary">
                Showing liquidity distribution within ${(currentPrice * 0.98).toFixed(2)} - ${(currentPrice * 1.02).toFixed(2)}
              </Typography>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={profileData} layout="vertical">
                  <XAxis type="number" label={{ value: 'Volume', position: 'insideBottom', offset: -5 }} />
                  <YAxis 
                    type="number" 
                    dataKey="price" 
                    domain={['dataMin', 'dataMax']}
                    tickFormatter={(value) => `$${value.toFixed(2)}`}
                    label={{ value: 'Price Level', angle: -90, position: 'insideLeft' }}
                  />
                  <Tooltip 
                    formatter={(value: number) => [value.toFixed(6), 'Volume']}
                    labelFormatter={(label: number) => `Price: $${label.toFixed(2)}`}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="volume" 
                    stroke="#1976d2" 
                    fill="#1976d2" 
                    strokeWidth={3}
                    dot={{ fill: '#1976d2', r: 3 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export const Microstructure: React.FC = () => {
  const { ticks } = useStore();
  const [symbol, setSymbol] = useState('BTCUSDT');

  const { symbols: availableSymbols } = useSymbols();

  const symbolTicks = ticks.get(symbol) || [];

  // Calculate metrics
  const metrics = [];
  let cumulativeVolume = 0;
  let cumulativePV = 0;

  for (let i = 0; i < symbolTicks.length; i++) {
    const tick = symbolTicks[i];
    cumulativeVolume += tick.quantity;
    cumulativePV += tick.price * tick.quantity;
    
    const vwap = cumulativeVolume > 0 ? cumulativePV / cumulativeVolume : tick.price;
    const vwapDeviation = ((tick.price - vwap) / vwap) * 100;
    
    // Estimate midpoint (simplified - use current price as proxy)
    const midpoint = tick.price;
    const effectiveSpread = 2 * Math.abs(tick.price - midpoint);
    
    metrics.push({
      index: i,
      price: tick.price,
      vwap: vwap,
      vwapDeviation: vwapDeviation,
      effectiveSpread: effectiveSpread,
      volume: tick.quantity,
    });
  }

  const recentMetrics = metrics.slice(-250); // Show last 250 ticks for better timeframe
  const latest = metrics[metrics.length - 1] || { vwap: 0, vwapDeviation: 0, effectiveSpread: 0 };

  // Trade intensity: ticks per minute with proper time labels
  const timestamps = symbolTicks.map(t => t.timestamp);
  const minuteBuckets: { [minute: string]: number } = {};
  for (const ts of timestamps) {
    const minuteKey = new Date(Math.floor(ts / 60000) * 60000).toLocaleTimeString();
    minuteBuckets[minuteKey] = (minuteBuckets[minuteKey] || 0) + 1;
  }
  const intensityData = Object.entries(minuteBuckets).map(([minuteLabel, count]) => ({
    minute: minuteLabel,
    intensity: count,
  })).slice(-30); // Show last 30 minutes
  
  const avgIntensity = intensityData.length > 0 ? intensityData.reduce((sum, d) => sum + d.intensity, 0) / intensityData.length : 0;

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Market Microstructure</Typography>
      <Alert severity="info" sx={{ mb: 3 }}>
        Order flow analysis, VWAP deviation, and trade intensity metrics.
      </Alert>

      {/* Symbol Selection */}
      <TextField
        select
        fullWidth
        label="Symbol"
        value={symbol}
        onChange={(e) => setSymbol(e.target.value)}
        sx={{ mb: 3, maxWidth: 300 }}
      >
        {availableSymbols.map((sym) => (
          <MenuItem key={sym} value={sym}>{sym}</MenuItem>
        ))}
      </TextField>

      <Grid container spacing={3}>
        {/* Metrics */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">VWAP</Typography>
              <Typography variant="h5">${latest.vwap?.toFixed(2) || 'N/A'}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">VWAP Deviation</Typography>
              <Typography variant="h5" color={latest.vwapDeviation > 0 ? 'success.main' : 'error.main'}>
                {latest.vwapDeviation?.toFixed(2) || '0.00'}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">Effective Spread</Typography>
              <Typography variant="h5">${latest.effectiveSpread?.toFixed(2) || 'N/A'}</Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* VWAP Chart */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Price vs VWAP</Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={recentMetrics}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="index" />
                  <YAxis 
                    domain={[(dataMin: number) => Math.floor(dataMin * 0.999), (dataMax: number) => Math.ceil(dataMax * 1.001)]}
                    tickFormatter={(value) => value.toFixed(2)}
                  />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="price" stroke="#8884d8" dot={false} name="Price" />
                  <Line type="monotone" dataKey="vwap" stroke="#82ca9d" dot={false} name="VWAP" strokeDasharray="5 5" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Trade Intensity */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Trade Intensity (Ticks per Minute)</Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Measures trading activity frequency. Higher intensity = more market activity/volatility. Average: <strong>{avgIntensity.toFixed(1)} ticks/min</strong>. Spikes indicate increased order flow.
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={intensityData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="minute" angle={-45} textAnchor="end" height={80} tick={{ fontSize: 10 }} />
                  <YAxis label={{ value: 'Ticks/Minute', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="intensity" stroke="#ff7300" strokeWidth={2} name="Tick Count" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export const Correlation: React.FC = () => {
  const { ticks } = useStore();

  const { symbols: availableSymbols } = useSymbols();

  // Calculate pairwise correlations
  const calculateCorrelation = (prices1: number[], prices2: number[]): number => {
    if (prices1.length < 2 || prices2.length < 2) return 0;
    
    const n = Math.min(prices1.length, prices2.length);
    const p1 = prices1.slice(-n);
    const p2 = prices2.slice(-n);
    
    const mean1 = p1.reduce((a, b) => a + b, 0) / n;
    const mean2 = p2.reduce((a, b) => a + b, 0) / n;
    
    let numerator = 0;
    let denom1 = 0;
    let denom2 = 0;
    
    for (let i = 0; i < n; i++) {
      const diff1 = p1[i] - mean1;
      const diff2 = p2[i] - mean2;
      numerator += diff1 * diff2;
      denom1 += diff1 * diff1;
      denom2 += diff2 * diff2;
    }
    
    if (denom1 === 0 || denom2 === 0) return 0;
    return numerator / Math.sqrt(denom1 * denom2);
  };

  // Build correlation matrix
  const correlationMatrix: { sym1: string; sym2: string; correlation: number }[] = [];
  
  for (let i = 0; i < availableSymbols.length; i++) {
    for (let j = 0; j < availableSymbols.length; j++) {
      const sym1 = availableSymbols[i];
      const sym2 = availableSymbols[j];
      
      const prices1 = (ticks.get(sym1) || []).map(t => t.price);
      const prices2 = (ticks.get(sym2) || []).map(t => t.price);
      
      const corr = i === j ? 1.0 : calculateCorrelation(prices1, prices2);
      
      correlationMatrix.push({
        sym1,
        sym2,
        correlation: corr,
      });
    }
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Correlation Matrix</Typography>
      <Alert severity="info" sx={{ mb: 3 }}>
        Pairwise correlation analysis for all tracked symbols. Values range from -1 (inverse) to +1 (perfect positive).
      </Alert>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Correlation Heatmap</Typography>
              <Box sx={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'center' }}>
                  <thead>
                    <tr>
                      <th style={{ padding: '8px', border: '1px solid #ddd' }}>Symbol</th>
                      {availableSymbols.map(sym => (
                        <th key={sym} style={{ padding: '8px', border: '1px solid #ddd' }}>{sym}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {availableSymbols.map(sym1 => (
                      <tr key={sym1}>
                        <td style={{ padding: '8px', border: '1px solid #ddd', fontWeight: 'bold' }}>{sym1}</td>
                        {availableSymbols.map(sym2 => {
                          const entry = correlationMatrix.find(e => e.sym1 === sym1 && e.sym2 === sym2);
                          const corr = entry?.correlation || 0;
                          const color = corr > 0.7 ? '#4caf50' : corr > 0.3 ? '#ffeb3b' : corr > -0.3 ? '#fff' : '#f44336';
                          return (
                            <td key={sym2} style={{ 
                              padding: '8px', 
                              border: '1px solid #ddd', 
                              backgroundColor: color,
                              color: Math.abs(corr) > 0.5 ? '#000' : '#666'
                            }}>
                              {corr.toFixed(2)}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Pairwise Details */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Pairwise Correlations</Typography>
              <Stack spacing={1}>
                {correlationMatrix
                  .filter(e => e.sym1 !== e.sym2)
                  .slice(0, 6)
                  .map((entry, idx) => (
                    <Box key={idx} display="flex" justifyContent="space-between" alignItems="center">
                      <Typography variant="body2">{entry.sym1} ↔ {entry.sym2}</Typography>
                      <Typography variant="body2" fontWeight="bold" color={entry.correlation > 0.5 ? 'success.main' : 'text.secondary'}>
                        {entry.correlation.toFixed(3)}
                      </Typography>
                    </Box>
                  ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export const TimeSeriesTable: React.FC = () => {
  const { ticks } = useStore();
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);

  const { symbols: availableSymbols } = useSymbols();

  const symbolTicks = ticks.get(symbol) || [];
  const displayTicks = symbolTicks.slice().reverse().slice(page * rowsPerPage, (page + 1) * rowsPerPage);

  const handleExportCSV = () => {
    const headers = ['Timestamp', 'Symbol', 'Price', 'Quantity'];
    const rows = symbolTicks.map(tick => [
      new Date(tick.timestamp).toISOString(),
      tick.symbol,
      tick.price.toFixed(2),
      tick.quantity.toFixed(4),
    ]);
    
    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${symbol}_ticks_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportJSON = () => {
    const json = JSON.stringify(symbolTicks, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${symbol}_ticks_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Time Series Data Table</Typography>
      <Alert severity="info" sx={{ mb: 3 }}>
        Comprehensive data table with CSV/JSON export. Showing {symbolTicks.length} total ticks for {symbol}.
      </Alert>

      {/* Symbol Selection and Export */}
      <Stack direction="row" spacing={2} sx={{ mb: 3 }} alignItems="center">
        <TextField
          select
          label="Symbol"
          value={symbol}
          onChange={(e) => {
            setSymbol(e.target.value);
            setPage(0);
          }}
          sx={{ minWidth: 200 }}
        >
          {availableSymbols.map((sym) => (
            <MenuItem key={sym} value={sym}>{sym}</MenuItem>
          ))}
        </TextField>
        
        <Button variant="contained" onClick={handleExportCSV} disabled={symbolTicks.length === 0}>
          Export CSV
        </Button>
        <Button variant="contained" onClick={handleExportJSON} disabled={symbolTicks.length === 0}>
          Export JSON
        </Button>
      </Stack>

      <Card>
        <CardContent>
          <Box sx={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: 'rgba(0, 0, 0, 0.04)' }}>
                  <th style={{ padding: '12px', border: '1px solid rgba(224, 224, 224, 1)', textAlign: 'left', color: 'inherit' }}>Timestamp</th>
                  <th style={{ padding: '12px', border: '1px solid rgba(224, 224, 224, 1)', textAlign: 'left', color: 'inherit' }}>Symbol</th>
                  <th style={{ padding: '12px', border: '1px solid rgba(224, 224, 224, 1)', textAlign: 'right', color: 'inherit' }}>Price</th>
                  <th style={{ padding: '12px', border: '1px solid rgba(224, 224, 224, 1)', textAlign: 'right', color: 'inherit' }}>Quantity</th>
                </tr>
              </thead>
              <tbody>
                {displayTicks.map((tick, idx) => (
                  <tr key={idx} style={{ backgroundColor: idx % 2 === 0 ? 'rgba(0, 0, 0, 0.02)' : 'transparent' }}>
                    <td style={{ padding: '8px', border: '1px solid rgba(224, 224, 224, 1)', color: 'inherit' }}>
                      {new Date(tick.timestamp).toLocaleString()}
                    </td>
                    <td style={{ padding: '8px', border: '1px solid rgba(224, 224, 224, 1)', color: 'inherit' }}>{tick.symbol}</td>
                    <td style={{ padding: '8px', border: '1px solid rgba(224, 224, 224, 1)', textAlign: 'right', color: 'inherit' }}>
                      ${tick.price.toFixed(2)}
                    </td>
                    <td style={{ padding: '8px', border: '1px solid rgba(224, 224, 224, 1)', textAlign: 'right', color: 'inherit' }}>
                      {tick.quantity.toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Box>
          
          {/* Pagination */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Showing {page * rowsPerPage + 1} - {Math.min((page + 1) * rowsPerPage, symbolTicks.length)} of {symbolTicks.length}
            </Typography>
            <Stack direction="row" spacing={1}>
              <Button 
                size="small" 
                onClick={() => setPage(Math.max(0, page - 1))} 
                disabled={page === 0}
              >
                Previous
              </Button>
              <Button 
                size="small" 
                onClick={() => setPage(page + 1)} 
                disabled={(page + 1) * rowsPerPage >= symbolTicks.length}
              >
                Next
              </Button>
            </Stack>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};
