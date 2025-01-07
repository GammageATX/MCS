import React, { createContext, useContext, useEffect, useState } from 'react';

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

interface Position {
  x: number;
  y: number;
  z: number;
}

interface MotionState {
  position: Position;
  status: SystemStatus;
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

interface WebSocketContextType {
  connected: boolean;
  equipment: EquipmentState | null;
  sendMessage?: (message: any) => void;
}

const WebSocketContext = createContext<WebSocketContextType>({
  connected: false,
  equipment: null
});

export function useWebSocket() {
  return useContext(WebSocketContext);
}

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const [connected, setConnected] = useState(false);
  const [equipment, setEquipment] = useState<EquipmentState | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);

  const sendMessage = (message: any) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message));
    }
  };

  useEffect(() => {
    console.log('Attempting to connect to WebSocket...');
    const socket = new WebSocket('ws://localhost:8003/ws/state');
    setWs(socket);

    socket.onopen = () => {
      console.log('WebSocket connected successfully');
      setConnected(true);
    };

    socket.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason);
      setConnected(false);
      setEquipment(null);
      setWs(null);
      
      // Attempt to reconnect after 5 seconds
      setTimeout(() => {
        console.log('Attempting to reconnect...');
      }, 5000);
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('Received WebSocket data:', data);
        setEquipment(data);
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    return () => {
      console.log('Cleaning up WebSocket connection');
      socket.close();
    };
  }, []);

  return (
    <WebSocketContext.Provider value={{ connected, equipment, sendMessage }}>
      {children}
    </WebSocketContext.Provider>
  );
}