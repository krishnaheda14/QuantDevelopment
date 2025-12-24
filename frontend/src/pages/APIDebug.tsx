import React, { useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Paper,
  Divider,
  TextField,
  MenuItem,
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Stack,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  ExpandMore,
  PlayArrow,
  ContentCopy,
  CheckCircle,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useStore } from '@/store';
import { debug } from '@/types';
import api from '@/services/api';

const COMPONENT_NAME = 'APIDebug';

interface APIEndpoint {
  name: string;
  method: 'GET' | 'POST';
  path: string;
  tab: string;
  params?: Record<string, string>;
  body?: Record<string, any>;
  description: string;
}

const API_ENDPOINTS: APIEndpoint[] = [
  // Dashboard & Health
  {
    name: 'Health Check',
    method: 'GET',
    path: '/health',
    tab: 'Dashboard',
    description: 'System health status, uptime, tick count, service status',
  },
  {
    name: 'Available Symbols',
    method: 'GET',
    path: '/symbols',
    tab: 'Dashboard',
    description: 'List of active trading symbols',
  },
  
  // Spread Analysis
  {
    name: 'Spread Analysis',
    method: 'GET',
    path: '/api/analytics/spread',
    tab: 'Spread Analysis',
    params: { symbol1: 'BTCUSDT', symbol2: 'ETHUSDT', lookback: '500' },
    description: 'OLS regression, spread, z-score, hedge ratio, R-squared, trading signal',
  },
  {
    name: 'OLS Regression',
    method: 'POST',
    path: '/api/analytics/ols',
    tab: 'Spread Analysis',
    body: { symbol1: 'BTCUSDT', symbol2: 'ETHUSDT', lookback: 500 },
    description: 'Ordinary Least Squares regression between two symbols',
  },
  
  // Strategy Signals
  {
    name: 'Technical Indicators',
    method: 'GET',
    path: '/api/analytics/indicators',
    tab: 'Strategy Signals',
    params: { symbol: 'BTCUSDT', lookback: '200' },
    description: 'RSI, MACD, Bollinger Bands with configurable parameters',
  },
  
  // Statistical Tests
  {
    name: 'ADF Test (Symbol 1)',
    method: 'POST',
    path: '/api/analytics/adf',
    tab: 'Statistical Tests',
    body: { symbol: 'BTCUSDT', lookback: 500 },
    description: 'Augmented Dickey-Fuller test for stationarity',
  },
  {
    name: 'ADF Test (Symbol 2)',
    method: 'POST',
    path: '/api/analytics/adf',
    tab: 'Statistical Tests',
    body: { symbol: 'ETHUSDT', lookback: 500 },
    description: 'Augmented Dickey-Fuller test for stationarity',
  },
  {
    name: 'Cointegration Test',
    method: 'GET',
    path: '/api/analytics/cointegration',
    tab: 'Statistical Tests',
    params: { symbol1: 'BTCUSDT', symbol2: 'ETHUSDT', lookback: '500', interval: '1s' },
    description: 'Engle-Granger cointegration test, statistic, p-value, interpretation',
  },
  
  // Backtesting
  {
    name: 'Backtest Z-Score Strategy',
    method: 'POST',
    path: '/api/analytics/backtest',
    tab: 'Backtesting',
    body: {
      symbol1: 'BTCUSDT',
      symbol2: 'ETHUSDT',
      lookback: 500,
      strategy: 'zscore',
      entry_threshold: 2.0,
      exit_threshold: 0.5,
      initial_capital: 100000,
      trade_size: 1.0,
      commission: 0.001,
      slippage: 0.0005,
    },
    description: 'Backtest with equity curve, trades, Sharpe ratio, max drawdown, win rate',
  },
  {
    name: 'Backtest RSI Strategy',
    method: 'POST',
    path: '/api/analytics/backtest',
    tab: 'Backtesting',
    body: {
      symbol1: 'BTCUSDT',
      symbol2: 'ETHUSDT',
      lookback: 500,
      strategy: 'rsi',
      params: { rsi_period: 14, rsi_buy: 30, rsi_sell: 70 },
      initial_capital: 100000,
      trade_size: 1.0,
      commission: 0.001,
    },
    description: 'RSI-based strategy backtest with indicator parameters',
  },
  
  // Alerts
  {
    name: 'Get Active Alerts',
    method: 'GET',
    path: '/api/alerts',
    tab: 'Alerts',
    description: 'List of all active alerts with metadata',
  },
  
  // Quick Compare (OHLC data)
  {
    name: 'OHLC Data (Symbol 1)',
    method: 'GET',
    path: '/api/ohlc/BTCUSDT',
    tab: 'Quick Compare',
    params: { interval: '1m', limit: '500' },
    description: 'OHLC bars for charting and analysis',
  },
  {
    name: 'OHLC Data (Symbol 2)',
    method: 'GET',
    path: '/api/ohlc/ETHUSDT',
    tab: 'Quick Compare',
    params: { interval: '1m', limit: '500' },
    description: 'OHLC bars for charting and analysis',
  },
  
  // Export
  {
    name: 'Export Full Analytics',
    method: 'GET',
    path: '/api/export/full',
    tab: 'Export',
    params: { symbol1: 'BTCUSDT', symbol2: 'ETHUSDT', lookback: '500' },
    description: 'Complete analytics bundle: OLS, spread, ADF, cointegration, indicators',
  },
];

