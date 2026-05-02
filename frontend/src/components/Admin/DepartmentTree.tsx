import React from "react";
import { Box, Typography, Grid, Paper } from "@mui/material";
import { DepartmentAdminEntry } from "../../services/adminService";

interface DepartmentTreeProps {
  departments: DepartmentAdminEntry[];
}

const DepartmentTree: React.FC<DepartmentTreeProps> = ({ departments }) => {
  if (!departments.length) {
    return <Typography>No departments available.</Typography>;
  }

  return (
    <Grid container spacing={2}>
      {departments.map((department) => (
        <Grid item xs={12} md={6} key={department.id}>
          <Paper variant="outlined" sx={{ p: 2, minHeight: 140 }}>
            <Typography variant="subtitle1" gutterBottom>
              {department.name}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              {department.description || "No description available."}
            </Typography>
            <Typography variant="body2">
              Active users: {department.active_user_count ?? 0}
            </Typography>
          </Paper>
        </Grid>
      ))}
    </Grid>
  );
};

export default DepartmentTree;
