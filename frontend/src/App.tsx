import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { WebSocketProvider } from './context/WebSocketContext';
import theme from './theme';
import Layout from './components/Layout';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <WebSocketProvider>
        <BrowserRouter>
          <Layout />
        </BrowserRouter>
      </WebSocketProvider>
    </ThemeProvider>
  );
}

export default App; 