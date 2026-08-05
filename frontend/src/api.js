import axios from 'axios';

// In production (Vercel), set REACT_APP_API_URL to your Railway backend URL
// e.g. https://your-app.up.railway.app
// Locally, falls back to http://localhost:8000
const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const API = axios.create({ baseURL: BASE_URL });

API.interceptors.request.use(cfg => {
  const token = localStorage.getItem('token');
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

export default API;