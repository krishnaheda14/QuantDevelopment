import React from 'react';
import { Box, Card, CardContent, Chip, Typography, Stack, Divider } from '@mui/material';
import { CheckCircle, WifiOff, TrendingUp, ShowChart, Timer } from '@mui/icons-material';
import { useStore } from '@/store';
import { debug } from '@/types';

const COMPONENT_NAME = 'ConnectionStatus';

const ConnectionStatus: React.FC = () => {
  const { connectionStatus, ticks, ohlcBars } = useStore();

  debug(COMPONENT_NAME, 'Rendering connection status', {
    connected: connectionStatus?.connected,
    tickCount: ticks.size,
    barCount: ohlcBars.size,
  });

  // Get status icon and color
  const getStatusConfig = () => {
    if (connectionStatus?.connected) {
      return { icon: <CheckCircle />, color: 'success' as const, label: 'Connected' };
    }

    return { icon: <WifiOff />, color: 'default' as const, label: 'Disconnected' };
  };

  const statusConfig = getStatusConfig();

  // Calculate uptime from seconds (if provided)
  const getUptime = (): string => {
    const uptimeSeconds = connectionStatus?.uptime;
    if (uptimeSeconds === undefined || uptimeSeconds === null) return 'N/A';

    const hours = Math.floor(uptimeSeconds / 3600);
    const minutes = Math.floor((uptimeSeconds % 3600) / 60);
    const seconds = Math.floor(uptimeSeconds % 60);

    if (hours > 0) return `${hours}h ${minutes}m`;
    if (minutes > 0) return `${minutes}m ${seconds}s`;
    return `${seconds}s`;
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Stack spacing={2}>
          {/* Connection Status */}
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Typography variant="h6" component="div">
              Connection
            </Typography>
            <Chip
              icon={statusConfig.icon}
              label={statusConfig.label}
              color={statusConfig.color}
              size="small"
            />
          </Box>

          <Divider />

          {/* Statistics */}
          <Stack spacing={1.5}>
            {/* Symbols */}
            <Box display="flex" alignItems="center" gap={1}>
              <ShowChart color="primary" fontSize="small" />
              <Typography variant="body2" color="text.secondary">
                Symbols:
              </Typography>
              <Typography variant="body2" fontWeight="bold">
                {connectionStatus?.symbols ?? 0}
              </Typography>
            </Box>

            {/* Ticks Received */}
            <Box display="flex" alignItems="center" gap={1}>
              <TrendingUp color="success" fontSize="small" />
              <Typography variant="body2" color="text.secondary">
                Ticks:
              </Typography>
              <Typography variant="body2" fontWeight="bold">
                {ticks.size.toLocaleString()}
              </Typography>
            </Box>

            {/* OHLC Bars */}
            <Box display="flex" alignItems="center" gap={1}>
              <ShowChart color="info" fontSize="small" />
              <Typography variant="body2" color="text.secondary">
                OHLC Bars:
              </Typography>
              <Typography variant="body2" fontWeight="bold">
                {ohlcBars.size.toLocaleString()}
              </Typography>
            </Box>

            {/* Uptime */}
            <Box display="flex" alignItems="center" gap={1}>
              <Timer color="action" fontSize="small" />
              <Typography variant="body2" color="text.secondary">
                Uptime:
              </Typography>
              <Typography variant="body2" fontWeight="bold">
                {getUptime()}
              </Typography>
            </Box>
          </Stack>

          {/* Active Symbols List */}
          {/* Active symbols count (no list available in current type) */}
          <Divider />
          <Box display="flex" alignItems="center" gap={1}>
            <Typography variant="body2" color="text.secondary">
              Active Symbols:
            </Typography>
            <Typography variant="body2" fontWeight="bold">
              {connectionStatus?.active_symbols ?? 0}
            </Typography>
          </Box>

          {/* Last Update */}
          <Typography variant="caption" color="text.secondary" textAlign="center">
            Uptime: {getUptime()}
          </Typography>
        </Stack>
      </CardContent>
    </Card>
  );
};

export default ConnectionStatus;
