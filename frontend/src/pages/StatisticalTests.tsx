import React from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Alert,
  CircularProgress,
  Paper,
  Chip,
  Divider,
  Stack,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  TextField,
} from '@mui/material';
import { FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import { useStore } from '@/store';
import api from '@/services/api';
import { debug, info as logInfo } from '@/types';
import { useQuery } from '@tanstack/react-query';
import { CheckCircle, Cancel, Info, InfoOutlined } from '@mui/icons-material';

const COMPONENT_NAME = 'StatisticalTests';

export const StatisticalTests: React.FC = () => {
  const { selectedSymbol1, selectedSymbol2, settings, setLookbackMinutes } = useStore();
  const [showAdfDebug, setShowAdfDebug] = React.useState(false);
  const [showCointegDebug, setShowCointegDebug] = React.useState(false);

  debug(COMPONENT_NAME, 'Rendering statistical tests', {
    symbol1: selectedSymbol1,
    symbol2: selectedSymbol2,
  });

  // Fetch ADF test results with rolling window analysis (30-bar window, step 5)
  const { data: adfData, isLoading: adfLoading, error: adfError } = useQuery({
    queryKey: ['adf', selectedSymbol1, selectedSymbol2, settings.lookbackPeriod, settings.aggregationInterval],
    queryFn: () => api.getADFTest(selectedSymbol1!, selectedSymbol2!, settings.lookbackPeriod, settings.aggregationInterval, 30, 5),
    enabled: !!selectedSymbol1 && !!selectedSymbol2,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch cointegration test results
  const { data: cointegData, isLoading: cointegLoading, error: cointegError } = useQuery({
    queryKey: ['cointegration', selectedSymbol1, selectedSymbol2, settings.lookbackPeriod, settings.aggregationInterval, settings.apiInterval],
    queryFn: () => api.getCointegration(selectedSymbol1!, selectedSymbol2!, settings.lookbackPeriod, settings.apiInterval || settings.aggregationInterval),
    enabled: !!selectedSymbol1 && !!selectedSymbol2,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  React.useEffect(() => {
    if (adfData) {
      logInfo(COMPONENT_NAME, 'ADF test results', adfData);
    }
    if (cointegData) {
      logInfo(COMPONENT_NAME, 'Cointegration test results', cointegData);
    }
  }, [adfData, cointegData]);

  const isLoading = adfLoading || cointegLoading;
  const hasError = adfError || cointegError;

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Statistical Tests - Stationarity & Cointegration
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Augmented Dickey-Fuller (ADF) test for stationarity and cointegration analysis for pairs trading.
      </Typography>

      {/* Timeframe and API Interval selectors */}
      <Box mb={2} display="flex" gap={2} flexWrap="wrap" alignItems="center">
        <FormControl sx={{ minWidth: 160 }}>
          <InputLabel id="st-timeframe-label">Timeframe</InputLabel>
          <Select
            labelId="st-timeframe-label"
            value={settings.aggregationInterval}
            label="Timeframe"
            onChange={(e) => useStore.getState().setAggregationInterval(e.target.value as string)}
          >
            <MenuItem value="1s">1s</MenuItem>
            <MenuItem value="1m">1m</MenuItem>
            <MenuItem value="5m">5m</MenuItem>
            <MenuItem value="15m">15m</MenuItem>
            <MenuItem value="1h">1h</MenuItem>
            <MenuItem value="4h">4h</MenuItem>
            <MenuItem value="1d">1d</MenuItem>
          </Select>
        </FormControl>

        <FormControl sx={{ minWidth: 160 }}>
          <InputLabel id="st-api-interval-label">API Interval</InputLabel>
          <Select
            labelId="st-api-interval-label"
            value={settings.apiInterval}
            label="API Interval"
            onChange={(e) => useStore.getState().setApiInterval(e.target.value as string)}
          >
            <MenuItem value="1s">1s</MenuItem>
            <MenuItem value="1m">1m</MenuItem>
            <MenuItem value="5m">5m</MenuItem>
            <MenuItem value="1h">1h</MenuItem>
          </Select>
        </FormControl>
        <TextField
          label="Lookback (bars)"
          type="number"
          size="small"
          value={settings.lookbackPeriod}
          onChange={(e) => {
            const v = Math.max(1, Math.min(1440, Number(e.target.value) || 1));
            setLookbackMinutes(v);
          }}
          inputProps={{ min: 1, max: 1440 }}
          sx={{ width: 140 }}
        />
      </Box>

      <Grid container spacing={3}>
        {/* No symbols selected */}
        {(!selectedSymbol1 || !selectedSymbol2) && (
          <Grid item xs={12}>
            <Alert severity="info">
              Please select symbols in the Spread Analysis tab to run statistical tests.
            </Alert>
          </Grid>
        )}

        {/* Error */}
        {hasError && (
          <Grid item xs={12}>
            <Alert severity="error">
              Failed to fetch statistical tests:
              {adfError && ` ADF: ${adfError instanceof Error ? adfError.message : 'Unknown error'}`}
              {cointegError && ` Cointegration: ${cointegError instanceof Error ? cointegError.message : 'Unknown error'}`}
            </Alert>
          </Grid>
        )}

        {/* Loading */}
        {isLoading && (
          <Grid item xs={12}>
            <Box display="flex" alignItems="center" justifyContent="center" py={5}>
              <CircularProgress />
              <Typography variant="body1" ml={2}>
                Running statistical tests...
              </Typography>
            </Box>
          </Grid>
        )}

        {/* ADF Test Results */}
        {adfData && (
          <>
            <Grid item xs={12}>
              <Typography variant="h5" gutterBottom>
                Augmented Dickey-Fuller (ADF) Test
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Tests whether the spread time series is stationary (mean-reverting). Lower p-value indicates stronger stationarity.
              </Typography>
            </Grid>

            {/* ADF Summary Cards */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Stack spacing={2}>
                    <Box display="flex" alignItems="center" justifyContent="space-between">
                      <Typography variant="h6">Stationarity Status</Typography>
                      {adfData.is_stationary ? (
                        <CheckCircle color="success" fontSize="large" />
                      ) : (
                        <Cancel color="error" fontSize="large" />
                      )}
                    </Box>
                    <Chip
                      label={adfData.is_stationary ? 'STATIONARY' : 'NON-STATIONARY'}
                      color={adfData.is_stationary ? 'success' : 'error'}
                      size="medium"
                      sx={{ fontSize: '1.1rem', py: 2 }}
                    />
                    <Typography variant="body2" color="text.secondary">
                      {adfData.is_stationary
                        ? 'The spread exhibits mean-reverting behavior, suitable for pairs trading.'
                        : 'The spread does not exhibit stationarity. Pairs trading may be risky.'}
                    </Typography>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>

            {/* Rolling-window stationary percentage (optional) */}
            {typeof adfData.stationary_pct !== 'undefined' && adfData.stationary_pct !== null && (
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Stack spacing={2}>
                      <Typography variant="h6">Rolling ADF Stability</Typography>
                      <Typography variant="body2" color="text.secondary">
                        Percentage of rolling windows where ADF indicated stationarity.
                      </Typography>
                      <Box display="flex" alignItems="center" justifyContent="space-between">
                        <Typography variant="h4">{(adfData.stationary_pct * 100).toFixed(1)}%</Typography>
                        <Chip
                          label={adfData.is_stationary_by_threshold ? 'OK to Trade' : 'Avoid Trading'}
                          color={adfData.is_stationary_by_threshold ? 'success' : 'error'}
                        />
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        Recommendation: Trade only if ADF is stationary in ≥70% of rolling windows.
                      </Typography>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            )}

            {/* Rolling ADF Visualization Chart */}
            {typeof adfData.stationary_pct !== 'undefined' && adfData.stationary_pct !== null && (
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Rolling Window Stationarity Analysis
                    </Typography>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      Summary: {(adfData.stationary_pct * 100).toFixed(1)}% of rolling windows are stationary (p {'<'} 0.05)
                    </Typography>
                    <Alert severity={adfData.is_stationary_by_threshold ? 'success' : 'warning'} sx={{ mb: 2 }}>
                      {adfData.is_stationary_by_threshold
                        ? '✓ Stationarity is consistent across rolling windows. Spread is reliable for mean-reversion.'
                        : '⚠ Stationarity varies significantly. Spread may have unstable mean-reversion properties.'}
                    </Alert>
                    <Typography variant="caption" color="text.secondary">
                      Note: Detailed window-by-window p-values require backend enhancement. This shows aggregate stability.
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            )}

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Stack spacing={2}>
                    <Typography variant="h6">Test Statistics</Typography>
                    <Divider />
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        ADF Statistic
                      </Typography>
                      <Typography variant="h5" fontWeight="bold">
                        {adfData.adf_statistic.toFixed(4)}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        P-Value
                      </Typography>
                      <Typography
                        variant="h5"
                        fontWeight="bold"
                        color={adfData.p_value < 0.05 ? 'success.main' : 'error.main'}
                      >
                        {adfData.p_value.toFixed(6)}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {adfData.p_value < 0.05 ? '✓ Statistically significant (< 0.05)' : '✗ Not significant (≥ 0.05)'}
                      </Typography>
                    </Box>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>

            {/* Critical Values */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Critical Values
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    ADF statistic must be more negative than critical values to reject the null hypothesis of non-stationarity.
                  </Typography>
                  <Grid container spacing={2} mt={1}>
                    {Object.entries(adfData.critical_values).map(([level, value]) => {
                      const isSatisfied = adfData.adf_statistic < (value as number);
                      return (
                        <Grid item xs={12} sm={4} key={level}>
                          <Paper
                            sx={{
                              p: 2,
                              bgcolor: isSatisfied ? 'success.dark' : 'background.paper',
                              border: isSatisfied ? 2 : 1,
                              borderColor: isSatisfied ? 'success.main' : 'divider',
                            }}
                          >
                            <Box display="flex" alignItems="center" justifyContent="space-between">
                              <Box>
                                <Typography variant="caption" color="text.secondary">
                                  {level} Confidence
                                </Typography>
                                <Typography variant="h6" fontWeight="bold">
                                  {(value as number).toFixed(4)}
                                </Typography>
                              </Box>
                              {isSatisfied ? (
                                <CheckCircle color="success" />
                              ) : (
                                <Cancel color="error" />
                              )}
                            </Box>
                            <Typography variant="caption" color="text.secondary" mt={1}>
                              {isSatisfied ? 'Satisfied' : 'Not satisfied'}
                            </Typography>
                          </Paper>
                        </Grid>
                      );
                    })}
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </>
        )}

        {/* Cointegration Test Results */}
        {cointegData && (
          <>
            <Grid item xs={12} mt={4}>
              <Typography variant="h5" gutterBottom>
                Engle-Granger Cointegration Test
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Tests whether two non-stationary price series have a stationary linear combination (cointegration).
                Cointegrated pairs are ideal candidates for pairs trading.
              </Typography>
            </Grid>

            {/* Cointegration Summary */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Stack spacing={2}>
                    <Box display="flex" alignItems="center" justifyContent="space-between">
                      <Box>
                        <Typography variant="h6">Cointegration Status</Typography>
                        {cointegData.timestamp && (
                          <Typography variant="caption" color="text.secondary">
                            Last calculated: {new Date(cointegData.timestamp).toLocaleString()}
                          </Typography>
                        )}
                      </Box>
                      {cointegData.is_cointegrated ? (
                        <CheckCircle color="success" fontSize="large" />
                      ) : (
                        <Cancel color="error" fontSize="large" />
                      )}
                    </Box>
                    <Chip
                      label={cointegData.is_cointegrated ? 'COINTEGRATED' : 'NOT COINTEGRATED'}
                      color={cointegData.is_cointegrated ? 'success' : 'error'}
                      size="medium"
                      sx={{ fontSize: '1.1rem', py: 2 }}
                    />
                    <Typography variant="body2" color="text.secondary">
                      {cointegData.is_cointegrated
                        ? 'Strong evidence of long-term equilibrium relationship. Excellent for pairs trading.'
                        : 'No evidence of cointegration. Pair may diverge indefinitely.'}
                    </Typography>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Stack spacing={2}>
                    <Box display="flex" alignItems="center" justifyContent="space-between">
                      <Typography variant="h6">Test Statistics</Typography>
                      <Tooltip title="Show backend response">
                        <IconButton size="small" onClick={() => setShowCointegDebug(true)}>
                          <InfoOutlined />
                        </IconButton>
                      </Tooltip>
                    </Box>
                    <Divider />
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Cointegration Statistic
                      </Typography>
                      <Typography variant="h5" fontWeight="bold">
                        {cointegData.cointegration_statistic != null
                          ? (cointegData.cointegration_statistic).toFixed(4)
                          : 'N/A'}
                      </Typography>
                      {cointegData.cointegration_statistic == null && (
                        <Typography variant="caption" color="warning.main">
                          Unable to compute (insufficient data or zero variance)
                        </Typography>
                      )}
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        P-Value
                      </Typography>
                      <Typography
                        variant="h5"
                        fontWeight="bold"
                        color={(cointegData.p_value ?? 1) < 0.05 ? 'success.main' : 'error.main'}
                      >
                        {(cointegData.p_value ?? 1).toFixed(6)}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {(cointegData.p_value ?? 1) < 0.05 ? '✓ Statistically significant (< 0.05)' : '✗ Not significant (≥ 0.05)'}
                      </Typography>
                    </Box>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>

            {/* Interpretation Guide */}
            <Grid item xs={12}>
              <Card sx={{ bgcolor: 'info.dark' }}>
                <CardContent>
                  <Stack spacing={2}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Info color="info" />
                      <Typography variant="h6">Interpretation Guide</Typography>
                    </Box>
                    <Divider />
                    <Typography variant="body2">
                      <strong>ADF Test:</strong>
                      <br />
                      • Tests if spread is stationary (mean-reverting)
                      <br />
                      • Null hypothesis: Spread has a unit root (non-stationary)
                      <br />
                      • P-value {'<'} 0.05 → Reject null → Spread is stationary
                      <br />
                      <br />
                      <strong>Cointegration Test:</strong>
                      <br />
                      • Tests if two prices move together long-term
                      <br />
                      • Null hypothesis: No cointegration
                      <br />
                      • P-value {'<'} 0.05 → Reject null → Pair is cointegrated
                      <br />
                      <br />
                      <strong>For Pairs Trading:</strong>
                      <br />
                      ✓ Both stationary spread AND cointegration = Excellent pair
                      <br />
                      ⚠ Only one satisfied = Proceed with caution
                      <br />
                      ✗ Neither satisfied = Avoid trading this pair
                    </Typography>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          </>
        )}
      </Grid>

      {/* Debug Dialogs */}
      {adfData && (
        <Dialog open={showAdfDebug} onClose={() => setShowAdfDebug(false)} maxWidth="md" fullWidth>
          <DialogTitle>ADF Test - Backend Response</DialogTitle>
          <DialogContent>
            <pre style={{ fontSize: '0.85rem', overflow: 'auto' }}>
              {JSON.stringify(adfData, null, 2)}
            </pre>
          </DialogContent>
        </Dialog>
      )}

      {cointegData && (
        <Dialog open={showCointegDebug} onClose={() => setShowCointegDebug(false)} maxWidth="md" fullWidth>
          <DialogTitle>Cointegration Test - Backend Response</DialogTitle>
          <DialogContent>
            <pre style={{ fontSize: '0.85rem', overflow: 'auto' }}>
              {JSON.stringify(cointegData, null, 2)}
            </pre>
          </DialogContent>
        </Dialog>
      )}
    </Box>
  );
};
