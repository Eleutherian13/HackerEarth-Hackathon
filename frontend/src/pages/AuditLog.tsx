import React, { useEffect, useState } from "react";
import {
  Container,
  Box,
  Typography,
  CircularProgress,
  Alert,
  Button,
  TextField,
  Pagination,
} from "@mui/material";
import { Refresh as RefreshIcon } from "@mui/icons-material";
import AuditLogTable from "../components/Audit/AuditLogTable";
import { adminService, AuditLogEntry } from "../services/adminService";

const AuditLog: React.FC = () => {
  const [items, setItems] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [perPage] = useState(25);
  const [pages, setPages] = useState(1);
  const [query, setQuery] = useState("");

  const loadLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await adminService.fetchAuditLogs({
        page,
        per_page: perPage,
        action: query,
      });
      setItems(response.items);
      setPages(response.pages);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadLogs();
  }, [page, query]);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box
        sx={{
          mb: 4,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 2,
          flexWrap: "wrap",
        }}
      >
        <Box>
          <Typography variant="h4" gutterBottom>
            Audit Log Viewer
          </Typography>
          <Typography color="text.secondary">
            Inspect system events, user activity, and immutable change history.
          </Typography>
        </Box>
        <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => void loadLogs()}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ mb: 3, display: "flex", gap: 2, flexWrap: "wrap" }}>
        <TextField
          label="Filter by action"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          size="small"
        />
      </Box>

      {loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          <AuditLogTable items={items} />
          <Box sx={{ display: "flex", justifyContent: "center", mt: 3 }}>
            <Pagination
              count={pages}
              page={page}
              onChange={(_, value) => setPage(value)}
              color="primary"
            />
          </Box>
        </>
      )}
    </Container>
  );
};

export default AuditLog;
