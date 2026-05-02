import React from "react";
import {
  Box,
  Button,
  Chip,
  Pagination,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { DashboardActionItem } from "../../services/dashboardService";

interface ActionsTableProps {
  items: DashboardActionItem[];
  total: number;
  page: number;
  perPage: number;
  pages: number;
  onPageChange: (page: number) => void;
  onMarkComplete: (actionId: string) => void;
}

const ActionsTable: React.FC<ActionsTableProps> = ({
  items,
  total,
  page,
  perPage,
  pages,
  onPageChange,
  onMarkComplete,
}) => {
  return (
    <Box>
      <TableContainer component={Paper} variant="outlined">
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Case</TableCell>
              <TableCell>Title</TableCell>
              <TableCell>Department</TableCell>
              <TableCell>Priority</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Due</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {items.map((item) => (
              <TableRow key={item.id} hover>
                <TableCell>{item.case_number || "N/A"}</TableCell>
                <TableCell>
                  <Typography variant="body2" noWrap>
                    {item.title}
                  </Typography>
                </TableCell>
                <TableCell>{item.department_name || "Unassigned"}</TableCell>
                <TableCell>
                  <Chip
                    label={item.priority_badge}
                    size="small"
                    color={
                      item.priority_badge === "CRITICAL"
                        ? "error"
                        : item.priority_badge === "HIGH"
                          ? "warning"
                          : "default"
                    }
                  />
                </TableCell>
                <TableCell>{item.item_type.replaceAll("_", " ")}</TableCell>
                <TableCell>{item.due_date || "TBD"}</TableCell>
                <TableCell>{item.status_chip}</TableCell>
                <TableCell align="right">
                  <Button
                    size="small"
                    variant="contained"
                    onClick={() => onMarkComplete(item.id)}
                    disabled={item.completion_status === "COMPLETED"}
                  >
                    Mark Complete
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {items.length === 0 && (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <Typography color="text.secondary" sx={{ py: 4 }}>
                    No verified actions found.
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Box
        sx={{
          mt: 2,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 2,
        }}
      >
        <Typography variant="body2" color="text.secondary">
          Showing {items.length} of {total} actions
        </Typography>
        <Pagination
          count={pages}
          page={page}
          onChange={(_, value) => onPageChange(value)}
          color="primary"
        />
      </Box>
    </Box>
  );
};

export default ActionsTable;
