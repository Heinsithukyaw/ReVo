// src/services/api.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:12001/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor for logging or adding auth tokens
apiClient.interceptors.request.use(
  (config) => {
    // You can add authentication tokens here if needed
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add a response interceptor for handling errors globally
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle common errors like 401, 403, 500
    if (error.response) {
      switch (error.response.status) {
        case 401:
          // Handle unauthorized access, e.g., redirect to login
          console.error('Unauthorized access - 401');
          break;
        case 403:
          // Handle forbidden access
          console.error('Forbidden access - 403');
          break;
        case 500:
          // Handle server errors
          console.error('Server error - 500');
          break;
        default:
          console.error(`Unhandled error: ${error.response.status}`);
      }
    } else if (error.request) {
      // The request was made but no response was received
      console.error('Network error:', error.request);
    } else {
      // Something happened in setting up the request that triggered an Error
      console.error('Error', error.message);
    }
    return Promise.reject(error);
  }
);

export default apiClient;
