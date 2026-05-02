import React, { useEffect, useState } from "react";
import {
  Container,
  Box,
  Typography,
  CircularProgress,
  Alert,
  Paper,
} from "@mui/material";
import {
  adminService,
  DepartmentAdminEntry,
} from "../../services/adminService";
import DepartmentTree from "../../components/Admin/DepartmentTree";

const Departments: React.FC = () => {
  const [departments, setDepartments] = useState<DepartmentAdminEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadDepartments = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await adminService.fetchDepartments({ per_page: 100 });
        setDepartments(response.items);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };
    void loadDepartments();
  }, []);

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
            Department Administration
          </Typography>
          <Typography color="text.secondary">
            View active departments, headcounts, and department-level
            organization.
          </Typography>
        </Box>
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
          <DepartmentTree departments={departments} />
        </Paper>
      )}
    </Container>
  );
};

export default Departments;
