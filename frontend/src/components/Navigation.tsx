import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Box,
  Typography
} from '@mui/material';
import SettingsIcon from '@mui/icons-material/Settings';
import BuildIcon from '@mui/icons-material/Build';
import FolderIcon from '@mui/icons-material/Folder';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import MonitorIcon from '@mui/icons-material/Monitor';

const drawerWidth = 240;

const menuItems = [
  { path: '/config', text: 'Configuration', icon: <SettingsIcon /> },
  { path: '/equipment', text: 'Equipment Control', icon: <BuildIcon /> },
  { path: '/files', text: 'File Management', icon: <FolderIcon /> },
  { path: '/sequences', text: 'Sequence Execution', icon: <PlayArrowIcon /> },
  { path: '/monitor', text: 'System Monitoring', icon: <MonitorIcon /> },
];

export default function Navigation() {
  const location = useLocation();

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
        },
      }}
    >
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" noWrap component="div">
          Micro Cold Spray System
        </Typography>
      </Box>
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.path} disablePadding>
            <ListItemButton
              component={Link}
              to={item.path}
              selected={location.pathname === item.path}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Drawer>
  );
} 