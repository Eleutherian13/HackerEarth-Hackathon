import React, { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Container,
  Box,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Grid,
  Paper,
} from "@mui/material";
import { Refresh as RefreshIcon } from "@mui/icons-material";
import { useDashboard } from "../hooks/useDashboard";
import { dashboardService } from "../services/dashboardService";
import SummaryCards from "../components/Dashboard/SummaryCards";
import FilterBar from "../components/Dashboard/FilterBar";
import ComplianceChart from "../components/Dashboard/ComplianceChart";
import DepartmentChart from "../components/Dashboard/DepartmentChart";
import ActionsTable from "../components/Dashboard/ActionsTable";
import ExportButton from "../components/Dashboard/ExportButton";

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [localFilters, setLocalFilters] = useState({ per_page: 25 });
  const {
    summary,
    actions,
    departments,
    loading,
    error,
    total,
    pages,
    filters,
    setFilters,
    refetch,
  } = useDashboard(localFilters);
  const [exporting, setExporting] = useState(false);

  const summaryItems = useMemo(
    () => [
      {
        label: "Critical Actions",
        count: summary?.actions_by_priority?.CRITICAL ?? 0,
        color: "#dc2626",
        subtitle: "Highest priority items",
        onClick: () =>
          setFilters({ ...filters, priority: ["CRITICAL"], page: 1 }),
      },
      {
        label: "Overdue",
        count: summary?.overdue_items_count ?? 0,
        color: "#b91c1c",
        subtitle: "Past due date",
        onClick: () => setFilters({ ...filters, status: ["OVERDUE"], page: 1 }),
      },
      {
        label: "Due in 7 days",
        count: summary?.due_within_7_days ?? 0,
        color: "#f59e0b",
        subtitle: "Urgent deadlines",
        onClick: () =>
          setFilters({
            ...filters,
            due_date_to: new Date(new Date().setDate(new Date().getDate() + 7))
              .toISOString()
              .slice(0, 10),
            page: 1,
          }),
      },
      {
        label: "Verified this week",
        count:
          summary?.weekly_trend?.reduce<number>(
            (acc: number, item: { verified_count: number }) =>
              acc + item.verified_count,
            0,
          ) ?? 0,
        color: "#16a34a",
        subtitle: "Recent verified actions",
        onClick: () =>
          setFilters({
            ...filters,
            sort_by: "due_date",
            sort_order: "asc",
            page: 1,
          }),
      },
    ],
    [filters, setFilters, summary],
  );

  const handleClearFilters = () => {
    setFilters({ per_page: 25, page: 1 });
    setLocalFilters({ per_page: 25 });
  };

  const handleExport = async (type: "csv" | "pdf") => {
    setExporting(true);
    try {
      const blob =
        type === "csv"
          ? await dashboardService.exportCsv(filters)
          : await dashboardService.exportPdf(filters);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download =
        type === "csv"
          ? "verified_actions_export.csv"
          : "verified_actions_report.pdf";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
    } finally {
      setExporting(false);
    }
  };

  const handleMarkComplete = async (actionId: string) => {
    try {
      await dashboardService.markActionComplete(actionId);
      await refetch();
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return (
      <Container
        maxWidth="lg"
        sx={{ py: 4, display: "flex", justifyContent: "center" }}
      >
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box
        sx={{
          mb: 4,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 2,
        }}
      >
        <Box>
          <Typography variant="h4" gutterBottom>
            Verified Actions Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitor approved action items, department performance, and urgent
            deadlines.
          </Typography>
        </Box>
        <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
          <ExportButton
            disabled={exporting}
            onExportCsv={() => handleExport("csv")}
            onExportPdf={() => handleExport("pdf")}
          />
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => void refetch()}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <FilterBar
        filters={filters}
        departments={departments}
        onChange={setFilters}
        onClear={handleClearFilters}
      />
      <SummaryCards items={summaryItems} />

      <Grid container spacing={3}>
        <Grid item xs={12} lg={6}>
          <Paper variant="outlined" sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Compliance status
            </Typography>
            <ComplianceChart summary={summary} />
          </Paper>
        </Grid>
        <Grid item xs={12} lg={6}>
          <Paper variant="outlined" sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Department breakdown
            </Typography>
            <DepartmentChart
              departments={departments}
              onSelect={(department_id: string | undefined) =>
                setFilters({ ...filters, department_id, page: 1 })
              }
            />
          </Paper>
        </Grid>
      </Grid>

      <Paper variant="outlined" sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Verified actions table
        </Typography>
        <ActionsTable
          items={actions}
          total={total}
          page={filters.page ?? 1}
          perPage={filters.per_page ?? 25}
          pages={pages}
          onPageChange={(newPage: number) =>
            setFilters({ ...filters, page: newPage })
          }
          onMarkComplete={handleMarkComplete}
        />
      </Paper>

      <Box
        sx={{
          mt: 2,
          display: "flex",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: 2,
        }}
      >
        <Button variant="outlined" onClick={() => navigate("/documents")}>
          Back to Documents
        </Button>
      </Box>
    </Container>
  );
};

export default Dashboard;
