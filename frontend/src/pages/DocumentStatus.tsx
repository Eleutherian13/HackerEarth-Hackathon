import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Box,
  Typography,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Button,
  CircularProgress,
  Alert,
  Divider,
  LinearProgress,
  Grid,
  Tab,
  Tabs,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  CheckCircleIcon,
  ErrorIcon,
  HourglassEmptyIcon,
  RefreshIcon,
  FileDownloadIcon,
} from '@mui/icons-material';
import { formatDistanceToNow, format } from 'date-fns';
import { useDocumentStatus } from '../hooks/useDocumentStatus';
import ProcessingTimeline from '../components/Processing/ProcessingTimeline';

interface PagePreview {
  page_number: number;
  preview_text: string;
  confidence: number;
  is_low_confidence: boolean;
  has_text: boolean;
  has_ocr: boolean;
}

interface DocumentStatusData {
  document: {
    id: string;
    filename: string;
    status: string;
    status_label?: string;
    status_color?: string;
    error_message?: string;
    page_count?: number;
    file_size_mb: number;
    is_text_based?: boolean;
    metadata: Record<string, string>;
    uploaded_by_department?: string;
    created_at: string;
    updated_at: string;
  };
  progress_percentage: number;
  current_stage: string;
  estimated_time_remaining_seconds?: number | null;
  processing_log: any[];
  page_previews: PagePreview[];
  low_confidence_pages: number[];
  can_retry: boolean;
  retry_endpoint?: string | null;
  processing_jobs: ProcessingJob[];
  extracted_fields: ExtractedField[];
  action_plan_items: ActionPlanItem[];
  summary: {
    total_fields_extracted: number;
    fields_verified: number;
    total_action_items: number;
    action_items_completed: number;
    action_items_pending: number;
  };
}

interface ProcessingJob {
  id: string;
  type: string;
  status: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  retry_count: number;
  created_at: string;
}

interface ExtractedField {
  id: string;
  field_type: string;
  value: string;
  normalized_value?: string;
  confidence_score: number;
  extraction_method: string;
  verification_status: string;
  is_inferred: boolean;
  source_page_ids: number[];
}

interface ActionPlanItem {
  id: string;
  title: string;
  type: string;
  priority: string;
  due_date?: string;
  completion_status: string;
  verification_status: string;
  description: string;
}

function TabPanel(props: any) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 2 }}>{children}</Box>}
    </div>
  );
}

const StatusIcon: React.FC<{ status: string }> = ({ status }) => {
  const statusMap: Record<string, { icon: React.ReactNode; color: string }> = {
    COMPLETED: { icon: <CheckCircleIcon />, color: 'success' },
    FAILED: { icon: <ErrorIcon />, color: 'error' },
    IN_PROGRESS: { icon: <CircularProgress size={24} />, color: 'info' },
    PENDING: { icon: <HourglassEmptyIcon />, color: 'warning' },
    UPLOADED: { icon: <HourglassEmptyIcon />, color: 'info' },
    QUEUED: { icon: <HourglassEmptyIcon />, color: 'info' },
  };

  const config = statusMap[status] || statusMap.PENDING;
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <Box sx={{ color: `${config.color}.main` }}>{config.icon}</Box>
      <span>{status}</span>
    </Box>
  );
};

