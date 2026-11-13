import axios from 'axios';

const API_BASE_URL =
  (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL) ||
  'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Request Interceptor: Attach JWT Bearer Token if present
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('medicall_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Handle Token Expiration and Errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Token is invalid or expired
      localStorage.removeItem('medicall_token');
      localStorage.removeItem('medicall_user');
      // If not already on login or landing page, optionally redirect
      const basename =
        (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.BASE_URL) || '/';
      const cleanBase = basename.endsWith('/') ? basename.slice(0, -1) : basename;
      if (
        !window.location.pathname.includes('/login') &&
        !window.location.pathname.includes('/register') &&
        window.location.pathname !== '/' &&
        window.location.pathname !== basename
      ) {
        window.location.href = `${cleanBase}/login?expired=true`;
      }
    }
    return Promise.reject(error);
  }
);

export default api;

