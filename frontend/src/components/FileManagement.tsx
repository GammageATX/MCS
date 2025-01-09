import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  Button,
  Alert,
  CircularProgress
} from '@mui/material';
import { API_CONFIG } from '../config/api';

interface Pattern {
  id: string;
  name: string;
  type: string;
  description: string;
}

interface Parameter {
  id: string;
  name: string;
  value: any;
}

interface Nozzle {
  id: string;
  name: string;
  type: string;
}

interface Powder {
  id: string;
  name: string;
  properties: any;
}

interface Sequence {
  id: string;
  name: string;
  steps: any[];
}

export default function FileManagement() {
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [parameters, setParameters] = useState<Parameter[]>([]);
  const [nozzles, setNozzles] = useState<Nozzle[]>([]);
  const [powders, setPowders] = useState<Powder[]>([]);
  const [sequences, setSequences] = useState<Sequence[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch data functions
  const fetchPatterns = async () => {
    try {
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/patterns/`);
      if (!response.ok) throw new Error('Failed to fetch patterns');
      const data = await response.json();
      setPatterns(data.patterns);
    } catch (err) {
      setError('Failed to load patterns');
    }
  };

  const fetchParameters = async () => {
    try {
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/parameters/`);
      if (!response.ok) throw new Error('Failed to fetch parameters');
      const data = await response.json();
      setParameters(data.parameters);
    } catch (err) {
      setError('Failed to load parameters');
    }
  };

  const fetchNozzles = async () => {
    try {
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/parameters/nozzles`);
      if (!response.ok) throw new Error('Failed to fetch nozzles');
      const data = await response.json();
      setNozzles(data.nozzles);
    } catch (err) {
      setError('Failed to load nozzles');
    }
  };

  const fetchPowders = async () => {
    try {
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/parameters/powders`);
      if (!response.ok) throw new Error('Failed to fetch powders');
      const data = await response.json();
      setPowders(data.powders);
    } catch (err) {
      setError('Failed to load powders');
    }
  };

  const fetchSequences = async () => {
    try {
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/sequences/`);
      if (!response.ok) throw new Error('Failed to fetch sequences');
      const data = await response.json();
      setSequences(data.sequences);
    } catch (err) {
      setError('Failed to load sequences');
    }
  };

  // Load all data on component mount
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        await Promise.all([
          fetchPatterns(),
          fetchParameters(),
          fetchNozzles(),
          fetchPowders(),
          fetchSequences()
        ]);
      } catch (err) {
        setError('Failed to load data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Grid container spacing={3}>
        {/* Patterns */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Patterns
            </Typography>
            <List>
              {patterns.map((pattern) => (
                <ListItem key={pattern.id}>
                  <ListItemText
                    primary={pattern.name}
                    secondary={`Type: ${pattern.type}, ${pattern.description}`}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* Parameters */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Parameters
            </Typography>
            <List>
              {parameters.map((param) => (
                <ListItem key={param.id}>
                  <ListItemText
                    primary={param.name}
                    secondary={`Value: ${JSON.stringify(param.value)}`}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* Nozzles */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Nozzles
            </Typography>
            <List>
              {nozzles.map((nozzle) => (
                <ListItem key={nozzle.id}>
                  <ListItemText
                    primary={nozzle.name}
                    secondary={`Type: ${nozzle.type}`}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* Powders */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Powders
            </Typography>
            <List>
              {powders.map((powder) => (
                <ListItem key={powder.id}>
                  <ListItemText
                    primary={powder.name}
                    secondary={`Properties: ${JSON.stringify(powder.properties)}`}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* Sequences */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Sequences
            </Typography>
            <List>
              {sequences.map((sequence) => (
                <ListItem key={sequence.id}>
                  <ListItemText
                    primary={sequence.name}
                    secondary={`Steps: ${sequence.steps.length}`}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
} 