const DocumentStatus: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [tabValue, setTabValue] = useState(0);

  const { data, loading, error, refetch } = useDocumentStatus(id, {
    autoRefresh: true,
    processingIntervalMs: 3000,
    idleIntervalMs: 30000,
  });
  const [retrying, setRetrying] = useState(false);

  const handleRetry = async () => {
    if (!data?.retry_endpoint) return;

    try {
      setRetrying(true);
      const response = await fetch(data.retry_endpoint, { method: 'POST' });
      if (!response.ok) {
        throw new Error('Retry request failed');
      }
      await refetch();
    } catch (err) {
      console.error(err);
    } finally {
      setRetrying(false);
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
        <Alert severity="warning">No data available</Alert>
      </Container>
    );
  }

  const getStatusColor = (status: string) => {
    if (status === 'COMPLETED') return 'success';
    if (status === 'FAILED') return 'error';
    if (status === 'IN_PROGRESS') return 'info';
    return 'warning';
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Document Processing Status
          </Typography>
          <Typography variant="body1" color="textSecondary">
            {data.document.filename}
          </Typography>
        </Box>
        <Button
          variant="outlined"
          onClick={refetch}
          startIcon={<RefreshIcon />}
        >
          Refresh
        </Button>
      </Box>

      {/* Overall Status Card */}
      <Paper elevation={0} sx={{ border: '1px solid', borderColor: 'divider', p: 3, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={8}>
            <Typography variant="h6" gutterBottom>
              Processing Status
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1, flexWrap: 'wrap' }}>
              <Chip
                label={data.document.status.replace(/_/g, ' ')}
                color={getStatusColor(data.document.status) as any}
                variant="filled"
              />
              <Typography variant="body2" color="textSecondary">
                Uploaded {formatDistanceToNow(new Date(data.document.created_at), { addSuffix: true })}
              </Typography>
            </Box>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
              Current stage: {data.current_stage}
            </Typography>
            <Box sx={{ mb: 2 }}>
              <LinearProgress value={data.progress_percentage} variant="determinate" sx={{ height: 12, borderRadius: 6 }} />
              <Typography variant="caption" color="textSecondary">
                {data.progress_percentage}% complete
                {data.estimated_time_remaining_seconds ? ` · ${Math.ceil(data.estimated_time_remaining_seconds / 60)} min remaining` : ''}
              </Typography>
            </Box>
            {data.document.error_message && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {data.document.error_message}
              </Alert>
            )}
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card variant="outlined">
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  File Information
                </Typography>
                <Typography variant="body2">
                  <strong>Size:</strong> {data.document.file_size_mb.toFixed(2)} MB
                </Typography>
                <Typography variant="body2">
                  <strong>Pages:</strong> {data.document.page_count || 'N/A'}
                </Typography>
                <Typography variant="body2">
                  <strong>Text-based:</strong> {data.document.is_text_based ? 'Yes' : 'No'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Summary Stats */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Fields Extracted
              </Typography>
              <Typography variant="h5">
                {data.summary.total_fields_extracted}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                {data.summary.fields_verified} verified
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Action Items
              </Typography>
              <Typography variant="h5">
                {data.summary.total_action_items}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                {data.summary.action_items_completed} completed
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Processing Jobs
              </Typography>
              <Typography variant="h5">
                {data.processing_jobs.length}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                {data.processing_jobs.filter(j => j.status === 'COMPLETED').length} completed
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Pending Items
              </Typography>
              <Typography variant="h5">
                {data.summary.action_items_pending}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                action items
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {data.low_confidence_pages.length > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          Low confidence detected on pages: {data.low_confidence_pages.join(', ')}. These pages may require manual review.
        </Alert>
      )}

      <Paper elevation={0} sx={{ border: '1px solid', borderColor: 'divider', mb: 3, p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Page Previews
        </Typography>
        <Grid container spacing={2}>
          {data.page_previews.slice(0, 6).map((page) => (
            <Grid item xs={12} sm={6} md={4} key={page.page_number}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent>
                  <Typography variant="subtitle2" gutterBottom>
                    Page {page.page_number}
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    {page.preview_text}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Confidence {(page.confidence * 100).toFixed(0)}%
                  </Typography>
                  {page.is_low_confidence && (
                    <Chip label="Low confidence" color="warning" size="small" sx={{ mt: 1 }} />
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
          {data.page_previews.length > 6 && (
            <Grid item xs={12}>
              <Typography variant="body2" color="textSecondary">
                Showing first 6 pages. Refresh for the latest previews.
              </Typography>
            </Grid>
          )}
        </Grid>
      </Paper>

      {/* Tabs for Details */}
      <Paper elevation={0} sx={{ border: '1px solid', borderColor: 'divider' }}>
        <Tabs
          value={tabValue}
          onChange={(_, newValue) => setTabValue(newValue)}
          variant="fullWidth"
          sx={{ borderBottom: '1px solid', borderColor: 'divider' }}
        >
          <Tab label="Processing Jobs" />
          <Tab label="Extracted Fields" />
          <Tab label="Action Plan" />
          <Tab label="Timeline" />
        </Tabs>

        {/* Processing Jobs Tab */}
        <TabPanel value={tabValue} index={0}>
          {data.processing_jobs.length === 0 ? (
            <Typography color="textSecondary">No processing jobs yet</Typography>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow sx={{ backgroundColor: 'action.hover' }}>
                    <TableCell>Job Type</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Started</TableCell>
                    <TableCell>Completed</TableCell>
                    <TableCell>Error</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.processing_jobs.map((job) => (
                    <TableRow key={job.id}>
                      <TableCell>{job.type}</TableCell>
                      <TableCell>
                        <Chip
                          label={job.status}
                          color={getStatusColor(job.status) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {job.started_at
                          ? format(new Date(job.started_at), 'MM/dd/yyyy HH:mm:ss')
                          : '-'}
                      </TableCell>
                      <TableCell>
                        {job.completed_at
                          ? format(new Date(job.completed_at), 'MM/dd/yyyy HH:mm:ss')
                          : '-'}
                      </TableCell>
                      <TableCell>
                        {job.error_message ? (
                          <Typography variant="caption" color="error">
                            {job.error_message}
                          </Typography>
                        ) : (
                          '-'
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </TabPanel>

        {/* Extracted Fields Tab */}
        <TabPanel value={tabValue} index={1}>
          {data.extracted_fields.length === 0 ? (
            <Typography color="textSecondary">No fields extracted yet</Typography>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow sx={{ backgroundColor: 'action.hover' }}>
                    <TableCell>Field Type</TableCell>
                    <TableCell>Value</TableCell>
                    <TableCell>Confidence</TableCell>
                    <TableCell>Verification</TableCell>
                    <TableCell>Pages</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.extracted_fields.map((field) => (
                    <TableRow key={field.id}>
                      <TableCell>{field.field_type}</TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ maxWidth: '300px', overflow: 'hidden' }}>
                          {field.value.substring(0, 100)}
                          {field.value.length > 100 ? '...' : ''}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <LinearProgress
                            variant="determinate"
                            value={field.confidence_score * 100}
                            sx={{ width: '100px' }}
                          />
                          <Typography variant="caption">
                            {(field.confidence_score * 100).toFixed(0)}%
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={field.verification_status}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>{field.source_page_ids.join(', ')}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </TabPanel>

        {/* Action Plan Tab */}
        <TabPanel value={tabValue} index={2}>
          {data.action_plan_items.length === 0 ? (
            <Typography color="textSecondary">No action items generated yet</Typography>
          ) : (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {data.action_plan_items.map((item) => (
                <Card key={item.id} variant="outlined">
                  <CardHeader
                    title={item.title}
                    subheader={
                      <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                        <Chip
                          label={item.priority}
                          size="small"
                          color={
                            item.priority === 'HIGH'
                              ? 'error'
                              : item.priority === 'MEDIUM'
                              ? 'warning'
                              : 'success'
                          }
                        />
                        <Chip
                          label={item.completion_status}
                          size="small"
                          variant="outlined"
                        />
                        {item.due_date && (
                          <Typography variant="caption" sx={{ alignSelf: 'center' }}>
                            Due: {format(new Date(item.due_date), 'MMM dd, yyyy')}
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                  <CardContent>
                    <Typography variant="body2" color="textSecondary">
                      {item.description}
                    </Typography>
                  </CardContent>
                </Card>
              ))}
            </Box>
          )}
        </TabPanel>

        {/* Timeline Tab */}
        <TabPanel value={tabValue} index={3}>
          <ProcessingTimeline entries={data.processing_log} lowConfidencePages={data.low_confidence_pages} />
        </TabPanel>
      </Paper>

      {/* Actions */}
      <Box sx={{ mt: 4, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Button variant="contained" color="primary" onClick={() => navigate('/documents')}>
          View All Documents
        </Button>
        {data.can_retry && data.retry_endpoint && (
          <Button
            variant="contained"
            color="error"
            onClick={handleRetry}
            disabled={retrying}
          >
            {retrying ? 'Retrying...' : 'Retry Processing'}
          </Button>
        )}
        {['EXTRACTION_COMPLETE', 'PENDING_REVIEW', 'UNDER_REVIEW', 'VERIFIED'].includes(data.document.status) && (
          <Button
            variant="outlined"
            onClick={() => navigate(`/documents/${data.document.id}/review`)}
            startIcon={<FileDownloadIcon />}
          >
            View Extraction
          </Button>
        )}
        {(data.action_plan_items.length > 0 || data.document.status === 'VERIFIED') && (
          <Button
            variant="outlined"
            onClick={() => navigate(`/documents/${data.document.id}/action-plan-review`)}
          >
            Review Action Plan
          </Button>
        )}
        <Button variant="outlined" onClick={refetch} startIcon={<RefreshIcon />}>
          Refresh Status
        </Button>
      </Box>
    </Container>
  );
};

export default DocumentStatus;
