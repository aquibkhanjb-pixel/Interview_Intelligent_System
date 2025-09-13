import React, { useState, useEffect } from 'react';
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Box,
  CircularProgress,
  Alert,
  Typography
} from '@mui/material';
import { interviewAPI } from '../../services/api.js';

const CompanySelector = ({ selectedCompanies, onSelectionChange, maxSelection = 5 }) => {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    try {
      setLoading(true);
      const response = await interviewAPI.getCompanies();
      console.log('Raw companies data:', response.data);
      
      // Filter and clean company data
      const activeCompanies = response.data.companies.filter(company => {
        // Skip companies named "Unknown" or with 0 experiences
        return company.experience_count > 0 && 
               company.name !== 'Unknown' && 
               company.name.trim() !== '';
      });
      
      console.log('Filtered companies:', activeCompanies);
      setCompanies(activeCompanies);
      
      // If no valid companies, show available ones anyway for debugging
      if (activeCompanies.length === 0) {
        setCompanies(response.data.companies);
        setError('No companies with valid experiences found. Showing all for debugging.');
      }
      
    } catch (error) {
      setError('Failed to load companies');
      console.error('Error fetching companies:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCompanyToggle = (companyName) => {
    const isSelected = selectedCompanies.includes(companyName);
    
    if (isSelected) {
      onSelectionChange(selectedCompanies.filter(name => name !== companyName));
    } else if (selectedCompanies.length < maxSelection) {
      onSelectionChange([...selectedCompanies, companyName]);
    }
  };

  const handleRemoveCompany = (companyName) => {
    onSelectionChange(selectedCompanies.filter(name => name !== companyName));
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={2}>
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading companies...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="warning">
        {error}
        <br />
        <small>Available companies: {companies.map(c => c.name).join(', ')}</small>
      </Alert>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      <FormControl fullWidth margin="normal">
        <InputLabel>Select Companies</InputLabel>
        <Select
          multiple
          value={selectedCompanies}
          label="Select Companies"
          renderValue={() => ''}
          sx={{ minWidth: 300 }}
        >
          {companies.map((company) => (
            <MenuItem 
              key={company.name}
              value={company.name}
              onClick={() => handleCompanyToggle(company.name)}
              disabled={selectedCompanies.length >= maxSelection && !selectedCompanies.includes(company.name)}
            >
              <Box display="flex" justifyContent="space-between" width="100%">
                <span>{company.display_name || company.name}</span>
                <small>({company.experience_count} experiences)</small>
              </Box>
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {selectedCompanies.length > 0 && (
        <Box mt={2}>
          <Box display="flex" flexWrap="wrap" gap={1}>
            {selectedCompanies.map((company) => (
              <Chip
                key={company}
                label={company}
                onDelete={() => handleRemoveCompany(company)}
                color="primary"
                variant="outlined"
              />
            ))}
          </Box>
          <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
            {selectedCompanies.length}/{maxSelection} companies selected
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default CompanySelector;
