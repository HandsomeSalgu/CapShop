import axios from 'axios'

const BASE_URL = '/api/users/me/wishlist'

const getHeaders = () => {
  const token = localStorage.getItem('accessToken')
  if (token) {
    return {
      Authorization: `Bearer ${token}`
    }
  }
  return {}
}

export const wishlistApi = {
  /**
   * 상품을 위시리스트에 추가
   * @param {number|string} productId 
   */
  addWishlist: async (productId) => {
    try {
      const response = await axios.post(`${BASE_URL}/${productId}`, {}, {
        headers: getHeaders()
      })
      return response.data
    } catch (error) {
      console.error('Failed to add to wishlist:', error)
      throw error
    }
  },
  
  /**
   * 상품을 위시리스트에서 제거
   * @param {number|string} productId 
   */
  removeWishlist: async (productId) => {
    try {
      const response = await axios.delete(`${BASE_URL}/${productId}`, {
        headers: getHeaders()
      })
      return response.data
    } catch (error) {
      console.error('Failed to remove from wishlist:', error)
      throw error
    }
  },

  /**
   * 상품 위시리스트 추가 여부 확인
   * @param {number|string} productId 
   */
  checkWishlist: async (productId) => {
    try {
      const response = await axios.get(`${BASE_URL}/check/${productId}`, {
        headers: getHeaders()
      })
      return response.data // { data: boolean }
    } catch (error) {
      console.error('Failed to check wishlist status:', error)
      throw error
    }
  }
}
