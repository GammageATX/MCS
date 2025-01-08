import React, { useEffect, useState } from 'react';
import { JsonForms } from '@jsonforms/react';
import { materialRenderers, materialCells } from '@jsonforms/material-renderers';
import { rankWith, isNumberControl, and, scopeEndsWith, isObjectControl } from '@jsonforms/core';
import {
  Box,
  Button,
  Container,
  Grid,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Paper,
  Typography,
  Alert,
  CircularProgress,
  Divider,
  IconButton,
  TextField,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import { API_CONFIG } from '../config/api';

// Custom number renderer to preserve decimal places
const NumberRenderer = ({ data, path, handleChange, schema, uischema }: any) => {
  const [value, setValue] = useState(data?.toString() || '');
  const label = schema?.title || uischema?.label || (path ? path.split('.').pop() : '');

  useEffect(() => {
    setValue(data?.toString() || '');
  }, [data]);

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = event.target.value;
    setValue(newValue);
    
    // Convert to number while preserving decimal places
    const numValue = Number(newValue);
    if (!isNaN(numValue)) {
      // Force decimal places if schema specifies multipleOf
      if (schema?.multipleOf && schema.multipleOf < 1) {
        const decimalPlaces = schema.multipleOf.toString().split('.')[1].length;
        handleChange(path, Number(numValue.toFixed(decimalPlaces)));
      } else {
        handleChange(path, numValue);
      }
    }
  };

  return (
    <TextField
      type="number"
      value={value}
      onChange={handleInputChange}
      fullWidth
      label={label}
      required={schema?.required}
      inputProps={{
        step: schema?.multipleOf || "any",
        min: schema?.minimum,
        max: schema?.maximum
      }}
      helperText={schema?.description}
    />
  );
};

// Custom object renderer for better nested object handling
const ObjectRenderer = ({ schema, uischema, path, renderers, cells, data }: any) => {
  const label = schema?.title || uischema?.label || (path ? path.split('.').pop() : '');
  
  return (
    <Box sx={{ mb: 2 }}>
      <Typography variant="subtitle1" sx={{ mb: 1 }}>
        {label}
      </Typography>
      <Box sx={{ pl: 2 }}>
        <JsonForms
          schema={schema || {}}
          uischema={uischema || {}}
          data={data || {}}
          renderers={renderers}
          cells={cells}
        />
      </Box>
    </Box>
  );
};

const renderers = [
  ...materialRenderers,
  {
    tester: rankWith(3, isNumberControl),
    renderer: NumberRenderer
  },
  {
    tester: rankWith(3, and(isObjectControl, scopeEndsWith('safety'))),
    renderer: ObjectRenderer
  }
];

interface Config {
  name: string;
  data: Record<string, any>;
  format: 'yaml' | 'json';
}

interface Schema {
  name: string;
  schema_definition: Record<string, any>;
}

interface ConfigList {
  configs: string[];
}

interface SchemaList {
  schemas: string[];
}

