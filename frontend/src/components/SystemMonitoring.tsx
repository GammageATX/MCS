import React, { useEffect, useState } from 'react';
import { Grid, Paper, Typography, Chip, Box, Button, IconButton, Divider } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import { useWebSocket } from '../context/WebSocketContext';
import { API_CONFIG } from '../config/api';

interface ComponentHealth {
  status: 'ok' | 'error';
  error?: string;
}

interface ServiceHealth {
  status: 'ok' | 'error';
  service_name: string;
  version: string;
  port: number;
  uptime: number;
  mode: string;
  error_message?: string;
  components: {
    [key: string]: ComponentHealth;
  };
}

export default function SystemMonitoring() {
  const { connected } = useWebSocket();
  const [services, setServices] = useState<{ [key: string]: ServiceHealth }>({});
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchHealth = async () => {
    try {
      const responses = await Promise.all([
        fetch(`${API_CONFIG.UI_SERVICE}/health`),
        fetch(`${API_CONFIG.CONFIG_SERVICE}/health`),
        fetch(`${API_CONFIG.COMMUNICATION_SERVICE}/health`),
        fetch(`${API_CONFIG.PROCESS_SERVICE}/health`),
        fetch(`${API_CONFIG.DATA_COLLECTION_SERVICE}/health`)
      ]);

      const results = await Promise.all(responses.map(r => r.json()));
      
      const servicesMap = {
        'UI Service': results[0],
        'Config Service': results[1],
        'Communication Service': results[2],
        'Process Service': results[3],
        'Data Collection Service': results[4]
      };

      setServices(servicesMap);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Failed to fetch health status:', err);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const formatUptime = (uptime: number) => {
    const hours = Math.floor(uptime / 3600);
    const minutes = Math.floor((uptime % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  return (
    <Box sx={{ p: 3, maxWidth: 1400, margin: '0 auto' }}>
      {/* Header */}
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
            Last updated: {lastUpdated.toLocaleTimeString()}
          </Typography>
        </Box>
        <IconButton 
          onClick={fetchHealth}
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

      {/* Services Grid */}
      <Grid container spacing={3}>
        {Object.entries(services).map(([name, service]) => (
          <Grid item xs={12} md={6} key={name}>
            <Paper 
              elevation={0}
              sx={{ 
                p: 3, 
                borderRadius: 2,
                border: '1px solid rgba(0, 0, 0, 0.12)',
                transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
                }
              }}
            >
              {/* Service Header */}
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 500 }}>
                  {name}
                </Typography>
                <Chip 
                  label={service.status.toUpperCase()}
                  color={service.status === 'ok' ? 'success' : 'error'}
                  size="small"
                  sx={{ 
                    fontWeight: 500,
                    borderRadius: 1
                  }}
                />
              </Box>

              {/* Service Info */}
              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">Version</Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>{service.version}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">Port</Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>{service.port}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">Uptime</Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>{formatUptime(service.uptime)}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">Mode</Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500, textTransform: 'capitalize' }}>
                    {service.mode || 'normal'}
                  </Typography>
                </Grid>
              </Grid>

              {/* Components */}
              {service.components && Object.keys(service.components).length > 0 && (
                <>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="subtitle2" sx={{ mb: 1.5, color: 'text.secondary' }}>
                    Components
                  </Typography>
                  <Grid container spacing={1}>
                    {Object.entries(service.components).map(([componentName, componentStatus]) => (
                      <Grid item xs={12} sm={6} key={componentName}>
                        <Box sx={{ 
                          display: 'flex', 
                          alignItems: 'center', 
                          gap: 1,
                          backgroundColor: 'rgba(0, 0, 0, 0.02)',
                          p: 1,
                          borderRadius: 1
                        }}>
                          <Typography 
                            variant="body2" 
                            sx={{ 
                              flex: 1,
                              fontWeight: 500,
                              textTransform: 'capitalize'
                            }}
                          >
                            {componentName.replace(/_/g, ' ')}
                          </Typography>
                          <Chip
                            label={componentStatus.status}
                            color={componentStatus.status === 'ok' ? 'success' : 'error'}
                            size="small"
                            sx={{ 
                              minWidth: 60,
                              borderRadius: 1
                            }}
                          />
                        </Box>
                      </Grid>
                    ))}
                  </Grid>
                </>
              )}
            </Paper>
          </Grid>
        ))}
      </Grid>

      {/* Footer */}
      <Typography 
        variant="caption" 
        sx={{ 
          display: 'block', 
          textAlign: 'center', 
          mt: 4,
          color: 'text.secondary'
        }}
      >
        MicroColdSpray v1.0.0 • © 2025
      </Typography>
    </Box>
  );
} 