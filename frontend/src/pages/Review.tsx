import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Grid,
  Card,
  CardContent,
  CardHeader,
  TextField,
  Chip,
  Stack,
  Divider,
  Paper,
  Snackbar,
} from '@mui/material';
import { Refresh as RefreshIcon } from '@mui/icons-material';
import { useDocumentStatus } from '../hooks/useDocumentStatus';
import { useDocumentReview } from '../hooks/useDocumentReview';
import { ReviewApiError, useVersionTracker } from '../hooks/useExtractionReview';

const Review: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data, loading, error, refetch } = useDocumentStatus(id, {
    autoRefresh: true,
    processingIntervalMs: 5000,
    idleIntervalMs: 30000,
  });
  const { submitReview, loading: reviewLoading, error: reviewError } = useDocumentReview(id);
  const [editedValues, setEditedValues] = useState<Record<string, string>>({});
  const [commentValues, setCommentValues] = useState<Record<string, string>>({});
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const { versionById, changedIds, recentlyReviewedItems, markConflict, clearChanged } = useVersionTracker(
    data?.extracted_fields ?? []
  );

  const handleChange = (fieldId: string, value: string) => {
    setEditedValues((prev) => ({ ...prev, [fieldId]: value }));
  };

  const handleCommentChange = (fieldId: string, value: string) => {
    setCommentValues((prev) => ({ ...prev, [fieldId]: value }));
  };

  const handleReviewAction = async (fieldId: string, action: 'APPROVE' | 'EDIT' | 'REJECT') => {
    if (!data) return;

    const field = data.extracted_fields.find((item: any) => item.id === fieldId);
    if (!field) return;

    const payload: any = {
      field_id: fieldId,
      action,
      comments: commentValues[fieldId] || undefined,
      expected_version: versionById[fieldId] ?? field.version ?? 1,
    };

    if (action === 'EDIT') {
      payload.edited_value = editedValues[fieldId] ?? field.value;
      payload.edit_reason = `Verified and corrected field ${field.field_type}`;
    }

    try {
      await submitReview(payload);
      setSuccessMessage(`Field ${action.toLowerCase()}ed successfully.`);
      setEditedValues((prev) => ({ ...prev, [fieldId]: '' }));
      setCommentValues((prev) => ({ ...prev, [fieldId]: '' }));
      clearChanged(fieldId);
      await refetch();
    } catch (err) {
      if (err instanceof ReviewApiError && err.status === 409) {
        const reviewerName = err.payload?.details?.last_modified_by ?? 'another reviewer';
        const currentVersion = err.payload?.current_version;
        const lastModifiedAt = err.payload?.details?.last_modified_at ?? null;
        markConflict(fieldId, reviewerName, lastModifiedAt ?? undefined, currentVersion);
        setSuccessMessage(null);
        setToastMessage(`This field was just modified by ${reviewerName}`);
        await refetch();
      }
      console.error(err);
    }
  };

  if (loading && !data) {
    return (
      <Container maxWidth="lg" sx={{ py: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error && !data) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">{error}</Alert>
        <Button onClick={() => navigate('/documents')} sx={{ mt: 2 }}>
          Back to Documents
        </Button>
      </Container>
    );
  }

  if (!data) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="warning">No document review data available</Alert>
      </Container>
    );
  }

  const reviewableFields = data.extracted_fields || [];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Extraction Review
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Review extracted fields for {data.document.filename}.
          </Typography>
        </Box>
        <Button variant="outlined" onClick={refetch} startIcon={<RefreshIcon />}>
          Refresh
        </Button>
      </Box>

      {(reviewError || successMessage) && (
        <Box sx={{ mb: 3 }}>
          {reviewError && <Alert severity="error">{reviewError}</Alert>}
          {successMessage && <Alert severity="success">{successMessage}</Alert>}
        </Box>
      )}

      <Snackbar
        open={Boolean(toastMessage)}
        autoHideDuration={5000}
        onClose={() => setToastMessage(null)}
        message={toastMessage}
      />

      <Grid container spacing={3}>
        <Grid item xs={12} lg={7}>
          <Paper variant="outlined" sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Extracted Fields
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Review each field and mark it as approved, edited, or rejected.
            </Typography>
            {reviewableFields.length === 0 ? (
              <Alert severity="info">No extracted fields are available for review yet.</Alert>
            ) : (
              <Stack spacing={2}>
                {reviewableFields.map((field: any) => (
                  <Card
                    key={field.id}
                    variant="outlined"
                    sx={{
                      borderColor: changedIds[field.id] ? 'warning.main' : undefined,
                      boxShadow: changedIds[field.id] ? '0 0 0 1px rgba(245,158,11,0.4)' : undefined,
                    }}
                  >
                    <CardHeader
                      title={field.field_type.replace(/_/g, ' ')}
                      subheader={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            Confidence {(field.confidence_score * 100).toFixed(0)}% · {field.verification_status}
                          </Typography>
                          {recentlyReviewedItems[field.id] && (
                            <Chip
                              size="small"
                              color="warning"
                              label={`Recently reviewed by ${recentlyReviewedItems[field.id].reviewerName}`}
                              sx={{ mt: 1 }}
                            />
                          )}
                          {changedIds[field.id] && (
                            <Chip size="small" color="info" label="Updated since load" sx={{ mt: 1, ml: 1 }} />
                          )}
                        </Box>
                      }
                    />
                    <CardContent>
                      <Typography variant="body2" sx={{ mb: 2 }}>
                        {field.value}
                      </Typography>
                      {field.source_quotes?.length > 0 && (
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="subtitle2">Source Quote</Typography>
                          <Typography variant="body2" color="text.secondary">
                            {field.source_quotes[0].text}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Page {field.source_quotes[0].page}
                          </Typography>
                        </Box>
                      )}

                      <TextField
                        fullWidth
                        multiline
                        minRows={2}
                        label="Edited Value"
                        value={editedValues[field.id] ?? field.value}
                        onChange={(event) => handleChange(field.id, event.target.value)}
                        sx={{ mb: 2 }}
                      />
                      <TextField
                        fullWidth
                        multiline
                        minRows={2}
                        label="Reviewer comments"
                        value={commentValues[field.id] ?? ''}
                        onChange={(event) => handleCommentChange(field.id, event.target.value)}
                        sx={{ mb: 2 }}
                      />
                      <Stack direction="row" spacing={1} flexWrap="wrap">
                        <Button
                          variant="contained"
                          onClick={() => handleReviewAction(field.id, 'APPROVE')}
                          disabled={reviewLoading}
                        >
                          Approve
                        </Button>
                        <Button
                          variant="outlined"
                          onClick={() => handleReviewAction(field.id, 'EDIT')}
                          disabled={reviewLoading || editedValues[field.id]?.trim().length === 0}
                        >
                          Save Edit
                        </Button>
                        <Button
                          variant="outlined"
                          color="error"
                          onClick={() => handleReviewAction(field.id, 'REJECT')}
                          disabled={reviewLoading}
                        >
                          Reject
                        </Button>
                      </Stack>
                    </CardContent>
                  </Card>
                ))}
              </Stack>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} lg={5}>
          <Paper variant="outlined" sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Document Preview
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Review source pages and confidence summaries while making verification decisions.
            </Typography>
            {data.page_previews.length === 0 ? (
              <Alert severity="info">No page previews available.</Alert>
            ) : (
              <Stack spacing={2}>
                {data.page_previews.slice(0, 6).map((preview: any) => (
                  <Box key={preview.page_number} sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 1, p: 2 }}>
                    <Typography variant="subtitle2">Page {preview.page_number}</Typography>
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      {preview.preview_text}
                    </Typography>
                    <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                      <Chip label={`Confidence ${(preview.confidence * 100).toFixed(0)}%`} size="small" />
                      {preview.is_low_confidence && <Chip label="Low confidence" size="small" color="warning" />}
                      {preview.has_ocr && <Chip label="OCR" size="small" color="secondary" />}
                    </Stack>
                  </Box>
                ))}
                {data.page_previews.length > 6 && (
                  <Typography variant="caption" color="text.secondary">
                    Showing first 6 page previews. Refresh for the latest data.
                  </Typography>
                )}
              </Stack>
            )}
          </Paper>

          <Paper variant="outlined" sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Review Summary
            </Typography>
            <Stack spacing={1}>
              <Typography variant="body2">Fields extracted: {data.summary.total_fields_extracted}</Typography>
              <Typography variant="body2">Verified: {data.summary.fields_verified}</Typography>
              <Typography variant="body2">Action items pending: {data.summary.action_items_pending}</Typography>
              <Divider />
              <Typography variant="body2">Status: {data.document.status.replace(/_/g, ' ')}</Typography>
              <Typography variant="body2">Last updated: {new Date(data.document.updated_at).toLocaleString()}</Typography>
            </Stack>
          </Paper>
        </Grid>
      </Grid>

      <Box sx={{ mt: 4, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Button variant="outlined" onClick={() => navigate(`/documents/${data.document.id}/status`)}>
          Back to Status
        </Button>
        <Button variant="contained" onClick={() => navigate('/documents')}>
          Documents List
        </Button>
      </Box>
    </Container>
  );
};

export default Review;
