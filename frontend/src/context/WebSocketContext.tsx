import React, { createContext, useContext } from 'react';

export interface WebSocketContextType {
  connected: boolean;
  lastMessage: MessageEvent | null;
  sendMessage: (message: string) => void;
}

const WebSocketContext = createContext<WebSocketContextType>({
  connected: true  // Default to true since we're not using global WebSocket anymore
});

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  return (
    <WebSocketContext.Provider value={{ connected: true }}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  return useContext(WebSocketContext);
}