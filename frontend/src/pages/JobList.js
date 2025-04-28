import React from 'react';
import { Typography, Box } from '@mui/material';

const JobList = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Job Listings
      </Typography>
      <Typography variant="body1">
        View and manage your job listings here.
      </Typography>
    </Box>
  );
};

export default JobList; 