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
  const [equipmentStatus, setEquipmentStatus] = useState<EquipmentState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchEquipmentStatus = async () => {
      try {
        const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/process/equipment/status`);
        if (!response.ok) {
          throw new Error(`Failed to fetch equipment status: ${response.status}`);
        }
        const data = await response.json();
        setEquipmentStatus(data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch equipment status:', err);
        setError('Failed to load equipment status');
      } finally {
        setLoading(false);
      }
    };

    fetchEquipmentStatus();
  }, []);

  const handleEquipmentCommand = async (command: string, equipmentId: string) => {
    try {
      const response = await fetch(`${API_CONFIG.COMMUNICATION_SERVICE}/equipment/${equipmentId}/command`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ command })
      });
      
      if (!response.ok) {
        throw new Error(`Failed to send command: ${response.status}`);
      }

      // Refresh equipment status after command
      const statusResponse = await fetch(`${API_CONFIG.PROCESS_SERVICE}/process/equipment/status`);
      if (statusResponse.ok) {
        const data = await statusResponse.json();
        setEquipmentStatus(data);
      }
    } catch (err) {
      console.error('Failed to send equipment command:', err);
      setError('Failed to send command');
    }
  };

  if (loading) {
    return <Typography>Loading equipment state...</Typography>;
  }

  if (error) {
    return <Typography color="error">{error}</Typography>;
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
                onClick={() => handleEquipmentCommand('controlGas', 'main')}
              >
                {equipmentStatus?.gas.main_valve_state ? 'Close' : 'Open'} Valve
              </Button>
              <Slider
                value={equipmentStatus?.gas.main_flow_rate}
                onChange={(_, value) => handleEquipmentCommand('controlGas', 'main')}
                min={0}
                max={100}
                valueLabelDisplay="auto"
                disabled={!equipmentStatus?.gas.main_valve_state}
              />
              <Typography variant="caption">
                Flow: {equipmentStatus?.gas.main_flow_rate.toFixed(1)} SLPM
              </Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography>Feeder Gas</Typography>
              <Button
                variant="contained"
                onClick={() => handleEquipmentCommand('controlGas', 'feeder')}
              >
                {equipmentStatus?.gas.feeder_valve_state ? 'Close' : 'Open'} Valve
              </Button>
              <Slider
                value={equipmentStatus?.gas.feeder_flow_rate}
                onChange={(_, value) => handleEquipmentCommand('controlGas', 'feeder')}
                min={0}
                max={10}
                valueLabelDisplay="auto"
                disabled={!equipmentStatus?.gas.feeder_valve_state}
              />
              <Typography variant="caption">
                Flow: {equipmentStatus?.gas.feeder_flow_rate.toFixed(1)} SLPM
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
                {equipmentStatus?.pressure.chamber.toExponential(2)} Torr
              </Typography>
            </Grid>
            <Grid item xs={6}>
              <Button
                variant="contained"
                onClick={() => handleEquipmentCommand('controlVacuum', 'gate')}
              >
                Gate Valve {equipmentStatus?.vacuum.gate_valve_state ? 'Close' : 'Open'}
              </Button>
              <Button
                variant="contained"
                onClick={() => handleEquipmentCommand('controlVacuum', 'vent')}
              >
                Vent Valve {equipmentStatus?.vacuum.vent_valve_state ? 'Close' : 'Open'}
              </Button>
            </Grid>
            <Grid item xs={6}>
              <Button
                variant="contained"
                onClick={() => handleEquipmentCommand('controlVacuum', 'mechanical_pump')}
              >
                Mechanical Pump {equipmentStatus?.vacuum.mechanical_pump_state ? 'Stop' : 'Start'}
              </Button>
            </Grid>
            <Grid item xs={6}>
              <Button
                variant="contained"
                onClick={() => handleEquipmentCommand('controlVacuum', 'booster_pump')}
                disabled={!equipmentStatus?.vacuum.mechanical_pump_state}
              >
                Booster Pump {equipmentStatus?.vacuum.booster_pump_state ? 'Stop' : 'Start'}
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
                onClick={() => handleEquipmentCommand('controlFeeder', '1')}
              >
                {equipmentStatus?.feeder.running ? 'Stop' : 'Start'}
              </Button>
              <Slider
                value={equipmentStatus?.feeder.frequency}
                onChange={(_, value) => handleEquipmentCommand('controlFeeder', '1')}
                min={0}
                max={100}
                valueLabelDisplay="auto"
                disabled={!equipmentStatus?.feeder.running}
              />
              <Typography variant="caption">
                Frequency: {equipmentStatus?.feeder.frequency.toFixed(1)} Hz
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
                value={equipmentStatus?.deagglomerator.duty_cycle}
                onChange={(_, value) => handleEquipmentCommand('controlDeagglomerator', '1')}
                min={0}
                max={100}
                valueLabelDisplay="auto"
              />
              <Typography variant="caption">
                Speed: {getDeaggSpeed(equipmentStatus?.deagglomerator.duty_cycle)}
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
                onClick={() => handleEquipmentCommand('controlNozzle', 'shutter')}
              >
                {equipmentStatus?.nozzle.shutter_state ? 'Close' : 'Open'} Shutter
              </Button>
            </Grid>
            <Grid item xs={6}>
              <Button
                variant="contained"
                onClick={() => handleEquipmentCommand('controlNozzle', 'select')}
              >
                Select Nozzle {equipmentStatus?.nozzle.active_nozzle === 1 ? '2' : '1'}
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
                control={<Switch checked={equipmentStatus?.hardware.motion_enabled} disabled />}
                label="Motion Enabled"
              />
            </Grid>
            <Grid item xs={4}>
              <FormControlLabel
                control={<Switch checked={equipmentStatus?.hardware.plc_connected} disabled />}
                label="PLC Connected"
              />
            </Grid>
            <Grid item xs={4}>
              <FormControlLabel
                control={<Switch checked={equipmentStatus?.hardware.position_valid} disabled />}
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
                control={<Switch checked={equipmentStatus?.process.gas_flow_stable} disabled />}
                label="Gas Flow Stable"
              />
            </Grid>
            <Grid item xs={4}>
              <FormControlLabel
                control={<Switch checked={equipmentStatus?.process.powder_feed_active} disabled />}
                label="Powder Feed Active"
              />
            </Grid>
            <Grid item xs={4}>
              <FormControlLabel
                control={<Switch checked={equipmentStatus?.process.process_ready} disabled />}
                label="Process Ready"
              />
            </Grid>
          </Grid>
        </Paper>
      </Grid>
    </Grid>
  );
} 