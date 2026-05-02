import React from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Box,
  Chip,
} from "@mui/material";
import ChangesViewer from "./ChangesViewer";
import { AuditLogEntry } from "../../services/adminService";

interface AuditLogTableProps {
  items: AuditLogEntry[];
}

const AuditLogTable: React.FC<AuditLogTableProps> = ({ items }) => {
  return (
    <Paper variant="outlined" sx={{ width: "100%", overflowX: "auto" }}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>ID</TableCell>
            <TableCell>Event</TableCell>
            <TableCell>User</TableCell>
            <TableCell>Entity</TableCell>
            <TableCell>Action</TableCell>
            <TableCell>Changes</TableCell>
            <TableCell>When</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {items.map((item) => (
            <TableRow key={item.id}>
              <TableCell sx={{ fontSize: 12, wordBreak: "break-all" }}>
                {item.id}
              </TableCell>
              <TableCell>
                <Chip label={item.event_type} size="small" />
              </TableCell>
              <TableCell>{item.user_id ?? "System"}</TableCell>
              <TableCell>
                {item.entity_type}
                {item.entity_id ? ` (${item.entity_id.slice(0, 8)})` : ""}
              </TableCell>
              <TableCell>{item.action}</TableCell>
              <TableCell>
                <ChangesViewer changes={item.changes} />
              </TableCell>
              <TableCell>
                {new Date(item.created_at).toLocaleString()}
              </TableCell>
            </TableRow>
          ))}
          {items.length === 0 && (
            <TableRow>
              <TableCell colSpan={7}>
                <Box sx={{ py: 4, textAlign: "center" }}>
                  <Typography variant="body2" color="text.secondary">
                    No audit records found.
                  </Typography>
                </Box>
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </Paper>
  );
};

export default AuditLogTable;
