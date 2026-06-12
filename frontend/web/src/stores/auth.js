import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', () => {
  const isLoggedIn = ref(false)
  const userInfo = ref(null)

  // 앱 로드 시 localStorage에서 정보 복구
  const init = () => {
    const token = localStorage.getItem('accessToken')
    const userStr = localStorage.getItem('userInfo')
    
    if (token && userStr) {
      isLoggedIn.value = true
      userInfo.value = JSON.parse(userStr)
    }
  }

  const login = (token, user) => {
    localStorage.setItem('accessToken', token)
    localStorage.setItem('userInfo', JSON.stringify(user))
    isLoggedIn.value = true
    userInfo.value = user
  }

  const logout = () => {
    localStorage.removeItem('accessToken')
    localStorage.removeItem('userInfo')
    isLoggedIn.value = false
    userInfo.value = null
  }

  return { isLoggedIn, userInfo, init, login, logout }
})
