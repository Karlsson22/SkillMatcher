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
  Card,
  CardContent,
  CardActions,
  CardHeader,
  Divider,
  Tooltip,
  Stack,
  Fade,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import SearchIcon from '@mui/icons-material/Search';
import WorkIcon from '@mui/icons-material/Work';
import BusinessIcon from '@mui/icons-material/Business';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth';
import axios from 'axios';

const sourceColors = {
  Jobbsafari: 'primary',
  Demando: 'secondary',
  Ledigajobb: 'success',
  Arbetsformedlingen: 'info',
};

const JobList = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedLocations, setSelectedLocations] = useState([]);
  const [minYears, setMinYears] = useState('');
  const [maxYears, setMaxYears] = useState('');
  const [searchTitle, setSearchTitle] = useState('');
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

  const handleSearch = async () => {
    setSearchLoading(true);
    setSearchError('');
    try {
      const params = { keyword, location, maxJobs, daysBack };
      const response = await axios.post('http://localhost:8080/api/jobs/analyze-and-save', null, { params });
      setJobs(response.data);
      setSearchOpen(false);
    } catch (err) {
      setSearchError('Failed to fetch jobs. Please try again.');
      console.error('Error:', err);
    }
    setSearchLoading(false);
  };

  const uniqueLocations = Array.from(new Set(jobs.map(job => job.location).filter(Boolean)));

  const filteredJobs = jobs.filter(job => {
    const locationMatch = selectedLocations.length === 0 || selectedLocations.includes(job.location);
    const years = job.maxYearsRequired ?? 0;
    const minOk = minYears === '' || years >= Number(minYears);
    const maxOk = maxYears === '' || years <= Number(maxYears);
    const titleMatch = job.title.toLowerCase().includes(searchTitle.toLowerCase());
    return locationMatch && minOk && maxOk && titleMatch;
  });

  const experienceChip = (years) => {
    if (years === undefined || years === null) return null;
    let color = 'default';
    if (years <= 1) color = 'success';
    else if (years <= 3) color = 'info';
    else if (years <= 5) color = 'warning';
    else color = 'error';
    return (
      <Chip
        icon={<WorkIcon />}
        label={`Exp: ${years} yrs`}
        color={color}
        size="small"
        sx={{ fontWeight: 500 }}
      />
    );
  };

  const sourceChip = (source) => (
    <Chip
      label={source}
      color={sourceColors[source] || 'default'}
      size="small"
      sx={{ fontWeight: 500 }}
    />
  );

  const locationChip = (location) => (
    <Chip
      icon={<LocationOnIcon />}
      label={location}
      color="default"
      size="small"
      sx={{ fontWeight: 500 }}
    />
  );

  return (
    <Box sx={{ p: { xs: 1, sm: 3 }, background: '#f5f7fa', minHeight: '100vh' }}>
      <Typography variant="h3" fontWeight={700} gutterBottom sx={{ letterSpacing: 1, color: '#1a237e', mb: 3, textAlign: 'center' }}>
        SkillMatcher Job Listings
      </Typography>
      <Fade in={true} timeout={700}>
        <Card elevation={4} sx={{ mb: 4, maxWidth: 1100, mx: 'auto', borderRadius: 3, p: 2 }}>
          <CardHeader
            avatar={<SearchIcon color="primary" />}
            title={<Typography variant="h6" fontWeight={600}>Search & Scrape New Jobs</Typography>}
            action={
              <Button onClick={() => setSearchOpen(!searchOpen)} size="small" color="primary">
                {searchOpen ? 'Hide' : 'Show'}
              </Button>
            }
            sx={{ pb: 0 }}
          />
          {searchOpen && (
            <CardContent sx={{ pt: 1 }}>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} sm={4} md={3}>
                  <TextField
                    fullWidth
                    label="Job Keyword"
                    value={keyword}
                    onChange={e => setKeyword(e.target.value)}
                    placeholder="e.g., Java"
                    variant="outlined"
                  />
                </Grid>
                <Grid item xs={12} sm={4} md={3}>
                  <TextField
                    fullWidth
                    label="Location"
                    value={location}
                    onChange={e => setLocation(e.target.value)}
                    placeholder="e.g., Stockholm"
                    variant="outlined"
                  />
                </Grid>
                <Grid item xs={6} sm={2} md={2}>
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
                <Grid item xs={6} sm={2} md={2}>
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
                <Grid item xs={12} sm={12} md={2}>
                  <Button
                    fullWidth
                    variant="contained"
                    onClick={handleSearch}
                    disabled={searchLoading || !keyword || !location}
                    sx={{ mt: { xs: 1, sm: 0 }, height: 48, fontWeight: 600, fontSize: 16 }}
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
            </CardContent>
          )}
        </Card>
      </Fade>
      <Card elevation={2} sx={{ mb: 4, maxWidth: 1100, mx: 'auto', borderRadius: 3, p: 2, background: '#fff' }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems="center" justifyContent="space-between">
          <TextField
            label="Search Title"
            value={searchTitle}
            onChange={e => setSearchTitle(e.target.value)}
            sx={{ width: 220 }}
            variant="outlined"
          />
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
          <TextField
            label="Min Years"
            type="number"
            value={minYears}
            onChange={e => setMinYears(e.target.value)}
            sx={{ width: 120 }}
            variant="outlined"
          />
          <TextField
            label="Max Years"
            type="number"
            value={maxYears}
            onChange={e => setMaxYears(e.target.value)}
            sx={{ width: 120 }}
            variant="outlined"
          />
        </Stack>
      </Card>
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}>
          <CircularProgress size={60} thickness={4} color="primary" />
        </Box>
      ) : filteredJobs.length === 0 ? (
        <Box sx={{ textAlign: 'center', mt: 8 }}>
          <img src="https://cdn-icons-png.flaticon.com/512/4076/4076549.png" alt="No jobs" width={120} style={{ opacity: 0.5 }} />
          <Typography variant="h5" color="textSecondary" sx={{ mt: 2 }}>
            No jobs found. Try adjusting your filters or search.
          </Typography>
        </Box>
      ) : (
        <Grid container spacing={3} justifyContent="center">
          {filteredJobs.map((job) => (
            <Grid item xs={12} sm={10} md={8} key={job.id}>
              <Card
                elevation={5}
                sx={{
                  borderRadius: 4,
                  transition: 'box-shadow 0.3s, transform 0.2s',
                  '&:hover': {
                    boxShadow: 10,
                    transform: 'translateY(-4px) scale(1.01)',
                  },
                  mb: 2,
                }}
              >
                <CardHeader
                  title={<Typography variant="h6" fontWeight={700}>{job.title}</Typography>}
                  subheader={
                    <Stack direction="row" spacing={1} alignItems="center">
                      {job.company && <Chip icon={<BusinessIcon />} label={job.company} size="small" sx={{ fontWeight: 500 }} />}
                      {job.location && locationChip(job.location)}
                      {job.source && sourceChip(job.source)}
                      {experienceChip(job.maxYearsRequired)}
                    </Stack>
                  }
                  sx={{ pb: 0, background: '#f0f4fa', borderTopLeftRadius: 16, borderTopRightRadius: 16 }}
                />
                <Divider />
                <CardContent sx={{ pt: 2, pb: 1 }}>
                  <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems="center" mb={1}>
                    {job.postedDate && (
                      <Tooltip title="Posted Date">
                        <Chip icon={<CalendarMonthIcon />} label={`Posted: ${job.postedDate?.split('T')[0]}`} size="small" />
                      </Tooltip>
                    )}
                    {job.deadline && (
                      <Tooltip title="Deadline">
                        <Chip icon={<CalendarMonthIcon />} label={`Deadline: ${job.deadline}`} size="small" color="warning" />
                      </Tooltip>
                    )}
                  </Stack>
                  <Typography variant="body2" sx={{ whiteSpace: 'pre-line', mb: 1, color: '#333', fontSize: 16 }}>
                    {job.description}
                  </Typography>
                </CardContent>
                <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
                  <Typography variant="body2" color="textSecondary">
                    Source: {job.source}
                  </Typography>
                  <Button
                    variant="contained"
                    color="primary"
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    sx={{ fontWeight: 600, borderRadius: 2, boxShadow: 1 }}
                  >
                    View Job
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
};

export default JobList; 