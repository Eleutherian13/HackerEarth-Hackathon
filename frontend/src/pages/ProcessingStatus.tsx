import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Grid,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  SelectChangeEvent,
  MenuItem,
  TablePagination,
} from '@mui/material';
import { Search as SearchIcon, Refresh as RefreshIcon } from '@mui/icons-material';
import DocumentStatusCard from '../components/Processing/DocumentStatusCard';

interface DocumentItem {
  id: string;
  original_filename: string;
  processing_status: string;
  page_count?: number;
  file_size_bytes: number;
  uploaded_by_department?: string | null;
  created_at: string;
  updated_at: string;
}

interface DocumentsListResponse {
  items: DocumentItem[];
  total: number;
  page: number;
  page_size: number;
}

const STATUS_OPTIONS = [
  { value: '', label: 'All' },
  { value: 'UPLOADED', label: 'Uploaded' },
  { value: 'CLASSIFYING', label: 'Classifying' },
  { value: 'EXTRACTING', label: 'Extracting' },
  { value: 'EXTRACTION_COMPLETE', label: 'Extraction Complete' },
  { value: 'PENDING_REVIEW', label: 'Pending Review' },
  { value: 'UNDER_REVIEW', label: 'Under Review' },
  { value: 'VERIFIED', label: 'Verified' },
  { value: 'FAILED', label: 'Failed' },
];

const ProcessingStatus: React.FC = () => {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(12);
  const [total, setTotal] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState('');
  const [sortOrder, setSortOrder] = useState<'desc' | 'asc'>('desc');

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: (page + 1).toString(),
        page_size: pageSize.toString(),
        sort_by: 'created_at',
        sort_order: sortOrder,
      });

      if (searchQuery) params.append('search', searchQuery);
      if (statusFilter) params.append('status', statusFilter);
      if (departmentFilter) params.append('department', departmentFilter);

      const response = await fetch(`/api/v1/documents?${params.toString()}`);
      if (!response.ok) {
        throw new Error(response.statusText || 'Failed to load documents');
      }

      const data: DocumentsListResponse = await response.json();
      setDocuments(data.items);
      setTotal(data.total);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load documents');
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [page, pageSize, searchQuery, statusFilter, departmentFilter, sortOrder]);

  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    setPage(0);
  };

  const handleStatusChange = (event: SelectChangeEvent) => {
    setStatusFilter(event.target.value as string);
    setPage(0);
  };

  const handleDepartmentChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setDepartmentFilter(event.target.value);
    setPage(0);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Processing Status
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitor document progress and review extraction status as it updates.
          </Typography>
        </Box>
        <Button variant="contained" onClick={fetchDocuments} startIcon={<RefreshIcon />}>
          Refresh
        </Button>
      </Box>

      <Card variant="outlined" sx={{ mb: 3, p: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              placeholder="Search by filename"
              value={searchQuery}
              onChange={(event) => handleSearchChange(event.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select value={statusFilter} label="Status" onChange={handleStatusChange}>
                {STATUS_OPTIONS.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              label="Department"
              value={departmentFilter}
              onChange={(e) => handleDepartmentChange(e as any)}
              placeholder="Filter by uploader department"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <FormControl fullWidth>
              <InputLabel>Sort</InputLabel>
              <Select
                value={sortOrder}
                label="Sort"
                onChange={(event) => setSortOrder(event.target.value as 'asc' | 'desc')}
              >
                <MenuItem value="desc">Newest first</MenuItem>
                <MenuItem value="asc">Oldest first</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Card>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
          <CircularProgress />
        </Box>
      ) : documents.length === 0 ? (
        <Alert severity="info">No documents match these filters.</Alert>
      ) : (
        <Box>
          <Grid container spacing={2}>
            {documents.map((document) => (
              <Grid item xs={12} sm={6} md={4} key={document.id}>
                <DocumentStatusCard
                  document={{
                    ...document,
                    progress_percentage: undefined,
                  }}
                  onClick={() => navigate(`/documents/${document.id}/status`)}
                />
              </Grid>
            ))}
          </Grid>

          <TablePagination
            component="div"
            count={total}
            page={page}
            onPageChange={(_, nextPage) => setPage(nextPage)}
            rowsPerPage={pageSize}
            onRowsPerPageChange={(event) => {
              setPageSize(parseInt(event.target.value, 10));
              setPage(0);
            }}
            rowsPerPageOptions={[6, 12, 24]}
            sx={{ mt: 3 }}
          />
        </Box>
      )}
    </Container>
  );
};

export default ProcessingStatus;
