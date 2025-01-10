import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import { API_CONFIG } from '../config/api';

interface Sequence {
  id: string;
  metadata: {
    name: string;
    version: string;
    created: string;
    author: string;
    description: string;
  };
  steps: Array<{
    name: string;
    step_type: string;
    description: string;
    pattern_id: string | null;
    parameters: any | null;
    origin: any | null;
  }>;
}

interface SequenceListResponse {
  sequences: Array<{
    id: string;
    metadata: {
      name: string;
      description: string;
    };
  }>;
}

export default function SequenceExecution() {
  const [sequences, setSequences] = useState<SequenceListResponse['sequences']>([]);
  const [selectedSequence, setSelectedSequence] = useState<string>('');
  const [loadedSequence, setLoadedSequence] = useState<Sequence | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSequences();
  }, []);

  const fetchSequences = async () => {
    try {
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/sequences/`);
      if (!response.ok) {
        throw new Error('Failed to fetch sequences');
      }
      const data = await response.json();
      console.log('Fetched sequences:', data);
      
      if (data && Array.isArray(data.sequences)) {
        setSequences(data.sequences);
      } else {
        console.warn('Unexpected response format:', data);
        setSequences([]);
      }
      setError(null);
    } catch (err) {
      console.error('Error fetching sequences:', err);
      setError('Failed to load sequences. Please check your connection and try again.');
      setSequences([]);
    }
  };

  const loadSequence = async () => {
    if (!selectedSequence) return;
    
    try {
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/sequences/${selectedSequence}`);
      if (!response.ok) {
        throw new Error('Failed to load sequence details');
      }
      const data = await response.json();
      console.log('Loaded sequence:', data);
      if (data && data.sequence) {
        setLoadedSequence(data.sequence);
      } else {
        throw new Error('Invalid sequence data format');
      }
      setError(null);
    } catch (err) {
      console.error('Error loading sequence:', err);
      setError('Failed to load sequence details. Please try again.');
    }
  };

  const startSequence = async () => {
    if (!selectedSequence) return;
    
    try {
      const encodedName = encodeURIComponent(selectedSequence);
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/sequences/${encodedName}/start`, {
        method: 'POST'
      });
      if (!response.ok) {
        throw new Error('Failed to start sequence');
      }
      console.log('Sequence started');
      // Refresh sequence status after starting
      await loadSequence();
    } catch (err) {
      console.error('Error starting sequence:', err);
      setError('Failed to start sequence. Please try again.');
    }
  };

  const stopSequence = async () => {
    if (!selectedSequence) return;
    
    try {
      const encodedName = encodeURIComponent(selectedSequence);
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/sequences/${encodedName}/stop`, {
        method: 'POST'
      });
      if (!response.ok) {
        throw new Error('Failed to stop sequence');
      }
      console.log('Sequence stopped');
      // Refresh sequence status after stopping
      await loadSequence();
    } catch (err) {
      console.error('Error stopping sequence:', err);
      setError('Failed to stop sequence. Please try again.');
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Sequence Execution
      </Typography>

      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}

      <FormControl fullWidth sx={{ mb: 3 }}>
        <InputLabel id="sequence-select-label">Select Sequence</InputLabel>
        <Select
          labelId="sequence-select-label"
          value={selectedSequence}
          label="Select Sequence"
          onChange={(e) => {
            console.log('Selected sequence:', e.target.value);
            setSelectedSequence(e.target.value);
          }}
        >
          {sequences.length === 0 ? (
            <MenuItem value="">
              <em>No sequences available</em>
            </MenuItem>
          ) : (
            sequences.map((sequence) => (
              <MenuItem key={sequence.id} value={sequence.id}>
                {sequence.metadata.name}
              </MenuItem>
            ))
          )}
        </Select>
      </FormControl>

      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <Button
          variant="contained"
          onClick={loadSequence}
          disabled={!selectedSequence}
        >
          Load Sequence
        </Button>
        <Button
          variant="contained"
          color="primary"
          onClick={startSequence}
          disabled={!selectedSequence}
        >
          Start
        </Button>
        <Button
          variant="contained"
          color="secondary"
          onClick={stopSequence}
          disabled={!selectedSequence}
        >
          Stop
        </Button>
      </Box>

      {loadedSequence && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            {loadedSequence.metadata.name}
          </Typography>
          <Typography variant="body2" color="textSecondary" gutterBottom>
            {loadedSequence.metadata.description}
          </Typography>
          <List>
            {loadedSequence.steps.map((step, index) => (
              <ListItem key={index}>
                <ListItemText
                  primary={step.name}
                  secondary={`Type: ${step.step_type}${step.description ? ` - ${step.description}` : ''}`}
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}
    </Box>
  );
} 