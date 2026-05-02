import React, { useMemo } from "react";
import { Box, Typography, Chip } from "@mui/material";

interface ChangesViewerProps {
  changes: Record<string, unknown>;
}

const renderChanges = (changes: Record<string, unknown>): React.ReactNode => {
  return Object.entries(changes).map(([key, value]) => {
    const displayValue =
      typeof value === "object" && value !== null
        ? JSON.stringify(value, null, 2)
        : String(value);
    return (
      <Box key={key} sx={{ mb: 1 }}>
        <Typography variant="subtitle2">{key}</Typography>
        <Box
          component="pre"
          sx={{
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            fontSize: 12,
            m: 0,
          }}
        >
          {displayValue}
        </Box>
      </Box>
    );
  });
};

const ChangesViewer: React.FC<ChangesViewerProps> = ({ changes }) => {
  const rendered = useMemo(() => renderChanges(changes), [changes]);

  if (!changes || Object.keys(changes).length === 0) {
    return <Typography variant="body2">No change payload</Typography>;
  }

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 1, py: 1 }}>
      <Chip label="Details" size="small" />
      {rendered}
    </Box>
  );
};

export default ChangesViewer;
