import axios from 'axios';

// API base URL configuration
const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json'
  }
});

// 프론트엔드 인메모리 캐시 (새로고침 시 초기화됨)
// UX 향상 및 불필요한 API 호출 방지
const searchCache = new Map();

export const commerceApi = {
  /**
   * Search commerce products using Naver Shopping API
   * @param {string} query - Search keyword
   * @param {number} [display] - Number of items to retrieve
   * @param {number} [start] - Start index for pagination
   * @param {string} [sort] - Sort order (sim, date, asc, dsc)
   * @returns {Promise<Array>} Array of product objects
   */
  async searchProducts(query, display = 10, start = 1, sort = 'sim') {
    // 캐시 키 생성 (페이지네이션 포함)
    const cacheKey = `${query}_${display}_${start}_${sort}`;

    // 1. 캐시에 데이터가 있으면 즉시 반환 (API 호출 X)
    if (searchCache.has(cacheKey)) {
      console.log(`[Cache Hit] Returning cached results for: ${cacheKey}`);
      return searchCache.get(cacheKey);
    }

    try {
      // 2. 캐시에 없으면 API 호출
      const response = await apiClient.get('/commerce/search', {
        params: {
          query,
          display,
          start,
          sort
        }
      });
      
      if (response.data && response.data.data) {
        const results = response.data.data;
        // 3. 결과를 캐시에 저장
        searchCache.set(cacheKey, results);
        return results;
      }
      return [];
    } catch (error) {
      console.error('Failed to search commerce products:', error);
      throw error;
    }
  },
  
  /**
   * 캐시 수동 초기화 (필요시 사용)
   */
  clearCache() {
    searchCache.clear();
  }
};
