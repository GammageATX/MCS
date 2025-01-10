import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  Button,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Tooltip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack,
  ListItemSecondaryAction
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import VisibilityIcon from '@mui/icons-material/Visibility';
import UploadIcon from '@mui/icons-material/Upload';
import DownloadIcon from '@mui/icons-material/Download';
import { API_CONFIG } from '../config/api';

interface Pattern {
  id: string;
  name: string;
  type: string;
  description: string;
}

interface Parameter {
  id: string;
  name: string;
  value: any;
}

interface Nozzle {
  id: string;
  name: string;
  type: string;
}

interface Powder {
  id: string;
  name: string;
  properties: any;
}

interface Sequence {
  id: string;
  name: string;
  steps: any[];
}

interface CreatePatternData {
  name: string;
  type: string;
  description: string;
}

interface CreateParameterData {
  name: string;
  value: any;
}

interface CreateNozzleData {
  name: string;
  type: string;
}

interface CreatePowderData {
  name: string;
  properties: {
    material: string;
    size: string;
    manufacturer: string;
  };
}

interface CreateSequenceData {
  name: string;
  steps: any[];
}

interface FileAction {
  type: 'edit' | 'delete' | 'preview';
  fileType: 'pattern' | 'parameter' | 'nozzle' | 'powder' | 'sequence';
  fileId: string;
}

