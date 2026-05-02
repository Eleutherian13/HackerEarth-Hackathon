import { rest } from "msw";

export const handlers = [
  rest.get("/api/v1/admin/audit-logs", (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
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
      }),
    );
  }),

  rest.get("/api/v1/admin/users", (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
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
      }),
    );
  }),
];
