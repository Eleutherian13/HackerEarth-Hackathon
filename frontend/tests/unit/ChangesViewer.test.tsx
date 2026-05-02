import React from "react";
import { render, screen } from "@testing-library/react";
import ChangesViewer from "../../src/components/Audit/ChangesViewer";

describe("ChangesViewer", () => {
  it("renders change details when provided", () => {
    render(
      <ChangesViewer
        changes={{
          field: { old: "A", new: "B" },
          metadata: { user: "tester" },
        }}
      />,
    );

    expect(screen.getByText(/Details/i)).toBeInTheDocument();
    expect(screen.getByText(/field/i)).toBeInTheDocument();
    expect(screen.getByText(/metadata/i)).toBeInTheDocument();
    expect(screen.getByText(/"old": "A"/i)).toBeInTheDocument();
  });

  it("shows a fallback message when no changes are present", () => {
    render(<ChangesViewer changes={{}} />);
    expect(screen.getByText(/No change payload/i)).toBeInTheDocument();
  });
});
