import React, { useEffect, useState } from 'react';
import { JsonForms } from '@jsonforms/react';
import { materialRenderers, materialCells } from '@jsonforms/material-renderers';
import { JsonSchema, UISchemaElement, rankWith, isNumberControl, and, scopeEndsWith, isObjectControl } from '@jsonforms/core';
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
  IconButton,
  Tooltip,
  ListItemSecondaryAction,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  SelectChangeEvent
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import VisibilityIcon from '@mui/icons-material/Visibility';
import UploadIcon from '@mui/icons-material/Upload';
import DownloadIcon from '@mui/icons-material/Download';
import { API_CONFIG } from '../config/api';
import {
  patternSchema,
  patternUiSchema,
  parameterSchema,
  parameterUiSchema,
  nozzleSchema,
  nozzleUiSchema,
  powderSchema,
  powderUiSchema,
  sequenceSchema,
  sequenceUiSchema
} from '../schemas/process';

interface Pattern {
  id: string;
  name: string;
  description: string;
  type: "linear" | "serpentine" | "spiral";
  params: Record<string, any>;
}

interface PatternResponse {
  pattern: Pattern;
}

interface PatternListResponse {
  patterns: string[];
}

interface Parameter {
  name: string;
  created: string;
  author: string;
  description: string;
  nozzle: string;
  main_gas: number;
  feeder_gas: number;
  frequency: number;
  deagglomerator_speed: number;
}

interface ParameterResponse {
  parameter: Parameter;
}

interface ParameterListResponse {
  parameters: string[];
}

interface Nozzle {
  name: string;
  manufacturer: string;
  type: "convergent-divergent" | "convergent" | "vented" | "flat-plate" | "de laval";
  description: string;
}

interface NozzleResponse {
  nozzle: Nozzle;
}

interface NozzleListResponse {
  nozzles: string[];
}

interface Powder {
  name: string;
  type: string;
  size: string;
  manufacturer: string;
  lot: string;
}

interface PowderResponse {
  powder: Powder;
}

interface PowderListResponse {
  powders: string[];
}

interface Sequence {
  id: string;
  metadata: {
    name: string;
    version: string;
    created: string;
    author: string;
    description: string;
  };
  steps: Array<{
    name: string;
    step_type: string;
    description?: string;
    pattern_id?: string;
    parameters?: string;
    origin?: number[];
  }>;
}

interface SequenceResponse {
  sequence: Sequence;
}

interface SequenceListResponse {
  sequences: string[];
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
  const [patterns, setPatterns] = useState<string[]>([]);
  const [parameters, setParameters] = useState<string[]>([]);
  const [nozzles, setNozzles] = useState<string[]>([]);
  const [powders, setPowders] = useState<string[]>([]);
  const [sequences, setSequences] = useState<string[]>([]);
  const [selectedPattern, setSelectedPattern] = useState<Pattern | null>(null);
  const [selectedParameter, setSelectedParameter] = useState<Parameter | null>(null);
  const [selectedNozzle, setSelectedNozzle] = useState<Nozzle | null>(null);
  const [selectedPowder, setSelectedPowder] = useState<Powder | null>(null);
  const [selectedSequence, setSelectedSequence] = useState<Sequence | null>(null);
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

  const getSchemaForType = (type: string): { schema: JsonSchema, uiSchema: UISchemaElement } => {
    switch (type) {
      case 'pattern':
        return { schema: patternSchema, uiSchema: patternUiSchema as UISchemaElement };
      case 'parameter':
        return { schema: parameterSchema, uiSchema: parameterUiSchema as UISchemaElement };
      case 'nozzle':
        return { schema: nozzleSchema, uiSchema: nozzleUiSchema as UISchemaElement };
      case 'powder':
        return { schema: powderSchema, uiSchema: powderUiSchema as UISchemaElement };
      case 'sequence':
        return { schema: sequenceSchema, uiSchema: sequenceUiSchema as UISchemaElement };
      default:
        return { 
          schema: {} as JsonSchema, 
          uiSchema: {
            type: 'VerticalLayout',
            elements: []
          } as UISchemaElement 
        };
    }
  };

