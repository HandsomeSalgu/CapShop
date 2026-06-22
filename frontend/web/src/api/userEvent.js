import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const BASE_URL = '/api/user-events'

// Axios 인스턴스에 토큰 자동 추가 로직 (필요시 별도 모듈로 분리 가능)
const getHeaders = () => {
  const token = localStorage.getItem('accessToken')
  if (token) {
    return {
      Authorization: `Bearer ${token}`
    }
  }
  return {}
}

export const userEventApi = {
  /**
   * 상품 상세 조회 이벤트 저장
   * @param {Object} data - { productId, product, sourcePage }
   */
  logProductDetailView: async (data) => {
    try {
      const response = await axios.post(`${BASE_URL}/product-detail-view`, data, {
        headers: getHeaders()
      })
      return response.data
    } catch (error) {
      console.error('Failed to log product detail view:', error)
      throw error
    }
  }
}
