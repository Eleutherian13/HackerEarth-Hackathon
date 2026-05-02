import React from "react";
import { Grid, Card, CardContent, Typography } from "@mui/material";
import { ActionPlanItem } from "../../hooks/useActionPlan";

interface SummaryCardsProps {
  items: ActionPlanItem[];
}

const CARD_CONFIG = [
  { label: "Compliance", type: "COMPLIANCE" },
  { label: "Appeal", type: "APPEAL_CONSIDERATION" },
  { label: "Review", type: "INTERNAL_REVIEW" },
  { label: "Escalation", type: "ESCALATION" },
  { label: "Monitoring", type: "MONITORING" },
];

const SummaryCards: React.FC<SummaryCardsProps> = ({ items }) => {
  const counts = CARD_CONFIG.reduce<Record<string, number>>((acc, item) => {
    acc[item.type] = items.filter(
      (plan) => plan.item_type === item.type,
    ).length;
    return acc;
  }, {});

  return (
    <Grid container spacing={2} sx={{ mb: 2 }}>
      {CARD_CONFIG.map((card) => (
        <Grid item xs={12} sm={6} md={4} lg={2} key={card.type}>
          <Card variant="outlined" sx={{ minHeight: 120 }}>
            <CardContent>
              <Typography
                variant="subtitle2"
                color="text.secondary"
                gutterBottom
              >
                {card.label}
              </Typography>
              <Typography variant="h4">{counts[card.type] || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
};

export default SummaryCards;
