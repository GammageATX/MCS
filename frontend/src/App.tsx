import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import MaterialUILayout from './components/MaterialUILayout';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#1976d2',
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route path="/" element={<MaterialUILayout component="ConfigManagement" />} />
          <Route path="/config" element={<MaterialUILayout component="ConfigManagement" />} />
          <Route path="/equipment" element={<MaterialUILayout component="EquipmentControl" />} />
          <Route path="/files" element={<MaterialUILayout component="FileManagement" />} />
          <Route path="/sequences" element={<MaterialUILayout component="SequenceExecution" />} />
          <Route path="/monitor" element={<MaterialUILayout component="SystemMonitoring" />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App; 