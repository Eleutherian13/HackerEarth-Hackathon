import React from 'react';
import { Card, CardActionArea, CardContent, Box, Typography, Chip, LinearProgress, Stack } from '@mui/material';
import { format } from 'date-fns';

interface DocumentStatusCardProps {
  document: {
    id: string;
    original_filename: string;
    processing_status: string;
    page_count?: number;
    file_size_bytes: number;
    uploaded_by_department?: string | null;
    created_at: string;
    updated_at: string;
    progress_percentage?: number;
  };
  onClick: () => void;
}

const STATUS_COLOR_MAP: Record<string, 'info' | 'warning' | 'success' | 'error' | 'secondary'> = {
  UPLOADED: 'info',
  CLASSIFYING: 'warning',
  EXTRACTING: 'warning',
  EXTRACTION_COMPLETE: 'warning',
  PENDING_REVIEW: 'secondary',
  UNDER_REVIEW: 'secondary',
  VERIFIED: 'success',
  REJECTED: 'error',
  FAILED: 'error',
};

const PROGRESS_MAP: Record<string, number> = {
  UPLOADED: 5,
  CLASSIFYING: 15,
  EXTRACTING: 35,
  EXTRACTION_COMPLETE: 80,
  PENDING_REVIEW: 90,
  UNDER_REVIEW: 95,
  VERIFIED: 100,
  REJECTED: 100,
  FAILED: 100,
};

const DocumentStatusCard: React.FC<DocumentStatusCardProps> = ({ document, onClick }) => {
  const statusColor = STATUS_COLOR_MAP[document.processing_status] || 'info';
  const progress = document.progress_percentage ?? PROGRESS_MAP[document.processing_status] ?? 0;

  return (
    <Card variant="outlined" sx={{ minWidth: 280, '&:hover': { boxShadow: 4 } }}>
      <CardActionArea onClick={onClick} sx={{ p: 1 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
            <Box>
              <Typography variant="subtitle1" fontWeight={600} noWrap>
                {document.original_filename}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {format(new Date(document.created_at), 'MMM dd, yyyy')}
              </Typography>
            </Box>
            <Chip
              label={document.processing_status.replace(/_/g, ' ')}
              color={statusColor}
              size="small"
            />
          </Box>

          <Stack spacing={1} sx={{ mb: 1 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="caption" color="text.secondary">
                Pages
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {document.page_count ?? 'N/A'}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="caption" color="text.secondary">
                Department
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {document.uploaded_by_department ?? 'Unknown'}
              </Typography>
            </Box>
          </Stack>

          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {document.file_size_bytes ? `${(document.file_size_bytes / (1024 * 1024)).toFixed(2)} MB` : 'Size unknown'}
          </Typography>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <LinearProgress
              variant="determinate"
              value={progress}
              sx={{ width: '100%', height: 8, borderRadius: 4 }}
            />
          </Box>
          <Typography variant="caption" color="text.secondary">
            {progress}% complete
          </Typography>
        </CardContent>
      </CardActionArea>
    </Card>
  );
};

export default DocumentStatusCard;
