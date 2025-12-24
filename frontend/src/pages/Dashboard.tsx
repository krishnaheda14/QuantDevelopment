import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Stack,
  Chip,
  Paper,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  DialogContentText,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  ShowChart,
  Notifications,
  Speed,
  Timeline,
  InfoOutlined,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import ConnectionStatus from '@/components/ConnectionStatus';
import { useStore } from '@/store';
import api from '@/services/api';
import { debug, info } from '@/types';

const COMPONENT_NAME = 'Dashboard';

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color?: string;
  subtitle?: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  icon,
  color = 'primary.main',
  subtitle,
  trend,
  trendValue,
}) => {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Stack spacing={2}>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box sx={{ color }}>{icon}</Box>
            <Typography variant="caption" color="text.secondary">
              {title}
            </Typography>
          </Box>
          
          <Typography variant="h4" component="div" fontWeight="bold">
            {value}
          </Typography>

          {subtitle && (
            <Typography variant="body2" color="text.secondary">
              {subtitle}
            </Typography>
          )}

          {trend && trendValue && (
            <Box display="flex" alignItems="center" gap={0.5}>
              {trend === 'up' && <TrendingUp color="success" fontSize="small" />}
              {trend === 'down' && <TrendingDown color="error" fontSize="small" />}
              <Typography
                variant="caption"
                color={trend === 'up' ? 'success.main' : trend === 'down' ? 'error.main' : 'text.secondary'}
              >
                {trendValue}
              </Typography>
            </Box>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
};

export const Dashboard: React.FC = () => {
  const [debugOpen, setDebugOpen] = useState(false)
  const [debugPayload, setDebugPayload] = useState<any>(null)
  const [debugLoading, setDebugLoading] = useState(false)
  const [metricsInfoOpen, setMetricsInfoOpen] = useState(false)
  const { selectedSymbol1, selectedSymbol2, ticks, ohlcBars, alerts, settings } = useStore();

  debug(COMPONENT_NAME, 'Rendering dashboard', {
    symbol1: selectedSymbol1,
    symbol2: selectedSymbol2,
    tickCount: ticks.size,
    barCount: ohlcBars.size,
    alertCount: alerts.length,
  });

  // Fetch health status
  const { data: healthData, isLoading: healthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: api.getHealth,
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  // Fetch spread analysis if symbols selected
  const { data: spreadData, isLoading: spreadLoading } = useQuery({
    queryKey: ['spread', selectedSymbol1, selectedSymbol2, settings.aggregationInterval, settings.lookbackPeriod],
    queryFn: () => api.getSpreadAnalysis(selectedSymbol1!, selectedSymbol2!, settings.lookbackPeriod, settings.aggregationInterval),
    enabled: !!selectedSymbol1 && !!selectedSymbol2,
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  useEffect(() => {
    info(COMPONENT_NAME, 'Dashboard mounted');
    return () => {
      info(COMPONENT_NAME, 'Dashboard unmounted');
    };
  }, []);

  useEffect(() => {
    if (healthData) {
      debug(COMPONENT_NAME, 'Health data received', healthData);
    }
  }, [healthData]);

  useEffect(() => {
    if (spreadData) {
      debug(COMPONENT_NAME, 'Spread data received', spreadData);
    }
  }, [spreadData]);

  // Get latest ticks for selected symbols
  const getLatestTick = (symbol: string | null) => {
    if (!symbol) return null;
    const symbolTicks = ticks.get(symbol);
    if (!symbolTicks || symbolTicks.length === 0) return null;
    return symbolTicks[symbolTicks.length - 1];
  };

  const tick1 = getLatestTick(selectedSymbol1);
  const tick2 = getLatestTick(selectedSymbol2);

  // Count alerts by severity
  const criticalAlerts = alerts.filter(a => a.severity === 'error').length;
  const warningAlerts = alerts.filter(a => a.severity === 'warning').length;

  return (
    <Box>
      {/* Loading indicator */}
      {(healthLoading || spreadLoading) && <LinearProgress sx={{ mb: 2 }} />}

      <Grid container spacing={3}>
        {/* Connection Status */}
        <Grid item xs={12} md={6} lg={4}>
          <ConnectionStatus />
        </Grid>

        {/* Quick Metrics */}
        <Grid item xs={12} md={6} lg={4}>
          <MetricCard
            title="Active Symbols"
            value={healthData?.active_symbols || 0}
            icon={<ShowChart fontSize="large" />}
            color="primary.main"
            subtitle="Trading pairs monitored"
          />
        </Grid>

        <Grid item xs={12} md={6} lg={4}>
          <MetricCard
            title="Total Alerts"
            value={alerts.length}
            icon={<Notifications fontSize="large" />}
            color={criticalAlerts > 0 ? 'error.main' : warningAlerts > 0 ? 'warning.main' : 'success.main'}
            subtitle={`${criticalAlerts} critical, ${warningAlerts} warnings`}
          />
        </Grid>

        {/* Real-time Prices */}
        {selectedSymbol1 && (
          <Grid item xs={12} md={6} lg={4}>
            <Card>
              <CardContent>
                <Stack spacing={1.5}>
                  <Box display="flex" alignItems="center" justifyContent="space-between">
                    <Typography variant="h6">{selectedSymbol1}</Typography>
                    <Chip label="Symbol 1" size="small" color="primary" />
                  </Box>
                  
                  {tick1 ? (
                    <>
                      <Typography variant="h4" fontWeight="bold" color="primary.main">
                        ${typeof tick1.price === 'number' ? tick1.price.toFixed(2) : 'N/A'}
                      </Typography>
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="caption" color="text.secondary">
                          Qty: {typeof tick1.quantity === 'number' ? tick1.quantity.toFixed(4) : 'N/A'}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {new Date(tick1.timestamp).toLocaleTimeString()}
                        </Typography>
                      </Box>
                    </>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No data available
                    </Typography>
                  )}
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        )}

        {selectedSymbol2 && (
          <Grid item xs={12} md={6} lg={4}>
            <Card>
              <CardContent>
                <Stack spacing={1.5}>
                  <Box display="flex" alignItems="center" justifyContent="space-between">
                    <Typography variant="h6">{selectedSymbol2}</Typography>
                    <Chip label="Symbol 2" size="small" color="secondary" />
                  </Box>
                  
                  {tick2 ? (
                    <>
                      <Typography variant="h4" fontWeight="bold" color="secondary.main">
                        ${typeof tick2.price === 'number' ? tick2.price.toFixed(2) : 'N/A'}
                      </Typography>
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="caption" color="text.secondary">
                          Qty: {typeof tick2.quantity === 'number' ? tick2.quantity.toFixed(4) : 'N/A'}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {new Date(tick2.timestamp).toLocaleTimeString()}
                        </Typography>
                      </Box>
                    </>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No data available
                    </Typography>
                  )}
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Spread Metrics */}
        {spreadData && (
          <>
            <Grid item xs={12}>
              <Box display="flex" alignItems="center" gap={1}>
                <Typography variant="h6">Spread Analysis Metrics</Typography>
                <IconButton size="small" onClick={() => setMetricsInfoOpen(true)} aria-label="info">
                  <InfoOutlined fontSize="small" />
                </IconButton>
              </Box>
            </Grid>
            <Grid item xs={12} md={6} lg={4}>
              <MetricCard
                title="Hedge Ratio"
                value={typeof spreadData.hedge_ratio === 'number' ? spreadData.hedge_ratio.toFixed(4) : 'N/A'}
                icon={<Speed fontSize="large" />}
                color="info.main"
                subtitle="OLS regression slope"
              />
            </Grid>

            <Grid item xs={12} md={6} lg={4}>
              <MetricCard
                title="R-Squared"
                value={typeof spreadData.r_squared === 'number' ? spreadData.r_squared.toFixed(4) : 'N/A'}
                icon={<Timeline fontSize="large" />}
                color="success.main"
                subtitle="Goodness of fit"
              />
            </Grid>

            <Grid item xs={12} md={6} lg={4}>
              <Card>
                <CardContent>
                  <Stack spacing={1.5}>
                    <Typography variant="caption" color="text.secondary">
                      Current Signal
                    </Typography>
                    <Chip
                      label={spreadData.signal}
                      color={
                        spreadData.signal === 'LONG'
                          ? 'success'
                          : spreadData.signal === 'SHORT'
                          ? 'error'
                          : 'default'
                      }
                      sx={{ fontSize: '1rem', py: 2 }}
                    />
                    <Typography variant="body2" color="text.secondary" textAlign="center">
                      Z-Score: {(() => {
                        const z = spreadData.z_score ?? spreadData.zscore ?? spreadData.current_zscore
                        return typeof z === 'number' ? z.toFixed(2) : 'N/A'
                      })()}
                    </Typography>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          </>
        )}

        {/* Recent Alerts */}
        {alerts.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Recent Alerts
                </Typography>
                <Stack spacing={1} mt={2}>
                  {alerts.slice(0, 5).map((alert) => (
                    <Paper
                      key={alert.id}
                      sx={{
                        p: 2,
                        borderLeft: 4,
                        borderColor:
                          alert.severity === 'error'
                            ? 'error.main'
                            : alert.severity === 'warning'
                            ? 'warning.main'
                            : 'info.main',
                      }}
                    >
                      <Box display="flex" alignItems="center" justifyContent="space-between">
                        <Box flex={1}>
                          <Typography variant="subtitle2" fontWeight="bold">
                            {alert.type.toUpperCase()}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {alert.message}
                          </Typography>
                          {alert.value !== undefined && (
                            <Typography variant="caption" color="text.secondary">
                              Value: {alert.value.toFixed(4)}
                            </Typography>
                          )}
                        </Box>
                        <Typography variant="caption" color="text.secondary" ml={2}>
                          {new Date(alert.timestamp).toLocaleString()}
                        </Typography>
                      </Box>
                    </Paper>
                  ))}
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* System Status */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Information
              </Typography>
              <Box display="flex" justifyContent="flex-end" mb={1}>
                <Button size="small" variant="outlined" onClick={async () => {
                  try {
                    setDebugLoading(true)
                    const [health, sys, redis, services] = await Promise.all([
                      api.getHealth(),
                      api.getDebugSystemStatus(),
                      api.getDebugRedisStatus(),
                      api.getDebugServicesStatus(),
                    ])
                    setDebugPayload({ health, sys, redis, services })
                    setDebugOpen(true)
                  } catch (e: any) {
                    setDebugPayload({ error: e.message || String(e) })
                    setDebugOpen(true)
                  } finally {
                    setDebugLoading(false)
                  }
                }}>
                  API Debug
                </Button>
              </Box>
              <Grid container spacing={2} mt={1}>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="caption" color="text.secondary">
                      Database
                    </Typography>
                    <Typography variant="h6" color={healthData?.database ? 'success.main' : 'error.main'}>
                      {healthData?.database ? 'Connected' : 'Disconnected'}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="caption" color="text.secondary">
                      WebSocket
                    </Typography>
                    <Typography variant="h6" color={healthData?.websocket ? 'success.main' : 'error.main'}>
                      {healthData?.websocket ? 'Active' : 'Inactive'}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="caption" color="text.secondary">
                      Ticks Stored
                    </Typography>
                    <Typography variant="h6">{ticks.size.toLocaleString()}</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="caption" color="text.secondary">
                      OHLC Bars
                    </Typography>
                    <Typography variant="h6">{ohlcBars.size.toLocaleString()}</Typography>
                  </Paper>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Getting Started */}
        {!selectedSymbol1 && !selectedSymbol2 && (
          <Grid item xs={12}>
            <Card sx={{ bgcolor: 'primary.dark', color: 'primary.contrastText' }}>
              <CardContent>
                <Typography variant="h5" gutterBottom>
                  Welcome to GEMSCAP Quant Analytics
                </Typography>
                <Typography variant="body1" paragraph>
                  Get started by selecting trading symbols in the <strong>Spread Analysis</strong> tab.
                </Typography>
                <Typography variant="body2">
                  • Monitor real-time tick data and OHLC bars
                  <br />
                  • Analyze statistical relationships between pairs
                  <br />
                  • Execute sophisticated pairs trading strategies
                  <br />
                  • Track performance with comprehensive backtesting
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
      {debugPayload && (
        <Dialog open={debugOpen} onClose={() => setDebugOpen(false)} maxWidth="md" fullWidth>
          <DialogTitle>API Debug {debugLoading ? '(loading...)' : ''}</DialogTitle>
          <DialogContent dividers>
            <pre style={{ whiteSpace: 'pre-wrap', fontSize: 12 }}>{JSON.stringify(debugPayload, null, 2)}</pre>
          </DialogContent>
          <DialogActions>
            <Button size="small" onClick={() => { navigator.clipboard?.writeText(JSON.stringify(debugPayload, null, 2)) }}>Copy</Button>
            <Button size="small" onClick={() => setDebugOpen(false)}>Close</Button>
          </DialogActions>
        </Dialog>
      )}
      
      {/* Metrics Info Dialog */}
      <Dialog open={metricsInfoOpen} onClose={() => setMetricsInfoOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Spread Metrics — Detailed Explanation</DialogTitle>
        <DialogContent dividers>
          <DialogContentText component="div">
            <Typography variant="subtitle1" gutterBottom><strong>What these metrics mean</strong></Typography>
            <Typography variant="body2" paragraph>
              <strong>Hedge Ratio:</strong> OLS regression slope (Symbol2 = alpha + hedge_ratio × Symbol1). Determines position sizing for the spread.
            </Typography>
            <Typography variant="body2" paragraph>
              <strong>R-Squared:</strong> Goodness-of-fit (0-1). Measures how much variance in Symbol2 is explained by Symbol1. Higher R² = stronger relationship.
            </Typography>
            <Typography variant="body2" paragraph>
              <strong>Z-Score:</strong> Standardized spread deviation: (spread - mean) / std. Shows how many std deviations away from the mean. Trading signals trigger at thresholds (typically ±2).
            </Typography>

            <Typography variant="subtitle1" gutterBottom><strong>Current Values</strong></Typography>
            <Typography variant="body2">
              Hedge Ratio: <strong>{spreadData?.hedge_ratio?.toFixed(4) ?? 'N/A'}</strong>
            </Typography>
            <Typography variant="body2">
              R-Squared: <strong>{spreadData?.r_squared?.toFixed(4) ?? 'N/A'}</strong> ({((spreadData?.r_squared ?? 0) * 100).toFixed(2)}%)
            </Typography>
            <Typography variant="body2" paragraph>
              Z-Score: <strong>{(spreadData?.z_score ?? spreadData?.current_zscore ?? 0).toFixed(2)}</strong>
            </Typography>

            <Typography variant="subtitle1" gutterBottom><strong>Are they dynamic?</strong></Typography>
            <Typography variant="body2" paragraph>
              <strong>Yes</strong> — metrics are recomputed every <strong>10 seconds</strong> from the most recent {settings.lookbackPeriod} minutes of OHLC data. The backend performs OLS regression and recalculates spread statistics on each request.
            </Typography>

            <Typography variant="subtitle1" gutterBottom><strong>How to interpret</strong></Typography>
            <Typography variant="body2">
              • <strong>Hedge Ratio {'>'} 1:</strong> Symbol1 moves more than Symbol2 (per unit)
              <br />• <strong>R² {'>'} 0.8:</strong> Strong fit, reliable spread
              <br />• <strong>|Z-Score| {'>'} 2:</strong> Spread is stretched → potential mean reversion
              <br />• <strong>LONG signal:</strong> Z {'<'} -2 → spread undervalued, buy the spread
              <br />• <strong>SHORT signal:</strong> Z {'>'} 2 → spread overvalued, sell the spread
            </Typography>
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMetricsInfoOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
