import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import Users from "../../src/pages/admin/Users";
import { adminService } from "../../src/services/adminService";
import { Mock, vi } from "vitest";

vi.mock("../../src/services/adminService", () => ({
  adminService: {
    fetchUsers: vi.fn(),
    updateUser: vi.fn(),
  },
}));

describe("Admin Users Page", () => {
  it("shows a user list and opens the edit form", async () => {
    (adminService.fetchUsers as Mock).mockResolvedValue({
      items: [
        {
          id: "44444444-4444-4444-4444-444444444444",
          email: "admin@example.com",
          full_name: "Admin User",
          role: "ADMIN",
          department_id: null,
          is_active: true,
        },
      ],
      total: 1,
    });

    render(<Users />);

    await waitFor(() => {
      expect(adminService.fetchUsers).toHaveBeenCalled();
    });

    expect(screen.getByText("Admin User")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Edit/i }));
    expect(screen.getByText(/Edit User/i)).toBeInTheDocument();
  });
});
