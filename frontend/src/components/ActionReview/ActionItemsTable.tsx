import React, { useMemo, useState } from "react";
import {
  Box,
  Paper,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  TableSortLabel,
  TextField,
  Select,
  MenuItem,
  InputLabel,
  FormControl,
  Typography,
  Chip,
  Stack,
} from "@mui/material";
import { ActionPlanItem } from "../../hooks/useActionPlan";

const ITEM_TYPES = [
  "ALL",
  "COMPLIANCE",
  "APPEAL_CONSIDERATION",
  "INTERNAL_REVIEW",
  "ESCALATION",
  "MONITORING",
];

type SortKey =
  | "title"
  | "item_type"
  | "priority"
  | "due_date"
  | "department_name"
  | "verification_status";

interface ActionItemsTableProps {
  items: ActionPlanItem[];
  selectedItemId?: string;
  onSelect: (id: string) => void;
}

const ActionItemsTable: React.FC<ActionItemsTableProps> = ({
  items,
  selectedItemId,
  onSelect,
}) => {
  const [filterType, setFilterType] = useState<string>("ALL");
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("priority");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");

  const filteredItems = useMemo(() => {
    return items
      .filter((item) => {
        if (filterType !== "ALL" && item.item_type !== filterType) {
          return false;
        }
        const query = search.toLowerCase();
        return (
          item.title.toLowerCase().includes(query) ||
          item.description.toLowerCase().includes(query) ||
          (item.department_name || "").toLowerCase().includes(query)
        );
      })
      .sort((a, b) => {
        const aValue = a[sortKey] ?? "";
        const bValue = b[sortKey] ?? "";
        const aText = String(aValue).toLowerCase();
        const bText = String(bValue).toLowerCase();
        if (aText < bText) return sortDirection === "asc" ? -1 : 1;
        if (aText > bText) return sortDirection === "asc" ? 1 : -1;
        return 0;
      });
  }, [items, filterType, search, sortKey, sortDirection]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDirection((current) => (current === "asc" ? "desc" : "asc"));
      return;
    }
    setSortKey(key);
    setSortDirection("asc");
  };

  return (
    <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        spacing={2}
        alignItems="center"
        sx={{ mb: 2 }}
      >
        <TextField
          size="small"
          label="Search action items"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          sx={{ minWidth: 240 }}
        />
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Filter by type</InputLabel>
          <Select
            value={filterType}
            label="Filter by type"
            onChange={(event) => setFilterType(event.target.value)}
          >
            {ITEM_TYPES.map((type) => (
              <MenuItem key={type} value={type}>
                {type.replaceAll("_", " ")}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Stack>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>#</TableCell>
            <TableCell
              sortDirection={sortKey === "title" ? sortDirection : false}
            >
              <TableSortLabel
                active={sortKey === "title"}
                direction={sortDirection}
                onClick={() => handleSort("title")}
              >
                Title
              </TableSortLabel>
            </TableCell>
            <TableCell
              sortDirection={sortKey === "item_type" ? sortDirection : false}
            >
              <TableSortLabel
                active={sortKey === "item_type"}
                direction={sortDirection}
                onClick={() => handleSort("item_type")}
              >
                Type
              </TableSortLabel>
            </TableCell>
            <TableCell
              sortDirection={sortKey === "priority" ? sortDirection : false}
            >
              <TableSortLabel
                active={sortKey === "priority"}
                direction={sortDirection}
                onClick={() => handleSort("priority")}
              >
                Priority
              </TableSortLabel>
            </TableCell>
            <TableCell
              sortDirection={sortKey === "due_date" ? sortDirection : false}
            >
              <TableSortLabel
                active={sortKey === "due_date"}
                direction={sortDirection}
                onClick={() => handleSort("due_date")}
              >
                Due Date
              </TableSortLabel>
            </TableCell>
            <TableCell
              sortDirection={
                sortKey === "department_name" ? sortDirection : false
              }
            >
              <TableSortLabel
                active={sortKey === "department_name"}
                direction={sortDirection}
                onClick={() => handleSort("department_name")}
              >
                Dept
              </TableSortLabel>
            </TableCell>
            <TableCell
              sortDirection={
                sortKey === "verification_status" ? sortDirection : false
              }
            >
              <TableSortLabel
                active={sortKey === "verification_status"}
                direction={sortDirection}
                onClick={() => handleSort("verification_status")}
              >
                Status
              </TableSortLabel>
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {filteredItems.map((item, index) => (
            <TableRow
              key={item.id}
              hover
              selected={item.id === selectedItemId}
              onClick={() => onSelect(item.id)}
              sx={{ cursor: "pointer" }}
            >
              <TableCell>{index + 1}</TableCell>
              <TableCell>
                <Typography variant="body2" noWrap>
                  {item.title}
                </Typography>
              </TableCell>
              <TableCell>{item.item_type.replaceAll("_", " ")}</TableCell>
              <TableCell>
                <Chip label={item.priority} size="small" />
              </TableCell>
              <TableCell>{item.due_date || "TBD"}</TableCell>
              <TableCell>{item.department_name || "Unassigned"}</TableCell>
              <TableCell>{item.verification_status}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {filteredItems.length === 0 && (
        <Box sx={{ p: 4, textAlign: "center" }}>
          <Typography color="text.secondary">
            No action items match the current filter.
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

export default ActionItemsTable;
