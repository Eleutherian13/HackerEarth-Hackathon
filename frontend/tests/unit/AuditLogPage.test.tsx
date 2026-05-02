import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import AuditLog from "../../src/pages/AuditLog";
import { adminService } from "../../src/services/adminService";
import { Mock, vi } from "vitest";

vi.mock("../../src/services/adminService", () => ({
  adminService: {
    fetchAuditLogs: vi.fn(),
  },
}));

describe("AuditLog Page", () => {
  it("renders the audit viewer and loads audit log entries", async () => {
    (adminService.fetchAuditLogs as Mock).mockResolvedValue({
      items: [
        {
          id: "11111111-1111-1111-1111-111111111111",
          event_type: "DOCUMENT_UPLOADED",
          user_id: "22222222-2222-2222-2222-222222222222",
          document_id: "33333333-3333-3333-3333-333333333333",
          entity_type: "Document",
          entity_id: "33333333-3333-3333-3333-333333333333",
          action: "UPLOAD",
          changes: { field: { old: null, new: "value" } },
          ip_address: "127.0.0.1",
          user_agent: "test-agent",
          created_at: new Date().toISOString(),
        },
      ],
      total: 1,
      page: 1,
      per_page: 25,
      pages: 1,
    });

    render(<AuditLog />);

    await waitFor(() => {
      expect(adminService.fetchAuditLogs).toHaveBeenCalled();
    });

    expect(screen.getByText(/Audit Log Viewer/i)).toBeInTheDocument();
    expect(screen.getByText(/DOCUMENT_UPLOADED/i)).toBeInTheDocument();
    expect(screen.getByText(/UPLOAD/i)).toBeInTheDocument();
  });
});
