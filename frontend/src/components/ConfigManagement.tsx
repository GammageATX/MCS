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
} from '@mui/material';

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

  useEffect(() => {
    refreshAll();
  }, []);

  const refreshAll = async () => {
    try {
      await Promise.all([
        fetchConfigList(),
        fetchSchemaList()
      ]);
      setError('');
    } catch (err) {
      setError('Failed to refresh data');
      console.error('Refresh failed:', err);
    }
  };

  const fetchConfigList = async () => {
    try {
      const response = await fetch('http://localhost:8001/config/list');
      const data: ConfigList = await response.json();
      setConfigs(data.configs);
    } catch (err) {
      setError('Failed to fetch config list');
      console.error('Config list fetch failed:', err);
    }
  };

  const fetchSchemaList = async () => {
    try {
      const response = await fetch('http://localhost:8001/schema/list');
      const data: SchemaList = await response.json();
      setSchemas(data.schemas);
    } catch (err) {
      setError('Failed to fetch schema list');
      console.error('Schema list fetch failed:', err);
    }
  };

  const fetchConfigContent = async (configName: string) => {
    try {
      const response = await fetch(`http://localhost:8001/config/${configName}`);
      const config: Config = await response.json();
      setConfigData(config.data);
      setError('');
    } catch (err) {
      setError('Failed to fetch config content');
      console.error('Config content fetch failed:', err);
    }
  };

  const fetchSchemaContent = async (schemaName: string) => {
    try {
      const response = await fetch(`http://localhost:8001/schema/${schemaName}`);
      const schema: Schema = await response.json();
      setSchemaData(schema.schema_definition);
      setError('');
    } catch (err) {
      setError('Failed to fetch schema content');
      console.error('Schema content fetch failed:', err);
    }
  };

  const handleConfigSelect = async (configName: string) => {
    setSelectedConfig(configName);
    await fetchConfigContent(configName);
  };

  const handleSchemaSelect = async (schemaName: string) => {
    setSelectedSchema(schemaName);
    await fetchSchemaContent(schemaName);
  };

  const handleSave = async () => {
    if (!selectedConfig || !configData) return;

    try {
      const response = await fetch(`http://localhost:8001/config/${selectedConfig}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          data: configData,
          format: 'json'
        }),
      });

      if (response.ok) {
        setSuccessMessage('Config saved successfully');
        setTimeout(() => setSuccessMessage(''), 3000);
      } else {
        throw new Error('Save failed');
      }
    } catch (err) {
      setError('Failed to save config');
      console.error('Save failed:', err);
    }
  };

  const handleFormChange = ({ data }: any) => {
    setConfigData(data);
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ mt: 4 }}>
        <Grid container spacing={3}>
          {/* Left sidebar - Config & Schema Lists */}
          <Grid item xs={3}>
            <Paper sx={{ p: 2, mb: 2 }}>
              <Typography variant="h6" gutterBottom>
                Configurations
              </Typography>
              <List>
                {configs.map((config) => (
                  <ListItem key={config} disablePadding>
                    <ListItemButton
                      selected={selectedConfig === config}
                      onClick={() => handleConfigSelect(config)}
                    >
                      <ListItemText primary={config} />
                    </ListItemButton>
                  </ListItem>
                ))}
              </List>
            </Paper>

            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Schemas
              </Typography>
              <List>
                {schemas.map((schema) => (
                  <ListItem key={schema} disablePadding>
                    <ListItemButton
                      selected={selectedSchema === schema}
                      onClick={() => handleSchemaSelect(schema)}
                    >
                      <ListItemText primary={schema} />
                    </ListItemButton>
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>

          {/* Right side - Form */}
          <Grid item xs={9}>
            <Paper sx={{ p: 2 }}>
              {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {error}
                </Alert>
              )}
              {successMessage && (
                <Alert severity="success" sx={{ mb: 2 }}>
                  {successMessage}
                </Alert>
              )}

              {selectedConfig && configData && schemaData && (
                <>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="h6" gutterBottom>
                      Editing: {selectedConfig}
                    </Typography>
                    <Button
                      variant="contained"
                      color="primary"
                      onClick={handleSave}
                      sx={{ mr: 1 }}
                    >
                      Save
                    </Button>
                    <Button
                      variant="outlined"
                      onClick={refreshAll}
                    >
                      Refresh
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
              )}
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </Container>
  );
};

export default ConfigManagement; 