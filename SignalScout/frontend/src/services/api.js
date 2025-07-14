import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method.toUpperCase()} request to ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Trend Analysis APIs
export const fetchRedditTrends = async (subreddit, limit = 25) => {
  const response = await api.post('/trends/reddit', { subreddit, limit });
  return response.data;
};

export const fetchYouTubeTrends = async () => {
  const response = await api.post('/trends/youtube');
  return response.data;
};

export const getTrends = async (limit = 50, platform = null) => {
  const params = { limit };
  if (platform) params.platform = platform;
  
  const response = await api.get('/trends', { params });
  return response.data;
};

// Content Generation APIs
export const generateContent = async (trendId, contentType, brandVoice, targetAudience) => {
  const response = await api.post('/content/generate', {
    trend_id: trendId,
    content_type: contentType,
    brand_voice: brandVoice,
    target_audience: targetAudience
  });
  return response.data;
};

export const getContentVault = async (limit = 50, topic = null) => {
  const params = { limit };
  if (topic) params.topic = topic;
  
  const response = await api.get('/content/vault', { params });
  return response.data;
};

// Brand Voice APIs
export const trainBrandVoice = async (sampleContent, brandName, tone) => {
  const response = await api.post('/brand-voice/train', {
    sample_content: sampleContent,
    brand_name: brandName,
    tone: tone
  });
  return response.data;
};

// Analytics APIs
export const getViralityAnalytics = async (days = 7) => {
  const response = await api.get('/analytics/virality', { params: { days } });
  return response.data;
};

// Health Check
export const healthCheck = async () => {
  const response = await api.get('/');
  return response.data;
};

export default api;