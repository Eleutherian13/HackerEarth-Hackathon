import React from "react";
import { Box, Button } from "@mui/material";

interface ExportButtonProps {
  onExportCsv: () => void;
  onExportPdf: () => void;
  disabled?: boolean;
}

const ExportButton: React.FC<ExportButtonProps> = ({
  onExportCsv,
  onExportPdf,
  disabled,
}) => (
  <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
    <Button
      variant="contained"
      color="secondary"
      onClick={onExportCsv}
      disabled={disabled}
    >
      Export CSV
    </Button>
    <Button variant="contained" onClick={onExportPdf} disabled={disabled}>
      Export PDF
    </Button>
  </Box>
);

export default ExportButton;
