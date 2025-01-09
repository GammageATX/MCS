import React, { useEffect, useState } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Button,
  Slider,
  FormControlLabel,
  Switch,
  Box,
  List,
  ListItem,
  ListItemText,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import { useWebSocket } from '../context/WebSocketContext';
import { API_CONFIG } from '../config/api';

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

interface InternalState {
  name: string;
  value: any;
  timestamp: string;
}

export default function EquipmentControl() {
  const [equipmentState, setEquipmentState] = useState<EquipmentState | null>(null);
  const [internalStates, setInternalStates] = useState<InternalState[]>([]);
  const [selectedInternalState, setSelectedInternalState] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { connected, lastMessage } = useWebSocket();

  // Fetch main equipment state
  useEffect(() => {
    const fetchEquipmentState = async () => {
      try {
        const response = await fetch(`${API_CONFIG.EQUIPMENT_SERVICE}/equipment/state`);
        if (!response.ok) {
          throw new Error(`Failed to fetch equipment state: ${response.status}`);
        }
        const data = await response.json();
        setEquipmentState(data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch equipment state:', err);
        setError('Failed to load equipment state');
      }
    };

    fetchEquipmentState();
    // Only poll if WebSocket is not connected
    const interval = !connected ? setInterval(fetchEquipmentState, 1000) : null;
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [connected]);

  // Update equipment state from WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      setEquipmentState(lastMessage);
    }
  }, [lastMessage]);

  // Fetch internal states
  useEffect(() => {
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
      }
    };

    fetchInternalStates();
    const interval = setInterval(fetchInternalStates, 1000);
    return () => clearInterval(interval);
  }, []);

  // Fetch individual internal state when selected
  useEffect(() => {
    if (!selectedInternalState) return;

    const fetchSelectedState = async () => {
      try {
        const response = await fetch(
          `${API_CONFIG.EQUIPMENT_SERVICE}/equipment/internal_states/${selectedInternalState}`
        );
        if (!response.ok) {
          throw new Error(`Failed to fetch state ${selectedInternalState}: ${response.status}`);
        }
        const data = await response.json();
        // Update the specific internal state in the list
        setInternalStates(prev => 
          prev.map(state => 
            state.name === selectedInternalState 
              ? { ...state, value: data.value, timestamp: data.timestamp }
              : state
          )
        );
      } catch (err) {
        console.error(`Failed to fetch state ${selectedInternalState}:`, err);
      }
    };

    fetchSelectedState();
    const interval = setInterval(fetchSelectedState, 1000);
    return () => clearInterval(interval);
  }, [selectedInternalState]);

  if (loading && !equipmentState) {
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
        {/* Main Equipment State */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Equipment State
            </Typography>
            {equipmentState && (
              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <Typography variant="subtitle2">Hardware Status</Typography>
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
                  <Typography variant="subtitle2">Process Status</Typography>
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
                  <Typography variant="subtitle2">System Ready</Typography>
                  <Chip 
                    label={equipmentState.process.process_ready ? 'Ready' : 'Not Ready'}
                    color={equipmentState.process.process_ready ? 'success' : 'warning'}
                    sx={{ mt: 1 }}
                  />
                </Grid>
              </Grid>
            )}
          </Paper>
        </Grid>

        {/* Gas System Controls */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Gas System
            </Typography>
            {equipmentState && (
              <Grid container spacing={2}>
                {/* Main Gas */}
                <Grid item xs={12}>
                  <Typography variant="subtitle2" gutterBottom>
                    Main Gas
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Button
                      variant="contained"
                      onClick={async () => {
                        try {
                          const response = await fetch(
                            `${API_CONFIG.EQUIPMENT_SERVICE}/equipment/gas/main/valve`,
                            {
                              method: 'PUT',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({ state: !equipmentState.gas.main_valve_state })
                            }
                          );
                          if (!response.ok) throw new Error('Failed to control valve');
                        } catch (err) {
                          setError('Failed to control main gas valve');
                        }
                      }}
                      color={equipmentState.gas.main_valve_state ? 'error' : 'primary'}
                      sx={{ mr: 2 }}
                    >
                      {equipmentState.gas.main_valve_state ? 'Close' : 'Open'} Valve
                    </Button>
                    <Typography>
                      Flow Rate: {equipmentState.gas.main_flow_rate.toFixed(1)} SLPM
                    </Typography>
                  </Box>
                  <Box sx={{ px: 2 }}>
                    <Slider
                      value={equipmentState.gas.main_flow_rate}
                      onChange={async (_, value) => {
                        try {
                          const response = await fetch(
                            `${API_CONFIG.EQUIPMENT_SERVICE}/equipment/gas/main/flow`,
                            {
                              method: 'POST',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({ flow_rate: value })
                            }
                          );
                          if (!response.ok) throw new Error('Failed to set flow rate');
                        } catch (err) {
                          setError('Failed to set main gas flow rate');
                        }
                      }}
                      min={0}
                      max={100}
                      step={0.1}
                      valueLabelDisplay="auto"
                      disabled={!equipmentState.gas.main_valve_state}
                    />
                  </Box>
                </Grid>

                {/* Feeder Gas */}
                <Grid item xs={12}>
                  <Typography variant="subtitle2" gutterBottom>
                    Feeder Gas
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Button
                      variant="contained"
                      onClick={async () => {
                        try {
                          const response = await fetch(
                            `${API_CONFIG.EQUIPMENT_SERVICE}/equipment/gas/feeder/valve`,
                            {
                              method: 'PUT',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({ state: !equipmentState.gas.feeder_valve_state })
                            }
                          );
                          if (!response.ok) throw new Error('Failed to control valve');
                        } catch (err) {
                          setError('Failed to control feeder gas valve');
                        }
                      }}
                      color={equipmentState.gas.feeder_valve_state ? 'error' : 'primary'}
                      sx={{ mr: 2 }}
                    >
                      {equipmentState.gas.feeder_valve_state ? 'Close' : 'Open'} Valve
                    </Button>
                    <Typography>
                      Flow Rate: {equipmentState.gas.feeder_flow_rate.toFixed(1)} SLPM
                    </Typography>
                  </Box>
                  <Box sx={{ px: 2 }}>
                    <Slider
                      value={equipmentState.gas.feeder_flow_rate}
                      onChange={async (_, value) => {
                        try {
                          const response = await fetch(
                            `${API_CONFIG.EQUIPMENT_SERVICE}/equipment/gas/feeder/flow`,
                            {
                              method: 'POST',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({ flow_rate: value })
                            }
                          );
                          if (!response.ok) throw new Error('Failed to set flow rate');
                        } catch (err) {
                          setError('Failed to set feeder gas flow rate');
                        }
                      }}
                      min={0}
                      max={10}
                      step={0.1}
                      valueLabelDisplay="auto"
                      disabled={!equipmentState.gas.feeder_valve_state}
                    />
                  </Box>
                </Grid>
              </Grid>
            )}
          </Paper>
        </Grid>

        {/* Vacuum System Controls */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Vacuum System
            </Typography>
            {equipmentState && (
              <Grid container spacing={2}>
                {/* Valve Controls */}
                <Grid item xs={12}>
                  <Typography variant="subtitle2" gutterBottom>
                    Valve Controls
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                    <Button
                      variant="contained"
                      onClick={async () => {
                        try {
                          const response = await fetch(
                            `${API_CONFIG.EQUIPMENT_SERVICE}/equipment/vacuum/gate`,
                            {
                              method: 'PUT',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({ state: !equipmentState.vacuum.gate_valve_state })
                            }
                          );
                          if (!response.ok) throw new Error('Failed to control gate valve');
                        } catch (err) {
                          setError('Failed to control gate valve');
                        }
                      }}
                      color={equipmentState.vacuum.gate_valve_state ? 'error' : 'primary'}
                    >
                      Gate Valve: {equipmentState.vacuum.gate_valve_state ? 'Close' : 'Open'}
                    </Button>
                    <Button
                      variant="contained"
                      onClick={async () => {
                        try {
                          const endpoint = equipmentState.vacuum.vent_valve_state
                            ? '/equipment/vacuum/vent/close'
                            : '/equipment/vacuum/vent/open';
                          const response = await fetch(
                            `${API_CONFIG.EQUIPMENT_SERVICE}${endpoint}`,
                            {
                              method: 'PUT',
                              headers: { 'Content-Type': 'application/json' }
                            }
                          );
                          if (!response.ok) throw new Error('Failed to control vent valve');
                        } catch (err) {
                          setError('Failed to control vent valve');
                        }
                      }}
                      color={equipmentState.vacuum.vent_valve_state ? 'error' : 'primary'}
                    >
                      Vent Valve: {equipmentState.vacuum.vent_valve_state ? 'Close' : 'Open'}
                    </Button>
                  </Box>
                </Grid>

                {/* Mechanical Pump Controls */}
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Mechanical Pump
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Button
                      variant="contained"
                      onClick={async () => {
                        try {
                          const response = await fetch(
                            `${API_CONFIG.EQUIPMENT_SERVICE}/equipment/vacuum/mechanical_pump/state`,
                            {
                              method: 'PUT',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({ state: !equipmentState.vacuum.mechanical_pump_state })
                            }
                          );
                          if (!response.ok) throw new Error('Failed to control mechanical pump state');
                        } catch (err) {
                          setError('Failed to control mechanical pump state');
                        }
                      }}
                      color={equipmentState.vacuum.mechanical_pump_state ? 'error' : 'primary'}
                    >
                      State: {equipmentState.vacuum.mechanical_pump_state ? 'On' : 'Off'}
                    </Button>
                    <Button
                      variant="contained"
                      onClick={async () => {
                        try {
                          const endpoint = equipmentState.vacuum.mechanical_pump_state
                            ? '/equipment/vacuum/mech/stop'
                            : '/equipment/vacuum/mech/start';
                          const response = await fetch(
                            `${API_CONFIG.EQUIPMENT_SERVICE}${endpoint}`,
                            {
                              method: 'PUT',
                              headers: { 'Content-Type': 'application/json' }
                            }
                          );
                          if (!response.ok) throw new Error('Failed to start/stop mechanical pump');
                        } catch (err) {
                          setError('Failed to start/stop mechanical pump');
                        }
                      }}
                    >
                      {equipmentState.vacuum.mechanical_pump_state ? 'Stop' : 'Start'} Pump
                    </Button>
                  </Box>
                </Grid>

                {/* Booster Pump Controls */}
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Booster Pump
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Button
                      variant="contained"
                      onClick={async () => {
                        try {
                          const response = await fetch(
                            `${API_CONFIG.EQUIPMENT_SERVICE}/equipment/vacuum/booster_pump/state`,
                            {
                              method: 'PUT',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({ state: !equipmentState.vacuum.booster_pump_state })
                            }
                          );
                          if (!response.ok) throw new Error('Failed to control booster pump state');
                        } catch (err) {
                          setError('Failed to control booster pump state');
                        }
                      }}
                      color={equipmentState.vacuum.booster_pump_state ? 'error' : 'primary'}
                      disabled={!equipmentState.vacuum.mechanical_pump_state}
                    >
                      State: {equipmentState.vacuum.booster_pump_state ? 'On' : 'Off'}
                    </Button>
                    <Button
                      variant="contained"
                      onClick={async () => {
                        try {
                          const endpoint = equipmentState.vacuum.booster_pump_state
                            ? '/equipment/vacuum/booster/stop'
                            : '/equipment/vacuum/booster/start';
                          const response = await fetch(
                            `${API_CONFIG.EQUIPMENT_SERVICE}${endpoint}`,
                            {
                              method: 'PUT',
                              headers: { 'Content-Type': 'application/json' }
                            }
                          );
                          if (!response.ok) throw new Error('Failed to start/stop booster pump');
                        } catch (err) {
                          setError('Failed to start/stop booster pump');
                        }
                      }}
                      disabled={!equipmentState.vacuum.mechanical_pump_state}
                    >
                      {equipmentState.vacuum.booster_pump_state ? 'Stop' : 'Start'} Pump
                    </Button>
                  </Box>
                </Grid>

                {/* Chamber Pressure Display */}
                <Grid item xs={12}>
                  <Typography variant="subtitle2" gutterBottom>
                    Chamber Pressure
                  </Typography>
                  <Typography variant="h4" align="center">
                    {equipmentState.pressure.chamber.toExponential(2)} Torr
                  </Typography>
                </Grid>
              </Grid>
            )}
          </Paper>
        </Grid>

        {/* Powder Feed System Controls */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Powder Feed System
            </Typography>
            {equipmentState && (
              <Grid container spacing={2}>
                {/* Feeder Controls */}
                <Grid item xs={12}>
                  <Typography variant="subtitle2" gutterBottom>
                    Feeder Control
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Button
                      variant="contained"
                      onClick={async () => {
                        try {
                          const response = await fetch(
                            `${API_CONFIG.EQUIPMENT_SERVICE}/equipment/feeder/1/state`,
                            {
                              method: 'PUT',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({ state: !equipmentState.feeder.running })
                            }
                          );
                          if (!response.ok) throw new Error('Failed to control feeder');
                        } catch (err) {
                          setError('Failed to control feeder state');
                        }
                      }}
                      color={equipmentState.feeder.running ? 'error' : 'primary'}
                      sx={{ mr: 2 }}
                    >
                      {equipmentState.feeder.running ? 'Stop' : 'Start'} Feeder
                    </Button>
                    <Typography>
                      Frequency: {equipmentState.feeder.frequency.toFixed(1)} Hz
                    </Typography>
                  </Box>
                  <Box sx={{ px: 2 }}>
                    <Slider
                      value={equipmentState.feeder.frequency}
                      onChange={async (_, value) => {
                        try {
                          const response = await fetch(
                            `${API_CONFIG.EQUIPMENT_SERVICE}/equipment/feeder/1/frequency`,
                            {
                              method: 'POST',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({ frequency: value })
                            }
                          );
                          if (!response.ok) throw new Error('Failed to set frequency');
                        } catch (err) {
                          setError('Failed to set feeder frequency');
                        }
                      }}
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
                </Grid>

                {/* Feeder Status */}
                <Grid item xs={12}>
                  <List dense>
                    <ListItem>
                      <ListItemText
                        primary="Operating State"
                        secondary={equipmentState.feeder.running ? 'Running' : 'Stopped'}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Feed Rate"
                        secondary={`${equipmentState.feeder.frequency.toFixed(1)} Hz`}
                      />
                    </ListItem>
                  </List>
                </Grid>
              </Grid>
            )}
          </Paper>
        </Grid>

        {/* Deagglomerator Controls */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Deagglomerator System
            </Typography>
            {equipmentState && (
              <Grid container spacing={2}>
                {/* Speed Control */}
                <Grid item xs={12}>
                  <Typography variant="subtitle2" gutterBottom>
                    Speed Control
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Box sx={{ display: 'flex', gap: 2 }}>
                      <Button
                        variant="contained"
                        onClick={async () => {
                          try {
                            const response = await fetch(
                              `${API_CONFIG.EQUIPMENT_SERVICE}/equipment/deagg/1/duty_cycle`,
                              {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ duty_cycle: 35 }) // Off
                              }
                            );
                            if (!response.ok) throw new Error('Failed to stop deagglomerator');
                          } catch (err) {
                            setError('Failed to control deagglomerator');
                          }
                        }}
                        color={equipmentState.deagglomerator.duty_cycle === 35 ? 'error' : 'primary'}
                      >
                        {equipmentState.deagglomerator.duty_cycle === 35 ? 'Stopped' : 'Stop'}
                      </Button>
                      <Button
                        variant="contained"
                        onClick={async () => {
                          try {
                            const response = await fetch(
                              `${API_CONFIG.EQUIPMENT_SERVICE}/equipment/deagg/1/duty_cycle`,
                              {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ duty_cycle: 30 }) // Low Speed
                              }
                            );
                            if (!response.ok) throw new Error('Failed to set low speed');
                          } catch (err) {
                            setError('Failed to control deagglomerator');
                          }
                        }}
                        color={equipmentState.deagglomerator.duty_cycle === 30 ? 'success' : 'primary'}
                        disabled={equipmentState.deagglomerator.duty_cycle === 35}
                      >
                        Low
                      </Button>
                      <Button
                        variant="contained"
                        onClick={async () => {
                          try {
                            const response = await fetch(
                              `${API_CONFIG.EQUIPMENT_SERVICE}/equipment/deagg/1/duty_cycle`,
                              {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ duty_cycle: 25 }) // Medium Speed
                              }
                            );
                            if (!response.ok) throw new Error('Failed to set medium speed');
                          } catch (err) {
                            setError('Failed to control deagglomerator');
                          }
                        }}
                        color={equipmentState.deagglomerator.duty_cycle === 25 ? 'success' : 'primary'}
                        disabled={equipmentState.deagglomerator.duty_cycle === 35}
                      >
                        Medium
                      </Button>
                      <Button
                        variant="contained"
                        onClick={async () => {
                          try {
                            const response = await fetch(
                              `${API_CONFIG.EQUIPMENT_SERVICE}/equipment/deagg/1/duty_cycle`,
                              {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ duty_cycle: 20 }) // High Speed
                              }
                            );
                            if (!response.ok) throw new Error('Failed to set high speed');
                          } catch (err) {
                            setError('Failed to control deagglomerator');
                          }
                        }}
                        color={equipmentState.deagglomerator.duty_cycle === 20 ? 'success' : 'primary'}
                        disabled={equipmentState.deagglomerator.duty_cycle === 35}
                      >
                        High
                      </Button>
                    </Box>
                  </Box>
                </Grid>

                {/* Status Display */}
                <Grid item xs={12}>
                  <List dense>
                    <ListItem>
                      <ListItemText
                        primary="Current Speed"
                        secondary={
                          equipmentState.deagglomerator.duty_cycle === 35 ? 'Stopped' :
                          equipmentState.deagglomerator.duty_cycle === 30 ? 'Low' :
                          equipmentState.deagglomerator.duty_cycle === 25 ? 'Medium' :
                          equipmentState.deagglomerator.duty_cycle === 20 ? 'High' :
                          `Custom (${equipmentState.deagglomerator.duty_cycle}%)`
                        }
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Duty Cycle"
                        secondary={`${equipmentState.deagglomerator.duty_cycle}%`}
                      />
                    </ListItem>
                  </List>
                </Grid>
              </Grid>
            )}
          </Paper>
        </Grid>

        {/* Nozzle Control System */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Nozzle System
            </Typography>
            {equipmentState && (
              <Grid container spacing={2}>
                {/* Nozzle Selection */}
                <Grid item xs={12}>
                  <Typography variant="subtitle2" gutterBottom>
                    Nozzle Selection
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <Button
                      variant="contained"
                      onClick={async () => {
                        try {
                          const response = await fetch(
                            `${API_CONFIG.EQUIPMENT_SERVICE}/equipment/nozzle/select`,
                            {
                              method: 'PUT',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({ nozzle: 1 })
                            }
                          );
                          if (!response.ok) throw new Error('Failed to select nozzle');
                        } catch (err) {
                          setError('Failed to select nozzle');
                        }
                      }}
                      color={equipmentState.nozzle.active_nozzle === 1 ? 'success' : 'primary'}
                    >
                      Nozzle 1
                    </Button>
                    <Button
                      variant="contained"
                      onClick={async () => {
                        try {
                          const response = await fetch(
                            `${API_CONFIG.EQUIPMENT_SERVICE}/equipment/nozzle/select`,
                            {
                              method: 'PUT',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({ nozzle: 2 })
                            }
                          );
                          if (!response.ok) throw new Error('Failed to select nozzle');
                        } catch (err) {
                          setError('Failed to select nozzle');
                        }
                      }}
                      color={equipmentState.nozzle.active_nozzle === 2 ? 'success' : 'primary'}
                    >
                      Nozzle 2
                    </Button>
                  </Box>
                </Grid>

                {/* Shutter Control */}
                <Grid item xs={12}>
                  <Typography variant="subtitle2" gutterBottom>
                    Shutter Control
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <Button
                      variant="contained"
                      onClick={async () => {
                        try {
                          const endpoint = equipmentState.nozzle.shutter_state
                            ? '/equipment/nozzle/shutter/close'
                            : '/equipment/nozzle/shutter/open';
                          const response = await fetch(
                            `${API_CONFIG.EQUIPMENT_SERVICE}${endpoint}`,
                            {
                              method: 'PUT',
                              headers: { 'Content-Type': 'application/json' }
                            }
                          );
                          if (!response.ok) throw new Error('Failed to control shutter');
                        } catch (err) {
                          setError('Failed to control shutter');
                        }
                      }}
                      color={equipmentState.nozzle.shutter_state ? 'error' : 'primary'}
                    >
                      {equipmentState.nozzle.shutter_state ? 'Close' : 'Open'} Shutter
                    </Button>
                  </Box>
                </Grid>

                {/* Status Display */}
                <Grid item xs={12}>
                  <List dense>
                    <ListItem>
                      <ListItemText
                        primary="Active Nozzle"
                        secondary={`Nozzle ${equipmentState.nozzle.active_nozzle}`}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Shutter State"
                        secondary={equipmentState.nozzle.shutter_state ? 'Open' : 'Closed'}
                      />
                    </ListItem>
                  </List>
                </Grid>
              </Grid>
            )}
          </Paper>
        </Grid>

        {/* Internal States */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Internal States
            </Typography>
            <List>
              {internalStates.map((state) => (
                <ListItem 
                  key={state.name}
                  button
                  selected={selectedInternalState === state.name}
                  onClick={() => setSelectedInternalState(state.name)}
                >
                  <ListItemText
                    primary={state.name}
                    secondary={`Value: ${JSON.stringify(state.value)} (${new Date(state.timestamp).toLocaleString()})`}
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