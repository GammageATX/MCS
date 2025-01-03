import React, { useState } from 'react';
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Drawer, 
  List, 
  ListItem, 
  ListItemButton,
  ListItemIcon, 
  ListItemText, 
  Container, 
  CssBaseline,
  Box,
  SvgIcon,
  SvgIconProps
} from '@mui/material';
import SystemMonitoring from './SystemMonitoring';
import EquipmentControl from './EquipmentControl';
import FileManagement from './FileManagement';
import SequenceExecution from './SequenceExecution';
import ConfigManagement from './ConfigManagement';
import { WebSocketProvider } from '../context/WebSocketContext';

interface MaterialUILayoutProps {
  children?: React.ReactNode;
}

const drawerWidth = 240;

const MonitorIcon = (props: SvgIconProps) => (
  <SvgIcon {...props}>
    <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14H6v-2h6v2zm4-4H6v-2h10v2zm0-4H6V7h10v2z"/>
  </SvgIcon>
);

const ControlIcon = (props: SvgIconProps) => (
  <SvgIcon {...props}>
    <path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z" />
  </SvgIcon>
);

const FileIcon = (props: SvgIconProps) => (
  <SvgIcon {...props}>
    <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z" />
  </SvgIcon>
);

const ExecuteIcon = (props: SvgIconProps) => (
  <SvgIcon {...props}>
    <path d="M8 5v14l11-7z" />
  </SvgIcon>
);

const ConfigIcon = (props: SvgIconProps) => (
  <SvgIcon {...props}>
    <path d="M19.43 12.98c.04-.32.07-.64.07-.98 0-.34-.03-.66-.07-.98l2.11-1.65c.19-.15.24-.42.12-.64l-2-3.46c-.09-.16-.26-.25-.44-.25-.06 0-.12.01-.17.03l-2.49 1c-.52-.4-1.08-.73-1.69-.98l-.38-2.65C14.46 2.18 14.25 2 14 2h-4c-.25 0-.46.18-.49.42l-.38 2.65c-.61.25-1.17.59-1.69.98l-2.49-1c-.06-.02-.12-.03-.18-.03-.17 0-.34.09-.43.25l-2 3.46c-.13.22-.07.49.12.64l2.11 1.65c-.04.32-.07.65-.07.98 0 .33.03.66.07.98l-2.11 1.65c-.19.15-.24.42-.12.64l2 3.46c.09.16.26.25.44.25.06 0 .12-.01.17-.03l2.49-1c.52.4 1.08.73 1.69.98l.38 2.65c.03.24.24.42.49.42h4c.25 0 .46-.18.49-.42l.38-2.65c.61-.25 1.17-.59 1.69-.98l2.49 1c.06.02.12.03.18.03.17 0 .34-.09.43-.25l2-3.46c.12-.22.07-.49-.12-.64l-2.11-1.65zm-1.98-1.71c.04.31.05.52.05.73 0 .21-.02.43-.05.73l-.14 1.13.89.7 1.08.84-.7 1.21-1.27-.51-1.04-.42-.9.68c-.43.32-.84.56-1.25.73l-1.06.43-.16 1.13-.2 1.35h-1.4l-.19-1.35-.16-1.13-1.06-.43c-.43-.18-.83-.41-1.23-.71l-.91-.7-1.06.43-1.27.51-.7-1.21 1.08-.84.89-.7-.14-1.13c-.03-.31-.05-.54-.05-.74s.02-.43.05-.73l.14-1.13-.89-.7-1.08-.84.7-1.21 1.27.51 1.04.42.9-.68c.43-.32.84-.56 1.25-.73l1.06-.43.16-1.13.2-1.35h1.39l.19 1.35.16 1.13 1.06.43c.43.18.83.41 1.23.71l.91.7 1.06-.43 1.27-.51.7 1.21-1.07.85-.89.7.14 1.13zM12 8c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4zm0 6c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2z"/>
  </SvgIcon>
);

export default function MaterialUILayout({ children }: MaterialUILayoutProps) {
  const [selectedSection, setSelectedSection] = useState('Sequence Execution');

  const sections = [
    { name: 'Sequence Execution', icon: ExecuteIcon, description: 'Execute and monitor spray sequences' },
    { name: 'Equipment Control', icon: ControlIcon, description: 'Monitor and control system hardware' },
    { name: 'File Management', icon: FileIcon, description: 'Manage nozzle, powder, pattern, and sequence files' },
    { name: 'System Monitoring', icon: MonitorIcon, description: 'Monitor system status and parameters' },
    { name: 'Configuration', icon: ConfigIcon, description: 'Manage system configuration files' }
  ];

  const renderSection = () => {
    switch (selectedSection) {
      case 'Sequence Execution':
        return (
          <WebSocketProvider>
            <SequenceExecution />
          </WebSocketProvider>
        );
      case 'Equipment Control':
        return (
          <WebSocketProvider>
            <EquipmentControl />
          </WebSocketProvider>
        );
      case 'File Management':
        return <FileManagement />;
      case 'System Monitoring':
        return <SystemMonitoring />;
      case 'Configuration':
        return <ConfigManagement />;
      default:
        return <Typography>Select a section</Typography>;
    }
  };

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <Typography variant="h6" noWrap component="div">
            Micro Cold Spray System
          </Typography>
        </Toolbar>
      </AppBar>
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: 'border-box' },
        }}
      >
        <Toolbar />
        <List>
          {sections.map(({ name, icon: Icon, description }) => (
            <ListItem key={name} disablePadding>
              <ListItemButton 
                onClick={() => setSelectedSection(name)} 
                selected={selectedSection === name}
                title={description}
              >
                <ListItemIcon>
                  <Icon />
                </ListItemIcon>
                <ListItemText primary={name} />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar />
        <Container>
          {renderSection()}
        </Container>
      </Box>
    </Box>
  );
}

