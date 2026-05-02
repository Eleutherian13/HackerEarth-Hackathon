import React, { useState, useCallback } from 'react';
import {
  Box,
  Typography,
  Paper,
  Avatar,
  CircularProgress,
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import ErrorIcon from '@mui/icons-material/Error';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

interface DropZoneProps {
  onFileSelected: (file: File) => void;
}

const MAX_FILE_SIZE_MB = 50;
const ALLOWED_TYPES = ['application/pdf'];

const DropZone: React.FC<DropZoneProps> = ({ onFileSelected }) => {
  const [isDragActive, setIsDragActive] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  const validateFile = (file: File): string | null => {
    // Check file type
    if (!ALLOWED_TYPES.includes(file.type)) {
      return 'Only PDF files are allowed';
    }

    // Check file size
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > MAX_FILE_SIZE_MB) {
      return `File size must be less than ${MAX_FILE_SIZE_MB}MB (current: ${fileSizeMB.toFixed(2)}MB)`;
    }

    // Basic magic bytes check (if available)
    return null;
  };

  const handleFile = useCallback(
    (file: File) => {
      const error = validateFile(file);
      if (error) {
        setValidationError(error);
        return;
      }

      setValidationError(null);
      onFileSelected(file);
    },
    [onFileSelected]
  );

  const handleDrag = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragActive(true);
    } else if (e.type === 'dragleave') {
      setIsDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragActive(false);

      const files = e.dataTransfer.files;
      if (files && files.length > 0) {
        handleFile(files[0]);
      }
    },
    [handleFile]
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        handleFile(files[0]);
      }
    },
    [handleFile]
  );

  return (
    <Box
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      sx={{
        position: 'relative',
        border: '2px dashed',
        borderColor: isDragActive ? 'primary.main' : 'divider',
        borderRadius: 2,
        p: 4,
        textAlign: 'center',
        cursor: 'pointer',
        transition: 'all 0.3s ease',
        backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
        '&:hover': {
          borderColor: 'primary.main',
          backgroundColor: 'action.hover',
        },
      }}
    >
      <input
        type="file"
        accept=".pdf,application/pdf"
        onChange={handleInputChange}
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          opacity: 0,
          cursor: 'pointer',
          left: 0,
          top: 0,
        }}
      />

      {validationError ? (
        <>
          <Avatar
            sx={{
              width: 64,
              height: 64,
              mx: 'auto',
              mb: 2,
              backgroundColor: 'error.light',
              color: 'error.main',
            }}
          >
            <ErrorIcon />
          </Avatar>
          <Typography variant="h6" gutterBottom color="error">
            Upload Failed
          </Typography>
          <Typography variant="body2" color="error">
            {validationError}
          </Typography>
          <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mt: 1 }}>
            Please check your file and try again
          </Typography>
        </>
      ) : (
        <>
          <Avatar
            sx={{
              width: 64,
              height: 64,
              mx: 'auto',
              mb: 2,
              backgroundColor: 'primary.light',
              color: 'primary.main',
            }}
          >
            <CloudUploadIcon />
          </Avatar>
          <Typography variant="h6" gutterBottom>
            Drop PDF here or click to browse
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Supported format: PDF (Max {MAX_FILE_SIZE_MB}MB)
          </Typography>
        </>
      )}
    </Box>
  );
};

export default DropZone;
