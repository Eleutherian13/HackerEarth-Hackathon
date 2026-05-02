import React, { useState } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Alert,
  Button,
  Card,
  CardContent,
  Divider,
  Grid,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import DropZone from '../components/Upload/DropZone';
import UploadProgress from '../components/Upload/UploadProgress';

interface UploadResponse {
  id: string;
  original_filename: string;
  page_count: number;
  processing_status: string;
}

interface UploadError {
  message: string;
  code?: string;
}

const Upload: React.FC = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedDocument, setUploadedDocument] = useState<UploadResponse | null>(null);
  const [error, setError] = useState<UploadError | null>(null);
  const [metadata, setMetadata] = useState<Record<string, string>>({});

  const handleFileSelected = (selectedFile: File) => {
    setFile(selectedFile);
    setError(null);
    setUploadedDocument(null);
  };

  const handleMetadataChange = (key: string, value: string) => {
    setMetadata((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleUpload = async () => {
    if (!file) {
      setError({ message: 'Please select a file', code: 'NO_FILE' });
      return;
    }

    setIsUploading(true);
    setError(null);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('metadata_json', JSON.stringify(metadata));

      const xhr = new XMLHttpRequest();

      // Track upload progress
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const percentComplete = (event.loaded / event.total) * 100;
          setUploadProgress(Math.round(percentComplete));
        }
      });

      // Handle completion
      xhr.addEventListener('load', () => {
        if (xhr.status === 202 || xhr.status === 200) {
          const response = JSON.parse(xhr.responseText);
          setUploadedDocument(response);
          setFile(null);
          setMetadata({});
        } else {
          const errorResponse = JSON.parse(xhr.responseText);
          setError({
            message: errorResponse.detail || 'Upload failed',
            code: xhr.status.toString(),
          });
        }
        setIsUploading(false);
        setUploadProgress(0);
      });

      // Handle error
      xhr.addEventListener('error', () => {
        setError({
          message: 'Network error during upload',
          code: 'NETWORK_ERROR',
        });
        setIsUploading(false);
        setUploadProgress(0);
      });

      xhr.open('POST', '/api/v1/documents/upload');
      xhr.send(formData);
    } catch (err) {
      setError({
        message: err instanceof Error ? err.message : 'Unknown error',
        code: 'UPLOAD_ERROR',
      });
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const handleViewStatus = () => {
    if (uploadedDocument) {
      navigate(`/documents/${uploadedDocument.id}/status`);
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Upload Court Judgment
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Upload a PDF document of a court judgment. The system will extract key information
          and generate an action plan.
        </Typography>
      </Box>

      {/* Success State */}
      {uploadedDocument && (
        <Alert severity="success" sx={{ mb: 3 }}>
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Document uploaded successfully!
            </Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>
              Document ID: <code>{uploadedDocument.id}</code>
            </Typography>
            <Typography variant="body2">
              Status: <strong>{uploadedDocument.processing_status}</strong>
            </Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              Pages: {uploadedDocument.page_count}
            </Typography>
            <Button
              variant="contained"
              color="success"
              onClick={handleViewStatus}
              sx={{ mt: 2 }}
              size="small"
            >
              View Processing Status
            </Button>
            <Button
              variant="outlined"
              onClick={() => {
                setUploadedDocument(null);
                setFile(null);
              }}
              sx={{ mt: 2, ml: 1 }}
              size="small"
            >
              Upload Another
            </Button>
          </Box>
        </Alert>
      )}

      {/* Error State */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Upload Failed
            </Typography>
            <Typography variant="body2">{error.message}</Typography>
            {error.code === 'DUPLICATE' && (
              <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                This document already exists in the system. Contact administrator to reprocess.
              </Typography>
            )}
            {error.code === 'FILE_TOO_LARGE' && (
              <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                Maximum file size is 50MB. Please choose a smaller file.
              </Typography>
            )}
            {error.code === 'INVALID_PDF' && (
              <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                Please ensure the file is a valid, unencrypted PDF document.
              </Typography>
            )}
          </Box>
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Main Upload Zone */}
        <Grid item xs={12} md={8}>
          <Paper elevation={0} sx={{ border: '1px solid', borderColor: 'divider', p: 3 }}>
            {isUploading ? (
              <UploadProgress progress={uploadProgress} />
            ) : (
              <>
                <DropZone onFileSelected={handleFileSelected} />

                {file && !isUploading && (
                  <Box sx={{ mt: 3 }}>
                    <Divider sx={{ mb: 2 }} />
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle2" gutterBottom>
                          Selected File
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          Name: {file.name}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          Size: {(file.size / 1024 / 1024).toFixed(2)} MB
                        </Typography>
                      </CardContent>
                    </Card>
                  </Box>
                )}

                {file && !isUploading && (
                  <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
                    <Button
                      variant="contained"
                      color="primary"
                      onClick={handleUpload}
                      size="large"
                    >
                      Upload Document
                    </Button>
                    <Button
                      variant="outlined"
                      onClick={() => setFile(null)}
                      size="large"
                    >
                      Cancel
                    </Button>
                  </Box>
                )}

                {!file && !isUploading && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="caption" display="block" color="textSecondary">
                      Maximum file size: 50 MB
                    </Typography>
                  </Box>
                )}
              </>
            )}
          </Paper>
        </Grid>

        {/* Sidebar - Info & Metadata */}
        <Grid item xs={12} md={4}>
          <Paper elevation={0} sx={{ border: '1px solid', borderColor: 'divider', p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Guidelines
            </Typography>
            <Box component="ul" sx={{ pl: 2, mb: 2 }}>
              <Typography component="li" variant="body2" color="textSecondary">
                PDF format only
              </Typography>
              <Typography component="li" variant="body2" color="textSecondary">
                Maximum 50 MB
              </Typography>
              <Typography component="li" variant="body2" color="textSecondary">
                No password protection
              </Typography>
              <Typography component="li" variant="body2" color="textSecondary">
                Clear, readable text
              </Typography>
            </Box>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Metadata (Optional)
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
              <Box>
                <Typography variant="caption" color="textSecondary">
                  Case Reference
                </Typography>
                <input
                  type="text"
                  placeholder="e.g., 2024-HC-1234"
                  value={metadata.case_ref || ''}
                  onChange={(e) => handleMetadataChange('case_ref', e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '14px',
                  }}
                />
              </Box>
              <Box>
                <Typography variant="caption" color="textSecondary">
                  Source System
                </Typography>
                <input
                  type="text"
                  placeholder="e.g., eCourts"
                  value={metadata.source_system || ''}
                  onChange={(e) => handleMetadataChange('source_system', e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '14px',
                  }}
                />
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Upload;
