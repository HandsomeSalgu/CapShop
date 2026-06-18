import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api/posts',
  headers: {
    'Content-Type': 'application/json'
  }
});

export const boardApi = {
  /**
   * 공지사항 목록 조회
   * @param {number} page 
   * @param {number} size 
   */
  async getNotices(page = 1, size = 10) {
    const response = await apiClient.get('/notices', { params: { page, size } });
    return response.data;
  },

  /**
   * FAQ 목록 조회
   * @param {number} page 
   * @param {number} size 
   */
  async getFaqs(page = 1, size = 10) {
    const response = await apiClient.get('/faqs', { params: { page, size } });
    return response.data;
  },

  /**
   * 이벤트 목록 조회
   * @param {number} page 
   * @param {number} size 
   */
  async getEvents(page = 1, size = 10) {
    const response = await apiClient.get('/events', { params: { page, size } });
    return response.data;
  },

  /**
   * 게시글 상세 조회
   * @param {number} postId 
   */
  async getPostDetail(postId) {
    const response = await apiClient.get(`/${postId}`);
    return response.data;
  }
};
