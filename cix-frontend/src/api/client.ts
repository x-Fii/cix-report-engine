import axios from 'axios';

// Detect the current domain/IP used to load the UI and swap the port to our API
const currentHost = window.location.hostname;
const API_BASE_URL = import.meta.env.VITE_API_URL || `http://${currentHost}:8000/api/v1`;

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default apiClient;