export const APIDebug: React.FC = () => {
  const { selectedSymbol1, selectedSymbol2, settings } = useStore();
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [results, setResults] = useState<Record<string, any>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [selectedTab, setSelectedTab] = useState<string>('All');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  debug(COMPONENT_NAME, 'Rendering API Debug', { selectedTab });

  const tabs = ['All', 'Dashboard', 'Spread Analysis', 'Strategy Signals', 'Statistical Tests', 'Backtesting', 'Alerts', 'Quick Compare', 'Export'];

  const executeEndpoint = async (endpoint: APIEndpoint) => {
    const key = `${endpoint.method}:${endpoint.path}`;
    setLoading((prev) => ({ ...prev, [key]: true }));
    setErrors((prev) => ({ ...prev, [key]: '' }));

    try {
      let response;
      const url = endpoint.path;

      if (endpoint.method === 'GET') {
        // Build params but do NOT overwrite explicit endpoint params (respect their provided values).
        const params: Record<string, string> = {};
        if (endpoint.params) {
          Object.assign(params, endpoint.params);
        }
        // Fill in missing dynamic values from current selections
        if (!params.symbol1) params.symbol1 = selectedSymbol1 || 'BTCUSDT';
        if (!params.symbol2) params.symbol2 = selectedSymbol2 || 'ETHUSDT';
        if (!params.lookback) params.lookback = String(settings.lookbackPeriod);
        if (!params.symbol && selectedSymbol1) params.symbol = selectedSymbol1;
        // Add cache-busting timestamp to avoid any cached responses
        params._ts = String(Date.now());

        const queryString = new URLSearchParams(params).toString();
        response = await fetch(`http://localhost:8000${url}?${queryString}`, { cache: 'no-store' });
      } else {
        // POST
        const body = { ...endpoint.body };
        if (body.symbol1 === 'BTCUSDT') body.symbol1 = selectedSymbol1 || 'BTCUSDT';
        if (body.symbol2 === 'ETHUSDT') body.symbol2 = selectedSymbol2 || 'ETHUSDT';
        if (body.lookback === undefined || body.lookback === null) body.lookback = settings.lookbackPeriod;
        if (body.symbol === 'BTCUSDT') body.symbol = selectedSymbol1 || 'BTCUSDT';

        response = await fetch(`http://localhost:8000${url}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
          cache: 'no-store'
        });
      }

      const data = await response.json();
      setResults((prev) => ({ ...prev, [key]: data }));
    } catch (error: any) {
      setErrors((prev) => ({ ...prev, [key]: error.message }));
    } finally {
      setLoading((prev) => ({ ...prev, [key]: false }));
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredEndpoints = selectedTab === 'All' 
    ? API_ENDPOINTS 
    : API_ENDPOINTS.filter((e) => e.tab === selectedTab);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        API Debug & Validation
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Test and inspect all backend API endpoints. Use this tab to validate data flow and explain system internals to examiners.
      </Typography>

      {/* Tab Filter */}
      <Box mb={3}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Filter by Tab:
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {tabs.map((tab) => (
              <Chip
                key={tab}
                label={tab}
                onClick={() => setSelectedTab(tab)}
                color={selectedTab === tab ? 'primary' : 'default'}
                variant={selectedTab === tab ? 'filled' : 'outlined'}
              />
            ))}
          </Stack>
        </Paper>
      </Box>

      {/* Endpoints List */}
      <Grid container spacing={2}>
        {filteredEndpoints.map((endpoint) => {
          const key = `${endpoint.method}:${endpoint.path}`;
          const isLoading = loading[key];
          const result = results[key];
          const error = errors[key];

          return (
            <Grid item xs={12} key={key}>
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Box display="flex" alignItems="center" gap={2} width="100%">
                    <Chip
                      label={endpoint.method}
                      size="small"
                      color={endpoint.method === 'GET' ? 'info' : 'warning'}
                    />
                    <Typography variant="body1" fontWeight="bold">
                      {endpoint.name}
                    </Typography>
                    <Chip label={endpoint.tab} size="small" variant="outlined" />
                    {result && <CheckCircle color="success" fontSize="small" />}
                    {error && <ErrorIcon color="error" fontSize="small" />}
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Stack spacing={2}>
                    {/* Description */}
                    <Alert severity="info" icon={false}>
                      <Typography variant="body2">{endpoint.description}</Typography>
                    </Alert>

                    {/* Endpoint Details */}
                    <Paper sx={{ p: 2, bgcolor: '#1a1a2e' }}>
                      <Typography variant="caption" color="text.secondary">
                        Endpoint
                      </Typography>
                      <Typography variant="body2" fontFamily="monospace">
                        {endpoint.method} {endpoint.path}
                      </Typography>
                      {endpoint.params && (
                        <Box mt={1}>
                          <Typography variant="caption" color="text.secondary">
                            Query Params
                          </Typography>
                          <Typography variant="body2" fontFamily="monospace">
                            {JSON.stringify(endpoint.params, null, 2)}
                          </Typography>
                        </Box>
                      )}
                      {endpoint.body && (
                        <Box mt={1}>
                          <Typography variant="caption" color="text.secondary">
                            Request Body
                          </Typography>
                          <Typography variant="body2" fontFamily="monospace">
                            {JSON.stringify(endpoint.body, null, 2)}
                          </Typography>
                        </Box>
                      )}
                    </Paper>

                    {/* Execute Button */}
                    <Button
                      variant="contained"
                      onClick={() => executeEndpoint(endpoint)}
                      disabled={isLoading}
                      startIcon={isLoading ? <CircularProgress size={20} /> : <PlayArrow />}
                    >
                      {isLoading ? 'Running...' : 'Execute'}
                    </Button>

                    {/* Result */}
                    {result && (
                      <Paper sx={{ p: 2, bgcolor: '#0f1115', maxHeight: 400, overflow: 'auto' }}>
                        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                          <Typography variant="subtitle2" color="success.main">
                            ✓ Response
                          </Typography>
                          <Tooltip title={copiedId === key ? 'Copied!' : 'Copy to clipboard'}>
                            <IconButton
                              size="small"
                              onClick={() => copyToClipboard(JSON.stringify(result, null, 2), key)}
                            >
                              {copiedId === key ? <CheckCircle fontSize="small" /> : <ContentCopy fontSize="small" />}
                            </IconButton>
                          </Tooltip>
                        </Box>
                        <pre style={{ color: '#00ff88', fontSize: 12, margin: 0, whiteSpace: 'pre-wrap' }}>
                          {JSON.stringify(result, null, 2)}
                        </pre>
                      </Paper>
                    )}

                    {/* Error */}
                    {error && (
                      <Alert severity="error">
                        <Typography variant="body2">{error}</Typography>
                      </Alert>
                    )}
                  </Stack>
                </AccordionDetails>
              </Accordion>
            </Grid>
          );
        })}
      </Grid>

      {/* Tips */}
      <Box mt={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              💡 Usage Tips
            </Typography>
            <Typography variant="body2" paragraph>
              • Use this tab to demonstrate data flow during project presentations
              <br />
              • Copy responses to show exact payload structures
              <br />
              • Filter by tab to focus on specific feature areas
              <br />
              • All endpoints use current symbol selections and lookback settings
              <br />
              • Endpoints are color-coded: <Chip label="GET" size="small" color="info" /> = read-only, <Chip label="POST" size="small" color="warning" /> = computational
            </Typography>
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
};

export default APIDebug;
