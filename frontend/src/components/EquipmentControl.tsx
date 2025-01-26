import React, { useState, useEffect } from 'react';
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
  Chip,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
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
  main_flow_setpoint: number;
  main_flow_actual: number;
  feeder_flow_setpoint: number;
  feeder_flow_actual: number;
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
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const pollEquipmentState = async () => {
      try {
        const response = await fetch(`${API_CONFIG.COMMUNICATION_SERVICE}/equipment/state`);
        if (!response.ok) {
          throw new Error('Failed to fetch equipment state');
        }
        const data = await response.json();
        setEquipmentState(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching equipment state:', err);
        setError('Failed to fetch equipment state');
      }
    };

    // Initial fetch
    pollEquipmentState();

    // Set up polling interval
    const interval = setInterval(pollEquipmentState, 1000);

    return () => clearInterval(interval);
  }, []);

  // Control Functions
  const setMainGasFlow = async (value: number) => {
    try {
      const response = await fetch(`${API_CONFIG.COMMUNICATION_SERVICE}/equipment/gas/main/flow`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ flow_setpoint: value })
      });
      if (!response.ok) throw new Error('Failed to set main gas flow');
      // State will be updated by next poll
    } catch (err) {
      setError('Failed to set main gas flow rate');
      console.error(err);
    }
  };

  const setFeederGasFlow = async (value: number) => {
    try {
      const response = await fetch(`${API_CONFIG.COMMUNICATION_SERVICE}/equipment/gas/feeder/flow`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ flow_setpoint: value })
      });
      if (!response.ok) throw new Error('Failed to set feeder gas flow');
      // State will be updated by next poll
    } catch (err) {
      setError('Failed to set feeder gas flow rate');
      console.error(err);
    }
  };

  const toggleMainGasValve = async () => {
    if (!equipmentState) return;
    const newState = !equipmentState.gas.main_valve_state;
    try {
      const response = await fetch(`${API_CONFIG.COMMUNICATION_SERVICE}/equipment/gas/main/valve`, {
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
      const response = await fetch(`${API_CONFIG.COMMUNICATION_SERVICE}/equipment/gas/feeder/valve`, {
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
      const response = await fetch(`${API_CONFIG.COMMUNICATION_SERVICE}/equipment/vacuum/gate_valve`, {
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
    try {
      const response = await fetch(`${API_CONFIG.COMMUNICATION_SERVICE}/equipment/vacuum/vent_valve`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ open: newState })
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
      const response = await fetch(`${API_CONFIG.COMMUNICATION_SERVICE}/equipment/vacuum/mechanical_pump`, {
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
      const response = await fetch(`${API_CONFIG.COMMUNICATION_SERVICE}/equipment/vacuum/booster_pump`, {
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
      const response = await fetch(`${API_CONFIG.COMMUNICATION_SERVICE}/equipment/feeder/frequency`, {
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
      const response = await fetch(`${API_CONFIG.COMMUNICATION_SERVICE}/equipment/feeder/state`, {
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
      const response = await fetch(
        `${API_CONFIG.COMMUNICATION_SERVICE}/equipment/deagglomerator/duty_cycle`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ duty_cycle: value })
        }
      );
      if (!response.ok) throw new Error('Failed to set deagglomerator duty cycle');
      
      if (equipmentState) {
        setEquipmentState({
          ...equipmentState,
          deagglomerator: {
            ...equipmentState.deagglomerator,
            duty_cycle: value
          }
        });
      }
    } catch (err) {
      setError('Failed to set deagglomerator duty cycle');
    }
  };

  const setDeagglomeratorFrequency = async (value: number) => {
    try {
      const response = await fetch(
        `${API_CONFIG.COMMUNICATION_SERVICE}/equipment/deagglomerator/frequency`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ frequency: value })
        }
      );
      if (!response.ok) throw new Error('Failed to set deagglomerator frequency');
      
      if (equipmentState) {
        setEquipmentState({
          ...equipmentState,
          deagglomerator: {
            ...equipmentState.deagglomerator,
            frequency: value
          }
        });
      }
    } catch (err) {
      setError('Failed to set deagglomerator frequency');
    }
  };

  // Alias functions to match render function calls
  const setDeaggDutyCycle = setDeagglomeratorDutyCycle;
  const setDeaggFrequency = setDeagglomeratorFrequency;

  const selectNozzle = async (nozzleId: number) => {
    try {
      const response = await fetch(`${API_CONFIG.COMMUNICATION_SERVICE}/equipment/nozzle/select`, {
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
      const response = await fetch(`${API_CONFIG.COMMUNICATION_SERVICE}/equipment/nozzle/shutter`, {
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

  const togglePump = async (type: 'mechanical' | 'booster', start?: boolean) => {
    if (!equipmentState) return;
    
    const currentState = type === 'mechanical' 
      ? equipmentState.vacuum.mechanical_pump_state
      : equipmentState.vacuum.booster_pump_state;
    
    const newState = start ?? !currentState;
    const endpoint = type === 'mechanical' ? 'mech' : 'booster';
    const action = newState ? 'start' : 'stop';

    try {
      const response = await fetch(
        `${API_CONFIG.COMMUNICATION_SERVICE}/equipment/vacuum/${endpoint}/${action}`,
        { method: 'PUT' }
      );
      if (!response.ok) throw new Error(`Failed to ${action} ${type} pump`);
      
      // Update local state
      if (equipmentState) {
        setEquipmentState({
          ...equipmentState,
          vacuum: {
            ...equipmentState.vacuum,
            [`${type}_pump_state`]: newState
          }
        });
      }
    } catch (err) {
      setError(`Failed to control ${type} pump`);
    }
  };

  const renderProcessStatus = () => {
    if (!equipmentState) return null;

    return (
      <Paper sx={{ p: 2, mb: 2, backgroundColor: '#f8f9fa' }}>
        <Typography variant="h6" gutterBottom>Process Status</Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            p: 1, 
            borderRadius: 1,
            backgroundColor: equipmentState.process.gas_flow_stable ? '#e8f5e9' : '#ffebee'
          }}>
            <Typography sx={{ flex: 1 }}>Gas Flow State</Typography>
            <Chip 
              label={equipmentState.process.gas_flow_stable ? "Stable" : "Unstable"}
              color={equipmentState.process.gas_flow_stable ? "success" : "error"}
              size="small"
            />
          </Box>
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            p: 1, 
            borderRadius: 1,
            backgroundColor: equipmentState.process.powder_feed_active ? '#e8f5e9' : '#ffebee'
          }}>
            <Typography sx={{ flex: 1 }}>Powder Feed</Typography>
            <Chip 
              label={equipmentState.process.powder_feed_active ? "Active" : "Inactive"}
              color={equipmentState.process.powder_feed_active ? "success" : "error"}
              size="small"
            />
          </Box>
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            p: 1, 
            borderRadius: 1,
            backgroundColor: equipmentState.process.process_ready ? '#e8f5e9' : '#ffebee'
          }}>
            <Typography sx={{ flex: 1 }}>Process State</Typography>
            <Chip 
              label={equipmentState.process.process_ready ? "Ready" : "Not Ready"}
              color={equipmentState.process.process_ready ? "success" : "error"}
              size="small"
            />
          </Box>
        </Box>
      </Paper>
    );
  };

  const renderGasControls = () => {
    if (!equipmentState) return null;
    
    return (
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>Gas Control</Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
              <Box>
                <Typography variant="subtitle1" sx={{ fontWeight: 500, fontSize: '1.1rem' }}>
                  Main Flow Rate
                </Typography>
                <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                  {equipmentState.gas.main_flow_actual.toFixed(1)} SLPM
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                <Typography variant="body2">Set:</Typography>
                <TextField
                  type="number"
                  value={equipmentState.gas.main_flow_setpoint.toFixed(1)}
                  onChange={(e) => setMainGasFlow(parseFloat(e.target.value))}
                  inputProps={{
                    min: 0,
                    max: 100,
                    step: 0.1,
                    style: { 
                      width: '50px', 
                      textAlign: 'right',
                      fontSize: '0.875rem',
                    }
                  }}
                  sx={{
                    '& input::-webkit-outer-spin-button, & input::-webkit-inner-spin-button': {
                      WebkitAppearance: 'none',
                      margin: 0,
                    },
                    '& input[type=number]': {
                      MozAppearance: 'textfield',
                    },
                    width: '80px'
                  }}
                  size="small"
                  variant="outlined"
                />
                <Typography variant="body2">SLPM</Typography>
                <Button
                  variant="contained"
                  onClick={() => setMainGasFlow(equipmentState.gas.main_flow_setpoint)}
                  size="small"
                  sx={{ 
                    width: '80px',
                    py: 0.5,
                    fontSize: '0.875rem'
                  }}
                >
                  SET
                </Button>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
              <Slider
                value={equipmentState.gas.main_flow_setpoint}
                onChange={(_, value) => setMainGasFlow(value as number)}
                min={0}
                max={100}
                step={0.1}
                sx={{ flex: 1 }}
              />
              <Button
                variant="contained"
                onClick={toggleMainGasValve}
                color={equipmentState.gas.main_valve_state ? "error" : "primary"}
                size="small"
                sx={{ 
                  width: '80px',
                  py: 0.5,
                  fontSize: '0.875rem'
                }}
              >
                {equipmentState.gas.main_valve_state ? "CLOSE" : "OPEN"}
              </Button>
            </Box>
          </Box>

          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
              <Box>
                <Typography variant="subtitle1" sx={{ fontWeight: 500, fontSize: '1.1rem' }}>
                  Feeder Flow Rate
                </Typography>
                <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                  {equipmentState.gas.feeder_flow_actual.toFixed(1)} SLPM
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                <Typography variant="body2">Set:</Typography>
                <TextField
                  type="number"
                  value={equipmentState.gas.feeder_flow_setpoint.toFixed(1)}
                  onChange={(e) => setFeederGasFlow(parseFloat(e.target.value))}
                  inputProps={{
                    min: 0,
                    max: 10,
                    step: 0.1,
                    style: { 
                      width: '50px', 
                      textAlign: 'right',
                      fontSize: '0.875rem',
                    }
                  }}
                  sx={{
                    '& input::-webkit-outer-spin-button, & input::-webkit-inner-spin-button': {
                      WebkitAppearance: 'none',
                      margin: 0,
                    },
                    '& input[type=number]': {
                      MozAppearance: 'textfield',
                    },
                    width: '80px'
                  }}
                  size="small"
                  variant="outlined"
                />
                <Typography variant="body2">SLPM</Typography>
                <Button
                  variant="contained"
                  onClick={() => setFeederGasFlow(equipmentState.gas.feeder_flow_setpoint)}
                  size="small"
                  sx={{ 
                    width: '80px',
                    py: 0.5,
                    fontSize: '0.875rem'
                  }}
                >
                  SET
                </Button>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
              <Slider
                value={equipmentState.gas.feeder_flow_setpoint}
                onChange={(_, value) => setFeederGasFlow(value as number)}
                min={0}
                max={10}
                step={0.1}
                sx={{ flex: 1 }}
              />
              <Button
                variant="contained"
                onClick={toggleFeederGasValve}
                color={equipmentState.gas.feeder_valve_state ? "error" : "primary"}
                size="small"
                sx={{ 
                  width: '80px',
                  py: 0.5,
                  fontSize: '0.875rem'
                }}
              >
                {equipmentState.gas.feeder_valve_state ? "CLOSE" : "OPEN"}
              </Button>
            </Box>
          </Box>
        </Box>
      </Paper>
    );
  };

  const renderVacuumControls = () => {
    if (!equipmentState) return null;

    return (
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>Vacuum Control</Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Box sx={{ textAlign: 'center', mb: 2 }}>
            <Typography variant="h4" sx={{ fontFamily: 'monospace' }}>
              {equipmentState.vacuum.chamber_pressure.toExponential(2)} Torr
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              onClick={toggleGateValve}
              color={equipmentState.vacuum.gate_valve_state ? "error" : "primary"}
              size="small"
              sx={{ flex: 1, minWidth: 120 }}
            >
              Gate Valve {equipmentState.vacuum.gate_valve_state ? "Close" : "Open"}
            </Button>
            <Button
              variant="contained"
              onClick={toggleVentValve}
              color={equipmentState.vacuum.vent_valve_state ? "error" : "primary"}
              size="small"
              sx={{ flex: 1, minWidth: 120 }}
            >
              Vent {equipmentState.vacuum.vent_valve_state ? "Close" : "Open"}
            </Button>
          </Box>

          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              onClick={() => togglePump('mechanical')}
              color={equipmentState.vacuum.mechanical_pump_state ? "error" : "primary"}
              size="small"
              sx={{ flex: 1, minWidth: 120 }}
            >
              Mech Pump {equipmentState.vacuum.mechanical_pump_state ? "Stop" : "Start"}
            </Button>
            <Button
              variant="contained"
              onClick={() => togglePump('booster')}
              color={equipmentState.vacuum.booster_pump_state ? "error" : "primary"}
              size="small"
              disabled={!equipmentState.vacuum.mechanical_pump_state}
              sx={{ flex: 1, minWidth: 120 }}
            >
              Booster {equipmentState.vacuum.booster_pump_state ? "Stop" : "Start"}
            </Button>
          </Box>
        </Box>
      </Paper>
    );
  };

  const renderFeederControls = () => {
    if (!equipmentState) return null;

    return (
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>Feeder Control</Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography>Frequency</Typography>
              <Typography>{equipmentState.feeder.frequency} Hz</Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
              <Slider
                value={equipmentState.feeder.frequency}
                onChange={(_, value) => setFeederFrequency(value as number)}
                min={200}
                max={1200}
                step={200}
                disabled={!equipmentState.feeder.running}
                marks={[
                  { value: 200, label: '200' },
                  { value: 400, label: '400' },
                  { value: 600, label: '600' },
                  { value: 800, label: '800' },
                  { value: 1000, label: '1000' },
                  { value: 1200, label: '1200' }
                ]}
                sx={{ flex: 1 }}
              />
              <Button
                variant="contained"
                onClick={toggleFeeder}
                color={equipmentState.feeder.running ? "error" : "primary"}
                size="small"
              >
                {equipmentState.feeder.running ? "Stop" : "Start"}
              </Button>
            </Box>
          </Box>
        </Box>
      </Paper>
    );
  };

  const renderNozzleControls = () => {
    if (!equipmentState) return null;

    return (
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>Nozzle Control</Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            onClick={toggleShutter}
            color={equipmentState.nozzle.shutter_state ? "error" : "primary"}
            size="small"
            sx={{ flex: 1 }}
          >
            Shutter {equipmentState.nozzle.shutter_state ? "Close" : "Open"}
          </Button>
          <Button
            variant="contained"
            onClick={() => selectNozzle(equipmentState.nozzle.active_nozzle === 1 ? 2 : 1)}
            size="small"
            sx={{ flex: 1 }}
          >
            Nozzle {equipmentState.nozzle.active_nozzle === 1 ? "2" : "1"}
          </Button>
        </Box>
      </Paper>
    );
  };

  const renderDeagglomeratorControls = () => {
    if (!equipmentState) return null;

    return (
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>Deagglomerator Control</Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Button
            variant="contained"
            onClick={() => setDeaggDutyCycle(35)}
            color={equipmentState.deagglomerator.duty_cycle === 35 ? "error" : "primary"}
            size="small"
            sx={{ flex: 1, minWidth: 100 }}
          >
            Stop
          </Button>
          <Button
            variant="contained"
            onClick={() => setDeaggDutyCycle(30)}
            color={equipmentState.deagglomerator.duty_cycle === 30 ? "success" : "primary"}
            size="small"
            sx={{ flex: 1, minWidth: 100 }}
          >
            Low
          </Button>
          <Button
            variant="contained"
            onClick={() => setDeaggDutyCycle(25)}
            color={equipmentState.deagglomerator.duty_cycle === 25 ? "success" : "primary"}
            size="small"
            sx={{ flex: 1, minWidth: 100 }}
          >
            Medium
          </Button>
          <Button
            variant="contained"
            onClick={() => setDeaggDutyCycle(20)}
            color={equipmentState.deagglomerator.duty_cycle === 20 ? "success" : "primary"}
            size="small"
            sx={{ flex: 1, minWidth: 100 }}
          >
            High
          </Button>
        </Box>
      </Paper>
    );
  };

  return (
    <Box sx={{ p: 3, maxWidth: 800, margin: '0 auto' }}>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      {equipmentState ? (
        <>
          {renderProcessStatus()}
          {renderGasControls()}
          {renderVacuumControls()}
          {renderFeederControls()}
          {renderNozzleControls()}
          {renderDeagglomeratorControls()}
        </>
      ) : (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      )}
    </Box>
  );
} 