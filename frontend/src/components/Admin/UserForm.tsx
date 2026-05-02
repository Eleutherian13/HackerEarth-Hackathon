import React, { useState } from "react";
import {
  Box,
  Paper,
  Typography,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  FormControlLabel,
  Switch,
  Button,
} from "@mui/material";
import { UserAdminEntry } from "../../services/adminService";

interface UserFormProps {
  user: UserAdminEntry;
  onSave: (user: UserAdminEntry) => void;
  onCancel: () => void;
}

const roles = ["SUPERADMIN", "ADMIN", "REVIEWER", "OFFICER", "VIEWER"];

const UserForm: React.FC<UserFormProps> = ({ user, onSave, onCancel }) => {
  const [formState, setFormState] = useState<UserAdminEntry>(user);

  const handleChange = (
    field: keyof UserAdminEntry,
    value: string | boolean,
  ) => {
    setFormState((current) => ({ ...current, [field]: value }));
  };

  return (
    <Paper variant="outlined" sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Edit User
      </Typography>
      <Box sx={{ display: "grid", gap: 2 }}>
        <TextField label="Name" value={formState.full_name} disabled />
        <TextField label="Email" value={formState.email} disabled />
        <FormControl fullWidth>
          <InputLabel id="role-label">Role</InputLabel>
          <Select
            labelId="role-label"
            value={formState.role}
            label="Role"
            onChange={(event) => handleChange("role", event.target.value)}
          >
            {roles.map((role) => (
              <MenuItem key={role} value={role}>
                {role}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControlLabel
          control={
            <Switch
              checked={formState.is_active}
              onChange={(event) =>
                handleChange("is_active", event.target.checked)
              }
            />
          }
          label={formState.is_active ? "Active" : "Inactive"}
        />
        <Box sx={{ display: "flex", gap: 2, justifyContent: "flex-end" }}>
          <Button variant="outlined" onClick={onCancel}>
            Cancel
          </Button>
          <Button variant="contained" onClick={() => onSave(formState)}>
            Save
          </Button>
        </Box>
      </Box>
    </Paper>
  );
};

export default UserForm;
