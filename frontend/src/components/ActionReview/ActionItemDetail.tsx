import React from "react";
import {
  Box,
  Paper,
  Typography,
  Chip,
  TextField,
  MenuItem,
  Select,
  InputLabel,
  FormControl,
  Button,
  Divider,
  Stack,
} from "@mui/material";
import { ActionPlanItem } from "../../hooks/useActionPlan";

const PRIORITY_OPTIONS = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];
const DEPARTMENT_OPTIONS = [
  "Legal Department",
  "Compliance Department",
  "Operations",
  "Finance",
  "Audit",
  "Administration",
];

interface ActionItemDetailProps {
  item: ActionPlanItem;
  modifications: Record<string, string>;
  rationale: string;
  onFieldChange: (fieldKey: string, value: string) => void;
  onReviewAction: (action: "APPROVE" | "REJECT") => void;
  onSaveChanges: () => void;
  onRationaleChange: (value: string) => void;
  loading: boolean;
}

const ActionItemDetail: React.FC<ActionItemDetailProps> = ({
  item,
  modifications,
  rationale,
  onFieldChange,
  onReviewAction,
  onSaveChanges,
  onRationaleChange,
  loading,
}) => {
  const selectedDepartment =
    modifications.responsible_department_name ?? item.department_name ?? "";
  const sourceEvidence = item.source_evidence || {};
  const quotes = Array.isArray(sourceEvidence.source_quotes)
    ? sourceEvidence.source_quotes
    : [];
  const dueDateSource =
    item.due_date_source === "EXPLICIT_IN_JUDGMENT"
      ? "Explicit"
      : item.due_date_source === "INFERRED"
        ? "Inferred"
        : "Estimated";

  return (
    <Paper variant="outlined" sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Selected action item
      </Typography>
      <Typography variant="subtitle1" sx={{ mb: 2 }}>
        {item.title}
      </Typography>
      <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: "wrap" }}>
        <Chip label={item.item_type.replaceAll("_", " ")} />
        <Chip
          label={item.priority}
          color={
            item.priority === "CRITICAL"
              ? "error"
              : item.priority === "HIGH"
                ? "warning"
                : "default"
          }
        />
        <Chip label={`Due: ${item.due_date || "TBD"}`} />
        <Chip label={dueDateSource} />
      </Stack>
      <Typography variant="body2" sx={{ mb: 2 }}>
        {item.description}
      </Typography>
      <Typography variant="subtitle2">Risk assessment</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {item.risk_if_ignored}
      </Typography>
      <Typography variant="subtitle2">Source evidence</Typography>
      {quotes.length > 0 ? (
        quotes.map((quote, index) => (
          <Box
            key={index}
            sx={{ mb: 1, p: 1, bgcolor: "background.paper", borderRadius: 1 }}
          >
            <Typography variant="body2">
              {quote.text || JSON.stringify(quote)}
            </Typography>
            {quote.page !== undefined && (
              <Typography variant="caption" color="text.secondary">
                Page {quote.page}
              </Typography>
            )}
          </Box>
        ))
      ) : (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          No quote details available.
        </Typography>
      )}
      <Divider sx={{ my: 3 }} />
      <FormControl fullWidth sx={{ mb: 2 }}>
        <TextField
          label="Title"
          value={modifications.title ?? item.title}
          onChange={(event) => onFieldChange("title", event.target.value)}
        />
      </FormControl>
      <FormControl fullWidth sx={{ mb: 2 }}>
        <TextField
          label="Description"
          multiline
          minRows={3}
          value={modifications.description ?? item.description}
          onChange={(event) => onFieldChange("description", event.target.value)}
        />
      </FormControl>
      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>Responsible department</InputLabel>
        <Select
          value={selectedDepartment}
          label="Responsible department"
          onChange={(event) =>
            onFieldChange("responsible_department_name", event.target.value)
          }
        >
          {DEPARTMENT_OPTIONS.map((option) => (
            <MenuItem key={option} value={option}>
              {option}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      <FormControl fullWidth sx={{ mb: 2 }}>
        <TextField
          label="Responsible officer"
          value={
            modifications.responsible_officer ?? item.responsible_officer ?? ""
          }
          onChange={(event) =>
            onFieldChange("responsible_officer", event.target.value)
          }
        />
      </FormControl>
      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>Priority</InputLabel>
        <Select
          value={modifications.priority ?? item.priority}
          label="Priority"
          onChange={(event) => onFieldChange("priority", event.target.value)}
        >
          {PRIORITY_OPTIONS.map((option) => (
            <MenuItem key={option} value={option}>
              {option}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      <FormControl fullWidth sx={{ mb: 2 }}>
        <TextField
          label="Notes"
          multiline
          minRows={2}
          value={modifications.notes ?? item.notes ?? ""}
          onChange={(event) => onFieldChange("notes", event.target.value)}
        />
      </FormControl>
      <FormControl fullWidth sx={{ mb: 2 }}>
        <TextField
          label="Reviewer rationale"
          multiline
          minRows={2}
          value={rationale}
          onChange={(event) => onRationaleChange(event.target.value)}
        />
      </FormControl>
      <Stack direction="row" spacing={1} flexWrap="wrap">
        <Button variant="contained" onClick={onSaveChanges} disabled={loading}>
          Save changes
        </Button>
        <Button
          variant="contained"
          color="success"
          onClick={() => onReviewAction("APPROVE")}
          disabled={loading}
        >
          Approve
        </Button>
        <Button
          variant="outlined"
          color="error"
          onClick={() => onReviewAction("REJECT")}
          disabled={loading}
        >
          Reject
        </Button>
      </Stack>
    </Paper>
  );
};

export default ActionItemDetail;
