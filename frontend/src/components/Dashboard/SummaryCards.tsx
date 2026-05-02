import React from "react";
import { Box, Card, CardContent, Typography, Button } from "@mui/material";

interface SummaryCardItem {
  label: string;
  count: number;
  color: string;
  subtitle: string;
  onClick: () => void;
}

interface SummaryCardsProps {
  items: SummaryCardItem[];
}

const SummaryCards: React.FC<SummaryCardsProps> = ({ items }) => {
  return (
    <Box
      sx={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
        gap: 16,
        mb: 3,
      }}
    >
      {items.map((item) => (
        <Card
          key={item.label}
          variant="outlined"
          sx={{ borderColor: item.color }}
        >
          <CardContent>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              {item.label}
            </Typography>
            <Typography variant="h4" sx={{ color: item.color, mb: 1 }}>
              {item.count}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {item.subtitle}
            </Typography>
            <Button size="small" onClick={item.onClick}>
              View
            </Button>
          </CardContent>
        </Card>
      ))}
    </Box>
  );
};

export default SummaryCards;
