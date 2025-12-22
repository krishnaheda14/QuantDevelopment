import React from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Paper,
  Chip,
  Stack,
  IconButton,
  Badge,
  Divider,
} from '@mui/material';
import {
  NotificationsActive,
  Error,
  Warning,
  Info,
  Clear,
} from '@mui/icons-material';
import { useStore } from '@/store';
import { debug, info as logInfo } from '@/types';
import type { Alert as AlertType } from '@/types';

const COMPONENT_NAME = 'Alerts';

export const Alerts: React.FC = () => {
  const { alerts, clearAllAlerts } = useStore();

  debug(COMPONENT_NAME, 'Rendering alerts page', { alertCount: alerts.length });

  // Group alerts by severity
  const errorAlerts = alerts.filter((a) => a.severity === 'error');
  const warningAlerts = alerts.filter((a) => a.severity === 'warning');
  const infoAlerts = alerts.filter((a) => a.severity === 'info');

  const handleClearAll = () => {
    logInfo(COMPONENT_NAME, 'Clearing all alerts');
    clearAllAlerts();
  };

  const getAlertIcon = (severity: AlertType['severity']) => {
    switch (severity) {
      case 'error':
        return <Error color="error" />;
      case 'warning':
        return <Warning color="warning" />;
      case 'info':
        return <Info color="info" />;
    }
  };

  const getAlertColor = (severity: AlertType['severity']) => {
    switch (severity) {
      case 'error':
        return 'error.main';
      case 'warning':
        return 'warning.main';
      case 'info':
        return 'info.main';
    }
  };

  return (
    <Box>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Alerts & Notifications
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Real-time alerts for trading signals, statistical thresholds, and system events.
          </Typography>
        </Box>
        {alerts.length > 0 && (
          <IconButton onClick={handleClearAll} color="error" size="large">
            <Clear />
          </IconButton>
        )}
      </Box>

      <Grid container spacing={3}>
        {/* Summary Cards */}
        <Grid item xs={12} sm={4}>
          <Card sx={{ bgcolor: 'error.dark' }}>
            <CardContent>
              <Stack spacing={1}>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Typography variant="h6">Critical</Typography>
                  <Badge badgeContent={errorAlerts.length} color="error">
                    <Error />
                  </Badge>
                </Box>
                <Typography variant="h3" fontWeight="bold">
                  {errorAlerts.length}
                </Typography>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={4}>
          <Card sx={{ bgcolor: 'warning.dark' }}>
            <CardContent>
              <Stack spacing={1}>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Typography variant="h6">Warnings</Typography>
                  <Badge badgeContent={warningAlerts.length} color="warning">
                    <Warning />
                  </Badge>
                </Box>
                <Typography variant="h3" fontWeight="bold">
                  {warningAlerts.length}
                </Typography>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={4}>
          <Card sx={{ bgcolor: 'info.dark' }}>
            <CardContent>
              <Stack spacing={1}>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Typography variant="h6">Info</Typography>
                  <Badge badgeContent={infoAlerts.length} color="info">
                    <Info />
                  </Badge>
                </Box>
                <Typography variant="h3" fontWeight="bold">
                  {infoAlerts.length}
                </Typography>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* Alerts List */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                All Alerts ({alerts.length})
              </Typography>
              <Divider sx={{ my: 2 }} />

              {alerts.length === 0 ? (
                <Box textAlign="center" py={5}>
                  <NotificationsActive sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary">
                    No alerts at this time
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Alerts will appear here when trading signals or system events occur.
                  </Typography>
                </Box>
              ) : (
                <Stack spacing={2}>
                  {alerts.map((alert) => (
                    <Paper
                      key={alert.id}
                      sx={{
                        p: 2,
                        borderLeft: 4,
                        borderColor: getAlertColor(alert.severity),
                      }}
                    >
                      <Box display="flex" alignItems="start" gap={2}>
                        <Box mt={0.5}>{getAlertIcon(alert.severity)}</Box>
                        <Box flex={1}>
                          <Box display="flex" alignItems="center" gap={1} mb={1}>
                            <Chip
                              label={alert.type.toUpperCase()}
                              size="small"
                              color={alert.severity}
                            />
                            <Typography variant="caption" color="text.secondary">
                              {new Date(alert.timestamp).toLocaleString()}
                            </Typography>
                          </Box>
                          <Typography variant="body1" fontWeight="bold" gutterBottom>
                            {alert.message}
                          </Typography>
                          {alert.symbol && (
                            <Typography variant="body2" color="text.secondary">
                              Symbol: {alert.symbol}
                            </Typography>
                          )}
                          {alert.value !== undefined && (
                            <Typography variant="body2" color="text.secondary">
                              Value: {alert.value.toFixed(4)}
                            </Typography>
                          )}
                        </Box>
                      </Box>
                    </Paper>
                  ))}
                </Stack>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};
