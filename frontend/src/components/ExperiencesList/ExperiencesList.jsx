import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  List,
  ListItem,
  ListItemText,
  Button,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Tooltip,
  Avatar,
  Paper
} from '@mui/material';
import {
  ExpandMore,
  OpenInNew,
  AccessTime,
  Work,
  TrendingUp,
  CheckCircle,
  Cancel,
  Help,
  Reddit,
  Code,
  School
} from '@mui/icons-material';
import { interviewAPI } from '../../services/api.js';

const ExperiencesList = ({ company, onNotification }) => {
  const [experiences, setExperiences] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [selectedExperience, setSelectedExperience] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [totalCount, setTotalCount] = useState(0);

  // Pagination settings
  const INITIAL_LOAD = 5; // Show only 5 initially
  const LOAD_MORE_COUNT = 10; // Load 10 more each time

  useEffect(() => {
    if (company) {
      loadExperiences();
    }
  }, [company]);

  const loadExperiences = async (reset = true) => {
    if (reset) {
      setLoading(true);
      setExperiences([]);
      setHasMore(true);
    }

    try {
      const offset = reset ? 0 : experiences.length;
      const limit = reset ? INITIAL_LOAD : LOAD_MORE_COUNT;

      const response = await interviewAPI.getCompanyExperiences(company, {
        limit,
        offset
      });

      const newExperiences = response.data.experiences || [];
      const total = response.data.pagination?.total || newExperiences.length;

      if (reset) {
        setExperiences(newExperiences);
      } else {
        setExperiences(prev => [...prev, ...newExperiences]);
      }

      setTotalCount(total);
      setHasMore(newExperiences.length === limit && (offset + newExperiences.length) < total);

    } catch (error) {
      console.error('Error loading experiences:', error);
      onNotification(`Failed to load experiences for ${company}`, 'error');
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  const loadMoreExperiences = async () => {
    if (loadingMore || !hasMore) return;

    setLoadingMore(true);
    await loadExperiences(false);
  };

  const getPlatformIcon = (platform) => {
    switch (platform?.toLowerCase()) {
      case 'reddit':
        return <Reddit color="primary" />;
      case 'leetcode':
        return <Code color="primary" />;
      case 'geeksforgeeks':
        return <School color="primary" />;
      default:
        return <OpenInNew color="primary" />;
    }
  };

  const getPlatformColor = (platform) => {
    switch (platform?.toLowerCase()) {
      case 'reddit':
        return 'error';
      case 'leetcode':
        return 'warning';
      case 'geeksforgeeks':
        return 'success';
      default:
        return 'primary';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const openExperienceDialog = (experience) => {
    setSelectedExperience(experience);
    setDialogOpen(true);
  };

  const openOriginalSource = (url) => {
    if (url) {
      window.open(url, '_blank');
    }
  };

  const getOutcomeIcon = (success) => {
    if (success === true) return <CheckCircle color="success" />;
    if (success === false) return <Cancel color="error" />;
    return <Help color="disabled" />;
  };

  const getOutcomeText = (success) => {
    if (success === true) return 'Offer Received';
    if (success === false) return 'Rejected';
    return 'Unknown Outcome';
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" py={4}>
        <CircularProgress size={40} />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Loading interview experiences...
        </Typography>
      </Box>
    );
  }

  if (experiences.length === 0) {
    return (
      <Alert severity="info" sx={{ mt: 2 }}>
        No interview experiences found for {company}. Try running analysis to collect data.
      </Alert>
    );
  }

  return (
    <Box sx={{ width: '100%', mt: 3 }}>
      <Paper elevation={1} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          Interview Experiences for {company}
        </Typography>
        <Typography variant="body2" color="textSecondary">
          Showing {experiences.length} of {totalCount} experiences with reference links for verification
        </Typography>
      </Paper>

      <Grid container spacing={2}>
        {experiences.map((experience) => (
          <Grid item xs={12} key={experience.id}>
            <Card
              sx={{
                borderLeft: 4,
                borderColor: getPlatformColor(experience.source_platform) + '.main',
                '&:hover': {
                  boxShadow: 3,
                  transform: 'translateY(-2px)',
                  transition: 'all 0.2s ease-in-out'
                }
              }}
            >
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                  <Box flex={1}>
                    <Typography variant="h6" gutterBottom sx={{ fontWeight: 'medium' }}>
                      {experience.title}
                    </Typography>

                    <Box display="flex" alignItems="center" flexWrap="wrap" gap={1} mb={2}>
                      <Chip
                        icon={getPlatformIcon(experience.source_platform)}
                        label={experience.source_platform?.toUpperCase() || 'Unknown'}
                        size="small"
                        color={getPlatformColor(experience.source_platform)}
                        variant="outlined"
                      />

                      <Chip
                        icon={<Work />}
                        label={experience.role || 'Software Engineer'}
                        size="small"
                        variant="outlined"
                      />

                      <Chip
                        icon={<AccessTime />}
                        label={formatDate(experience.experience_date)}
                        size="small"
                        variant="outlined"
                      />

                      <Chip
                        icon={getOutcomeIcon(experience.success)}
                        label={getOutcomeText(experience.success)}
                        size="small"
                        color={experience.success === true ? 'success' : experience.success === false ? 'error' : 'default'}
                        variant="outlined"
                      />
                    </Box>
                  </Box>

                  <Box display="flex" gap={1}>
                    <Tooltip title="View Full Experience">
                      <IconButton
                        color="primary"
                        onClick={() => openExperienceDialog(experience)}
                      >
                        <ExpandMore />
                      </IconButton>
                    </Tooltip>

                    <Tooltip title="Open Original Source">
                      <IconButton
                        color="primary"
                        onClick={() => openOriginalSource(experience.source_url)}
                        disabled={!experience.source_url}
                      >
                        <OpenInNew />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Box>

                <Typography variant="body2" color="textSecondary" sx={{ lineHeight: 1.6 }}>
                  {experience.content_preview}
                </Typography>

                {experience.time_weight && (
                  <Box mt={2} display="flex" alignItems="center">
                    <TrendingUp fontSize="small" color="action" />
                    <Typography variant="caption" color="textSecondary" sx={{ ml: 1 }}>
                      Relevance Score: {(experience.time_weight * 100).toFixed(0)}%
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Load More Button */}
      {hasMore && (
        <Box display="flex" justifyContent="center" mt={4} mb={3}>
          <Button
            variant="outlined"
            size="large"
            onClick={loadMoreExperiences}
            disabled={loadingMore}
            startIcon={loadingMore ? <CircularProgress size={16} /> : null}
            sx={{
              px: 4,
              py: 1.5,
              borderRadius: 2,
              textTransform: 'none',
              '&:hover': {
                transform: 'translateY(-1px)',
                boxShadow: 2
              }
            }}
          >
            {loadingMore ? 'Loading more experiences...' : `Load More Experiences (${totalCount - experiences.length} remaining)`}
          </Button>
        </Box>
      )}

      {/* Show completion message */}
      {!hasMore && experiences.length > INITIAL_LOAD && (
        <Box textAlign="center" mt={3} mb={2}>
          <Typography variant="body2" color="textSecondary">
            ✨ All {totalCount} experiences loaded successfully
          </Typography>
        </Box>
      )}

      {/* Experience Detail Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: { maxHeight: '80vh' }
        }}
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">
              {selectedExperience?.title}
            </Typography>
            <Box display="flex" gap={1}>
              <Chip
                icon={getPlatformIcon(selectedExperience?.source_platform)}
                label={selectedExperience?.source_platform?.toUpperCase()}
                size="small"
                color={getPlatformColor(selectedExperience?.source_platform)}
              />
            </Box>
          </Box>
        </DialogTitle>

        <DialogContent dividers>
          {selectedExperience && (
            <Box>
              <Box mb={3}>
                <Grid container spacing={2}>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="textSecondary">Role</Typography>
                    <Typography variant="body2">{selectedExperience.role}</Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="textSecondary">Date</Typography>
                    <Typography variant="body2">{formatDate(selectedExperience.experience_date)}</Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="textSecondary">Outcome</Typography>
                    <Box display="flex" alignItems="center">
                      {getOutcomeIcon(selectedExperience.success)}
                      <Typography variant="body2" sx={{ ml: 1 }}>
                        {getOutcomeText(selectedExperience.success)}
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="textSecondary">Platform</Typography>
                    <Typography variant="body2">{selectedExperience.source_platform}</Typography>
                  </Grid>
                </Grid>
              </Box>

              <Typography variant="body1" sx={{
                lineHeight: 1.7,
                whiteSpace: 'pre-wrap',
                fontFamily: 'system-ui, -apple-system, sans-serif'
              }}>
                {selectedExperience.content_preview?.replace(/\\n/g, '\n')}
              </Typography>
            </Box>
          )}
        </DialogContent>

        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>
            Close
          </Button>
          <Button
            variant="contained"
            startIcon={<OpenInNew />}
            onClick={() => openOriginalSource(selectedExperience?.source_url)}
            disabled={!selectedExperience?.source_url}
          >
            View Original Source
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ExperiencesList;