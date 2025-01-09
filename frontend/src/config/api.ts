interface ApiConfig {
  EQUIPMENT_SERVICE: string;
  MOTION_SERVICE: string;
  PROCESS_SERVICE: string;
  DATA_SERVICE: string;
  CONFIG_SERVICE: string;
  UI_SERVICE: string;
  WS_ENDPOINT: string;
}

export const API_CONFIG: ApiConfig = {
  EQUIPMENT_SERVICE: 'http://localhost:8002',
  MOTION_SERVICE: 'http://localhost:8002',
  PROCESS_SERVICE: 'http://localhost:8003',
  DATA_SERVICE: 'http://localhost:8004',
  CONFIG_SERVICE: 'http://localhost:8001',
  UI_SERVICE: 'http://localhost:8000',
  WS_ENDPOINT: 'ws://localhost:8002/ws/state'
}; 