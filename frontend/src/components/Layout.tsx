import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Box from '@mui/material/Box';
import ConfigManagement from './ConfigManagement';
import EquipmentControl from './EquipmentControl';
import FileManagement from './FileManagement';
import SequenceExecution from './SequenceExecution';
import SystemMonitoring from './SystemMonitoring';
import Navigation from './Navigation';

export default function Layout() {
  return (
    <Box sx={{ display: 'flex' }}>
      <Navigation />
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Routes>
          <Route path="/" element={<ConfigManagement />} />
          <Route path="/config" element={<ConfigManagement />} />
          <Route path="/equipment" element={<EquipmentControl />} />
          <Route path="/files" element={<FileManagement />} />
          <Route path="/sequences" element={<SequenceExecution />} />
          <Route path="/monitor" element={<SystemMonitoring />} />
        </Routes>
      </Box>
    </Box>
  );
} 