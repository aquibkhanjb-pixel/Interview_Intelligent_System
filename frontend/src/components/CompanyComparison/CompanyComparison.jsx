import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  Card,
  CardContent,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert,
  CircularProgress,
  AppBar,
  Toolbar,
  useTheme,
  useMediaQuery
} from '@mui/material';
import { Compare, Download, ArrowBack } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import CompanySelector from '../CompanySelector/CompanySelector.jsx';
import { interviewAPI } from '../../services/api.js';

const CompanyComparison = ({ onNotification }) => {
  const [selectedCompanies, setSelectedCompanies] = useState([]);
  const [comparisonData, setComparisonData] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const runComparison = async () => {
    if (selectedCompanies.length < 2) {
      onNotification('Please select at least 2 companies to compare', 'warning');
      return;
    }

    setLoading(true);
    try {
      const response = await interviewAPI.compareCompanies(selectedCompanies);
      setComparisonData(response.data);
      onNotification(`Comparison completed for ${selectedCompanies.length} companies`, 'success');
    } catch (error) {
      console.error('Comparison error:', error);
      onNotification('Failed to run comparison. Please ensure companies have been analyzed.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const exportComparison = () => {
    if (!comparisonData) {
      onNotification('No comparison data to export', 'warning');
      return;
    }

    const exportData = {
      exportDate: new Date().toISOString(),
      companies: selectedCompanies,
      comparisonResults: comparisonData,
      summary: {
        totalCompanies: selectedCompanies.length,
        commonTopics: comparisonData.comparison_insights?.common_topics?.length || 0
      }
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `Company_Comparison_${selectedCompanies.join('_vs_')}_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
    
    onNotification('Comparison data exported successfully', 'success');
  };

  const renderMobileComparison = () => {
    if (!comparisonData || !comparisonData.comparison_data) return null;

    const { comparison_data } = comparisonData;
    const companies = Object.keys(comparison_data);

    return (
      <Box>
        {companies.map((company) => (
          <Card key={company} sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom color="primary">
                {company}
              </Typography>
              
              {comparison_data[company]?.insights && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Top Topics:
                  </Typography>
                  <Box display="flex" flexWrap="wrap" gap={1}>
                    {Object.entries(comparison_data[company].insights)
                      .slice(0, 5)
                      .map(([topic, data]) => (
                        <Chip
                          key={topic}
                          label={`${data.topic_name}: ${data.weighted_frequency}%`}
                          size="small"
                          color={
                            data.priority_level?.toUpperCase() === 'HIGH' ? 'error' :
                            data.priority_level?.toUpperCase() === 'MEDIUM' ? 'warning' : 'success'
                          }
                        />
                      ))}
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>
        ))}
      </Box>
    );
  };

  const renderDesktopComparison = () => {
    if (!comparisonData || !comparisonData.comparison_data) return null;

    const { comparison_data } = comparisonData;
    const companies = Object.keys(comparison_data);
    
    // Get all unique topics
    const allTopics = new Set();
    companies.forEach(company => {
      const companyData = comparison_data[company];
      if (companyData && companyData.insights) {
        Object.keys(companyData.insights).forEach(topic => allTopics.add(topic));
      }
    });

    if (allTopics.size === 0) {
      return (
        <Alert severity="info">
          No insights available for comparison. Please ensure selected companies have been analyzed.
        </Alert>
      );
    }

    return (
      <TableContainer component={Paper} sx={{ maxHeight: '70vh' }}>
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell sx={{ minWidth: 200, fontWeight: 'bold', bgcolor: 'primary.main', color: 'white' }}>
                Topic
              </TableCell>
              {companies.map(company => (
                <TableCell 
                  key={company} 
                  align="center" 
                  sx={{ minWidth: 150, fontWeight: 'bold', bgcolor: 'primary.main', color: 'white' }}
                >
                  {company}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {Array.from(allTopics).slice(0, 20).map(topic => {
              let topicDisplayName = topic;
              for (const company of companies) {
                const companyData = comparison_data[company];
                if (companyData?.insights?.[topic]) {
                  topicDisplayName = companyData.insights[topic].topic_name || topic;
                  break;
                }
              }

              return (
                <TableRow key={topic} hover>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {topicDisplayName}
                    </Typography>
                  </TableCell>
                  {companies.map(company => {
                    const companyData = comparison_data[company];
                    const topicData = companyData?.insights?.[topic];
                    
                    return (
                      <TableCell key={`${company}-${topic}`} align="center">
                        {topicData ? (
                          <Box>
                            <Typography variant="body2" fontWeight="bold">
                              {topicData.weighted_frequency}%
                            </Typography>
                            <Chip
                              label={topicData.priority_level || 'N/A'}
                              size="small"
                              color={
                                topicData.priority_level?.toUpperCase() === 'HIGH' ? 'error' :
                                topicData.priority_level?.toUpperCase() === 'MEDIUM' ? 'warning' : 'success'
                              }
                              sx={{ mt: 0.5 }}
                            />
                          </Box>
                        ) : (
                          <Typography variant="body2" color="textSecondary">
                            N/A
                          </Typography>
                        )}
                      </TableCell>
                    );
                  })}
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  return (
    <Box sx={{ flexGrow: 1, minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Navigation Bar */}
      <AppBar position="static" elevation={1}>
        <Toolbar>
          <Button
            color="inherit"
            startIcon={<ArrowBack />}
            onClick={() => navigate('/')}
            sx={{ mr: 2 }}
          >
            {isMobile ? '' : 'Back to Dashboard'}
          </Button>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Company Comparison
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ py: 4 }}>
        {/* Header */}
        <Paper elevation={0} sx={{ p: 3, mb: 4, bgcolor: 'transparent' }}>
          <Typography variant="h4" gutterBottom align="center">
            Company Comparison Tool
          </Typography>
          <Typography variant="subtitle1" color="textSecondary" align="center">
            Compare interview patterns and requirements across companies
          </Typography>
        </Paper>

        {/* Company Selection */}
        <Card sx={{ mb: 4 }} elevation={2}>
          <CardContent sx={{ p: 3 }}>
            <CompanySelector
              selectedCompanies={selectedCompanies}
              onSelectionChange={setSelectedCompanies}
              maxSelection={4}
            />
            
            <Box mt={3} display="flex" gap={2} flexWrap="wrap">
              <Button
                variant="contained"
                size="large"
                startIcon={loading ? <CircularProgress size={20} /> : <Compare />}
                onClick={runComparison}
                disabled={loading || selectedCompanies.length < 2}
                sx={{ minWidth: 200 }}
              >
                {loading ? 'Comparing...' : `Compare ${selectedCompanies.length} Companies`}
              </Button>
              
              {comparisonData && (
                <Button
                  variant="outlined"
                  size="large"
                  startIcon={<Download />}
                  onClick={exportComparison}
                >
                  Export Results
                </Button>
              )}
            </Box>
          </CardContent>
        </Card>

        {/* Loading State */}
        {loading && (
          <Box display="flex" justifyContent="center" alignItems="center" py={8}>
            <CircularProgress size={60} />
            <Typography variant="h6" sx={{ ml: 2 }}>
              Analyzing companies for comparison...
            </Typography>
          </Box>
        )}

        {/* Comparison Results */}
        {comparisonData && !loading && (
          <Card elevation={2}>
            <CardContent sx={{ p: 4 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={3} flexWrap="wrap" gap={2}>
                <Typography variant="h5">
                  Comparison Results
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  {selectedCompanies.length} companies compared
                </Typography>
              </Box>

              {/* Responsive comparison display */}
              {isMobile ? renderMobileComparison() : renderDesktopComparison()}

              {/* Common Topics Section */}
              {comparisonData.comparison_insights?.common_topics && comparisonData.comparison_insights.common_topics.length > 0 && (
                <Box mt={4}>
                  <Typography variant="h6" gutterBottom>
                    Common Focus Areas Across All Companies
                  </Typography>
                  <Grid container spacing={1}>
                    {comparisonData.comparison_insights.common_topics.slice(0, 12).map((commonTopic, index) => (
                      <Grid item xs={12} sm={6} md={4} key={index}>
                        <Chip
                          label={`${commonTopic.topic} (${commonTopic.average_frequency?.toFixed(1) || 0}% avg)`}
                          variant="outlined"
                          color="primary"
                          sx={{ width: '100%', justifyContent: 'flex-start' }}
                        />
                      </Grid>
                    ))}
                  </Grid>
                </Box>
              )}

              {/* Summary Statistics */}
              {comparisonData && (
                <Box mt={4} p={2} bgcolor="grey.50" borderRadius={2}>
                  <Typography variant="h6" gutterBottom>
                    Comparison Summary
                  </Typography>
                  <Grid container spacing={3}>
                    <Grid item xs={6} md={3}>
                      <Typography variant="h4" color="primary">{selectedCompanies.length}</Typography>
                      <Typography variant="caption">Companies</Typography>
                    </Grid>
                    <Grid item xs={6} md={3}>
                      <Typography variant="h4" color="success.main">
                        {comparisonData.comparison_insights?.common_topics?.length || 0}
                      </Typography>
                      <Typography variant="caption">Common Topics</Typography>
                    </Grid>
                    <Grid item xs={6} md={3}>
                      <Typography variant="h4" color="info.main">
                        {Object.keys(comparisonData.comparison_data || {}).length}
                      </Typography>
                      <Typography variant="caption">Analyzed</Typography>
                    </Grid>
                    <Grid item xs={6} md={3}>
                      <Typography variant="h4" color="warning.main">100%</Typography>
                      <Typography variant="caption">Coverage</Typography>
                    </Grid>
                  </Grid>
                </Box>
              )}
            </CardContent>
          </Card>
        )}
      </Container>
    </Box>
  );
};

export default CompanyComparison;