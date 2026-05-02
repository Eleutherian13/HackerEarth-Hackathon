import React from "react";
import { Box, LinearProgress, Paper, Stack, Typography } from "@mui/material";
import { DashboardSummary } from "../../services/dashboardService";

interface ComplianceChartProps {
  summary: DashboardSummary | null;
}

const ComplianceChart: React.FC<ComplianceChartProps> = ({ summary }) => {
  const total = summary?.total_verified_items || 0;
  const overdue = summary?.overdue_items_count || 0;
  const due7 = summary?.due_within_7_days || 0;
  const due30 = summary?.due_within_30_days || 0;

  const percentage = (value: number) =>
    total === 0 ? 0 : Math.round((value / total) * 100);

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Stack spacing={2}>
        <Box>
          <Typography variant="subtitle2" color="text.secondary">
            Total verified actions
          </Typography>
          <Typography variant="h5">{total}</Typography>
        </Box>

        <Box>
          <Typography variant="body2">
            Overdue: {overdue} ({percentage(overdue)}%)
          </Typography>
          <LinearProgress
            variant="determinate"
            value={percentage(overdue)}
            sx={{ height: 10, borderRadius: 5 }}
          />
        </Box>
        <Box>
          <Typography variant="body2">
            Due within 7 days: {due7} ({percentage(due7)}%)
          </Typography>
          <LinearProgress
            variant="determinate"
            value={percentage(due7)}
            sx={{ height: 10, borderRadius: 5 }}
          />
        </Box>
        <Box>
          <Typography variant="body2">
            Due within 30 days: {due30} ({percentage(due30)}%)
          </Typography>
          <LinearProgress
            variant="determinate"
            value={percentage(due30)}
            sx={{ height: 10, borderRadius: 5 }}
          />
        </Box>
      </Stack>
    </Paper>
  );
};

export default ComplianceChart;
