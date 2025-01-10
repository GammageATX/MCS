import React, { useEffect, useState } from 'react';
import { 
  Box, 
  Grid, 
  Paper, 
  Typography, 
  Button, 
  Slider, 
  CircularProgress, 
  Alert,
  List,
  ListItem,
  ListItemText,
  Chip
} from '@mui/material';
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
  id: number;
  running: boolean;
  frequency: number;
}

interface DeagglomeratorState {
  id: number;
  duty_cycle: number;
  frequency: number;
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
      if (!response.ok) throw new Error(`Failed to fetch equipment state: ${response.status}`);
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
      if (!response.ok) throw new Error(`Failed to fetch internal states: ${response.status}`);
      const data = await response.json();
      setInternalStates(data);
    } catch (err) {
      console.error('Failed to fetch internal states:', err);
    }
  };

  // Control Functions
  const setMainGasFlow = async (value: number) => {
    try {
      const response = await fetch(`${API_CONFIG.EQUIPMENT_SERVICE}/equipment/gas/main/flow`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ flow_rate: value })
      });
      if (!response.ok) throw new Error('Failed to set main gas flow');
      // Update local state
      if (equipmentState) {
        setEquipmentState({
          ...equipmentState,
          gas: { ...equipmentState.gas, main_flow_rate: value }
        });
      }
    } catch (err) {
      setError('Failed to set main gas flow rate');
    }
  };

  const setFeederGasFlow = async (value: number) => {
    try {
      const response = await fetch(`${API_CONFIG.EQUIPMENT_SERVICE}/equipment/gas/feeder/flow`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ flow_rate: value })
      });
      if (!response.ok) throw new Error('Failed to set feeder gas flow');
      // Update local state
      if (equipmentState) {
        setEquipmentState({
          ...equipmentState,
          gas: { ...equipmentState.gas, feeder_flow_rate: value }
        });
      }
    } catch (err) {
      setError('Failed to set feeder gas flow rate');
    }
  };

  const toggleMainGasValve = async () => {
    if (!equipmentState) return;
    const newState = !equipmentState.gas.main_valve_state;
    try {
      const response = await fetch(`${API_CONFIG.EQUIPMENT_SERVICE}/equipment/gas/main/valve`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ open: newState })
      });
      if (!response.ok) throw new Error('Failed to toggle main gas valve');
      // Update local state
      setEquipmentState({
        ...equipmentState,
        gas: { ...equipmentState.gas, main_valve_state: newState }
      });
    } catch (err) {
      setError('Failed to control main gas valve');
    }
  };

  const toggleFeederGasValve = async () => {
    if (!equipmentState) return;
    const newState = !equipmentState.gas.feeder_valve_state;
    try {
      const response = await fetch(`${API_CONFIG.EQUIPMENT_SERVICE}/equipment/gas/feeder/valve`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ open: newState })
      });
      if (!response.ok) throw new Error('Failed to toggle feeder gas valve');
      // Update local state
      setEquipmentState({
        ...equipmentState,
        gas: { ...equipmentState.gas, feeder_valve_state: newState }
      });
    } catch (err) {
      setError('Failed to control feeder gas valve');
    }
  };

  const toggleGateValve = async () => {
    if (!equipmentState) return;
    const newState = !equipmentState.vacuum.gate_valve_state;
    try {
      const response = await fetch(`${API_CONFIG.EQUIPMENT_SERVICE}/equipment/vacuum/gate`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ open: newState })
      });
      if (!response.ok) throw new Error('Failed to toggle gate valve');
      // Update local state
      setEquipmentState({
        ...equipmentState,
        vacuum: { ...equipmentState.vacuum, gate_valve_state: newState }
      });
    } catch (err) {
      setError('Failed to control gate valve');
    }
  };

  const toggleVentValve = async () => {
    if (!equipmentState) return;
    const newState = !equipmentState.vacuum.vent_valve_state;
    const endpoint = newState ? 'open' : 'close';
    try {
      const response = await fetch(`${API_CONFIG.EQUIPMENT_SERVICE}/equipment/vacuum/vent/${endpoint}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' }
      });
      if (!response.ok) throw new Error('Failed to toggle vent valve');
      // Update local state
      setEquipmentState({
        ...equipmentState,
        vacuum: { ...equipmentState.vacuum, vent_valve_state: newState }
      });
    } catch (err) {
      setError('Failed to control vent valve');
    }
  };

  const toggleMechanicalPump = async () => {
    if (!equipmentState) return;
    const newState = !equipmentState.vacuum.mechanical_pump_state;
    const endpoint = newState ? 'start' : 'stop';
    try {
      const response = await fetch(`${API_CONFIG.EQUIPMENT_SERVICE}/equipment/vacuum/mech/${endpoint}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' }
      });
      if (!response.ok) throw new Error('Failed to toggle mechanical pump');
      // Update local state
      setEquipmentState({
        ...equipmentState,
        vacuum: { ...equipmentState.vacuum, mechanical_pump_state: newState }
      });
    } catch (err) {
      setError('Failed to control mechanical pump');
    }
  };

  const toggleBoosterPump = async () => {
    if (!equipmentState) return;
    const newState = !equipmentState.vacuum.booster_pump_state;
    const endpoint = newState ? 'start' : 'stop';
    try {
      const response = await fetch(`${API_CONFIG.EQUIPMENT_SERVICE}/equipment/vacuum/booster/${endpoint}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' }
      });
      if (!response.ok) throw new Error('Failed to toggle booster pump');
      // Update local state
      setEquipmentState({
        ...equipmentState,
        vacuum: { ...equipmentState.vacuum, booster_pump_state: newState }
      });
    } catch (err) {
      setError('Failed to control booster pump');
    }
  };

  const setFeederFrequency = async (value: number) => {
    try {
      const response = await fetch(`${API_CONFIG.EQUIPMENT_SERVICE}/equipment/feeder/${equipmentState?.feeder.id || 1}/frequency`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ frequency: value })
      });
      if (!response.ok) throw new Error('Failed to set feeder frequency');
      // Update local state
      if (equipmentState) {
        setEquipmentState({
          ...equipmentState,
          feeder: { ...equipmentState.feeder, frequency: value }
        });
      }
    } catch (err) {
      setError('Failed to set feeder frequency');
    }
  };

  const toggleFeeder = async () => {
    if (!equipmentState) return;
    const newState = !equipmentState.feeder.running;
    try {
      const response = await fetch(`${API_CONFIG.EQUIPMENT_SERVICE}/equipment/feeder/${equipmentState?.feeder.id || 1}/state`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: newState })
      });
      if (!response.ok) throw new Error('Failed to toggle feeder');
      // Update local state
      setEquipmentState({
        ...equipmentState,
        feeder: { ...equipmentState.feeder, running: newState }
      });
    } catch (err) {
      setError('Failed to control feeder');
    }
  };

  const setDeagglomeratorDutyCycle = async (value: number) => {
    try {
      // Validate duty cycle is within acceptable range (0-100)
      if (value < 0 || value > 100) {
        throw new Error('Duty cycle must be between 0 and 100');
      }
      
      const response = await fetch(`${API_CONFIG.EQUIPMENT_SERVICE}/equipment/deagg/${equipmentState?.deagglomerator.id || 1}/duty_cycle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value })
      });
      if (!response.ok) throw new Error('Failed to set deagglomerator duty cycle');
      // Update local state
      if (equipmentState) {
        setEquipmentState({
          ...equipmentState,
          deagglomerator: { ...equipmentState.deagglomerator, duty_cycle: value }
        });
      }
    } catch (err) {
      setError('Failed to set deagglomerator duty cycle');
    }
  };

  const setDeagglomeratorFrequency = async (value: number) => {
    try {
      const response = await fetch(`${API_CONFIG.EQUIPMENT_SERVICE}/equipment/deagg/${equipmentState?.deagglomerator.id || 1}/frequency`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value })
      });
      if (!response.ok) throw new Error('Failed to set deagglomerator frequency');
    } catch (err) {
      setError('Failed to set deagglomerator frequency');
    }
  };

  const selectNozzle = async (nozzleId: number) => {
    try {
      const response = await fetch(`${API_CONFIG.EQUIPMENT_SERVICE}/equipment/nozzle/select`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nozzle_id: nozzleId })
      });
      if (!response.ok) throw new Error('Failed to select nozzle');
      // Update local state
      if (equipmentState) {
        setEquipmentState({
          ...equipmentState,
          nozzle: { ...equipmentState.nozzle, active_nozzle: nozzleId as 1 | 2 }
        });
      }
    } catch (err) {
      setError('Failed to select nozzle');
    }
  };

  const toggleShutter = async () => {
    if (!equipmentState) return;
    const newState = !equipmentState.nozzle.shutter_state;
    const endpoint = newState ? 'open' : 'close';
    try {
      const response = await fetch(`${API_CONFIG.EQUIPMENT_SERVICE}/equipment/nozzle/shutter/${endpoint}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' }
      });
      if (!response.ok) throw new Error('Failed to toggle shutter');
      // Update local state
      setEquipmentState({
        ...equipmentState,
        nozzle: { ...equipmentState.nozzle, shutter_state: newState }
      });
    } catch (err) {
      setError('Failed to control shutter');
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
          {/* System Status */}
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>System Status</Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <List dense>
                    <ListItem>
                      <ListItemText 
                        primary="PLC Connection" 
                        secondary={equipmentState.hardware.plc_connected ? 'Connected' : 'Disconnected'}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="Motion Enabled"
                        secondary={equipmentState.hardware.motion_enabled ? 'Yes' : 'No'}
                      />
                    </ListItem>
                  </List>
                </Grid>
                <Grid item xs={12} md={4}>
                  <List dense>
                    <ListItem>
                      <ListItemText 
                        primary="Gas Flow"
                        secondary={equipmentState.process.gas_flow_stable ? 'Stable' : 'Unstable'}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="Powder Feed"
                        secondary={equipmentState.process.powder_feed_active ? 'Active' : 'Inactive'}
                      />
                    </ListItem>
                  </List>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="subtitle2" gutterBottom>Process Ready</Typography>
                  <Chip 
                    label={equipmentState.process.process_ready ? 'Ready' : 'Not Ready'}
                    color={equipmentState.process.process_ready ? 'success' : 'warning'}
                  />
                </Grid>
              </Grid>
            </Paper>
          </Grid>

          {/* Gas System Controls */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>Gas System</Typography>
              
              {/* Main Gas */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" gutterBottom>Main Gas</Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Button
                    variant="contained"
                    onClick={toggleMainGasValve}
                    color={equipmentState.gas.main_valve_state ? 'error' : 'primary'}
                    sx={{ mr: 2 }}
                  >
                    {equipmentState.gas.main_valve_state ? 'Close' : 'Open'} Valve
                  </Button>
                  <Typography>
                    Flow Rate: {equipmentState.gas.main_flow_rate.toFixed(1)} SLPM
                  </Typography>
                </Box>
                <Slider
                  value={equipmentState.gas.main_flow_rate}
                  onChange={(_, value) => setMainGasFlow(value as number)}
                  min={0}
                  max={100}
                  step={0.1}
                  valueLabelDisplay="auto"
                  disabled={!equipmentState.gas.main_valve_state}
                />
              </Box>

              {/* Feeder Gas */}
              <Box>
                <Typography variant="subtitle2" gutterBottom>Feeder Gas</Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Button
                    variant="contained"
                    onClick={toggleFeederGasValve}
                    color={equipmentState.gas.feeder_valve_state ? 'error' : 'primary'}
                    sx={{ mr: 2 }}
                  >
                    {equipmentState.gas.feeder_valve_state ? 'Close' : 'Open'} Valve
                  </Button>
                  <Typography>
                    Flow Rate: {equipmentState.gas.feeder_flow_rate.toFixed(1)} SLPM
                  </Typography>
                </Box>
                <Slider
                  value={equipmentState.gas.feeder_flow_rate}
                  onChange={(_, value) => setFeederGasFlow(value as number)}
                  min={0}
                  max={10}
                  step={0.1}
                  valueLabelDisplay="auto"
                  disabled={!equipmentState.gas.feeder_valve_state}
                />
              </Box>
            </Paper>
          </Grid>

          {/* Vacuum System Controls */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>Vacuum System</Typography>
              
              {/* Valve Controls */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" gutterBottom>Valve Controls</Typography>
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <Button
                    variant="contained"
                    onClick={toggleGateValve}
                    color={equipmentState.vacuum.gate_valve_state ? 'error' : 'primary'}
                  >
                    Gate Valve: {equipmentState.vacuum.gate_valve_state ? 'Close' : 'Open'}
                  </Button>
                  <Button
                    variant="contained"
                    onClick={toggleVentValve}
                    color={equipmentState.vacuum.vent_valve_state ? 'error' : 'primary'}
                  >
                    Vent Valve: {equipmentState.vacuum.vent_valve_state ? 'Close' : 'Open'}
                  </Button>
                </Box>
              </Box>

              {/* Pump Controls */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" gutterBottom>Pump Controls</Typography>
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <Button
                    variant="contained"
                    onClick={toggleMechanicalPump}
                    color={equipmentState.vacuum.mechanical_pump_state ? 'error' : 'primary'}
                  >
                    Mechanical Pump: {equipmentState.vacuum.mechanical_pump_state ? 'Stop' : 'Start'}
                  </Button>
                  <Button
                    variant="contained"
                    onClick={toggleBoosterPump}
                    color={equipmentState.vacuum.booster_pump_state ? 'error' : 'primary'}
                    disabled={!equipmentState.vacuum.mechanical_pump_state}
                  >
                    Booster Pump: {equipmentState.vacuum.booster_pump_state ? 'Stop' : 'Start'}
                  </Button>
                </Box>
              </Box>

              {/* Chamber Pressure */}
              <Box>
                <Typography variant="subtitle2" gutterBottom>Chamber Pressure</Typography>
                <Typography variant="h4" align="center">
                  {equipmentState.vacuum.chamber_pressure.toExponential(2)} Torr
                </Typography>
              </Box>
            </Paper>
          </Grid>

          {/* Powder Feed System */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>Powder Feed System</Typography>
              
              {/* Feeder Control */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" gutterBottom>Feeder Control</Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Button
                    variant="contained"
                    onClick={toggleFeeder}
                    color={equipmentState.feeder.running ? 'error' : 'primary'}
                    sx={{ mr: 2 }}
                  >
                    {equipmentState.feeder.running ? 'Stop' : 'Start'} Feeder
                  </Button>
                  <Typography>
                    Frequency: {equipmentState.feeder.frequency.toFixed(1)} Hz
                  </Typography>
                </Box>
                <Slider
                  value={equipmentState.feeder.frequency}
                  onChange={(_, value) => setFeederFrequency(value as number)}
                  min={200}
                  max={1200}
                  step={200}
                  valueLabelDisplay="auto"
                  disabled={!equipmentState.feeder.running}
                  marks={[
                    { value: 200, label: '200 Hz' },
                    { value: 400, label: '400 Hz' },
                    { value: 600, label: '600 Hz' },
                    { value: 800, label: '800 Hz' },
                    { value: 1000, label: '1000 Hz' },
                    { value: 1200, label: '1200 Hz' }
                  ]}
                />
              </Box>

              {/* Deagglomerator Control */}
              <Box>
                <Typography variant="subtitle2" gutterBottom>Deagglomerator Control</Typography>
                <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                  <Button
                    variant="contained"
                    onClick={() => setDeagglomeratorDutyCycle(35)}
                    color={equipmentState.deagglomerator.duty_cycle === 35 ? 'error' : 'primary'}
                  >
                    Stop
                  </Button>
                  <Button
                    variant="contained"
                    onClick={() => setDeagglomeratorDutyCycle(30)}
                    color={equipmentState.deagglomerator.duty_cycle === 30 ? 'success' : 'primary'}
                  >
                    Low Speed
                  </Button>
                  <Button
                    variant="contained"
                    onClick={() => setDeagglomeratorDutyCycle(25)}
                    color={equipmentState.deagglomerator.duty_cycle === 25 ? 'success' : 'primary'}
                  >
                    Medium Speed
                  </Button>
                  <Button
                    variant="contained"
                    onClick={() => setDeagglomeratorDutyCycle(20)}
                    color={equipmentState.deagglomerator.duty_cycle === 20 ? 'success' : 'primary'}
                  >
                    High Speed
                  </Button>
                </Box>
                <Typography>
                  Current Duty Cycle: {equipmentState.deagglomerator.duty_cycle}%
                </Typography>
              </Box>
            </Paper>
          </Grid>

          {/* Nozzle System */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>Nozzle System</Typography>
              
              {/* Nozzle Selection */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" gutterBottom>Nozzle Selection</Typography>
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <Button
                    variant="contained"
                    onClick={() => selectNozzle(1)}
                    color={equipmentState.nozzle.active_nozzle === 1 ? 'success' : 'primary'}
                  >
                    Nozzle 1
                  </Button>
                  <Button
                    variant="contained"
                    onClick={() => selectNozzle(2)}
                    color={equipmentState.nozzle.active_nozzle === 2 ? 'success' : 'primary'}
                  >
                    Nozzle 2
                  </Button>
                </Box>
              </Box>

              {/* Shutter Control */}
              <Box>
                <Typography variant="subtitle2" gutterBottom>Shutter Control</Typography>
                <Button
                  variant="contained"
                  onClick={toggleShutter}
                  color={equipmentState.nozzle.shutter_state ? 'error' : 'primary'}
                >
                  {equipmentState.nozzle.shutter_state ? 'Close' : 'Open'} Shutter
                </Button>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      )}
    </Box>
  );
} 