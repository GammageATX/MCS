import React, { createContext, useContext, useEffect, useState } from 'react';

interface AxisStatus {
  homed: boolean;
  moving: boolean;
  in_position: boolean;
  error: boolean;
}

interface MotionStatus {
  x_axis: AxisStatus;
  y_axis: AxisStatus;
  z_axis: AxisStatus;
  module_ready: boolean;
}

interface MotionPosition {
  x: number;
  y: number;
  z: number;
}

interface MotionState {
  status: MotionStatus;
  position: MotionPosition;
}

interface GasState {
  main_flow: number;
  main_flow_measured: number;
  feeder_flow: number;
  feeder_flow_measured: number;
  main_valve: boolean;
  feeder_valve: boolean;
}

interface VacuumState {
  chamber_pressure: number;
  gate_valve: boolean;
  mech_pump: boolean;
  booster_pump: boolean;
  vent_valve: boolean;
}

interface HardwareState {
  motion_enabled: boolean;
  plc_connected: boolean;
  position_valid: boolean;
}

interface SafetyState {
  emergency_stop: boolean;
  interlocks_ok: boolean;
  limits_ok: boolean;
}

interface EquipmentState {
  motion: MotionState;
  gas: GasState;
  vacuum: VacuumState;
  hardware: HardwareState;
  safety: SafetyState;
}

interface WebSocketContextType {
  connected: boolean;
  equipment: EquipmentState | null;
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

  useEffect(() => {
    console.log('Attempting to connect to WebSocket...');
    const ws = new WebSocket('ws://localhost:8003/ws/state');

    ws.onopen = () => {
      console.log('WebSocket connected successfully');
      setConnected(true);
    };

    ws.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason);
      setConnected(false);
      setEquipment(null);
      
      // Attempt to reconnect after 5 seconds
      setTimeout(() => {
        console.log('Attempting to reconnect...');
      }, 5000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onmessage = (event) => {
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
      ws.close();
    };
  }, []);

  return (
    <WebSocketContext.Provider value={{ connected, equipment }}>
      {children}
    </WebSocketContext.Provider>
  );
}