const ConfigManagement: React.FC = () => {
  const [configs, setConfigs] = useState<string[]>([]);
  const [schemas, setSchemas] = useState<string[]>([]);
  const [selectedConfig, setSelectedConfig] = useState<string>('');
  const [selectedSchema, setSelectedSchema] = useState<string>('');
  const [configData, setConfigData] = useState<any>(null);
  const [schemaData, setSchemaData] = useState<any>(null);
  const [error, setError] = useState<string>('');
  const [successMessage, setSuccessMessage] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [originalFormat, setOriginalFormat] = useState<'yaml' | 'json'>('yaml');

  useEffect(() => {
    refreshAll();
  }, []);

  const refreshAll = async () => {
    setIsLoading(true);
    setError('');
    try {
      await Promise.all([
        fetchConfigList(),
        fetchSchemaList()
      ]);
    } catch (err) {
      setError('Failed to refresh data. The configuration service might be unavailable.');
      console.error('Refresh failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchConfigList = async () => {
    try {
      const response = await fetch(`${API_CONFIG.CONFIG_SERVICE}/config/list`);
      if (!response.ok) {
        throw new Error(`Failed to fetch config list: ${response.status}`);
      }
      const data: ConfigList = await response.json();
      setConfigs((data.configs || []).filter(config => config !== 'mock_data'));
    } catch (err) {
      console.error('Config list fetch failed:', err);
      throw err;
    }
  };

  const fetchSchemaList = async () => {
    try {
      const response = await fetch(`${API_CONFIG.CONFIG_SERVICE}/config/schema/list`);
      if (!response.ok) {
        throw new Error(`Failed to fetch schema list: ${response.status}`);
      }
      const data: SchemaList = await response.json();
      setSchemas(data.schemas || []);
    } catch (err) {
      console.error('Schema list fetch failed:', err);
      throw err;
    }
  };

  const handleConfigSelect = async (configName: string) => {
    console.log('Selected config:', configName);
    setSelectedConfig(configName);
    setIsLoading(true);
    setConfigData(null);
    setSchemaData(null);
    
    try {
      const [configResponse, schemaResponse] = await Promise.all([
        fetch(`${API_CONFIG.CONFIG_SERVICE}/config/${configName}`),
        fetch(`${API_CONFIG.CONFIG_SERVICE}/config/schema/${configName}`)
      ]);

      if (!configResponse.ok) {
        throw new Error(`Failed to fetch config content: ${configResponse.status}`);
      }
      if (!schemaResponse.ok) {
        throw new Error(`Failed to fetch schema content: ${schemaResponse.status}`);
      }

      const config: Config = await configResponse.json();
      const schema: Schema = await schemaResponse.json();

      console.log('Loaded config:', config);
      console.log('Loaded schema:', schema);

      setOriginalFormat(config.format);
      setConfigData(config.data);
      setSchemaData(schema.schema_definition);
      setSelectedSchema(configName);
      setError('');
    } catch (err) {
      console.error('Config selection failed:', err);
      setError('Failed to load configuration and schema');
      setConfigData(null);
      setSchemaData(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSchemaSelect = async (schemaName: string) => {
    setSelectedSchema(schemaName);
  };

  const handleSave = async () => {
    if (!selectedConfig || !configData) return;

    try {
      setIsLoading(true);
      const response = await fetch(`${API_CONFIG.CONFIG_SERVICE}/config/${selectedConfig}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          data: configData,
          format: originalFormat,
          preserve_format: true,
          preserve_comments: true
        }),
      });

      if (!response.ok) {
        throw new Error('Save failed');
      }

      setSuccessMessage('Config saved successfully');
      setTimeout(() => setSuccessMessage(''), 3000);
      
      // Reload the config after saving
      const configResponse = await fetch(`${API_CONFIG.CONFIG_SERVICE}/config/${selectedConfig}`);
      if (!configResponse.ok) {
        throw new Error(`Failed to reload config: ${configResponse.status}`);
      }
      const config: Config = await configResponse.json();
      setOriginalFormat(config.format);
      setConfigData(config.data);
      
    } catch (err) {
      setError('Failed to save config');
      console.error('Save failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFormChange = ({ data }: any) => {
    console.log('Form data changed:', data);
    setConfigData(data);
  };

  if (isLoading && !configs.length && !schemas.length) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 500 }}>Configuration Management</Typography>
        <IconButton 
          onClick={refreshAll}
          sx={{ 
            backgroundColor: '#1976d2',
            color: 'white',
            '&:hover': {
              backgroundColor: '#1565c0'
            }
          }}
        >
          <RefreshIcon />
        </IconButton>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {successMessage && (
        <Alert severity="success" sx={{ mb: 3 }}>
          {successMessage}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Left sidebar - Config List only */}
        <Grid item xs={12} md={3}>
          <Paper 
            elevation={0}
            sx={{ 
              p: 2,
              border: '1px solid rgba(0, 0, 0, 0.12)',
              borderRadius: 2,
              height: '100%'
            }}
          >
            <Typography variant="h6" gutterBottom>Configurations</Typography>
            <List>
              {configs.map((config) => (
                <ListItem disablePadding key={config}>
                  <ListItemButton 
                    selected={selectedConfig === config}
                    onClick={() => handleConfigSelect(config)}
                    sx={{
                      borderRadius: 1,
                      mb: 0.5
                    }}
                  >
                    <ListItemText 
                      primary={config} 
                      secondary={selectedConfig === config ? 'Using matching schema' : undefined}
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* Right side - JSON Form */}
        <Grid item xs={12} md={9}>
          <Paper 
            elevation={0}
            sx={{ 
              p: 3,
              border: '1px solid rgba(0, 0, 0, 0.12)',
              borderRadius: 2,
              minHeight: 400
            }}
          >
            {isLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', pt: 8 }}>
                <CircularProgress />
              </Box>
            ) : selectedConfig && configData && schemaData ? (
              <>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
                  <Typography variant="h6">
                    Editing: {selectedConfig}
                  </Typography>
                  <Button 
                    variant="contained" 
                    onClick={handleSave}
                    disabled={isLoading}
                  >
                    Save Changes
                  </Button>
                </Box>
                {configData && schemaData ? (
                  <>
                    {console.log('Rendering form with:', { configData, schemaData })}
                    <JsonForms
                      schema={schemaData}
                      data={configData}
                      renderers={renderers}
                      cells={materialCells}
                      onChange={handleFormChange}
                      config={{
                        showUnfocusedDescription: true,
                        hideRequiredAsterisk: false,
                        restrict: true,
                        trim: false,
                        preserveOptionalEmptyStrings: true
                      }}
                    />
                  </>
                ) : (
                  <Typography color="text.secondary">
                    Loading configuration data...
                  </Typography>
                )}
              </>
            ) : (
              <Box sx={{ 
                display: 'flex', 
                justifyContent: 'center', 
                alignItems: 'center',
                height: 300,
                color: 'text.secondary'
              }}>
                <Typography>
                  Select a configuration to begin editing
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default ConfigManagement; 