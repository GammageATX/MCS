import React, { useEffect, useState } from 'react';
import { Grid, Paper, Typography, Button, Box, Chip } from '@mui/material';
import { useWebSocket } from '../context/WebSocketContext';

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

export default function SequenceExecution() {
  const { connected } = useWebSocket();
  const [sequences, setSequences] = useState<Sequence[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSequences = async () => {
      try {
        const response = await fetch('/process/sequences');
        if (!response.ok) {
          throw new Error(`Failed to fetch sequences: ${response.status}`);
        }
        const data = await response.json();
        setSequences(data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch sequences:', err);
        setError('Failed to load sequences');
      } finally {
        setLoading(false);
      }
    };

    fetchSequences();
  }, []);

  const handleStartSequence = async (sequenceId: string) => {
    try {
      const response = await fetch(`/process/sequences/${sequenceId}/start`, {
        method: 'POST'
      });
      if (!response.ok) {
        throw new Error(`Failed to start sequence: ${response.status}`);
      }
      // Refresh sequences after starting
      const updatedResponse = await fetch('/process/sequences');
      if (updatedResponse.ok) {
        const data = await updatedResponse.json();
        setSequences(data);
      }
    } catch (err) {
      console.error('Failed to start sequence:', err);
      setError('Failed to start sequence');
    }
  };

  const handleStopSequence = async (sequenceId: string) => {
    try {
      const response = await fetch(`/process/sequences/${sequenceId}/stop`, {
        method: 'POST'
      });
      if (!response.ok) {
        throw new Error(`Failed to stop sequence: ${response.status}`);
      }
      // Refresh sequences after stopping
      const updatedResponse = await fetch('/process/sequences');
      if (updatedResponse.ok) {
        const data = await updatedResponse.json();
        setSequences(data);
      }
    } catch (err) {
      console.error('Failed to stop sequence:', err);
      setError('Failed to stop sequence');
    }
  };

  const getStatusColor = (status: string) => {
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

  if (loading) {
    return (
      <Typography>Loading sequences...</Typography>
    );
  }

  if (error) {
    return (
      <Typography color="error">{error}</Typography>
    );
  }

  if (!sequences || sequences.length === 0) {
    return (
      <Typography>No sequences available</Typography>
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