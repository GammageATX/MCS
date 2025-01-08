import React, { useEffect, useState } from 'react';
import { JsonForms } from '@jsonforms/react';
import { materialRenderers, materialCells } from '@jsonforms/material-renderers';
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
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import { API_CONFIG } from '../config/api';

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

  const fetchConfigContent = async (configName: string) => {
    try {
      setIsLoading(true);
      const response = await fetch(`${API_CONFIG.CONFIG_SERVICE}/config/${configName}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch config content: ${response.status}`);
      }
      const config: Config = await response.json();
      setOriginalFormat(config.format);
      setConfigData(config.data);
      setError('');
    } catch (err) {
      setError('Failed to fetch config content');
      console.error('Config content fetch failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchSchemaContent = async (schemaName: string) => {
    try {
      setIsLoading(true);
      const response = await fetch(`${API_CONFIG.CONFIG_SERVICE}/config/schema/${schemaName}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch schema content: ${response.status}`);
      }
      const schema: Schema = await response.json();
      setSchemaData(schema.schema_definition);
      setError('');
    } catch (err) {
      setError('Failed to fetch schema content');
      console.error('Schema content fetch failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfigSelect = async (configName: string) => {
    setSelectedConfig(configName);
    setIsLoading(true);
    try {
      await Promise.all([
        fetchConfigContent(configName),
        fetchSchemaContent(configName)
      ]);
      setSelectedSchema(configName);
    } catch (err) {
      setError('Failed to load configuration and schema');
      console.error('Config selection failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSchemaSelect = async (schemaName: string) => {
    setSelectedSchema(schemaName);
    await fetchSchemaContent(schemaName);
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
      
      await fetchConfigContent(selectedConfig);
    } catch (err) {
      setError('Failed to save config');
      console.error('Save failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFormChange = ({ data }: any) => {
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
                <JsonForms
                  schema={schemaData}
                  data={configData}
                  renderers={materialRenderers}
                  cells={materialCells}
                  onChange={handleFormChange}
                />
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