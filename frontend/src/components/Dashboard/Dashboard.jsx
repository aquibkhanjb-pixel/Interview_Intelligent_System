import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  CircularProgress,
  Alert,
  Grid,
  Card,
  CardContent,
  CardActions,
  Chip,
  AppBar,
  Toolbar,
  Paper
} from '@mui/material';
import { Refresh, Analytics, TrendingUp, Compare } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import CompanySelector from '../CompanySelector/CompanySelector.jsx';
import InsightsChart from '../InsightsChart/InsightsChart.jsx';
import StudyPlan from '../StudyPlan/StudyPlan.jsx';
import ExperiencesList from '../ExperiencesList/ExperiencesList.jsx';
import { interviewAPI } from '../../services/api.js';

const Dashboard = ({ onNotification }) => {
  const [selectedCompanies, setSelectedCompanies] = useState(['Amazon']);
  const [insights, setInsights] = useState({});
  const [loading, setLoading] = useState(false);
  const [analysisLoading, setAnalysisLoading] = useState({});
  const navigate = useNavigate();

  useEffect(() => {
    if (selectedCompanies.length > 0) {
      loadInsights();
    }
  }, [selectedCompanies]);

  const loadInsights = async () => {
    setLoading(true);
    const newInsights = {};

    try {
      for (const company of selectedCompanies) {
        try {
          const response = await interviewAPI.getCompanyInsights(company);
          newInsights[company] = response.data;
          console.log(`Loaded insights for ${company}:`, response.data);
        } catch (error) {
          console.error(`Error loading insights for ${company}:`, error);
          onNotification(`Failed to load insights for ${company}. Try running analysis first.`, 'warning');
        }
      }
      
      setInsights(newInsights);
    } catch (error) {
      console.error('Error loading insights:', error);
      onNotification('Failed to load insights', 'error');
    } finally {
      setLoading(false);
    }
  };

  const triggerAnalysis = async (company) => {
    setAnalysisLoading({ ...analysisLoading, [company]: true });
    
    try {
      onNotification(`Starting analysis for ${company}...`, 'info');
      
      const response = await interviewAPI.triggerAnalysis(company, {
        max_experiences: 20,
        force_refresh: false
      });
      
      if (response.data.status === 'success') {
        onNotification(`Analysis completed for ${company}! Found ${response.data.data_collection?.total_experiences || 0} experiences.`, 'success');
        // Wait a moment then reload insights
        setTimeout(() => loadInsights(), 1000);
      } else {
        onNotification(`Analysis failed for ${company}: ${response.data.error || 'Unknown error'}`, 'error');
      }
    } catch (error) {
      console.error(`Analysis error for ${company}:`, error);
      onNotification(`Analysis failed for ${company}: ${error.message}`, 'error');
    } finally {
      setAnalysisLoading({ ...analysisLoading, [company]: false });
    }
  };

  const getInsightsSummary = (companyInsights) => {
    if (!companyInsights.insights) return null;
    
    const topicEntries = Object.entries(companyInsights.insights);
    const topTopics = topicEntries.slice(0, 3).map(([key, data]) => data.topic_name);
    const highPriority = topicEntries.filter(([_, data]) => data.priority_level?.toUpperCase() === 'HIGH').length;
    const sampleSize = companyInsights.analysis_metadata?.sample_size || 0;
    
    return { topTopics, highPriority, sampleSize };
  };

  return (
    <Box sx={{ flexGrow: 1, minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Navigation Bar */}
      <AppBar position="static" elevation={1} sx={{ bgcolor: 'primary.main' }}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Interview Intelligence System
          </Typography>
          <Button 
            color="inherit" 
            onClick={() => navigate('/compare')}
            startIcon={<Compare />}
          >
            Compare Companies
          </Button>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Container maxWidth="xl" sx={{ py: 4 }}>
        {/* Header Section */}
        <Paper elevation={0} sx={{ p: 3, mb: 4, bgcolor: 'transparent' }}>
          <Typography variant="h4" component="h1" gutterBottom align="center">
            Interview Intelligence Dashboard
          </Typography>
          <Typography variant="subtitle1" color="textSecondary" align="center">
            Data-driven interview preparation insights powered by AI analysis
          </Typography>
        </Paper>

        {/* Company Selection */}
        <Card sx={{ mb: 4 }} elevation={2}>
          <CardContent sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Select Companies to Analyze
            </Typography>
            <CompanySelector
              selectedCompanies={selectedCompanies}
              onSelectionChange={setSelectedCompanies}
              maxSelection={3}
            />
          </CardContent>
        </Card>

        {loading && (
          <Box display="flex" justifyContent="center" alignItems="center" my={6}>
            <CircularProgress size={40} />
            <Typography variant="h6" sx={{ ml: 2 }}>
              Loading insights...
            </Typography>
          </Box>
        )}

        {/* Company Insights Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {selectedCompanies.map((company) => {
            const companyInsights = insights[company];
            const summary = companyInsights ? getInsightsSummary(companyInsights) : null;
            
            return (
              <Grid item xs={12} sm={6} md={4} key={company}>
                <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }} elevation={2}>
                  <CardContent sx={{ flexGrow: 1, p: 3 }}>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                      <Typography variant="h6">{company}</Typography>
                      {summary && (
                        <Chip 
                          label={`${summary.sampleSize} experiences`} 
                          size="small" 
                          color="primary"
                        />
                      )}
                    </Box>
                    
                    {summary ? (
                      <Box>
                        <Typography variant="body2" color="textSecondary" gutterBottom>
                          High Priority Topics: {summary.highPriority}
                        </Typography>
                        
                        <Typography variant="body2" gutterBottom sx={{ mt: 2 }}>
                          Top Focus Areas:
                        </Typography>
                        <Box>
                          {summary.topTopics.map((topic, index) => (
                            <Chip 
                              key={index}
                              label={topic}
                              size="small"
                              variant="outlined"
                              sx={{ mr: 1, mb: 1 }}
                            />
                          ))}
                        </Box>
                      </Box>
                    ) : (
                      <Alert severity="info" sx={{ mt: 2 }}>
                        No insights available. Run analysis to generate insights.
                      </Alert>
                    )}
                  </CardContent>
                  
                  <CardActions sx={{ p: 2, pt: 0 }}>
                    <Button
                      size="small"
                      fullWidth
                      variant="contained"
                      startIcon={analysisLoading[company] ? <CircularProgress size={16} /> : <Analytics />}
                      onClick={() => triggerAnalysis(company)}
                      disabled={analysisLoading[company]}
                    >
                      {analysisLoading[company] ? 'Analyzing...' : 'Run Analysis'}
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            );
          })}
        </Grid>

        {/* Detailed Insights */}
        {Object.keys(insights).length > 0 && (
          <Grid container spacing={4}>
            {Object.entries(insights).map(([company, companyInsights]) => (
              <Grid item xs={12} key={company}>
                <Card elevation={2}>
                  <CardContent sx={{ p: 4 }}>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                      <Typography variant="h5">{company} Detailed Analysis</Typography>
                      <Button
                        variant="outlined"
                        startIcon={<Refresh />}
                        onClick={loadInsights}
                        disabled={loading}
                      >
                        Refresh Data
                      </Button>
                    </Box>
                    
                    <Box mb={4}>
                      <InsightsChart 
                        insights={companyInsights}
                        title={`${company} Topic Analysis`}
                      />
                    </Box>
                    
                    <StudyPlan insights={companyInsights} company={company} />

                    {/* Interview Experiences Section */}
                    <Box mt={4}>
                      <ExperiencesList company={company} onNotification={onNotification} />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Container>
    </Box>
  );
};

export default Dashboard;