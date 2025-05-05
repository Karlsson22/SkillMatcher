import React, { useState } from 'react';
import { 
    Box, 
    TextField, 
    Button, 
    Typography, 
    Card, 
    CardContent,
    Grid,
    CircularProgress,
    FormControl,
    InputLabel,
    Select,
    MenuItem
} from '@mui/material';
import axios from 'axios';

const JobSearch = () => {
    const [keyword, setKeyword] = useState('');
    const [location, setLocation] = useState('');
    const [maxJobs, setMaxJobs] = useState(10);
    const [daysBack, setDaysBack] = useState(30);
    const [jobs, setJobs] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSearch = async () => {
        setLoading(true);
        setError('');
        try {
            const response = await axios.get(`http://localhost:8080/api/jobs/scrape`, {
                params: {
                    keyword,
                    location,
                    maxJobs,
                    daysBack
                }
            });
            setJobs(JSON.parse(response.data));
        } catch (err) {
            setError('Failed to fetch jobs. Please try again.');
            console.error('Error:', err);
        }
        setLoading(false);
    };

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom>
                Job Search
            </Typography>
            
            <Box sx={{ mb: 4 }}>
                <Grid container spacing={2}>
                    <Grid item xs={12} sm={4}>
                        <TextField
                            fullWidth
                            label="Job Keyword"
                            value={keyword}
                            onChange={(e) => setKeyword(e.target.value)}
                            placeholder="e.g., Software Engineer"
                        />
                    </Grid>
                    <Grid item xs={12} sm={4}>
                        <TextField
                            fullWidth
                            label="Location"
                            value={location}
                            onChange={(e) => setLocation(e.target.value)}
                            placeholder="e.g., New York"
                        />
                    </Grid>
                    <Grid item xs={12} sm={2}>
                        <FormControl fullWidth>
                            <InputLabel>Max Jobs</InputLabel>
                            <Select
                                value={maxJobs}
                                label="Max Jobs"
                                onChange={(e) => setMaxJobs(e.target.value)}
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
                            <InputLabel>Days Back</InputLabel>
                            <Select
                                value={daysBack}
                                label="Days Back"
                                onChange={(e) => setDaysBack(e.target.value)}
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
                            disabled={loading || !keyword || !location}
                            sx={{ mt: 2 }}
                        >
                            {loading ? <CircularProgress size={24} /> : 'Search'}
                        </Button>
                    </Grid>
                </Grid>
            </Box>

            {error && (
                <Typography color="error" sx={{ mb: 2 }}>
                    {error}
                </Typography>
            )}

            <Grid container spacing={2}>
                {jobs.map((job, index) => (
                    <Grid item xs={12} key={index}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    {job.title}
                                </Typography>
                                <Typography color="textSecondary" gutterBottom>
                                    {job.company}
                                </Typography>
                                <Typography variant="body2">
                                    {job.location}
                                </Typography>
                                {job.upload_date && (
                                    <Typography variant="body2" color="textSecondary">
                                        Posted: {job.upload_date}
                                    </Typography>
                                )}
                            </CardContent>
                        </Card>
                    </Grid>
                ))}
            </Grid>
        </Box>
    );
};

export default JobSearch; 