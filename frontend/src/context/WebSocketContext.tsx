import React, { createContext, useContext, useEffect, useState } from 'react';
import { API_CONFIG } from '../config/api';

interface WebSocketContextType {
  connected: boolean;
  lastMessage: any;
}

const WebSocketContext = createContext<WebSocketContextType>({
  connected: false,
  lastMessage: null
});

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any>(null);

  useEffect(() => {
    const ws = new WebSocket(API_CONFIG.WS_ENDPOINT);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);
      // Attempt to reconnect after 5 seconds
      setTimeout(() => {
        setSocket(new WebSocket(API_CONFIG.WS_ENDPOINT));
      }, 5000);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setLastMessage(data);
    };

    setSocket(ws);

    return () => {
      ws.close();
    };
  }, []);

  return (
    <WebSocketContext.Provider value={{ connected, lastMessage }}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  return useContext(WebSocketContext);
}