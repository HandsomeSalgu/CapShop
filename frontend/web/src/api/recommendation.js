import axios from 'axios';

// API base URL configuration
const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptor to inject JWT token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const recommendationApi = {
  /**
   * Get my personalized recommendation products
   * @param {number} [limit] - Maximum item count to retrieve
   * @returns {Promise<Array>} Array of recommendation product objects
   */
  async getMyRecommendations(limit = 6) {
    try {
      const response = await apiClient.get('/recommendations/me', {
        params: { limit }
      });
      
      if (response.data && response.data.data) {
        return response.data.data;
      }
      return [];
    } catch (error) {
      console.error('Failed to get recommendations:', error);
      throw error;
    }
  },

  /**
   * Generate rule-based recommendations explicitly
   * @param {number} [limit] - Maximum item count to retrieve
   * @returns {Promise<Array>} Array of recommendation product objects
   */
  async generateRuleBasedRecommendations(limit = 6) {
    try {
      const response = await apiClient.post('/recommendations/me/rule-based', null, {
        params: { limit }
      });
      
      if (response.data && response.data.data) {
        return response.data.data;
      }
      return [];
    } catch (error) {
      console.error('Failed to generate rule-based recommendations:', error);
      throw error;
    }
  },

  /**
   * Get my recommendation history with pagination
   * @param {number} [page] - Page number
   * @param {number} [size] - Page size
   * @returns {Promise<Object>} PageResponse containing recommendations and pagination info
   */
  async getMyRecommendationHistory(page = 1, size = 12) {
    try {
      const response = await apiClient.get('/recommendations/me/history', {
        params: { page, size }
      });
      
      if (response.data && response.data.data) {
        return response.data.data;
      }
      return { content: [], totalElements: 0, totalPages: 0 };
    } catch (error) {
      console.error('Failed to get recommendation history:', error);
      throw error;
    }
  }
};
