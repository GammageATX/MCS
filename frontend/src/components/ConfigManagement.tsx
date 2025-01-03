import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Typography,
  List,
  ListItem,
  ListItemText,
  Chip,
  Paper,
  Tabs,
  Tab,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import SaveIcon from '@mui/icons-material/Save';
import RestoreIcon from '@mui/icons-material/Restore';
import yaml from 'js-yaml';

interface Config {
  name: string;
  data: Record<string, any>;
  format: 'yaml' | 'json';
}

interface ConfigList {
  configs: string[];
}

interface ConfigUpdateRequest {
  data: Record<string, any>;
  format: 'yaml' | 'json';
}

interface ConfigUpdateResponse {
  message: string;
}

interface ConfigValidationResponse {
  message: string;
}

interface SchemaList {
  schemas: string[];
}

interface Schema {
  name: string;
  schema_definition: Record<string, any>;
}

// Backend API URL for Configuration Service
const API_BASE_URL = 'http://localhost:8001';

const ConfigManagement: React.FC = () => {
  const [configs, setConfigs] = useState<string[]>([]);
  const [schemas, setSchemas] = useState<string[]>([]);
  const [selectedConfig, setSelectedConfig] = useState<string>('');
  const [configContent, setConfigContent] = useState<Config | null>(null);
  const [originalContent, setOriginalContent] = useState<Config | null>(null);
  const [selectedSchema, setSelectedSchema] = useState<string>('');
  const [schemaContent, setSchemaContent] = useState<Schema | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);
  const [validationStatus, setValidationStatus] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [configText, setConfigText] = useState('');

  useEffect(() => {
    refreshAll();
    return () => {
      // Cleanup on unmount
      setConfigContent(null);
      setSchemaContent(null);
      setError(null);
    };
  }, []);

  const refreshAll = async () => {
    setError(null);
    try {
      setLoading(true);
      await Promise.all([
        fetchConfigList(),
        fetchSchemaList()
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleError = useCallback((err: any, defaultMessage: string) => {
    console.error(defaultMessage, err);
    if (err instanceof Error) {
      setError(err.message);
    } else if (typeof err === 'string') {
      setError(err);
    } else {
      setError(defaultMessage);
    }
  }, []);

  const fetchConfigList = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/config/list`);
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to fetch config list: ${response.status} ${errorText}`);
      }
      const data: ConfigList = await response.json();
      setConfigs(data.configs);
      setError(null);
    } catch (err) {
      handleError(err, 'Failed to fetch config list');
      setConfigs([]);
    }
  };

  const fetchSchemaList = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/config/schema/list`);
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to fetch schema list: ${response.status} ${errorText}`);
      }
      const data: SchemaList = await response.json();
      setSchemas(data.schemas);
      setError(null);
    } catch (err) {
      handleError(err, 'Failed to fetch schema list');
      setSchemas([]);
    }
  };

  const fetchConfigContent = async (configName: string) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/config/${configName}`);
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to fetch config content: ${response.status} ${errorText}`);
      }
      const data: Config = await response.json();
      setConfigContent(data);
      setOriginalContent(data);
      
      // Convert to YAML if needed
      if (data.format === 'yaml') {
        const yamlText = yaml.dump(data.data);
        setConfigText(yamlText);
      }
      
      setError(null);
    } catch (err) {
      handleError(err, 'Failed to fetch config content');
    } finally {
      setLoading(false);
    }
  };

  const validateConfig = async () => {
    if (!configContent) return false;
    
    try {
      setLoading(true);
      const validationRequest: ConfigUpdateRequest = {
        data: configContent.data,
        format: configContent.format as 'yaml' | 'json'
      };

      const response = await fetch(`${API_BASE_URL}/config/validate/${selectedConfig}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(validationRequest),
      });
      
      const result: ConfigValidationResponse = await response.json();
      
      if (!response.ok) {
        throw new Error(result.message || 'Validation failed');
      }
      
      setValidationStatus(result.message);
      return true;
    } catch (err) {
      handleError(err, 'Validation failed');
      return false;
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    if (!configContent) return;

    try {
      setLoading(true);
      const isValid = await validateConfig();
      if (!isValid) return;

      const updateRequest: ConfigUpdateRequest = {
        data: configContent.data,
        format: configContent.format as 'yaml' | 'json'
      };

      const response = await fetch(`${API_BASE_URL}/config/${selectedConfig}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateRequest),
      });

      const result: ConfigUpdateResponse = await response.json();
      
      if (!response.ok) {
        throw new Error(result.message || 'Failed to save config');
      }

      setSaveStatus(result.message);
      setOriginalContent(configContent);
      await fetchConfigList();
      setShowSaveDialog(false);
    } catch (err) {
      handleError(err, 'Failed to save config');
    } finally {
      setLoading(false);
    }
  };

  const handleConfigChange = (newText: string) => {
    if (!configContent) return;
    
    try {
      let newData;
      if (configContent.format === 'yaml') {
        newData = yaml.load(newText);
        setConfigText(newText);
      } else {
        newData = JSON.parse(newText);
      }
      
      setConfigContent(prev => prev ? {
        ...prev,
        data: newData
      } : null);
      
      setError(null);
      setSaveStatus(null);
      setValidationStatus(null);
    } catch (err) {
      setError(`Invalid ${configContent.format.toUpperCase()} format`);
    }
  };

  const handleResetChanges = () => {
    if (originalContent) {
      setConfigContent(originalContent);
      if (originalContent.format === 'yaml') {
        setConfigText(yaml.dump(originalContent.data));
      }
      setError(null);
      setSaveStatus(null);
      setValidationStatus(null);
    }
  };

  const hasChanges = () => {
    if (!configContent || !originalContent) return false;
    return JSON.stringify(configContent.data) !== JSON.stringify(originalContent.data);
  };

  const handleConfigSelect = (configName: string) => {
    setSelectedConfig(configName);
    if (configName) {
      fetchConfigContent(configName);
    } else {
      setConfigContent(null);
      setConfigText('');
    }
    setSaveStatus(null);
    setValidationStatus(null);
  };

  const handleSchemaSelect = (schemaName: string) => {
    setSelectedSchema(schemaName);
    if (schemaName) {
      fetchSchemaContent(schemaName);
    } else {
      setSchemaContent(null);
    }
  };

  const fetchSchemaContent = async (schemaName: string) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/config/schema/${schemaName}`);
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to fetch schema content: ${response.status} ${errorText}`);
      }
      const data: Schema = await response.json();
      setSchemaContent(data);
      setError(null);
    } catch (err) {
      handleError(err, 'Failed to fetch schema content');
    } finally {
      setLoading(false);
    }
  };

  const renderConfigForm = () => {
    if (!configContent) return null;

    return (
      <Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="subtitle1">
            Configuration Format: {configContent.format}
          </Typography>
          <Box display="flex" gap={1}>
            <Tooltip title="Reset changes">
              <IconButton 
                onClick={handleResetChanges}
                disabled={!hasChanges()}
              >
                <RestoreIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Save changes">
              <IconButton 
                onClick={() => setShowSaveDialog(true)}
                disabled={!hasChanges()}
                color="primary"
              >
                <SaveIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Configuration format is read-only">
              <Chip 
                label={configContent.format.toUpperCase()}
                color="primary"
                size="small"
              />
            </Tooltip>
          </Box>
        </Box>
        
        <TextField
          fullWidth
          multiline
          rows={15}
          value={configContent.format === 'yaml' ? configText : JSON.stringify(configContent.data, null, 2)}
          onChange={(e) => handleConfigChange(e.target.value)}
          variant="outlined"
          sx={{ 
            fontFamily: 'monospace',
            '& .MuiInputBase-input': {
              fontFamily: 'monospace',
            }
          }}
        />

        <Box mt={2} display="flex" gap={2}>
          <Button
            variant="contained"
            color="primary"
            onClick={validateConfig}
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : undefined}
          >
            Validate
          </Button>
        </Box>

        {validationStatus && (
          <Alert 
            severity={validationStatus.includes('failed') ? 'error' : 'success'}
            sx={{ mt: 2 }}
          >
            {validationStatus}
          </Alert>
        )}

        {saveStatus && (
          <Alert 
            severity={saveStatus.includes('failed') ? 'error' : 'success'}
            sx={{ mt: 2 }}
          >
            {saveStatus}
          </Alert>
        )}
      </Box>
    );
  };

  const renderSchemaView = () => {
    if (!schemaContent) return null;

    return (
      <Box>
        <Typography variant="subtitle1" gutterBottom>
          Schema: {schemaContent.name}
        </Typography>
        <Paper sx={{ p: 2, mt: 2 }}>
          <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
            {JSON.stringify(schemaContent.schema_definition, null, 2)}
          </pre>
        </Paper>
      </Box>
    );
  };

  return (
    <>
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h5">
              Configuration Management
            </Typography>
            <Tooltip title="Refresh configurations and schemas">
              <IconButton onClick={refreshAll} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>

          <Tabs
            value={activeTab}
            onChange={(_, newValue) => setActiveTab(newValue)}
            sx={{ mb: 2 }}
          >
            <Tab label="Configurations" />
            <Tab label="Schemas" />
          </Tabs>

          {activeTab === 0 && (
            <>
              <FormControl fullWidth margin="normal">
                <InputLabel>Select Configuration</InputLabel>
                <Select
                  value={selectedConfig}
                  onChange={(e) => handleConfigSelect(e.target.value as string)}
                  label="Select Configuration"
                >
                  <MenuItem value="">
                    <em>Select a configuration</em>
                  </MenuItem>
                  {configs.map((config) => (
                    <MenuItem key={config} value={config}>
                      {config}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {loading && (
                <Box display="flex" justifyContent="center" my={2}>
                  <CircularProgress />
                </Box>
              )}

              {error && (
                <Alert severity="error" sx={{ my: 2 }}>
                  {error}
                </Alert>
              )}

              {selectedConfig && !loading && renderConfigForm()}
            </>
          )}

          {activeTab === 1 && (
            <>
              <FormControl fullWidth margin="normal">
                <InputLabel>Select Schema</InputLabel>
                <Select
                  value={selectedSchema}
                  onChange={(e) => handleSchemaSelect(e.target.value as string)}
                  label="Select Schema"
                >
                  <MenuItem value="">
                    <em>Select a schema</em>
                  </MenuItem>
                  {schemas.map((schema) => (
                    <MenuItem key={schema} value={schema}>
                      {schema}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {loading && (
                <Box display="flex" justifyContent="center" my={2}>
                  <CircularProgress />
                </Box>
              )}

              {error && (
                <Alert severity="error" sx={{ my: 2 }}>
                  {error}
                </Alert>
              )}

              {selectedSchema && !loading && renderSchemaView()}
            </>
          )}
        </CardContent>
      </Card>

      <Dialog
        open={showSaveDialog}
        onClose={() => setShowSaveDialog(false)}
      >
        <DialogTitle>Save Configuration</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to save changes to {selectedConfig}?
          </Typography>
          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSaveDialog(false)}>
            Cancel
          </Button>
          <Button 
            onClick={saveConfig}
            variant="contained" 
            color="primary"
            disabled={loading}
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default ConfigManagement; 