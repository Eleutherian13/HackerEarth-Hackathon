import React from "react";
import {
  Box,
  TextField,
  Select,
  MenuItem,
  InputLabel,
  FormControl,
  Button,
  Chip,
  Stack,
} from "@mui/material";
import {
  DashboardFilters,
  DepartmentBreakdownItem,
} from "../../services/dashboardService";

interface FilterBarProps {
  filters: DashboardFilters;
  departments: DepartmentBreakdownItem[];
  onChange: (filters: DashboardFilters) => void;
  onClear: () => void;
}

const PRIORITY_OPTIONS = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];
const STATUS_OPTIONS = [
  "NOT_STARTED",
  "IN_PROGRESS",
  "COMPLETED",
  "OVERDUE",
  "CANCELLED",
];
const TYPE_OPTIONS = [
  "COMPLIANCE",
  "APPEAL_CONSIDERATION",
  "INTERNAL_REVIEW",
  "ESCALATION",
  "MONITORING",
];

const FilterBar: React.FC<FilterBarProps> = ({
  filters,
  departments,
  onChange,
  onClear,
}) => {
  const handleChange = (
    key: keyof DashboardFilters,
    value: string | string[] | undefined,
  ) => {
    onChange({ ...filters, [key]: value });
  };

  return (
    <Box
      sx={{
        p: 2,
        mb: 3,
        border: "1px solid",
        borderColor: "divider",
        borderRadius: 2,
      }}
    >
      <Stack
        direction={{ xs: "column", sm: "row" }}
        spacing={2}
        alignItems="flex-end"
        flexWrap="wrap"
      >
        <TextField
          label="Search"
          value={filters.search_query ?? ""}
          onChange={(event) => handleChange("search_query", event.target.value)}
          sx={{ minWidth: 220 }}
        />
        <FormControl sx={{ minWidth: 180 }}>
          <InputLabel>Department</InputLabel>
          <Select
            value={filters.department_id ?? ""}
            label="Department"
            onChange={(event) =>
              handleChange("department_id", event.target.value || undefined)
            }
          >
            <MenuItem value="">All Departments</MenuItem>
            {departments.map((department) => (
              <MenuItem
                key={department.department_id}
                value={department.department_id}
              >
                {department.department_name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl sx={{ minWidth: 180 }}>
          <InputLabel>Priority</InputLabel>
          <Select
            multiple
            value={filters.priority ?? []}
            label="Priority"
            onChange={(event) =>
              handleChange("priority", event.target.value as string[])
            }
            renderValue={(selected) => (
              <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                {(selected as string[]).map((value) => (
                  <Chip key={value} label={value} size="small" />
                ))}
              </Box>
            )}
          >
            {PRIORITY_OPTIONS.map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl sx={{ minWidth: 180 }}>
          <InputLabel>Status</InputLabel>
          <Select
            multiple
            value={filters.status ?? []}
            label="Status"
            onChange={(event) =>
              handleChange("status", event.target.value as string[])
            }
            renderValue={(selected) => (
              <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                {(selected as string[]).map((value) => (
                  <Chip key={value} label={value} size="small" />
                ))}
              </Box>
            )}
          >
            {STATUS_OPTIONS.map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <TextField
          label="Due date from"
          type="date"
          value={filters.due_date_from ?? ""}
          onChange={(event) =>
            handleChange("due_date_from", event.target.value || undefined)
          }
          InputLabelProps={{ shrink: true }}
          sx={{ minWidth: 180 }}
        />
        <TextField
          label="Due date to"
          type="date"
          value={filters.due_date_to ?? ""}
          onChange={(event) =>
            handleChange("due_date_to", event.target.value || undefined)
          }
          InputLabelProps={{ shrink: true }}
          sx={{ minWidth: 180 }}
        />
        <Button variant="outlined" onClick={onClear} sx={{ minWidth: 120 }}>
          Clear Filters
        </Button>
      </Stack>
    </Box>
  );
};

export default FilterBar;
