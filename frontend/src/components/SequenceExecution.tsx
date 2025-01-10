import React, { useEffect, useState } from 'react';
import { Grid, Paper, Typography, Button, Box, Chip } from '@mui/material';
import { useWebSocket } from '../context/WebSocketContext';
import { API_CONFIG } from '../config/api';

interface SequenceStep {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  error_message?: string;
}

interface Sequence {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  steps: SequenceStep[];
  error_message?: string;
}

interface SequenceUpdate {
  type: 'sequence_update';
  data: {
    sequence_id: string;
    status: string;
    error_message?: string;
    steps?: SequenceStep[];
  };
}

export default function SequenceExecution() {
  const { connected, lastMessage } = useWebSocket();
  const [sequences, setSequences] = useState<Sequence[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Handle WebSocket updates
  useEffect(() => {
    if (lastMessage) {
      try {
        // Handle both string and object message formats
        const messageData = typeof lastMessage.data === 'string' 
          ? JSON.parse(lastMessage.data)
          : lastMessage.data;

        // Validate message structure
        if (messageData && messageData.type === 'sequence_update' && messageData.data) {
          const update = messageData as SequenceUpdate;
          setSequences(prevSequences => 
            prevSequences.map(seq => 
              seq.id === update.data.sequence_id
                ? { 
                    ...seq, 
                    status: update.data.status,
                    error_message: update.data.error_message,
                    steps: update.data.steps || seq.steps
                  }
                : seq
            )
          );
        } else {
          console.warn('Received invalid WebSocket message format:', messageData);
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err, 'Raw message:', lastMessage.data);
      }
    }
  }, [lastMessage]);

  // Fetch sequences on mount and when connection changes
  useEffect(() => {
    const fetchSequences = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/sequences/`);
        if (!response.ok) {
          throw new Error(`Failed to fetch sequences: ${response.status}`);
        }
        const data = await response.json();
        setSequences(data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch sequences:', err);
        setError('Failed to load sequences. Please check your connection and try again.');
      } finally {
        setLoading(false);
      }
    };

    if (connected) {
      fetchSequences();
    }
  }, [connected]);

  const handleStartSequence = async (sequenceId: string) => {
    try {
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/sequences/${sequenceId}/start`, {
        method: 'POST'
      });
      if (!response.ok) {
        throw new Error(`Failed to start sequence: ${response.status}`);
      }
    } catch (err) {
      console.error('Failed to start sequence:', err);
      setError('Failed to start sequence. Please try again.');
    }
  };

  const handleStopSequence = async (sequenceId: string) => {
    try {
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/sequences/${sequenceId}/stop`, {
        method: 'POST'
      });
      if (!response.ok) {
        throw new Error(`Failed to stop sequence: ${response.status}`);
      }
    } catch (err) {
      console.error('Failed to stop sequence:', err);
      setError('Failed to stop sequence. Please try again.');
    }
  };

  const getStatusColor = (status: string): "success" | "primary" | "error" | "default" => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'running':
        return 'primary';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  if (!connected) {
    return (
      <Typography color="error">
        Not connected to server. Please check your connection.
      </Typography>
    );
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <Typography>Loading sequences...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  if (!sequences || sequences.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <Typography>No sequences available. Create a sequence in File Management.</Typography>
      </Box>
    );
  }

  return (
    <Grid container spacing={2}>
      {sequences.map((sequence) => (
        <Grid item xs={12} key={sequence.id}>
          <Paper sx={{ p: 2 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Box>
                <Typography variant="h6">{sequence.name}</Typography>
                <Typography variant="body2" color="textSecondary">
                  {sequence.description}
                </Typography>
              </Box>
              <Box display="flex" gap={1}>
                <Chip
                  label={sequence.status}
                  color={getStatusColor(sequence.status)}
                  size="small"
                />
                {sequence.status !== 'running' ? (
                  <Button
                    variant="contained"
                    onClick={() => handleStartSequence(sequence.id)}
                    disabled={!connected}
                  >
                    Start
                  </Button>
                ) : (
                  <Button
                    variant="contained"
                    color="error"
                    onClick={() => handleStopSequence(sequence.id)}
                    disabled={!connected}
                  >
                    Stop
                  </Button>
                )}
              </Box>
            </Box>

            {sequence.error_message && (
              <Typography color="error" variant="body2" mb={2}>
                Error: {sequence.error_message}
              </Typography>
            )}

            <Grid container spacing={1}>
              {sequence.steps.map((step) => (
                <Grid item xs={12} key={step.id}>
                  <Box
                    sx={{
                      p: 1,
                      borderRadius: 1,
                      bgcolor: 'background.default',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}
                  >
                    <Box>
                      <Typography variant="body1">{step.name}</Typography>
                      <Typography variant="body2" color="textSecondary">
                        {step.description}
                      </Typography>
                      {step.error_message && (
                        <Typography color="error" variant="body2">
                          Error: {step.error_message}
                        </Typography>
                      )}
                    </Box>
                    <Box display="flex" gap={1} alignItems="center">
                      <Chip
                        label={step.status}
                        color={getStatusColor(step.status)}
                        size="small"
                      />
                    </Box>
                  </Box>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>
      ))}
    </Grid>
  );
} 