import React from 'react';
import { Typography, Box } from '@mui/material';

const Home = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Welcome to Job Search Platform
      </Typography>
      <Typography variant="body1">
        Search for jobs and get detailed insights about requirements and skills.
      </Typography>
    </Box>
  );
};

export default Home; 