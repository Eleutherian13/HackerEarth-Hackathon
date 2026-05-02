import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Box,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  TextField,
  InputAdornment,
  Grid,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  SearchIcon,
  AddIcon,
  RefreshIcon,
  VisibilityIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';

interface Document {
  id: string;
  original_filename: string;
  processing_status: string;
  page_count?: number;
  file_size_bytes: number;
  created_at: string;
  updated_at: string;
  is_text_based?: boolean;
}

interface DocumentsListResponse {
  items: Document[];
  total: number;
  page: number;
  page_size: number;
}

const Documents: React.FC = () => {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [total, setTotal] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: (page + 1).toString(),
        page_size: pageSize.toString(),
        sort_by: sortBy,
        sort_order: sortOrder,
      });

      if (searchQuery) {
        params.append('search', searchQuery);
      }
      if (statusFilter) {
        params.append('status', statusFilter);
      }

      const response = await fetch(`/api/v1/documents?${params.toString()}`);

      if (!response.ok) {
        setError(`Error: ${response.statusText}`);
        setDocuments([]);
        return;
      }

      const data: DocumentsListResponse = await response.json();
      setDocuments(data.items);
      setTotal(data.total);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch documents');
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [page, pageSize, searchQuery, statusFilter, sortBy, sortOrder]);

  const getStatusColor = (status: string) => {
    if (status === 'COMPLETED') return 'success';
    if (status === 'FAILED') return 'error';
    if (status === 'IN_PROGRESS') return 'info';
    return 'warning';
  };

  const handleSearch = (value: string) => {
    setSearchQuery(value);
    setPage(0);
  };

  const handleStatusFilter = (status: string) => {
    setStatusFilter(status);
    setPage(0);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Documents
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Manage court judgments and legal documents
          </Typography>
        </Box>
        <Button
          variant="contained"
          color="primary"
          onClick={() => navigate('/upload')}
          startIcon={<AddIcon />}
        >
          Upload Document
        </Button>
      </Box>

      {/* Summary Stats */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Documents
              </Typography>
              <Typography variant="h5">{total}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Processing
              </Typography>
              <Typography variant="h5">
                {documents.filter((d) => d.processing_status === 'IN_PROGRESS').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Completed
              </Typography>
              <Typography variant="h5">
                {documents.filter((d) => d.processing_status === 'COMPLETED').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Failed
              </Typography>
              <Typography variant="h5">
                {documents.filter((d) => d.processing_status === 'FAILED').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper elevation={0} sx={{ border: '1px solid', borderColor: 'divider', p: 2, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={4}>
            <TextField
              fullWidth
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                label="Status"
                onChange={(e) => handleStatusFilter(e.target.value)}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="UPLOADED">Uploaded</MenuItem>
                <MenuItem value="IN_PROGRESS">In Progress</MenuItem>
                <MenuItem value="COMPLETED">Completed</MenuItem>
                <MenuItem value="FAILED">Failed</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Button
              fullWidth
              variant="outlined"
              onClick={fetchDocuments}
              startIcon={<RefreshIcon />}
            >
              Refresh
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Error */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Loading */}
      {loading && !documents.length ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : documents.length === 0 ? (
        <Alert severity="info">No documents found. Try uploading one!</Alert>
      ) : (
        <>
          {/* Table */}
          <TableContainer component={Paper} elevation={0} sx={{ border: '1px solid', borderColor: 'divider' }}>
            <Table>
              <TableHead>
                <TableRow sx={{ backgroundColor: 'action.hover' }}>
                  <TableCell>Filename</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Pages</TableCell>
                  <TableCell align="right">Size</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Uploaded</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {documents.map((doc) => (
                  <TableRow key={doc.id} hover>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {doc.original_filename.length > 40
                          ? `${doc.original_filename.substring(0, 40)}...`
                          : doc.original_filename}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={doc.processing_status}
                        color={getStatusColor(doc.processing_status) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="right">
                      {doc.page_count || '-'}
                    </TableCell>
                    <TableCell align="right">
                      {(doc.file_size_bytes / (1024 * 1024)).toFixed(2)} MB
                    </TableCell>
                    <TableCell>
                      {doc.is_text_based ? (
                        <Chip label="Text" size="small" variant="outlined" />
                      ) : (
                        <Chip label="Scanned" size="small" variant="outlined" />
                      )}
                    </TableCell>
                    <TableCell>
                      {format(new Date(doc.created_at), 'MMM dd, yyyy')}
                    </TableCell>
                    <TableCell align="right">
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={() => navigate(`/documents/${doc.id}/status`)}
                        startIcon={<VisibilityIcon />}
                      >
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Pagination */}
          <TablePagination
            rowsPerPageOptions={[5, 10, 25, 50]}
            component="div"
            count={total}
            rowsPerPage={pageSize}
            page={page}
            onPageChange={(_, newPage) => setPage(newPage)}
            onRowsPerPageChange={(event) => {
              setPageSize(parseInt(event.target.value, 10));
              setPage(0);
            }}
          />
        </>
      )}
    </Container>
  );
};

export default Documents;
