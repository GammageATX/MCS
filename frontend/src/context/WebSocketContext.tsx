import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { API_CONFIG } from '../config/api';

export interface WebSocketContextType {
  connected: boolean;
  lastMessage: MessageEvent | null;
  sendMessage: (message: string) => void;
}

const WebSocketContext = createContext<WebSocketContextType>({
  connected: false,
  lastMessage: null,
  sendMessage: () => {},
});

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<MessageEvent | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  // Convert http(s) to ws(s)
  const getWebSocketUrl = () => {
    const wsUrl = API_CONFIG.COMMUNICATION_SERVICE.replace(/^http/, 'ws');
    return `${wsUrl}/equipment/ws/state`;
  };

  const connectWebSocket = useCallback(() => {
    try {
      const ws = new WebSocket(getWebSocketUrl());

      ws.addEventListener('open', () => {
        console.log('WebSocket Connected');
        setConnected(true);
        setRetryCount(0);
      });

      ws.addEventListener('message', (event) => {
        setLastMessage(event);
      });

      ws.addEventListener('close', () => {
        console.log('WebSocket Disconnected');
        setConnected(false);
        
        // Exponential backoff for reconnection
        const timeout = Math.min(1000 * Math.pow(2, retryCount), 30000);
        console.log(`Attempting to reconnect in ${timeout/1000} seconds...`);
        
        setTimeout(() => {
          setRetryCount(prev => prev + 1);
          connectWebSocket();
        }, timeout);
      });

      ws.addEventListener('error', (error) => {
        console.error('WebSocket error:', error);
        setConnected(false);
      });

      setSocket(ws);
      
      return ws;
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      return null;
    }
  }, [retryCount]);

  useEffect(() => {
    const ws = connectWebSocket();
    
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [connectWebSocket]);

  const sendMessage = (message: string) => {
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(message);
    }
  };

  return (
    <WebSocketContext.Provider value={{ connected, lastMessage, sendMessage }}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  return useContext(WebSocketContext);
}