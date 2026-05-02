import React, { useEffect, useState } from "react";
import {
  Container,
  Box,
  Typography,
  CircularProgress,
  Alert,
  Paper,
  List,
  ListItem,
  ListItemText,
} from "@mui/material";
import { adminService, SystemSettings } from "../../services/adminService";

const Settings: React.FC = () => {
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadSettings = async () => {
      setLoading(true);
      setError(null);
      try {
        setSettings(await adminService.fetchSystemSettings());
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };
    void loadSettings();
  }, []);

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          System Settings
        </Typography>
        <Typography color="text.secondary">
          Review current runtime settings and audit system status.
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Paper variant="outlined" sx={{ p: 3 }}>
          <List>
            <ListItem>
              <ListItemText
                primary="Application Name"
                secondary={settings?.app_name}
              />
            </ListItem>
            <ListItem>
              <ListItemText
                primary="Environment"
                secondary={settings?.environment}
              />
            </ListItem>
            <ListItem>
              <ListItemText
                primary="Application Version"
                secondary={settings?.version}
              />
            </ListItem>
            <ListItem>
              <ListItemText
                primary="Audit Enabled"
                secondary={settings?.audit_enabled ? "Yes" : "No"}
              />
            </ListItem>
            <ListItem>
              <ListItemText
                primary="Default Page Size"
                secondary={settings?.default_page_size}
              />
            </ListItem>
          </List>
        </Paper>
      )}
    </Container>
  );
};

export default Settings;
