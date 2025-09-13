import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box, Alert, Snackbar } from '@mui/material';
import Dashboard from './components/Dashboard/Dashboard';
import CompanyComparison from './components/CompanyComparison/CompanyComparison';
import { interviewAPI } from './services/api';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 500,
    },
  },
});

function App() {
  const [apiHealthy, setApiHealthy] = useState(null);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'info' });

  useEffect(() => {
    checkAPIHealth();
  }, []);

  const checkAPIHealth = async () => {
    try {
      const response = await interviewAPI.healthCheck();
      setApiHealthy(response.data.status === 'healthy');
      if (response.data.status !== 'healthy') {
        showNotification('Backend API is not fully healthy', 'warning');
      }
    } catch (error) {
      setApiHealthy(false);
      showNotification('Unable to connect to backend API', 'error');
    }
  };

  const showNotification = (message, severity = 'info') => {
    setNotification({ open: true, message, severity });
  };

  const handleCloseNotification = () => {
    setNotification({ ...notification, open: false });
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ minHeight: '100vh', backgroundColor: 'background.default' }}>
          {apiHealthy === false && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Backend API is not accessible. Please ensure your Flask server is running on http://localhost:5000
            </Alert>
          )}
          
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route 
              path="/dashboard" 
              element={<Dashboard onNotification={showNotification} />} 
            />
            <Route 
              path="/compare" 
              element={<CompanyComparison onNotification={showNotification} />} 
            />
          </Routes>

          <Snackbar
            open={notification.open}
            autoHideDuration={6000}
            onClose={handleCloseNotification}
          >
            <Alert 
              onClose={handleCloseNotification} 
              severity={notification.severity}
              sx={{ width: '100%' }}
            >
              {notification.message}
            </Alert>
          </Snackbar>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;
