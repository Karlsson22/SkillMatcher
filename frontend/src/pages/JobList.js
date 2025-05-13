import React, { useEffect, useState } from 'react';
import {
  Typography,
  Box,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
  CircularProgress,
  Chip,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import axios from 'axios';

const JobList = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const response = await axios.get('http://localhost:8080/api/jobs/all');
        setJobs(response.data);
      } catch (error) {
        console.error('Failed to fetch jobs:', error);
      }
      setLoading(false);
    };
    fetchJobs();
  }, []);

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Job Listings
      </Typography>
      {loading ? (
        <CircularProgress />
      ) : (
        <Grid container spacing={2}>
          {jobs.map((job) => (
            <Grid item xs={12} md={8} key={job.id}>
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ width: '100%', display: 'flex', flexDirection: 'column' }}>
                    <Typography variant="h6">{job.title}</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 0.5 }}>
                      <Chip label={job.company} size="small" />
                      {job.postedDate && (
                        <Typography variant="body2" color="textSecondary">
                          Posted: {job.postedDate?.split('T')[0]}
                        </Typography>
                      )}
                    </Box>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                    Location: {job.location}
                  </Typography>
                  <Typography variant="body2" sx={{ whiteSpace: 'pre-line', mb: 1 }}>
                    {job.description}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Source: {job.source}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    <a href={job.url} target="_blank" rel="noopener noreferrer">
                      View Job
                    </a>
                  </Typography>
                </AccordionDetails>
              </Accordion>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
};

export default JobList; 