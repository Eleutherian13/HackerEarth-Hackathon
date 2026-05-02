import React, { useEffect, useState } from "react";
import {
  Container,
  Box,
  Typography,
  CircularProgress,
  Alert,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Paper,
  Button,
} from "@mui/material";
import { adminService, UserAdminEntry } from "../../services/adminService";
import UserForm from "../../components/Admin/UserForm";

const Users: React.FC = () => {
  const [users, setUsers] = useState<UserAdminEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingUser, setEditingUser] = useState<UserAdminEntry | null>(null);

  const loadUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await adminService.fetchUsers({ per_page: 50 });
      setUsers(response.items);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadUsers();
  }, []);

  const handleSave = async (user: UserAdminEntry) => {
    try {
      await adminService.updateUser(user.id, {
        role: user.role,
        is_active: user.is_active,
      });
      void loadUsers();
      setEditingUser(null);
    } catch (err) {
      setError((err as Error).message);
    }
  };

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
            User Administration
          </Typography>
          <Typography color="text.secondary">
            Manage user roles and active account status from one console.
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
        <Paper variant="outlined">
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Full Name</TableCell>
                <TableCell>Email</TableCell>
                <TableCell>Role</TableCell>
                <TableCell>Department</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.id}>
                  <TableCell>{user.full_name}</TableCell>
                  <TableCell>{user.email}</TableCell>
                  <TableCell>{user.role}</TableCell>
                  <TableCell>{user.department_id || "—"}</TableCell>
                  <TableCell>
                    {user.is_active ? "Active" : "Inactive"}
                  </TableCell>
                  <TableCell align="right">
                    <Button size="small" onClick={() => setEditingUser(user)}>
                      Edit
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}

      {editingUser ? (
        <Box sx={{ mt: 4 }}>
          <UserForm
            user={editingUser}
            onSave={handleSave}
            onCancel={() => setEditingUser(null)}
          />
        </Box>
      ) : null}
    </Container>
  );
};

export default Users;
