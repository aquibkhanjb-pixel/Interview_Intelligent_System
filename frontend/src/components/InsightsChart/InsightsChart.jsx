import React from 'react';
import { Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Box, Typography, Paper, Grid } from '@mui/material';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const InsightsChart = ({ insights, title = "Topic Analysis" }) => {
  if (!insights || !insights.insights) {
    return (
      <Paper sx={{ p: 2, textAlign: 'center' }}>
        <Typography variant="body1" color="textSecondary">
          No insights data available
        </Typography>
      </Paper>
    );
  }

  // Get top 10 topics for the chart
  const topicEntries = Object.entries(insights.insights).slice(0, 10);
  
  const frequencyData = {
    labels: topicEntries.map(([_, data]) => data.topic_name),
    datasets: [
      {
        label: 'Frequency (%)',
        data: topicEntries.map(([_, data]) => data.weighted_frequency),
        backgroundColor: topicEntries.map(([_, data]) => {
          switch(data.priority_level?.toUpperCase()) {
            case 'HIGH': return 'rgba(255, 99, 132, 0.8)';
            case 'MEDIUM': return 'rgba(54, 162, 235, 0.8)';
            default: return 'rgba(255, 206, 86, 0.8)';
          }
        }),
        borderColor: topicEntries.map(([_, data]) => {
          switch(data.priority_level?.toUpperCase()) {
            case 'HIGH': return 'rgba(255, 99, 132, 1)';
            case 'MEDIUM': return 'rgba(54, 162, 235, 1)';
            default: return 'rgba(255, 206, 86, 1)';
          }
        }),
        borderWidth: 1,
      },
    ],
  };

  // Category distribution
  const categories = {};
  Object.values(insights.insights).forEach(topic => {
    const category = topic.category || 'other';
    categories[category] = (categories[category] || 0) + 1;
  });
  
  const distributionData = {
    labels: Object.keys(categories),
    datasets: [
      {
        data: Object.values(categories),
        backgroundColor: [
          'rgba(255, 99, 132, 0.8)',
          'rgba(54, 162, 235, 0.8)',
          'rgba(255, 206, 86, 0.8)',
          'rgba(75, 192, 192, 0.8)',
          'rgba(153, 102, 255, 0.8)',
        ],
        borderWidth: 1,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
      },
    },
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right',
      },
    },
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2, height: 400 }}>
            <Typography variant="subtitle1" gutterBottom>
              Topic Frequency Analysis
            </Typography>
            <Box sx={{ height: 300 }}>
              <Bar data={frequencyData} options={chartOptions} />
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: 400 }}>
            <Typography variant="subtitle1" gutterBottom>
              Category Distribution
            </Typography>
            <Box sx={{ height: 300 }}>
              <Doughnut data={distributionData} options={doughnutOptions} />
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default InsightsChart;