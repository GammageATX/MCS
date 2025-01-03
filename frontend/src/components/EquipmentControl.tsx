import React from 'react';
import {
  Box,
  Typography,
  Grid,
  Paper,
  Switch,
  Slider,
  Alert,
  CircularProgress,
  Button
} from '@mui/material';
import { useWebSocket } from '../context/WebSocketContext';

const COMM_SERVICE = 'http://localhost:8003';

function getDeaggSpeed(dutyCycle: number): string {
  if (dutyCycle >= 35) return 'High';
  if (dutyCycle >= 30) return 'Med';
  if (dutyCycle >= 25) return 'Low';
  return 'Off';
}

type AxisName = 'x' | 'y' | 'z';
type AxisKey = 'x_axis' | 'y_axis' | 'z_axis';

function getAxisKey(axis: AxisName): AxisKey {
  return `${axis}_axis` as AxisKey;
}

export default function EquipmentControl() {
  const { connected, equipment } = useWebSocket();

  const controlGas = async (type: 'main' | 'feeder', action: 'valve' | 'flow', value: boolean | number) => {
    if (!connected) return;
    try {
      if (action === 'flow') {
        const response = await fetch(`${COMM_SERVICE}/gas/${type}/flow`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ flow_rate: Number(value) })
        });
        if (!response.ok) {
          throw new Error(`Failed to set ${type} gas flow: ${response.status}`);
        }
      } else {
        const response = await fetch(`${COMM_SERVICE}/gas/${type}/valve`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ open: value })
        });
        if (!response.ok) {
          throw new Error(`Failed to control ${type} gas valve: ${response.status}`);
        }
      }
    } catch (err) {
      console.error(`Gas control error:`, err);
    }
  };

  const controlVacuum = async (component: 'gate' | 'mech' | 'booster' | 'vent', action: 'open' | 'close' | 'start' | 'stop') => {
    if (!connected) return;
    try {
      let endpoint = '';
      let method = 'POST';
      
      switch (component) {
        case 'gate':
          endpoint = '/vacuum/gate';
          method = 'PUT';
          break;
        case 'vent':
          endpoint = `/vacuum/vent/${action}`;
          break;
        case 'mech':
        case 'booster':
          endpoint = `/vacuum/${component}/${action}`;
          break;
      }

      const response = await fetch(`${COMM_SERVICE}${endpoint}`, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: component === 'gate' ? JSON.stringify({ position: action }) : undefined
      });

      if (!response.ok) {
        throw new Error(`Failed to control vacuum ${component}: ${response.status}`);
      }
    } catch (err) {
      console.error(`Vacuum control error:`, err);
    }
  };

  const controlFeeder = async (id: 1 | 2, action: 'start' | 'stop' | 'frequency', value?: number) => {
    if (!connected) return;
    try {
      let endpoint = `/feeder/${id}`;
      
      if (action === 'frequency') {
        endpoint += '/frequency';
        const response = await fetch(`${COMM_SERVICE}${endpoint}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ frequency: value })
        });
        if (!response.ok) {
          throw new Error(`Failed to set feeder frequency: ${response.status}`);
        }
      } else {
        endpoint += `/${action}`;
        const response = await fetch(`${COMM_SERVICE}${endpoint}`, {
          method: 'POST'
        });
        if (!response.ok) {
          throw new Error(`Failed to ${action} feeder: ${response.status}`);
        }
      }
    } catch (err) {
      console.error(`Feeder control error:`, err);
    }
  };

  const controlDeagglomerator = async (id: 1 | 2, action: 'speed' | 'set', value: number) => {
    if (!connected) return;
    try {
      const endpoint = action === 'speed' 
        ? `/deagg/${id}/speed`
        : `/deagg/${id}/set`;

      const body = action === 'speed'
        ? { speed: value }
        : { duty_cycle: value, frequency: 500 }; // Default frequency

      const response = await fetch(`${COMM_SERVICE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      if (!response.ok) {
        throw new Error(`Failed to control deagglomerator: ${response.status}`);
      }
    } catch (err) {
      console.error(`Deagglomerator control error:`, err);
    }
  };

  const controlNozzle = async (action: 'shutter' | 'select', value: boolean | number) => {
    if (!connected) return;
    try {
      if (action === 'select') {
        const response = await fetch(`${COMM_SERVICE}/nozzle/select`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ nozzle_id: value })
        });
        if (!response.ok) {
          throw new Error(`Failed to select nozzle: ${response.status}`);
        }
      } else {
        const endpoint = `/nozzle/shutter/${value ? 'open' : 'close'}`;
        const response = await fetch(`${COMM_SERVICE}${endpoint}`, {
          method: 'POST'
        });
        if (!response.ok) {
          throw new Error(`Failed to control shutter: ${response.status}`);
        }
      }
    } catch (err) {
      console.error(`Nozzle control error:`, err);
    }
  };

  const handleJog = async (axis: AxisName, direction: 1 | -1) => {
    const axisKey = getAxisKey(axis);
    if (!connected || !equipment?.motion?.status[axisKey]?.homed) return;
    
    try {
      const response = await fetch(`${COMM_SERVICE}/motion/jog/${axis}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          distance: 10.0 * direction,
          velocity: 50.0
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to jog ${axis} axis: ${response.status}`);
      }
    } catch (err) {
      console.error(`Motion control error:`, err);
    }
  };

  if (!connected) {
    return (
      <Alert severity="warning">
        Not connected to equipment control service
      </Alert>
    );
  }

  if (!equipment) {
    return (
      <Box display="flex" justifyContent="center">
        <CircularProgress />
      </Box>
    );
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
              <Switch
                checked={equipment.gas.main_valve}
                onChange={(e) => controlGas('main', 'valve', e.target.checked)}
              />
              <Slider
                value={equipment.gas.main_flow}
                onChange={(_, value) => controlGas('main', 'flow', value as number)}
                min={0}
                max={100}
                valueLabelDisplay="auto"
                disabled={!equipment.gas.main_valve}
              />
              <Typography variant="caption">
                Flow: {equipment.gas.main_flow_measured.toFixed(1)} SLPM
              </Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography>Feeder Gas</Typography>
              <Switch
                checked={equipment.gas.feeder_valve}
                onChange={(e) => controlGas('feeder', 'valve', e.target.checked)}
              />
              <Slider
                value={equipment.gas.feeder_flow}
                onChange={(_, value) => controlGas('feeder', 'flow', value as number)}
                min={0}
                max={10}
                valueLabelDisplay="auto"
                disabled={!equipment.gas.feeder_valve}
              />
              <Typography variant="caption">
                Flow: {equipment.gas.feeder_flow_measured.toFixed(1)} SLPM
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
                {equipment.vacuum.chamber_pressure.toExponential(2)} Torr
              </Typography>
            </Grid>
            <Grid item xs={6}>
              <Button
                variant="contained"
                onClick={() => controlVacuum('gate', equipment.vacuum.gate_valve ? 'close' : 'open')}
              >
                Gate Valve {equipment.vacuum.gate_valve ? 'Close' : 'Open'}
              </Button>
              <Button
                variant="contained"
                onClick={() => controlVacuum('vent', equipment.vacuum.vent_valve ? 'close' : 'open')}
              >
                Vent Valve {equipment.vacuum.vent_valve ? 'Close' : 'Open'}
              </Button>
            </Grid>
            <Grid item xs={6}>
              <Button
                variant="contained"
                onClick={() => controlVacuum('mech', equipment.vacuum.mech_pump ? 'stop' : 'start')}
              >
                Mech Pump {equipment.vacuum.mech_pump ? 'Stop' : 'Start'}
              </Button>
            </Grid>
            <Grid item xs={6}>
              <Button
                variant="contained"
                onClick={() => controlVacuum('booster', equipment.vacuum.booster_pump ? 'stop' : 'start')}
                disabled={!equipment.vacuum.mech_pump}
              >
                Booster Pump {equipment.vacuum.booster_pump ? 'Stop' : 'Start'}
              </Button>
            </Grid>
          </Grid>
        </Paper>
      </Grid>

      {/* Motion Control */}
      <Grid item xs={12}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>Motion Control</Typography>
          <Grid container spacing={2}>
            {(['x', 'y', 'z'] as const).map((axis) => {
              const axisKey = getAxisKey(axis);
              return (
                <Grid item xs={4} key={axis}>
                  <Typography>
                    {axis.toUpperCase()} Axis: {equipment.motion.position[axis].toFixed(3)} mm
                  </Typography>
                  <Box display="flex" gap={1}>
                    <Button
                      variant="contained"
                      onClick={() => handleJog(axis, -1)}
                      disabled={!equipment.motion.status[axisKey].homed}
                    >
                      -
                    </Button>
                    <Button
                      variant="contained"
                      onClick={() => handleJog(axis, 1)}
                      disabled={!equipment.motion.status[axisKey].homed}
                    >
                      +
                    </Button>
                  </Box>
                  <Typography variant="caption" color={equipment.motion.status[axisKey].error ? 'error' : 'textSecondary'}>
                    {equipment.motion.status[axisKey].error ? 'Error' : 
                     equipment.motion.status[axisKey].moving ? 'Moving' :
                     equipment.motion.status[axisKey].in_position ? 'In Position' :
                     equipment.motion.status[axisKey].homed ? 'Ready' : 'Not Homed'}
                  </Typography>
                </Grid>
              );
            })}
          </Grid>
        </Paper>
      </Grid>

      {/* System Status */}
      <Grid item xs={12}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>System Status</Typography>
          <Grid container spacing={2}>
            <Grid item xs={4}>
              <Typography color={equipment.hardware.motion_enabled ? 'success.main' : 'error.main'}>
                Motion {equipment.hardware.motion_enabled ? 'Enabled' : 'Disabled'}
              </Typography>
            </Grid>
            <Grid item xs={4}>
              <Typography color={equipment.hardware.plc_connected ? 'success.main' : 'error.main'}>
                PLC {equipment.hardware.plc_connected ? 'Connected' : 'Disconnected'}
              </Typography>
            </Grid>
            <Grid item xs={4}>
              <Typography color={equipment.safety.emergency_stop ? 'error.main' : 'success.main'}>
                E-Stop {equipment.safety.emergency_stop ? 'Activated' : 'Clear'}
              </Typography>
            </Grid>
          </Grid>
        </Paper>
      </Grid>
    </Grid>
  );
} 