  // Fetch data functions
  const fetchPatterns = async () => {
    try {
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/patterns/`);
      if (!response.ok) throw new Error('Failed to fetch patterns');
      const data: PatternListResponse = await response.json();
      setPatterns(data.patterns);
    } catch (err) {
      setError('Failed to load patterns');
    }
  };

  const fetchParameters = async () => {
    try {
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/parameters/`);
      if (!response.ok) throw new Error('Failed to fetch parameters');
      const data: ParameterListResponse = await response.json();
      setParameters(data.parameters);
    } catch (err) {
      setError('Failed to load parameters');
    }
  };

  const fetchNozzles = async () => {
    try {
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/nozzles/`);
      if (!response.ok) throw new Error('Failed to fetch nozzles');
      const data: NozzleListResponse = await response.json();
      setNozzles(data.nozzles);
    } catch (err) {
      setError('Failed to load nozzles');
    }
  };

  const fetchPowders = async () => {
    try {
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/powders/`);
      if (!response.ok) throw new Error('Failed to fetch powders');
      const data: PowderListResponse = await response.json();
      setPowders(data.powders);
    } catch (err) {
      setError('Failed to load powders');
    }
  };

  const fetchSequences = async () => {
    try {
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/sequences/`);
      if (!response.ok) throw new Error('Failed to fetch sequences');
      const data: SequenceListResponse = await response.json();
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
      
      switch (createType) {
        case 'pattern':
          endpoint = `${API_CONFIG.PROCESS_SERVICE}/patterns/`;
          break;
        case 'parameter':
          endpoint = `${API_CONFIG.PROCESS_SERVICE}/parameters/`;
          break;
        case 'nozzle':
          endpoint = `${API_CONFIG.PROCESS_SERVICE}/nozzles/`;
          break;
        case 'powder':
          endpoint = `${API_CONFIG.PROCESS_SERVICE}/powders/`;
          break;
        case 'sequence':
          endpoint = `${API_CONFIG.PROCESS_SERVICE}/sequences/`;
          break;
      }
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(createData)
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

  // Load individual item functions
  const loadPattern = async (patternId: string) => {
    try {
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/patterns/${patternId}`);
      if (!response.ok) throw new Error('Failed to fetch pattern');
      const data: PatternResponse = await response.json();
      setSelectedPattern(data.pattern);
    } catch (err) {
      setError('Failed to load pattern');
    }
  };

  const loadParameter = async (parameterId: string) => {
    try {
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/parameters/${parameterId}`);
      if (!response.ok) throw new Error('Failed to fetch parameter');
      const data: ParameterResponse = await response.json();
      setSelectedParameter(data.parameter);
    } catch (err) {
      setError('Failed to load parameter');
    }
  };

  const loadNozzle = async (nozzleId: string) => {
    try {
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/nozzles/${nozzleId}`);
      if (!response.ok) throw new Error('Failed to fetch nozzle');
      const data: NozzleResponse = await response.json();
      setSelectedNozzle(data.nozzle);
    } catch (err) {
      setError('Failed to load nozzle');
    }
  };

  const loadPowder = async (powderId: string) => {
    try {
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/powders/${powderId}`);
      if (!response.ok) throw new Error('Failed to fetch powder');
      const data: PowderResponse = await response.json();
      setSelectedPowder(data.powder);
    } catch (err) {
      setError('Failed to load powder');
    }
  };

  const loadSequence = async (sequenceId: string) => {
    try {
      const response = await fetch(`${API_CONFIG.PROCESS_SERVICE}/sequences/${sequenceId}`);
      if (!response.ok) throw new Error('Failed to fetch sequence');
      const data: SequenceResponse = await response.json();
      setSelectedSequence(data.sequence);
    } catch (err) {
      setError('Failed to load sequence');
    }
  };

  const renderCreateDialog = () => {
    if (!createType) return null;

    const { schema, uiSchema } = getSchemaForType(createType);

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
          
          <Box sx={{ mt: 2 }}>
            <JsonForms
              schema={schema}
              uischema={uiSchema}
              data={createData}
              renderers={materialRenderers}
              cells={materialCells}
              onChange={({ data }) => setCreateData(data)}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button 
            onClick={handleCreate}
            variant="contained"
            disabled={!createData}
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

    if (fileAction.type === 'edit') {
      const { schema, uiSchema } = getSchemaForType(fileAction.fileType);

      return (
        <Dialog open={true} onClose={handleClose} maxWidth="md" fullWidth>
          <DialogTitle>Edit {fileAction.fileType}</DialogTitle>
          <DialogContent>
            <Box sx={{ mt: 2 }}>
              <JsonForms
                schema={schema}
                uischema={uiSchema}
                data={selectedFile}
                renderers={materialRenderers}
                cells={materialCells}
                onChange={({ data }) => setSelectedFile(data)}
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleClose}>Cancel</Button>
            <Button onClick={handleEdit} variant="contained">
              Save Changes
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
      <Typography variant="h4" gutterBottom>
        File Management
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <CircularProgress />
      ) : (
        <Grid container spacing={3}>
          {/* Patterns Section */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Stack direction="row" alignItems="center" justifyContent="space-between" mb={2}>
                <Typography variant="h6">Patterns</Typography>
                <Button
                  startIcon={<AddIcon />}
                  onClick={() => {
                    setCreateType('pattern');
                    setCreateDialogOpen(true);
                  }}
                >
                  Create
                </Button>
              </Stack>
              <List>
                {patterns.map((patternId) => (
                  <ListItem key={patternId}>
                    <ListItemText primary={patternId} />
                    <ListItemSecondaryAction>
                      <Tooltip title="View">
                        <IconButton
                          edge="end"
                          onClick={() => loadPattern(patternId)}
                        >
                          <VisibilityIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Edit">
                        <IconButton
                          edge="end"
                          onClick={() => {
                            setFileAction({
                              type: 'edit',
                              fileType: 'pattern',
                              fileId: patternId
                            });
                          }}
                        >
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton
                          edge="end"
                          onClick={() => {
                            setFileAction({
                              type: 'delete',
                              fileType: 'pattern',
                              fileId: patternId
                            });
                          }}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>

          {/* Parameters Section */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Stack direction="row" alignItems="center" justifyContent="space-between" mb={2}>
                <Typography variant="h6">Parameters</Typography>
                <Button
                  startIcon={<AddIcon />}
                  onClick={() => {
                    setCreateType('parameter');
                    setCreateDialogOpen(true);
                  }}
                >
                  Create
                </Button>
              </Stack>
              <List>
                {parameters.map((parameterId) => (
                  <ListItem key={parameterId}>
                    <ListItemText primary={parameterId} />
                    <ListItemSecondaryAction>
                      <Tooltip title="View">
                        <IconButton
                          edge="end"
                          onClick={() => loadParameter(parameterId)}
                        >
                          <VisibilityIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Edit">
                        <IconButton
                          edge="end"
                          onClick={() => {
                            setFileAction({
                              type: 'edit',
                              fileType: 'parameter',
                              fileId: parameterId
                            });
                          }}
                        >
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton
                          edge="end"
                          onClick={() => {
                            setFileAction({
                              type: 'delete',
                              fileType: 'parameter',
                              fileId: parameterId
                            });
                          }}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>

          {/* Nozzles Section */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Stack direction="row" alignItems="center" justifyContent="space-between" mb={2}>
                <Typography variant="h6">Nozzles</Typography>
                <Button
                  startIcon={<AddIcon />}
                  onClick={() => {
                    setCreateType('nozzle');
                    setCreateDialogOpen(true);
                  }}
                >
                  Create
                </Button>
              </Stack>
              <List>
                {nozzles.map((nozzleId) => (
                  <ListItem key={nozzleId}>
                    <ListItemText primary={nozzleId} />
                    <ListItemSecondaryAction>
                      <Tooltip title="View">
                        <IconButton
                          edge="end"
                          onClick={() => loadNozzle(nozzleId)}
                        >
                          <VisibilityIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Edit">
                        <IconButton
                          edge="end"
                          onClick={() => {
                            setFileAction({
                              type: 'edit',
                              fileType: 'nozzle',
                              fileId: nozzleId
                            });
                          }}
                        >
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton
                          edge="end"
                          onClick={() => {
                            setFileAction({
                              type: 'delete',
                              fileType: 'nozzle',
                              fileId: nozzleId
                            });
                          }}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>

          {/* Powders Section */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Stack direction="row" alignItems="center" justifyContent="space-between" mb={2}>
                <Typography variant="h6">Powders</Typography>
                <Button
                  startIcon={<AddIcon />}
                  onClick={() => {
                    setCreateType('powder');
                    setCreateDialogOpen(true);
                  }}
                >
                  Create
                </Button>
              </Stack>
              <List>
                {powders.map((powderId) => (
                  <ListItem key={powderId}>
                    <ListItemText primary={powderId} />
                    <ListItemSecondaryAction>
                      <Tooltip title="View">
                        <IconButton
                          edge="end"
                          onClick={() => loadPowder(powderId)}
                        >
                          <VisibilityIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Edit">
                        <IconButton
                          edge="end"
                          onClick={() => {
                            setFileAction({
                              type: 'edit',
                              fileType: 'powder',
                              fileId: powderId
                            });
                          }}
                        >
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton
                          edge="end"
                          onClick={() => {
                            setFileAction({
                              type: 'delete',
                              fileType: 'powder',
                              fileId: powderId
                            });
                          }}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>

          {/* Sequences Section */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Stack direction="row" alignItems="center" justifyContent="space-between" mb={2}>
                <Typography variant="h6">Sequences</Typography>
                <Button
                  startIcon={<AddIcon />}
                  onClick={() => {
                    setCreateType('sequence');
                    setCreateDialogOpen(true);
                  }}
                >
                  Create
                </Button>
              </Stack>
              <List>
                {sequences.map((sequenceId) => (
                  <ListItem key={sequenceId}>
                    <ListItemText primary={sequenceId} />
                    <ListItemSecondaryAction>
                      <Tooltip title="View">
                        <IconButton
                          edge="end"
                          onClick={() => loadSequence(sequenceId)}
                        >
                          <VisibilityIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Edit">
                        <IconButton
                          edge="end"
                          onClick={() => {
                            setFileAction({
                              type: 'edit',
                              fileType: 'sequence',
                              fileId: sequenceId
                            });
                          }}
                        >
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton
                          edge="end"
                          onClick={() => {
                            setFileAction({
                              type: 'delete',
                              fileType: 'sequence',
                              fileId: sequenceId
                            });
                          }}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Details Dialog */}
      <Dialog
        open={Boolean(selectedPattern || selectedParameter || selectedNozzle || selectedPowder || selectedSequence)}
        onClose={() => {
          setSelectedPattern(null);
          setSelectedParameter(null);
          setSelectedNozzle(null);
          setSelectedPowder(null);
          setSelectedSequence(null);
        }}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {selectedPattern ? 'Pattern Details' :
           selectedParameter ? 'Parameter Details' :
           selectedNozzle ? 'Nozzle Details' :
           selectedPowder ? 'Powder Details' :
           selectedSequence ? 'Sequence Details' : ''}
        </DialogTitle>
        <DialogContent>
          {selectedPattern && (
            <Box>
              <Typography variant="h6">{selectedPattern.name}</Typography>
              <Typography variant="body1">Type: {selectedPattern.type}</Typography>
              <Typography variant="body1">Description: {selectedPattern.description}</Typography>
              <Typography variant="body1">Parameters:</Typography>
              <pre>{JSON.stringify(selectedPattern.params, null, 2)}</pre>
            </Box>
          )}
          {selectedParameter && (
            <Box>
              <Typography variant="h6">{selectedParameter.name}</Typography>
              <Typography variant="body1">Created: {selectedParameter.created}</Typography>
              <Typography variant="body1">Author: {selectedParameter.author}</Typography>
              <Typography variant="body1">Description: {selectedParameter.description}</Typography>
              <Typography variant="body1">Nozzle: {selectedParameter.nozzle}</Typography>
              <Typography variant="body1">Main Gas: {selectedParameter.main_gas}</Typography>
              <Typography variant="body1">Feeder Gas: {selectedParameter.feeder_gas}</Typography>
              <Typography variant="body1">Frequency: {selectedParameter.frequency}</Typography>
              <Typography variant="body1">Deagglomerator Speed: {selectedParameter.deagglomerator_speed}</Typography>
            </Box>
          )}
          {selectedNozzle && (
            <Box>
              <Typography variant="h6">{selectedNozzle.name}</Typography>
              <Typography variant="body1">Manufacturer: {selectedNozzle.manufacturer}</Typography>
              <Typography variant="body1">Type: {selectedNozzle.type}</Typography>
              <Typography variant="body1">Description: {selectedNozzle.description}</Typography>
            </Box>
          )}
          {selectedPowder && (
            <Box>
              <Typography variant="h6">{selectedPowder.name}</Typography>
              <Typography variant="body1">Type: {selectedPowder.type}</Typography>
              <Typography variant="body1">Size: {selectedPowder.size}</Typography>
              <Typography variant="body1">Manufacturer: {selectedPowder.manufacturer}</Typography>
              <Typography variant="body1">Lot: {selectedPowder.lot}</Typography>
            </Box>
          )}
          {selectedSequence && (
            <Box>
              <Typography variant="h6">{selectedSequence.metadata.name}</Typography>
              <Typography variant="body1">Version: {selectedSequence.metadata.version}</Typography>
              <Typography variant="body1">Created: {selectedSequence.metadata.created}</Typography>
              <Typography variant="body1">Author: {selectedSequence.metadata.author}</Typography>
              <Typography variant="body1">Description: {selectedSequence.metadata.description}</Typography>
              <Typography variant="h6" sx={{ mt: 2 }}>Steps:</Typography>
              <List>
                {selectedSequence.steps.map((step, index) => (
                  <ListItem key={index}>
                    <ListItemText
                      primary={step.name}
                      secondary={
                        <>
                          Type: {step.step_type}
                          {step.description && ` - ${step.description}`}
                          {step.pattern_id && ` - Pattern: ${step.pattern_id}`}
                          {step.parameters && ` - Parameters: ${step.parameters}`}
                          {step.origin && ` - Origin: [${step.origin.join(', ')}]`}
                        </>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setSelectedPattern(null);
            setSelectedParameter(null);
            setSelectedNozzle(null);
            setSelectedPowder(null);
            setSelectedSequence(null);
          }}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
} 