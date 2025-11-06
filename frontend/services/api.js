import axios from 'axios';

// Real backend API
const BASE_URL = 'http://192.168.1.2:8000';



const api = axios.create({
  baseURL: BASE_URL,
  timeout: 15000, // Increased timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

console.log('🌐 API Base URL:', BASE_URL);

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Network connectivity test
const testConnection = async () => {
  const testUrls = [
    BASE_URL,                    // Current configured URL (tunnel)
    'http://10.0.2.2:8000',     // Android emulator
    'http://localhost:8000',     // iOS simulator / web
    'http://192.168.1.2:8000',  // Local IP
  ];
  
  for (const url of testUrls) {
    try {
      console.log(`🔍 Testing connection to: ${url}`);
      const response = await axios.get(`${url}/health`, { timeout: 5000 });
      if (response.status === 200) {
        console.log(`✅ Connected successfully to: ${url}`);
        return url;
      }
    } catch (error) {
      console.log(`❌ Failed to connect to: ${url}`);
    }
  }
  console.log('🚫 No backend server found');
  return null;
};

// API endpoints
export const disasterAPI = {
  // Test network connectivity
  testConnection,
  // Get all disaster news
  getAllNews: (limit = 20, minConfidence = 0.5) => 
    api.get(`/reddit/disaster-news?limit=${limit}&min_confidence=${minConfidence}`),

  // Get verified news only
  getVerifiedNews: (limit = 50, minConfidence = 0.6, category = 'all') => 
    api.get(`/reddit/verified?limit=${limit}&min_confidence=${minConfidence}&category=${category}`),

  // Get rumors/unverified news
  getRumors: (limit = 50, minConfidence = 0.5, category = 'all') => 
    api.get(`/reddit/rumors?limit=${limit}&min_confidence=${minConfidence}&category=${category}`),

  // Get available categories
  getCategories: () => 
    api.get('/categories'),

  // Force manual update
  forceUpdate: () => 
    api.post('/force-update'),

  // Get dashboard statistics
  getDashboardStats: () => 
    api.get('/stats/dashboard'),

  // Classify single text
  classifyText: (text) => 
    api.post('/predict', { text }),

  // Refresh data manually
  refreshData: () => 
    api.post('/refresh-data'),

  // Health check
  healthCheck: () => 
    api.get('/health'),

  // Simple Authentication endpoints
  signup: (userData) => 
    api.post('/auth/signup', userData),

  login: (credentials) => 
    api.post('/auth/login', credentials),

  getCurrentUser: (token) => 
    api.get(`/auth/me?token=${token}`),

  logout: () => 
    api.post('/auth/logout'),
};

export default api;