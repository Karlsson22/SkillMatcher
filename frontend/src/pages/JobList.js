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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  ListItemText,
  TextField,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import axios from 'axios';

const JobList = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedLocations, setSelectedLocations] = useState([]);
  const [minYears, setMinYears] = useState('');
  const [maxYears, setMaxYears] = useState('');

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

  const uniqueLocations = Array.from(new Set(jobs.map(job => job.location).filter(Boolean)));

  const filteredJobs = jobs.filter(job => {
    // Location filter
    const locationMatch = selectedLocations.length === 0 || selectedLocations.includes(job.location);
    // Years of experience filter
    const years = job.maxYearsRequired ?? 0;
    const minOk = minYears === '' || years >= Number(minYears);
    const maxOk = maxYears === '' || years <= Number(maxYears);
    return locationMatch && minOk && maxOk;
  });

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Job Listings
      </Typography>
      {/* Filter Controls */}
      <Box sx={{ mb: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        {/* Location Multi-select */}
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel>Location</InputLabel>
          <Select
            multiple
            value={selectedLocations}
            onChange={e => setSelectedLocations(e.target.value)}
            label="Location"
            renderValue={selected => selected.join(', ')}
          >
            {uniqueLocations.map(loc => (
              <MenuItem key={loc} value={loc}>
                <Checkbox checked={selectedLocations.indexOf(loc) > -1} />
                <ListItemText primary={loc} />
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        {/* Years of Experience Filter */}
        <TextField
          label="Min Years"
          type="number"
          value={minYears}
          onChange={e => setMinYears(e.target.value)}
          sx={{ width: 120 }}
        />
        <TextField
          label="Max Years"
          type="number"
          value={maxYears}
          onChange={e => setMaxYears(e.target.value)}
          sx={{ width: 120 }}
        />
      </Box>
      {loading ? (
        <CircularProgress />
      ) : (
        <Grid container spacing={2}>
          {filteredJobs.map((job) => (
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
                  {job.deadline && (
                    <Typography variant="body2" color="textSecondary">
                      Deadline: {job.deadline}
                    </Typography>
                  )}
                  {job.maxYearsRequired !== undefined && job.maxYearsRequired !== null && (
                    <Typography variant="body2" color="textSecondary">
                      Years of Experience Required: {job.maxYearsRequired}
                    </Typography>
                  )}
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