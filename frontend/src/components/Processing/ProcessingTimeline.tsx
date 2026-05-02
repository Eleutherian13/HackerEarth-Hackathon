import React from 'react';
import { Box, Typography, Chip, Paper } from '@mui/material';
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  TimelineOppositeContent,
} from '@mui/material';
import { CheckCircle as CheckCircleIcon, Error as ErrorIcon, HourglassEmpty as HourglassEmptyIcon } from '@mui/icons-material';
import { format } from 'date-fns';

export interface ProcessingTimelineEntry {
  stage: string;
  status: string;
  message: string;
  timestamp: string;
  page_number?: number;
  confidence?: number;
}

interface ProcessingTimelineProps {
  entries: ProcessingTimelineEntry[];
  lowConfidencePages?: number[];
}

const STATUS_ICON_MAP: Record<string, React.ReactNode> = {
  COMPLETED: <CheckCircleIcon fontSize="small" />, 
  FAILED: <ErrorIcon fontSize="small" />,
  EXTRACTING: <HourglassEmptyIcon fontSize="small" />,
  CLASSIFYING: <HourglassEmptyIcon fontSize="small" />,
  UPLOADED: <HourglassEmptyIcon fontSize="small" />,
};

const STATUS_COLOR_MAP: Record<string, 'success' | 'error' | 'warning' | 'info'> = {
  COMPLETED: 'success',
  FAILED: 'error',
  EXTRACTING: 'warning',
  CLASSIFYING: 'warning',
  UPLOADED: 'info',
  PENDING_REVIEW: 'info',
  UNDER_REVIEW: 'info',
  VERIFIED: 'success',
  REJECTED: 'error',
  EXTRACTION_COMPLETE: 'warning',
};

const ProcessingTimeline: React.FC<ProcessingTimelineProps> = ({ entries, lowConfidencePages = [] }) => {
  const sortedEntries = [...entries].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

  return (
    <Box>
      {lowConfidencePages.length > 0 && (
        <Paper elevation={0} sx={{ border: '1px solid', borderColor: 'warning.light', mb: 2, p: 2, backgroundColor: 'warning.lighter' }}>
          <Typography variant="subtitle2" color="warning.dark" gutterBottom>
            Low confidence warnings detected on pages: {lowConfidencePages.join(', ')}
          </Typography>
          <Typography variant="body2" color="textSecondary">
            These pages may require manual review or OCR correction.
          </Typography>
        </Paper>
      )}

      <Timeline position="alternate">
        {sortedEntries.map((entry, index) => {
          const dotColor = STATUS_COLOR_MAP[entry.status] || 'info';
          const icon = STATUS_ICON_MAP[entry.status] || <HourglassEmptyIcon fontSize="small" />;

          return (
            <TimelineItem key={`${entry.stage}-${entry.timestamp}-${index}`}>
              <TimelineOppositeContent color="textSecondary" sx={{ m: 'auto 0' }}>
                {format(new Date(entry.timestamp), 'MMM dd, HH:mm')}
              </TimelineOppositeContent>
              <TimelineSeparator>
                <TimelineDot color={dotColor}>{icon}</TimelineDot>
                {index < sortedEntries.length - 1 && <TimelineConnector />}
              </TimelineSeparator>
              <TimelineContent sx={{ py: '12px', px: 2 }}>
                <Typography variant="subtitle2">{entry.stage.replace(/_/g, ' ')}</Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, alignItems: 'center', mb: 1 }}>
                  <Chip label={entry.status} size="small" color={dotColor} />
                  {entry.page_number !== undefined && (
                    <Chip label={`Page ${entry.page_number}`} size="small" />
                  )}
                  {entry.confidence !== undefined && (
                    <Chip label={`Confidence ${(entry.confidence * 100).toFixed(0)}%`} size="small" />
                  )}
                </Box>
                <Typography variant="body2" color="textSecondary">
                  {entry.message}
                </Typography>
              </TimelineContent>
            </TimelineItem>
          );
        })}
      </Timeline>
    </Box>
  );
};

export default ProcessingTimeline;
