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
  Button,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import axios from 'axios';

const JobList = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedLocations, setSelectedLocations] = useState([]);
  const [minYears, setMinYears] = useState('');
  const [maxYears, setMaxYears] = useState('');
  const [searchTitle, setSearchTitle] = useState('');
  // Search form state
  const [searchOpen, setSearchOpen] = useState(true);
  const [keyword, setKeyword] = useState('');
  const [location, setLocation] = useState('');
  const [maxJobs, setMaxJobs] = useState(10);
  const [daysBack, setDaysBack] = useState(30);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState('');

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

  // Search handler for analyze-and-save
  const handleSearch = async () => {
    setSearchLoading(true);
    setSearchError('');
    try {
      const params = { keyword, location, maxJobs, daysBack };
      const response = await axios.post('http://localhost:8080/api/jobs/analyze-and-save', null, { params });
      setJobs(response.data);
      setSearchOpen(false); // Optionally close the search form after search
    } catch (err) {
      setSearchError('Failed to fetch jobs. Please try again.');
      console.error('Error:', err);
    }
    setSearchLoading(false);
  };

  const uniqueLocations = Array.from(new Set(jobs.map(job => job.location).filter(Boolean)));

  const filteredJobs = jobs.filter(job => {
    // Location filter
    const locationMatch = selectedLocations.length === 0 || selectedLocations.includes(job.location);
    // Years of experience filter
    const years = job.maxYearsRequired ?? 0;
    const minOk = minYears === '' || years >= Number(minYears);
    const maxOk = maxYears === '' || years <= Number(maxYears);
    // Title search filter
    const titleMatch = job.title.toLowerCase().includes(searchTitle.toLowerCase());
    return locationMatch && minOk && maxOk && titleMatch;
  });

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Job Listings
      </Typography>
      {/* Collapsible Search Form */}
      <Accordion expanded={searchOpen} onChange={() => setSearchOpen(!searchOpen)} sx={{ mb: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">Search & Scrape New Jobs</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Job Keyword"
                value={keyword}
                onChange={e => setKeyword(e.target.value)}
                placeholder="e.g., Java"
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Location"
                value={location}
                onChange={e => setLocation(e.target.value)}
                placeholder="e.g., Stockholm"
              />
            </Grid>
            <Grid item xs={12} sm={2}>
              <FormControl fullWidth>
                <InputLabel>Max Jobs</InputLabel>
                <Select
                  value={maxJobs}
                  label="Max Jobs"
                  onChange={e => setMaxJobs(e.target.value)}
                >
                  <MenuItem value={5}>5</MenuItem>
                  <MenuItem value={10}>10</MenuItem>
                  <MenuItem value={20}>20</MenuItem>
                  <MenuItem value={50}>50</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={2}>
              <FormControl fullWidth>
                <InputLabel>Max Age (days)</InputLabel>
                <Select
                  value={daysBack}
                  label="Max Age (days)"
                  onChange={e => setDaysBack(e.target.value)}
                >
                  <MenuItem value={7}>Last Week</MenuItem>
                  <MenuItem value={14}>Last 2 Weeks</MenuItem>
                  <MenuItem value={30}>Last Month</MenuItem>
                  <MenuItem value={90}>Last 3 Months</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <Button
                fullWidth
                variant="contained"
                onClick={handleSearch}
                disabled={searchLoading || !keyword || !location}
                sx={{ mt: 2 }}
              >
                {searchLoading ? <CircularProgress size={24} /> : 'Search & Save'}
              </Button>
            </Grid>
            {searchError && (
              <Grid item xs={12}>
                <Typography color="error">{searchError}</Typography>
              </Grid>
            )}
          </Grid>
        </AccordionDetails>
      </Accordion>
      {/* Filter Controls */}
      <Box sx={{ mb: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        {/* Title Search */}
        <TextField
          label="Search Title"
          value={searchTitle}
          onChange={e => setSearchTitle(e.target.value)}
          sx={{ width: 220 }}
        />
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
                    {/* Show Years of Experience Required in summary view */}
                    {job.maxYearsRequired !== undefined && job.maxYearsRequired !== null && (
                      <Typography variant="body2" color="textSecondary">
                        Years of Experience Required: {job.maxYearsRequired}
                      </Typography>
                    )}
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