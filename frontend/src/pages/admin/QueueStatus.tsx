import React, { useEffect, useState } from "react";
import {
  Container,
  Box,
  Typography,
  CircularProgress,
  Alert,
  Paper,
  Grid,
} from "@mui/material";
import { adminService, QueueStatus } from "../../services/adminService";

const QueueStatus: React.FC = () => {
  const [status, setStatus] = useState<QueueStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadStatus = async () => {
      setLoading(true);
      setError(null);
      try {
        setStatus(await adminService.fetchQueueStatus());
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };
    void loadStatus();
  }, []);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Queue Status
        </Typography>
        <Typography color="text.secondary">
          Monitor background processing jobs and queue throughput.
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
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Paper variant="outlined" sx={{ p: 3 }}>
              <Typography variant="subtitle2" color="text.secondary">
                In progress
              </Typography>
              <Typography variant="h5">{status?.processing ?? 0}</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper variant="outlined" sx={{ p: 3 }}>
              <Typography variant="subtitle2" color="text.secondary">
                Pending
              </Typography>
              <Typography variant="h5">{status?.pending ?? 0}</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper variant="outlined" sx={{ p: 3 }}>
              <Typography variant="subtitle2" color="text.secondary">
                Failed
              </Typography>
              <Typography variant="h5">{status?.failed ?? 0}</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper variant="outlined" sx={{ p: 3 }}>
              <Typography variant="subtitle2" color="text.secondary">
                Completed
              </Typography>
              <Typography variant="h5">{status?.completed ?? 0}</Typography>
            </Paper>
          </Grid>
        </Grid>
      )}
    </Container>
  );
};

export default QueueStatus;
