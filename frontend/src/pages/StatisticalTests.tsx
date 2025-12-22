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
} from '@mui/material';
import { useStore } from '@/store';
import api from '@/services/api';
import { debug, info as logInfo } from '@/types';
import { useQuery } from '@tanstack/react-query';
import { CheckCircle, Cancel, Info } from '@mui/icons-material';

const COMPONENT_NAME = 'StatisticalTests';

export const StatisticalTests: React.FC = () => {
  const { selectedSymbol1, selectedSymbol2, settings } = useStore();

  debug(COMPONENT_NAME, 'Rendering statistical tests', {
    symbol1: selectedSymbol1,
    symbol2: selectedSymbol2,
  });

  // Fetch ADF test results
  const { data: adfData, isLoading: adfLoading, error: adfError } = useQuery({
    queryKey: ['adf', selectedSymbol1, selectedSymbol2, settings.lookbackPeriod],
    queryFn: () => api.getADFTest(selectedSymbol1!, selectedSymbol2!, settings.lookbackPeriod),
    enabled: !!selectedSymbol1 && !!selectedSymbol2,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch cointegration test results
  const { data: cointegData, isLoading: cointegLoading, error: cointegError } = useQuery({
    queryKey: ['cointegration', selectedSymbol1, selectedSymbol2, settings.lookbackPeriod],
    queryFn: () => api.getCointegration(selectedSymbol1!, selectedSymbol2!, settings.lookbackPeriod),
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
                      <Typography variant="h6">Cointegration Status</Typography>
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
                    <Typography variant="h6">Test Statistics</Typography>
                    <Divider />
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Cointegration Statistic
                      </Typography>
                      <Typography variant="h5" fontWeight="bold">
                        {(cointegData.cointegration_statistic ?? 0).toFixed(4)}
                      </Typography>
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
    </Box>
  );
};