export default function FileManagement() {
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [parameters, setParameters] = useState<Parameter[]>([]);
  const [nozzles, setNozzles] = useState<Nozzle[]>([]);
  const [powders, setPowders] = useState<Powder[]>([]);
  const [sequences, setSequences] = useState<Sequence[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [createType, setCreateType] = useState<'pattern' | 'parameter' | 'nozzle' | 'powder' | 'sequence' | null>(null);
  const [createData, setCreateData] = useState<any>({});
  const [createError, setCreateError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<any>(null);
  const [fileAction, setFileAction] = useState<FileAction | null>(null);
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [yamlContent, setYamlContent] = useState('');
  const [importType, setImportType] = useState<'pattern' | 'parameter' | 'nozzle' | 'powder' | 'sequence' | null>(null);

  // Fetch data functions
  const fetchPatterns = async () => {
    try {
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/patterns/`);
      if (!response.ok) throw new Error('Failed to fetch patterns');
      const data = await response.json();
      setPatterns(data.patterns);
    } catch (err) {
      setError('Failed to load patterns');
    }
  };

  const fetchParameters = async () => {
    try {
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/parameters/`);
      if (!response.ok) throw new Error('Failed to fetch parameters');
      const data = await response.json();
      setParameters(data.parameters);
    } catch (err) {
      setError('Failed to load parameters');
    }
  };

  const fetchNozzles = async () => {
    try {
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/parameters/nozzles`);
      if (!response.ok) throw new Error('Failed to fetch nozzles');
      const data = await response.json();
      setNozzles(data.nozzles);
    } catch (err) {
      setError('Failed to load nozzles');
    }
  };

  const fetchPowders = async () => {
    try {
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/parameters/powders`);
      if (!response.ok) throw new Error('Failed to fetch powders');
      const data = await response.json();
      setPowders(data.powders);
    } catch (err) {
      setError('Failed to load powders');
    }
  };

  const fetchSequences = async () => {
    try {
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/sequences/`);
      if (!response.ok) throw new Error('Failed to fetch sequences');
      const data = await response.json();
      setSequences(data.sequences);
    } catch (err) {
      setError('Failed to load sequences');
    }
  };

  // Load all data on component mount
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        await Promise.all([
          fetchPatterns(),
          fetchParameters(),
          fetchNozzles(),
          fetchPowders(),
          fetchSequences()
        ]);
      } catch (err) {
        setError('Failed to load data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const handleCreate = async () => {
    if (!createType || !createData) return;
    
    setCreateError(null);
    try {
      let endpoint = '';
      let payload = {};
      
      switch (createType) {
        case 'pattern':
          endpoint = `${API_CONFIG.PROCESS_SERVICE}/patterns/`;
          payload = {
            name: createData.name,
            type: createData.type,
            description: createData.description
          };
          break;
          
        case 'parameter':
          endpoint = `${API_CONFIG.PROCESS_SERVICE}/parameters/`;
          payload = {
            name: createData.name,
            value: createData.value
          };
          break;
          
        case 'nozzle':
          endpoint = `${API_CONFIG.PROCESS_SERVICE}/parameters/nozzles`;
          payload = {
            name: createData.name,
            type: createData.type
          };
          break;
          
        case 'powder':
          endpoint = `${API_CONFIG.PROCESS_SERVICE}/parameters/powders`;
          payload = {
            name: createData.name,
            properties: {
              material: createData.material,
              size: createData.size,
              manufacturer: createData.manufacturer
            }
          };
          break;
          
        case 'sequence':
          endpoint = `${API_CONFIG.PROCESS_SERVICE}/sequences/`;
          payload = {
            name: createData.name,
            steps: []
          };
          break;
      }
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });
      
      if (!response.ok) {
        throw new Error(`Failed to create ${createType}`);
      }
      
      // Refresh the list
      await Promise.all([
        fetchPatterns(),
        fetchParameters(),
        fetchNozzles(),
        fetchPowders(),
        fetchSequences()
      ]);
      
      setCreateDialogOpen(false);
      setCreateType(null);
      setCreateData({});
      
    } catch (err) {
      console.error('Create failed:', err);
      setCreateError(`Failed to create ${createType}`);
    }
  };

  const handleImportYAML = async () => {
    if (!importType || !yamlContent) return;
    
    setError(null);
    try {
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/${importType}s/import`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-yaml'
        },
        body: yamlContent
      });
      
      if (!response.ok) {
        throw new Error(`Failed to import ${importType}`);
      }
      
      // Refresh the list
      await Promise.all([
        fetchPatterns(),
        fetchParameters(),
        fetchNozzles(),
        fetchPowders(),
        fetchSequences()
      ]);
      
      setImportDialogOpen(false);
      setYamlContent('');
      setImportType(null);
      
    } catch (err) {
      console.error('Import failed:', err);
      setError(`Failed to import ${importType}`);
    }
  };

  const handleExportYAML = async (type: string, id: string) => {
    try {
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/${type}s/${id}/export`);
      if (!response.ok) {
        throw new Error(`Failed to export ${type}`);
      }
      
      const yaml = await response.text();
      const blob = new Blob([yaml], { type: 'application/x-yaml' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${type}_${id}.yaml`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
    } catch (err) {
      console.error('Export failed:', err);
      setError(`Failed to export ${type}`);
    }
  };

  const handleDelete = async (type: string, id: string) => {
    try {
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/${type}s/${id}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        throw new Error(`Failed to delete ${type}`);
      }
      
      // Refresh the list
      await Promise.all([
        fetchPatterns(),
        fetchParameters(),
        fetchNozzles(),
        fetchPowders(),
        fetchSequences()
      ]);
      
      setFileAction(null);
      
    } catch (err) {
      console.error('Delete failed:', err);
      setError(`Failed to delete ${type}`);
    }
  };

  const handleEdit = async () => {
    if (!fileAction || !selectedFile) return;
    
    try {
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/${fileAction.fileType}s/${fileAction.fileId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(selectedFile)
      });
      
      if (!response.ok) {
        throw new Error(`Failed to update ${fileAction.fileType}`);
      }
      
      // Refresh the list
      await Promise.all([
        fetchPatterns(),
        fetchParameters(),
        fetchNozzles(),
        fetchPowders(),
        fetchSequences()
      ]);
      
      setFileAction(null);
      setSelectedFile(null);
      
    } catch (err) {
      console.error('Update failed:', err);
      setError(`Failed to update ${fileAction.fileType}`);
    }
  };

  const renderCreateDialog = () => {
    if (!createType) return null;

    const handleClose = () => {
      setCreateDialogOpen(false);
      setCreateType(null);
      setCreateData({});
      setCreateError(null);
    };

    return (
      <Dialog open={createDialogOpen} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>
          Create New {createType.charAt(0).toUpperCase() + createType.slice(1)}
        </DialogTitle>
        <DialogContent>
          {createError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {createError}
            </Alert>
          )}
          
          <Stack spacing={2} sx={{ mt: 2 }}>
            <TextField
              label="Name"
              value={createData.name || ''}
              onChange={(e) => setCreateData({ ...createData, name: e.target.value })}
              fullWidth
              required
            />
            
            {createType === 'pattern' && (
              <>
                <FormControl fullWidth>
                  <InputLabel>Type</InputLabel>
                  <Select
                    value={createData.type || ''}
                    onChange={(e) => setCreateData({ ...createData, type: e.target.value })}
                    label="Type"
                    required
                  >
                    <MenuItem value="linear">Linear</MenuItem>
                    <MenuItem value="circular">Circular</MenuItem>
                    <MenuItem value="spiral">Spiral</MenuItem>
                    <MenuItem value="custom">Custom</MenuItem>
                  </Select>
                </FormControl>
                <TextField
                  label="Description"
                  value={createData.description || ''}
                  onChange={(e) => setCreateData({ ...createData, description: e.target.value })}
                  fullWidth
                  multiline
                  rows={3}
                />
              </>
            )}
            
            {createType === 'parameter' && (
              <TextField
                label="Value"
                value={createData.value || ''}
                onChange={(e) => setCreateData({ ...createData, value: e.target.value })}
                fullWidth
                required
              />
            )}
            
            {createType === 'nozzle' && (
              <FormControl fullWidth>
                <InputLabel>Type</InputLabel>
                <Select
                  value={createData.type || ''}
                  onChange={(e) => setCreateData({ ...createData, type: e.target.value })}
                  label="Type"
                  required
                >
                  <MenuItem value="standard">Standard</MenuItem>
                  <MenuItem value="high_flow">High Flow</MenuItem>
                  <MenuItem value="low_flow">Low Flow</MenuItem>
                </Select>
              </FormControl>
            )}
            
            {createType === 'powder' && (
              <>
                <TextField
                  label="Material"
                  value={createData.material || ''}
                  onChange={(e) => setCreateData({ ...createData, material: e.target.value })}
                  fullWidth
                  required
                />
                <TextField
                  label="Size"
                  value={createData.size || ''}
                  onChange={(e) => setCreateData({ ...createData, size: e.target.value })}
                  fullWidth
                  required
                />
                <TextField
                  label="Manufacturer"
                  value={createData.manufacturer || ''}
                  onChange={(e) => setCreateData({ ...createData, manufacturer: e.target.value })}
                  fullWidth
                  required
                />
              </>
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button 
            onClick={handleCreate}
            variant="contained"
            disabled={!createData.name}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
    );
  };

  const renderImportDialog = () => {
    return (
      <Dialog open={importDialogOpen} onClose={() => setImportDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Import YAML</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Type</InputLabel>
              <Select
                value={importType || ''}
                onChange={(e) => setImportType(e.target.value as any)}
                label="Type"
              >
                <MenuItem value="pattern">Pattern</MenuItem>
                <MenuItem value="parameter">Parameter</MenuItem>
                <MenuItem value="nozzle">Nozzle</MenuItem>
                <MenuItem value="powder">Powder</MenuItem>
                <MenuItem value="sequence">Sequence</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="YAML Content"
              value={yamlContent}
              onChange={(e) => setYamlContent(e.target.value)}
              multiline
              rows={10}
              fullWidth
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setImportDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleImportYAML}
            variant="contained"
            disabled={!importType || !yamlContent}
          >
            Import
          </Button>
        </DialogActions>
      </Dialog>
    );
  };

  const renderActionDialog = () => {
    if (!fileAction) return null;

    const handleClose = () => {
      setFileAction(null);
      setSelectedFile(null);
    };

    if (fileAction.type === 'delete') {
      return (
        <Dialog open={true} onClose={handleClose}>
          <DialogTitle>Confirm Delete</DialogTitle>
          <DialogContent>
            Are you sure you want to delete this {fileAction.fileType}?
          </DialogContent>
          <DialogActions>
            <Button onClick={handleClose}>Cancel</Button>
            <Button
              onClick={() => handleDelete(fileAction.fileType, fileAction.fileId)}
              color="error"
              variant="contained"
            >
              Delete
            </Button>
          </DialogActions>
        </Dialog>
      );
    }

    if (fileAction.type === 'preview') {
      return (
        <Dialog open={true} onClose={handleClose} maxWidth="md" fullWidth>
          <DialogTitle>Preview {fileAction.fileType}</DialogTitle>
          <DialogContent>
            <pre style={{ whiteSpace: 'pre-wrap' }}>
              {JSON.stringify(selectedFile, null, 2)}
            </pre>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleClose}>Close</Button>
            <Button
              onClick={() => handleExportYAML(fileAction.fileType, fileAction.fileId)}
              variant="contained"
            >
              Export YAML
            </Button>
          </DialogActions>
        </Dialog>
      );
    }

    return null;
  };

  const renderListItem = (item: any, type: 'pattern' | 'parameter' | 'nozzle' | 'powder' | 'sequence') => (
    <ListItem key={item.id}>
      <ListItemText
        primary={item.name}
        secondary={
          type === 'pattern' ? `Type: ${item.type}, ${item.description}` :
          type === 'parameter' ? `Value: ${JSON.stringify(item.value)}` :
          type === 'nozzle' ? `Type: ${item.type}` :
          type === 'powder' ? `Properties: ${JSON.stringify(item.properties)}` :
          `Steps: ${item.steps.length}`
        }
      />
      <ListItemSecondaryAction>
        <Tooltip title="Preview">
          <IconButton
            onClick={() => {
              setSelectedFile(item);
              setFileAction({ type: 'preview', fileType: type, fileId: item.id });
            }}
          >
            <VisibilityIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Edit">
          <IconButton
            onClick={() => {
              setSelectedFile(item);
              setFileAction({ type: 'edit', fileType: type, fileId: item.id });
            }}
          >
            <EditIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Delete">
          <IconButton
            onClick={() => {
              setSelectedFile(item);
              setFileAction({ type: 'delete', fileType: type, fileId: item.id });
            }}
          >
            <DeleteIcon />
          </IconButton>
        </Tooltip>
      </ListItemSecondaryAction>
    </ListItem>
  );

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">File Management</Typography>
        <Box>
          <Tooltip title="Import YAML">
            <IconButton
              onClick={() => setImportDialogOpen(true)}
              sx={{ mr: 1 }}
            >
              <UploadIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Patterns */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Patterns</Typography>
              <Tooltip title="Create Pattern">
                <IconButton
                  onClick={() => {
                    setCreateType('pattern');
                    setCreateDialogOpen(true);
                  }}
                >
                  <AddIcon />
                </IconButton>
              </Tooltip>
            </Box>
            <List>
              {patterns.map((pattern) => renderListItem(pattern, 'pattern'))}
            </List>
          </Paper>
        </Grid>

        {/* Parameters */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Parameters</Typography>
              <Tooltip title="Create Parameter">
                <IconButton
                  onClick={() => {
                    setCreateType('parameter');
                    setCreateDialogOpen(true);
                  }}
                >
                  <AddIcon />
                </IconButton>
              </Tooltip>
            </Box>
            <List>
              {parameters.map((param) => renderListItem(param, 'parameter'))}
            </List>
          </Paper>
        </Grid>

        {/* Nozzles */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Nozzles</Typography>
              <Tooltip title="Create Nozzle">
                <IconButton
                  onClick={() => {
                    setCreateType('nozzle');
                    setCreateDialogOpen(true);
                  }}
                >
                  <AddIcon />
                </IconButton>
              </Tooltip>
            </Box>
            <List>
              {nozzles.map((nozzle) => renderListItem(nozzle, 'nozzle'))}
            </List>
          </Paper>
        </Grid>

        {/* Powders */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Powders</Typography>
              <Tooltip title="Create Powder">
                <IconButton
                  onClick={() => {
                    setCreateType('powder');
                    setCreateDialogOpen(true);
                  }}
                >
                  <AddIcon />
                </IconButton>
              </Tooltip>
            </Box>
            <List>
              {powders.map((powder) => renderListItem(powder, 'powder'))}
            </List>
          </Paper>
        </Grid>

        {/* Sequences */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Sequences</Typography>
              <Tooltip title="Create Sequence">
                <IconButton
                  onClick={() => {
                    setCreateType('sequence');
                    setCreateDialogOpen(true);
                  }}
                >
                  <AddIcon />
                </IconButton>
              </Tooltip>
            </Box>
            <List>
              {sequences.map((sequence) => renderListItem(sequence, 'sequence'))}
            </List>
          </Paper>
        </Grid>
      </Grid>

      {renderCreateDialog()}
      {renderImportDialog()}
      {renderActionDialog()}
    </Box>
  );
} 