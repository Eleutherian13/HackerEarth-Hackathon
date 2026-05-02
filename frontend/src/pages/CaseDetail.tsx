import React from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { caseService } from "../services/caseService";
import { useCaseDetail } from "../hooks/useCaseDetail";

const CaseDetail: React.FC = () => {
  const navigate = useNavigate();
  const { documentId } = useParams<{ documentId: string }>();
  const { caseDetail, history, loading, error, refresh } = useCaseDetail(
    documentId ?? "",
  );

  const handleDownloadReport = async () => {
    if (!documentId) return;
    try {
      const blob = await caseService.downloadCaseReport(documentId);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `case_report_${documentId}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return (
      <Box sx={{ py: 8, display: "flex", justifyContent: "center" }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box
        sx={{
          mb: 3,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 2,
          flexWrap: "wrap",
        }}
      >
        <Box>
          <Typography variant="h4">Case detail</Typography>
          <Typography variant="body2" color="text.secondary">
            View verified extractions, action plan items, and audit history for
            this case.
          </Typography>
        </Box>
        <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
          <Button variant="outlined" onClick={() => navigate("/dashboard")}>
            Back to Dashboard
          </Button>
          <Button variant="contained" onClick={handleDownloadReport}>
            Download Report
          </Button>
        </Box>
      </Box>

      {error && (
        <Paper variant="outlined" sx={{ p: 3, mb: 3 }}>
          <Typography color="error">{error}</Typography>
        </Paper>
      )}

      {caseDetail && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card variant="outlined" sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Case overview
                </Typography>
                <Typography variant="body2">
                  Case number: {caseDetail.document.case_number || "N/A"}
                </Typography>
                <Typography variant="body2">
                  Title: {caseDetail.document.case_title || "N/A"}
                </Typography>
                <Typography variant="body2">
                  Court: {caseDetail.document.court || "N/A"}
                </Typography>
                <Typography variant="body2">
                  Judgment date: {caseDetail.document.judgment_date || "N/A"}
                </Typography>
                <Typography variant="body2">
                  Parties: {caseDetail.document.parties || "N/A"}
                </Typography>
                <Typography variant="body2">
                  Uploaded: {caseDetail.document.uploaded_at || "N/A"}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card variant="outlined" sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Verified summary
                </Typography>
                <Typography variant="body2">
                  Verified extractions:{" "}
                  {caseDetail.overview.total_verified_extractions}
                </Typography>
                <Typography variant="body2">
                  Verified actions: {caseDetail.overview.verified_action_items}
                </Typography>
                <Typography variant="body2">
                  Completed actions: {caseDetail.overview.completed_actions}
                </Typography>
                <Typography variant="body2">
                  Pending actions: {caseDetail.overview.pending_actions}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Verified extractions
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Field</TableCell>
                      <TableCell>Value</TableCell>
                      <TableCell>Confidence</TableCell>
                      <TableCell>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {caseDetail.extractions.map((extraction) => (
                      <TableRow key={extraction.id}>
                        <TableCell>{extraction.field_type}</TableCell>
                        <TableCell>{extraction.value}</TableCell>
                        <TableCell>{extraction.confidence_score}</TableCell>
                        <TableCell>{extraction.verification_status}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Approved action plan
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Title</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Priority</TableCell>
                      <TableCell>Due</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {caseDetail.action_plan.map((item) => (
                      <TableRow key={item.id}>
                        <TableCell>{item.title}</TableCell>
                        <TableCell>
                          {item.item_type.replaceAll("_", " ")}
                        </TableCell>
                        <TableCell>{item.priority}</TableCell>
                        <TableCell>{item.due_date || "TBD"}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Grid>

          <Grid item xs={12}>
            <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Audit history
              </Typography>
              {history.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No history records found.
                </Typography>
              ) : (
                <Box>
                  {history.map((entry) => (
                    <Paper
                      key={entry.id}
                      variant="outlined"
                      sx={{ p: 2, mb: 1 }}
                    >
                      <Typography variant="subtitle2">
                        {entry.event_type}
                      </Typography>
                      <Typography variant="body2">{entry.action}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {new Date(entry.timestamp).toLocaleString()} by{" "}
                        {entry.user_id || "system"}
                      </Typography>
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        {entry.changes}
                      </Typography>
                    </Paper>
                  ))}
                </Box>
              )}
            </Paper>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default CaseDetail;
