<script setup>
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

onMounted(async () => {
  const { accessToken, error } = route.query

  if (error) {
    alert('소셜 로그인에 실패했습니다.')
    router.replace('/login')
    return
  }

  if (accessToken) {
    try {
      // 사용자 정보 가져오기
      const response = await axios.get('/api/auth/me', {
        headers: {
          Authorization: `Bearer ${accessToken}`
        }
      })
      
      const user = response.data.data
      
      // 스토어에 로그인 정보 저장
      authStore.login(accessToken, user)
      
      // 메인 페이지로 이동
      router.replace('/')
    } catch (e) {
      console.error('사용자 정보 가져오기 실패:', e)
      alert('사용자 정보를 불러오지 못했습니다. 다시 로그인해주세요.')
      router.replace('/login')
    }
  } else {
    alert('잘못된 접근입니다.')
    router.replace('/login')
  }
})
</script>

<template>
  <div class="callback-container">
    <div class="loader-content">
      <div class="spinner"></div>
      <p>로그인 처리 중입니다...</p>
    </div>
  </div>
</template>

<style scoped>
.callback-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 60vh;
}

.loader-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--border-color, #eaeaea);
  border-top-color: var(--primary-color, #333);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
