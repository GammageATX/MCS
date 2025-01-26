import React, { useEffect, useState } from 'react';
import { Grid, Paper, Typography, Chip, Box, Button, IconButton, Divider, Alert } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import { API_CONFIG } from '../config/api';

interface ComponentHealth {
  status: 'ok' | 'error';
  error: string | null;
  details: any;
}

interface ServiceHealth {
  name: string;
  port: number;
  status: 'ok' | 'error';
  uptime: number;
  version: string;
  mode: string;
  error: string | null;
  components: {
    [key: string]: ComponentHealth;
  };
}

interface SystemState {
  config: ServiceHealth;
  communication: ServiceHealth;
  process: ServiceHealth;
  data_collection: ServiceHealth;
}

export default function SystemMonitoring() {
  const [systemState, setSystemState] = useState<SystemState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(true);

  useEffect(() => {
    const pollSystemState = async () => {
      try {
        // Fetch health status from each service
        const [configHealth, commHealth, processHealth, dataHealth] = await Promise.all([
          fetch(`${API_CONFIG.CONFIG_SERVICE}/health`).then(res => res.json()),
          fetch(`${API_CONFIG.COMMUNICATION_SERVICE}/health`).then(res => res.json()),
          fetch(`${API_CONFIG.PROCESS_SERVICE}/health`).then(res => res.json()),
          fetch(`${API_CONFIG.DATA_COLLECTION_SERVICE}/health`).then(res => res.json())
        ]);

        // Construct system state from individual health responses
        const systemState: SystemState = {
          config: {
            name: 'config',
            port: parseInt(API_CONFIG.CONFIG_SERVICE.split(':').pop() || '8001'),
            status: configHealth.status,
            uptime: configHealth.uptime,
            version: configHealth.version,
            mode: configHealth.mode || 'production',
            error: configHealth.error,
            components: configHealth.components || {}
          },
          communication: {
            name: 'communication',
            port: parseInt(API_CONFIG.COMMUNICATION_SERVICE.split(':').pop() || '8002'),
            status: commHealth.status,
            uptime: commHealth.uptime,
            version: commHealth.version,
            mode: commHealth.mode || 'production',
            error: commHealth.error,
            components: commHealth.components || {}
          },
          process: {
            name: 'process',
            port: parseInt(API_CONFIG.PROCESS_SERVICE.split(':').pop() || '8003'),
            status: processHealth.status,
            uptime: processHealth.uptime,
            version: processHealth.version,
            mode: processHealth.mode || 'production',
            error: processHealth.error,
            components: processHealth.components || {}
          },
          data_collection: {
            name: 'data_collection',
            port: parseInt(API_CONFIG.DATA_COLLECTION_SERVICE.split(':').pop() || '8004'),
            status: dataHealth.status,
            uptime: dataHealth.uptime,
            version: dataHealth.version,
            mode: dataHealth.mode || 'production',
            error: dataHealth.error,
            components: dataHealth.components || {}
          }
        };

        setSystemState(systemState);
        setError(null);
      } catch (err) {
        console.error('Error fetching system health:', err);
        setError('Failed to fetch system health');
      }
    };

    // Initial fetch
    pollSystemState();

    // Set up polling interval
    const interval = setInterval(pollSystemState, 1000);

    return () => {
      clearInterval(interval);
      setIsPolling(false);
    };
  }, []);

  const formatUptime = (uptime: number) => {
    const hours = Math.floor(uptime / 3600);
    const minutes = Math.floor((uptime % 3600) / 60);
    const seconds = Math.floor(uptime % 60);
    return `${hours}h ${minutes}m ${seconds}s`;
  };

  const formatComponentValue = (value: any): string => {
    if (!value) return '';
    
    if (typeof value === 'object') {
      // Handle common patterns in our component details
      if ('path' in value) return value.path as string;
      if ('storage' in value) return value.storage as string;
      return 'Details available';
    }
    
    return String(value);
  };

  const renderComponentDetails = (component: ComponentHealth, name: string) => (
    <Box sx={{ 
      backgroundColor: 'rgba(0, 0, 0, 0.02)',
      p: 1,
      borderRadius: 1,
      mb: 0.5
    }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="body2" sx={{ fontWeight: 500, textTransform: 'capitalize' }}>
          {name.replace(/_/g, ' ')}
        </Typography>
        <Chip
          label={component.status.toUpperCase()}
          color={component.status === 'ok' ? 'success' : 'error'}
          size="small"
          sx={{ minWidth: 45, height: 20, '& .MuiChip-label': { px: 1, fontSize: '0.7rem' } }}
        />
      </Box>
      {component.details && (
        <Box sx={{ mt: 0.5, pl: 1 }}>
          {Object.entries(component.details).map(([key, value]) => {
            const displayValue = formatComponentValue(value);
            if (!displayValue) return null;
            
            return (
              <Typography 
                key={key} 
                variant="caption" 
                display="block" 
                color="text.secondary" 
                sx={{ 
                  fontSize: '0.7rem',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}
              >
                {key.replace(/_/g, ' ')}: {displayValue}
              </Typography>
            );
          })}
        </Box>
      )}
    </Box>
  );

  const renderServiceCard = (service: ServiceHealth) => (
    <Grid item xs={12} sm={6} key={service.name}>
      <Paper 
        elevation={0}
        sx={{ 
          p: 2, 
          borderRadius: 2,
          border: '1px solid rgba(0, 0, 0, 0.12)',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          maxHeight: '500px',
          overflow: 'auto'
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="h6" sx={{ fontSize: '1.1rem', fontWeight: 500, textTransform: 'capitalize' }}>
            {service.name.replace(/_/g, ' ')} Service
          </Typography>
          <Chip 
            label={service.status.toUpperCase()}
            color={service.status === 'ok' ? 'success' : 'error'}
            size="small"
            sx={{ fontWeight: 500, borderRadius: 1 }}
          />
        </Box>

        <Grid container spacing={1} sx={{ mb: 1 }}>
          <Grid item xs={3}>
            <Typography variant="caption" color="text.secondary">Ver</Typography>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>{service.version}</Typography>
          </Grid>
          <Grid item xs={3}>
            <Typography variant="caption" color="text.secondary">Port</Typography>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>{service.port}</Typography>
          </Grid>
          <Grid item xs={3}>
            <Typography variant="caption" color="text.secondary">Time</Typography>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>{formatUptime(service.uptime)}</Typography>
          </Grid>
          <Grid item xs={3}>
            <Typography variant="caption" color="text.secondary">Mode</Typography>
            <Typography variant="body2" sx={{ fontWeight: 500, textTransform: 'capitalize' }}>
              {service.mode}
            </Typography>
          </Grid>
        </Grid>

        {Object.keys(service.components).length > 0 && (
          <>
            <Divider sx={{ my: 1 }} />
            <Typography variant="subtitle2" sx={{ mb: 1, color: 'text.secondary', fontSize: '0.75rem' }}>
              Components
            </Typography>
            <Box sx={{ flex: 1, overflowY: 'auto' }}>
              {Object.entries(service.components).map(([name, component]) => 
                renderComponentDetails(component, name)
              )}
            </Box>
          </>
        )}
      </Paper>
    </Grid>
  );

  return (
    <Box sx={{ p: 3, maxWidth: 1600, margin: '0 auto' }}>
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        mb: 4,
        borderBottom: '1px solid rgba(0, 0, 0, 0.12)',
        pb: 2
      }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 500, color: '#1a237e' }}>
            System Status
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            Last updated: {new Date().toLocaleTimeString()}
          </Typography>
        </Box>
        <IconButton 
          onClick={() => {}}
          sx={{ 
            backgroundColor: '#1976d2',
            color: 'white',
            '&:hover': {
              backgroundColor: '#1565c0'
            }
          }}
        >
          <RefreshIcon />
        </IconButton>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Error fetching system health: {error}
        </Alert>
      )}

      {systemState && (
        <Grid container spacing={2}>
          {[
            systemState.config,
            systemState.process,
            systemState.communication,
            systemState.data_collection
          ].map(service => renderServiceCard(service))}
        </Grid>
      )}

      <Typography 
        variant="caption" 
        sx={{ 
          display: 'block', 
          textAlign: 'center', 
          mt: 4,
          color: 'text.secondary'
        }}
      >
        MicroColdSpray System Monitor • v1.0.0
      </Typography>
    </Box>
  );
} 