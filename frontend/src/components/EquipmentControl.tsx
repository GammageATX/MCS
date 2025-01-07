import React from 'react';
import {
  Grid,
  Paper,
  Typography,
  Button,
  Slider,
  FormControlLabel,
  Switch,
} from '@mui/material';
import { useWebSocket } from '../context/WebSocketContext';

const API_BASE_URL = 'http://localhost:8003';

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

function getDeaggSpeed(dutyCycle: number): string {
  return `${(dutyCycle * 100).toFixed(1)}%`;
}

type AxisName = 'x' | 'y' | 'z';
type AxisKey = 'x_axis' | 'y_axis' | 'z_axis';

function getAxisKey(axis: AxisName): AxisKey {
  return `${axis}_axis`;
}

export default function EquipmentControl() {
  const { equipment } = useWebSocket();

  // Gas Control Functions
  const controlGas = async (type: 'main' | 'feeder', action: 'valve' | 'flow', value: boolean | number) => {
    try {
      if (!equipment) return;

      if (action === 'valve') {
        await fetch(`${API_BASE_URL}/equipment/gas/${type}/valve`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ open: value })
        });
      } else {
        await fetch(`${API_BASE_URL}/equipment/gas/${type}/flow`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ flow_rate: value })
        });
      }
    } catch (error) {
      console.error(`Failed to control ${type} gas ${action}:`, error);
    }
  };

  // Vacuum Control Functions
  const controlVacuum = async (
    component: 'gate' | 'mechanical_pump' | 'booster_pump' | 'vent',
    action: 'open' | 'close' | 'start' | 'stop'
  ) => {
    try {
      if (!equipment) return;

      if (component === 'gate') {
        await fetch(`${API_BASE_URL}/equipment/vacuum/gate`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ position: action })
        });
      } else if (component === 'vent') {
        // TODO: Add vent valve control endpoint
      } else {
        const isStart = action === 'start';
        await fetch(`${API_BASE_URL}/equipment/vacuum/${component}/state`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ start: isStart })
        });
      }
    } catch (error) {
      console.error(`Failed to control vacuum ${component}:`, error);
    }
  };

  // Feeder Control Functions
  const controlFeeder = async (id: 1 | 2, action: 'start' | 'stop' | 'frequency', value?: number) => {
    try {
      if (!equipment) return;

      if (action === 'frequency' && value !== undefined) {
        await fetch(`${API_BASE_URL}/equipment/feeder/${id}/frequency`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ frequency: value })
        });
      } else {
        await fetch(`${API_BASE_URL}/equipment/feeder/${id}/state`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ running: action === 'start' })
        });
      }
    } catch (error) {
      console.error(`Failed to control feeder ${id}:`, error);
    }
  };

  // Deagglomerator Control Functions
  const controlDeagglomerator = async (id: 1 | 2, action: 'duty_cycle' | 'frequency', value: number) => {
    try {
      if (!equipment) return;

      await fetch(`${API_BASE_URL}/equipment/deagg/${id}/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          duty_cycle: action === 'duty_cycle' ? value : equipment.deagglomerator.duty_cycle,
          frequency: action === 'frequency' ? value : 0 // TODO: Add frequency to state
        })
      });
    } catch (error) {
      console.error(`Failed to control deagglomerator ${id}:`, error);
    }
  };

  // Nozzle Control Functions
  const controlNozzle = async (action: 'shutter' | 'select', value: boolean | number) => {
    try {
      if (!equipment) return;

      if (action === 'shutter') {
        await fetch(`${API_BASE_URL}/equipment/nozzle/shutter`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ open: value })
        });
      } else {
        await fetch(`${API_BASE_URL}/equipment/nozzle/select`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ nozzle_id: value })
        });
      }
    } catch (error) {
      console.error('Failed to control nozzle:', error);
    }
  };

  // Motion Control Functions
  const handleJog = async (axis: AxisName, direction: 1 | -1) => {
    try {
      if (!equipment) return;

      await fetch(`${API_BASE_URL}/motion/jog/${axis}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          distance: direction * 1.0, // 1mm jog
          velocity: 10.0 // 10mm/s
        })
      });
    } catch (error) {
      console.error(`Failed to jog ${axis} axis:`, error);
    }
  };

  if (!equipment) {
    return <Typography>Loading equipment state...</Typography>;
  }

  return (
    <Grid container spacing={2}>
      {/* Gas Control */}
      <Grid item xs={12} md={6}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>Gas Control</Typography>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Typography>Main Gas</Typography>
              <Button
                variant="contained"
                onClick={() => controlGas('main', 'valve', !equipment.gas.main_valve_state)}
              >
                {equipment.gas.main_valve_state ? 'Close' : 'Open'} Valve
              </Button>
              <Slider
                value={equipment.gas.main_flow_rate}
                onChange={(_, value) => controlGas('main', 'flow', value as number)}
                min={0}
                max={100}
                valueLabelDisplay="auto"
                disabled={!equipment.gas.main_valve_state}
              />
              <Typography variant="caption">
                Flow: {equipment.gas.main_flow_rate.toFixed(1)} SLPM
              </Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography>Feeder Gas</Typography>
              <Button
                variant="contained"
                onClick={() => controlGas('feeder', 'valve', !equipment.gas.feeder_valve_state)}
              >
                {equipment.gas.feeder_valve_state ? 'Close' : 'Open'} Valve
              </Button>
              <Slider
                value={equipment.gas.feeder_flow_rate}
                onChange={(_, value) => controlGas('feeder', 'flow', value as number)}
                min={0}
                max={10}
                valueLabelDisplay="auto"
                disabled={!equipment.gas.feeder_valve_state}
              />
              <Typography variant="caption">
                Flow: {equipment.gas.feeder_flow_rate.toFixed(1)} SLPM
              </Typography>
            </Grid>
          </Grid>
        </Paper>
      </Grid>

      {/* Vacuum Control */}
      <Grid item xs={12} md={6}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>Vacuum Control</Typography>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Typography>Chamber Pressure</Typography>
              <Typography variant="h6">
                {equipment.pressure.chamber.toExponential(2)} Torr
              </Typography>
            </Grid>
            <Grid item xs={6}>
              <Button
                variant="contained"
                onClick={() => controlVacuum('gate', equipment.vacuum.gate_valve_state ? 'close' : 'open')}
              >
                Gate Valve {equipment.vacuum.gate_valve_state ? 'Close' : 'Open'}
              </Button>
              <Button
                variant="contained"
                onClick={() => controlVacuum('vent', equipment.vacuum.vent_valve_state ? 'close' : 'open')}
              >
                Vent Valve {equipment.vacuum.vent_valve_state ? 'Close' : 'Open'}
              </Button>
            </Grid>
            <Grid item xs={6}>
              <Button
                variant="contained"
                onClick={() => controlVacuum('mechanical_pump', equipment.vacuum.mechanical_pump_state ? 'stop' : 'start')}
              >
                Mechanical Pump {equipment.vacuum.mechanical_pump_state ? 'Stop' : 'Start'}
              </Button>
            </Grid>
            <Grid item xs={6}>
              <Button
                variant="contained"
                onClick={() => controlVacuum('booster_pump', equipment.vacuum.booster_pump_state ? 'stop' : 'start')}
                disabled={!equipment.vacuum.mechanical_pump_state}
              >
                Booster Pump {equipment.vacuum.booster_pump_state ? 'Stop' : 'Start'}
              </Button>
            </Grid>
          </Grid>
        </Paper>
      </Grid>

      {/* Feeder Control */}
      <Grid item xs={12} md={6}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>Feeder Control</Typography>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Typography>Feeder 1</Typography>
              <Button
                variant="contained"
                onClick={() => controlFeeder(1, equipment.feeder.running ? 'stop' : 'start')}
              >
                {equipment.feeder.running ? 'Stop' : 'Start'}
              </Button>
              <Slider
                value={equipment.feeder.frequency}
                onChange={(_, value) => controlFeeder(1, 'frequency', value as number)}
                min={0}
                max={100}
                valueLabelDisplay="auto"
                disabled={!equipment.feeder.running}
              />
              <Typography variant="caption">
                Frequency: {equipment.feeder.frequency.toFixed(1)} Hz
              </Typography>
            </Grid>
          </Grid>
        </Paper>
      </Grid>

      {/* Deagglomerator Control */}
      <Grid item xs={12} md={6}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>Deagglomerator Control</Typography>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Typography>Deagglomerator 1</Typography>
              <Slider
                value={equipment.deagglomerator.duty_cycle}
                onChange={(_, value) => controlDeagglomerator(1, 'duty_cycle', value as number)}
                min={0}
                max={100}
                valueLabelDisplay="auto"
              />
              <Typography variant="caption">
                Speed: {getDeaggSpeed(equipment.deagglomerator.duty_cycle)}
              </Typography>
            </Grid>
          </Grid>
        </Paper>
      </Grid>

      {/* Nozzle Control */}
      <Grid item xs={12} md={6}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>Nozzle Control</Typography>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Button
                variant="contained"
                onClick={() => controlNozzle('shutter', !equipment.nozzle.shutter_state)}
              >
                {equipment.nozzle.shutter_state ? 'Close' : 'Open'} Shutter
              </Button>
            </Grid>
            <Grid item xs={6}>
              <Button
                variant="contained"
                onClick={() => controlNozzle('select', equipment.nozzle.active_nozzle === 1 ? 2 : 1)}
              >
                Select Nozzle {equipment.nozzle.active_nozzle === 1 ? '2' : '1'}
              </Button>
            </Grid>
          </Grid>
        </Paper>
      </Grid>

      {/* Hardware Status */}
      <Grid item xs={12}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>Hardware Status</Typography>
          <Grid container spacing={2}>
            <Grid item xs={4}>
              <FormControlLabel
                control={<Switch checked={equipment.hardware.motion_enabled} disabled />}
                label="Motion Enabled"
              />
            </Grid>
            <Grid item xs={4}>
              <FormControlLabel
                control={<Switch checked={equipment.hardware.plc_connected} disabled />}
                label="PLC Connected"
              />
            </Grid>
            <Grid item xs={4}>
              <FormControlLabel
                control={<Switch checked={equipment.hardware.position_valid} disabled />}
                label="Position Valid"
              />
            </Grid>
          </Grid>
        </Paper>
      </Grid>

      {/* Process Status */}
      <Grid item xs={12}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>Process Status</Typography>
          <Grid container spacing={2}>
            <Grid item xs={4}>
              <FormControlLabel
                control={<Switch checked={equipment.process.gas_flow_stable} disabled />}
                label="Gas Flow Stable"
              />
            </Grid>
            <Grid item xs={4}>
              <FormControlLabel
                control={<Switch checked={equipment.process.powder_feed_active} disabled />}
                label="Powder Feed Active"
              />
            </Grid>
            <Grid item xs={4}>
              <FormControlLabel
                control={<Switch checked={equipment.process.process_ready} disabled />}
                label="Process Ready"
              />
            </Grid>
          </Grid>
        </Paper>
      </Grid>
    </Grid>
  );
} 