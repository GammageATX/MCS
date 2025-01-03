import React, { useEffect, useState } from 'react';
import { Grid, Paper, Typography, Chip, Box } from '@mui/material';
import { useWebSocket } from '../context/WebSocketContext';

interface ComponentHealth {
  status: 'ok' | 'error';
  message?: string;
}

interface ServiceHealth {
  status: 'ok' | 'error';
  service_name: string;
  version: string;
  running: boolean;
  uptime: number;
  error_message?: string;
  components: {
    [key: string]: ComponentHealth;
  };
}

export default function SystemMonitoring() {
  const { connected } = useWebSocket();
  const [health, setHealth] = useState<ServiceHealth | null>(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const response = await fetch('/health');
        if (!response.ok) {
          throw new Error(`Health check failed: ${response.status}`);
        }
        const data = await response.json();
        setHealth(data);
      } catch (err) {
        console.error('Failed to fetch health status:', err);
      }
    };

    // Initial fetch
    fetchHealth();

    // Refresh every 30 seconds
    const interval = setInterval(fetchHealth, 30000);

    return () => clearInterval(interval);
  }, []);

  return (
    <Grid container spacing={2}>
      <Grid item xs={12}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>System Status</Typography>
          
          <Box display="flex" alignItems="center" gap={1} mb={2}>
            <Typography>Connection Status:</Typography>
            <Chip 
              label={connected ? 'Connected' : 'Disconnected'}
              color={connected ? 'success' : 'error'}
              size="small"
            />
          </Box>

          {health && (
            <>
              <Box display="flex" alignItems="center" gap={1} mb={1}>
                <Typography>Service Status:</Typography>
                <Chip 
                  label={health.status}
                  color={health.status === 'ok' ? 'success' : 'error'}
                  size="small"
                />
              </Box>

              <Typography variant="body2">
                Service: {health.service_name} v{health.version}
              </Typography>
              
              <Typography variant="body2">
                Uptime: {Math.floor(health.uptime / 3600)}h {Math.floor((health.uptime % 3600) / 60)}m
              </Typography>

              {health.error_message && (
                <Typography color="error" variant="body2">
                  Error: {health.error_message}
                </Typography>
              )}

              <Typography variant="subtitle1" sx={{ mt: 2, mb: 1 }}>
                Component Status
              </Typography>

              <Grid container spacing={1}>
                {Object.entries(health.components).map(([name, status]) => (
                  <Grid item key={name}>
                    <Chip
                      label={`${name}: ${status.status}`}
                      color={status.status === 'ok' ? 'success' : 'error'}
                      size="small"
                      title={status.message}
                    />
                  </Grid>
                ))}
              </Grid>
            </>
          )}
        </Paper>
      </Grid>
    </Grid>
  );
} 