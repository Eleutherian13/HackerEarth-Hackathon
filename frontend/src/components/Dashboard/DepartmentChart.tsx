import React from 'react';
import { Box, Chip, List, ListItem, ListItemText, Paper, Typography } from '@mui/material';
import { DepartmentBreakdownItem } from '../../services/dashboardService';

interface DepartmentChartProps {
  departments: DepartmentBreakdownItem[];
  onSelect: (department_id: string | undefined) => void;
}

const DepartmentChart: React.FC<DepartmentChartProps> = ({ departments, onSelect }) => {
  const sorted = [...departments].sort((a, b) => b.item_count - a.item_count).slice(0, 6);

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 2 }}>
        Departments by verified actions
      </Typography>
      <List dense>
        {sorted.map((department) => (
          <ListItem key={department.department_id} button onClick={() => onSelect(department.department_id)}>
            <ListItemText
              primary={department.department_name}
              secondary={`Verified ${department.item_count} • Overdue ${department.overdue_count}`}
            />
            <Chip label={department.item_count} size="small" color="primary" />
          </ListItem>
        ))}
      </List>
      <Box sx={{ mt: 2 }}>
        <Chip label="View all departments" onClick={() => onSelect(undefined)} clickable />
      </Box>
    </Paper>
  );
};

export default DepartmentChart;
