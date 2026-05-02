import React from 'react';
import {
  Box,
  LinearProgress,
  Typography,
  CircularProgress,
  Avatar,
} from '@mui/material';
import CloudSyncIcon from '@mui/icons-material/CloudSync';

interface UploadProgressProps {
  progress: number;
}

const UploadProgress: React.FC<UploadProgressProps> = ({ progress }) => {
  return (
    <Box sx={{ textAlign: 'center', py: 4 }}>
      <Avatar
        sx={{
          width: 64,
          height: 64,
          mx: 'auto',
          mb: 2,
          backgroundColor: 'primary.light',
          color: 'primary.main',
          position: 'relative',
        }}
      >
        <CloudSyncIcon />
        <CircularProgress
          variant="determinate"
          value={progress}
          size={64}
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
          }}
        />
      </Avatar>

      <Typography variant="h6" gutterBottom>
        Uploading Document
      </Typography>

      <Box sx={{ my: 2 }}>
        <LinearProgress
          variant="determinate"
          value={progress}
          sx={{ height: 8, borderRadius: 4 }}
        />
      </Box>

      <Typography variant="body2" color="textSecondary" gutterBottom>
        {progress}% Complete
      </Typography>

      <Typography variant="caption" color="textSecondary" display="block" sx={{ mt: 2 }}>
        Please wait while your document is being uploaded...
      </Typography>

      <Box
        component="ul"
        sx={{
          mt: 2,
          pl: 2,
          textAlign: 'left',
          display: 'inline-block',
          listStyle: 'none',
          p: 0,
        }}
      >
        <Typography component="li" variant="caption" color="textSecondary">
          ✓ Validating PDF
        </Typography>
        <Typography component="li" variant="caption" color="textSecondary">
          ✓ Computing file hash
        </Typography>
        <Typography component="li" variant="caption" color="textSecondary">
          {progress >= 30 ? '✓ Uploading...' : '◆ Uploading...'}
        </Typography>
        <Typography component="li" variant="caption" color="textSecondary">
          {progress >= 70 ? '✓ Creating record...' : '◆ Creating record...'}
        </Typography>
        <Typography component="li" variant="caption" color="textSecondary">
          {progress >= 100 ? '✓ Done!' : '◆ Enqueuing job...'}
        </Typography>
      </Box>
    </Box>
  );
};

export default UploadProgress;
