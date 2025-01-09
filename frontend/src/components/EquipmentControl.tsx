import React, { useEffect, useState } from 'react';
import { Box, Grid, Paper, Typography, CircularProgress, Alert } from '@mui/material';
import { API_CONFIG } from '../config/api';
import { useWebSocket } from '../context/WebSocketContext';

// Types from API spec
interface AxisStatus {
  position: number;
  in_position: boolean;
  moving: boolean;
  error: boolean;
  homed: boolean;
}

interface SystemStatus {
  x_axis: AxisStatus;
  y_axis: AxisStatus;
  z_axis: AxisStatus;
  module_ready: boolean;
}

interface GasState {
  main_flow_rate: number;
  feeder_flow_rate: number;
  main_valve_state: boolean;
  feeder_valve_state: boolean;
}

interface VacuumState {
  chamber_pressure: number;
  gate_valve_state: boolean;
  mechanical_pump_state: boolean;
  booster_pump_state: boolean;
  vent_valve_state: boolean;
}

interface FeederState {
  running: boolean;
  frequency: number;
}

interface DeagglomeratorState {
  duty_cycle: number;
}

interface NozzleState {
  active_nozzle: 1 | 2;
  shutter_state: boolean;
}

interface PressureState {
  chamber: number;
  feeder: number;
  main_supply: number;
  nozzle: number;
  regulator: number;
}

interface HardwareState {
  motion_enabled: boolean;
  plc_connected: boolean;
  position_valid: boolean;
}

interface ProcessState {
  gas_flow_stable: boolean;
  powder_feed_active: boolean;
  process_ready: boolean;
}

interface EquipmentState {
  gas: GasState;
  vacuum: VacuumState;
  feeder: FeederState;
  deagglomerator: DeagglomeratorState;
  nozzle: NozzleState;
  pressure: PressureState;
  hardware: HardwareState;
  process: ProcessState;
}

export default function EquipmentControl() {
  const [equipmentState, setEquipmentState] = useState<EquipmentState | null>(null);
  const [internalStates, setInternalStates] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const { connected, lastMessage } = useWebSocket();

  useEffect(() => {
    // Initial data fetch
    fetchEquipmentState();
    fetchInternalStates();

    // Set up polling interval for fallback
    const pollInterval = setInterval(() => {
      if (!connected) {
        fetchEquipmentState();
        fetchInternalStates();
      }
    }, 5000); // Poll every 5 seconds if WebSocket is down

    return () => clearInterval(pollInterval);
  }, [connected]);

  // Update state when WebSocket message is received
  useEffect(() => {
    if (lastMessage) {
      try {
        const data = lastMessage;
        if (data.type === 'equipment_state') {
          setEquipmentState(data.state);
        } else if (data.type === 'internal_states') {
          setInternalStates(data.states);
        }
      } catch (err) {
        console.error('Error processing WebSocket message:', err);
      }
    }
  }, [lastMessage]);

  const fetchEquipmentState = async () => {
    try {
      const response = await fetch(`${API_CONFIG.EQUIPMENT_SERVICE}/equipment/state`);
      if (!response.ok) {
        throw new Error(`Failed to fetch equipment state: ${response.status}`);
      }
      const data = await response.json();
      setEquipmentState(data);
      setError('');
    } catch (err) {
      console.error('Failed to fetch equipment state:', err);
      setError('Failed to load equipment state. The equipment service might be unavailable.');
    } finally {
      setLoading(false);
    }
  };

  const fetchInternalStates = async () => {
    try {
      const response = await fetch(`${API_CONFIG.EQUIPMENT_SERVICE}/equipment/internal_states`);
      if (!response.ok) {
        throw new Error(`Failed to fetch internal states: ${response.status}`);
      }
      const data = await response.json();
      setInternalStates(data);
    } catch (err) {
      console.error('Failed to fetch internal states:', err);
      // Don't set error here to avoid multiple error messages
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Equipment Control
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {!connected && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          Real-time updates unavailable. Falling back to polling.
        </Alert>
      )}

      {equipmentState && (
        <Grid container spacing={3}>
          {/* Gas System */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>Gas System</Typography>
              <Box>
                <Typography>Main Flow Rate: {equipmentState.gas.main_flow_rate} SLPM</Typography>
                <Typography>Feeder Flow Rate: {equipmentState.gas.feeder_flow_rate} SLPM</Typography>
                <Typography>Main Valve: {equipmentState.gas.main_valve_state ? 'Open' : 'Closed'}</Typography>
                <Typography>Feeder Valve: {equipmentState.gas.feeder_valve_state ? 'Open' : 'Closed'}</Typography>
              </Box>
            </Paper>
          </Grid>

          {/* Vacuum System */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>Vacuum System</Typography>
              <Box>
                <Typography>Chamber Pressure: {equipmentState.vacuum.chamber_pressure} Torr</Typography>
                <Typography>Gate Valve: {equipmentState.vacuum.gate_valve_state ? 'Open' : 'Closed'}</Typography>
                <Typography>Mechanical Pump: {equipmentState.vacuum.mechanical_pump_state ? 'Running' : 'Stopped'}</Typography>
                <Typography>Booster Pump: {equipmentState.vacuum.booster_pump_state ? 'Running' : 'Stopped'}</Typography>
              </Box>
            </Paper>
          </Grid>

          {/* Powder Feed System */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>Powder Feed System</Typography>
              <Box>
                <Typography>Status: {equipmentState.feeder.running ? 'Running' : 'Stopped'}</Typography>
                <Typography>Frequency: {equipmentState.feeder.frequency} Hz</Typography>
                <Typography>Deagglomerator Duty Cycle: {equipmentState.deagglomerator.duty_cycle}%</Typography>
              </Box>
            </Paper>
          </Grid>

          {/* Nozzle System */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>Nozzle System</Typography>
              <Box>
                <Typography>Active Nozzle: {equipmentState.nozzle.active_nozzle}</Typography>
                <Typography>Shutter: {equipmentState.nozzle.shutter_state ? 'Open' : 'Closed'}</Typography>
              </Box>
            </Paper>
          </Grid>

          {/* System Status */}
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>System Status</Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography>PLC Connection: {equipmentState.hardware.plc_connected ? 'Connected' : 'Disconnected'}</Typography>
                  <Typography>Motion Enabled: {equipmentState.hardware.motion_enabled ? 'Yes' : 'No'}</Typography>
                  <Typography>Position Valid: {equipmentState.hardware.position_valid ? 'Yes' : 'No'}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography>Gas Flow Stable: {equipmentState.process.gas_flow_stable ? 'Yes' : 'No'}</Typography>
                  <Typography>Powder Feed Active: {equipmentState.process.powder_feed_active ? 'Yes' : 'No'}</Typography>
                  <Typography>Process Ready: {equipmentState.process.process_ready ? 'Yes' : 'No'}</Typography>
                </Grid>
              </Grid>
            </Paper>
          </Grid>
        </Grid>
      )}
    </Box>
  );
} 