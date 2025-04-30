import React, { useState } from 'react';
import { 
    Box, 
    TextField, 
    Button, 
    Typography, 
    Card, 
    CardContent,
    Grid,
    CircularProgress
} from '@mui/material';
import axios from 'axios';

const JobSearch = () => {
    const [keyword, setKeyword] = useState('');
    const [location, setLocation] = useState('');
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
                    location
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
                    <Grid item xs={12} sm={5}>
                        <TextField
                            fullWidth
                            label="Job Keyword"
                            value={keyword}
                            onChange={(e) => setKeyword(e.target.value)}
                            placeholder="e.g., Software Engineer"
                        />
                    </Grid>
                    <Grid item xs={12} sm={5}>
                        <TextField
                            fullWidth
                            label="Location"
                            value={location}
                            onChange={(e) => setLocation(e.target.value)}
                            placeholder="e.g., New York"
                        />
                    </Grid>
                    <Grid item xs={12} sm={2}>
                        <Button
                            fullWidth
                            variant="contained"
                            onClick={handleSearch}
                            disabled={loading || !keyword || !location}
                            sx={{ height: '100%' }}
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
                            </CardContent>
                        </Card>
                    </Grid>
                ))}
            </Grid>
        </Box>
    );
};

export default JobSearch; 