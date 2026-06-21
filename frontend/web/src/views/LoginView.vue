<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const userId = ref('')
const userPassword = ref('')
const loginError = ref(false)

const handleLogin = async () => {
  try {
    const response = await axios.post('/api/auth/login', {
      email: userId.value,
      password: userPassword.value
    });
    
    // 성공 시 에러 문구 끄기
    loginError.value = false;
    
    // 백엔드가 준 토큰과 유저 정보를 Pinia store에 저장
    const token = response.data.data.accessToken; 
    const user = response.data.data.user;
    authStore.login(token, user);
    
    // 메인 화면으로 이동
    router.push('/');
    
  } catch {
    // 백엔드에서 거절(400, 401 에러 등)하면 에러 문구 띄우기
    loginError.value = true;
  }
}

const loginWithGoogle = () => {
  window.location.href = 'http://localhost:8080/oauth2/authorization/google';
}

const loginWithKakao = () => {
  window.location.href = 'http://localhost:8080/oauth2/authorization/kakao';
}

const alertPreparing = () => {
  alert('준비 중입니다')
}
</script>

<template>
  <main class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h2>로그인</h2>
      </div>
      
      <form class="login-form" @submit.prevent="handleLogin">
        <div class="input-group">
          <input 
            type="text" 
            v-model="userId" 
            placeholder="이메일" 
            class="login-input"
          />
        </div>
        <div class="input-group">
          <input 
            type="password" 
            v-model="userPassword" 
            placeholder="비밀번호" 
            class="login-input"
          />
        </div>
        <div v-if="loginError" class="error-msg">
          회원정보가 일치하지 않습니다.
        </div>
        
        <button type="submit" class="btn-login">로그인</button>
      </form>

      <div class="divider"></div>

      <div class="social-login">
        <button type="button" class="btn-social btn-google" @click="loginWithGoogle">
          <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA0OCA0OCIgd2lkdGg9IjQ4cHgiIGhlaWdodD0iNDhweCI+PHBhdGggZmlsbD0iI0ZGQzEwNyIgZD0iTTQzLjYxMSwyMC4wODNINDJWMjBIMjR2OGgxMS4zMDNjLTEuNjQ5LDQuNjU3LTYuMDgsOC0xMS4zMDMsOGMtNi42MjcsMC0xMi01LjM3My0xMi0xMmMwLTYuNjI3LDUuMzczLTEyLDEyLTEyYzMuMDU5LDAsNS44NDIsMS4xNTQsNy45NjEsMy4wMzlsNS42NTctNS42NTdDMzQuMDQ2LDYuMDUzLDI5LjI2OCw0LDI0LDRDMTIuOTU1LDQsNCwxMi45NTUsNCwyNGMwLDExLjA0NSw4Ljk1NSwyMCwyMCwyMGMxMS4wNDUsMCwyMC04Ljk1NSwyMC0yMEM0NCwyMi42NTksNDMuODYyLDIxLjM1LDQzLjYxMSwyMC4wODN6Ii8+PHBhdGggZmlsbD0iI0ZGM0QwMCIgZD0iTTYuMzA2LDE0LjY5MWw2LjU3MSw0LjgxOUMxNC42NTUsMTUuMTA4LDE4Ljk2MSwxMiwyNCwxMmMzLjA1OSwwLDUuODQyLDEuMTU0LDcuOTYxLDMuMDMxbDUuNjU3LTUuNjU3QzM0LjA0Niw2LjA1MywyOS4yNjgsNCwyNCw0QzE2LjMxOCw0LDkuNjU2LDguMzM3LDYuMzA2LDE0LjY5MXoiLz48cGF0aCBmaWxsPSIjNENBRjUwIiBkPSJNMjQsNDRjNS4xNjYsMCw5Ljg2LTEuOTc3LDEzLjQwOS01LjE5MmwtNi4xOS01LjIzOEMyOS4yMTEsMzUuMDkxLDI2LjcxNSwzNiwyNCwzNmMtNS4yMDIsMC05LjYxOS0zLjMxNy0xMS4yODMtNy45NDZsLTYuNTIyLDUuMDI1QzkuNTA1LDM5LjU1NiwxNi4yMjcsNDQsMjQsNDR6Ii8+PHBhdGggZmlsbD0iIzE5NzZEMiIgZD0iTTQzLjYxMSwyMC4wODNINDJWMjBIMjR2OGgxMS4zMDNjLTAuNzkyLDIuMjM3LTIuMjMxLDQuMTY2LTQuMDg3LDUuNTcxYzAuMDAxLTAuMDAxLDAuMDAyLTAuMDAxLDAuMDAzLTAuMDAybDYuMTksNS4yMzhDMzYuOTcxLDM5LjIwNSw0NCwzNCw0NCwyNEM0NCwyMi42NTksNDMuODYyLDIxLjM1LDQzLjYxMSwyMC4wODN6Ii8+PC9zdmc+" alt="Google" class="social-icon">
          구글 소셜 로그인
        </button>
        <button type="button" class="btn-social btn-kakao" @click="loginWithKakao">
          <i class="fa-solid fa-comment social-icon"></i>
          카카오 소셜 로그인
        </button>
      </div>

      <div class="login-links">
        <a href="#" @click.prevent="alertPreparing">아이디/비밀번호 찾기</a>
        <span class="separator">|</span>
        <a href="#" @click.prevent="router.push('/signup')">일반 회원가입</a>
      </div>
    </div>
  </main>
</template>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 600px;
  padding: 60px 20px;
  background-color: var(--bg-body);
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 40px;
  border: 1px solid var(--border-color);
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: var(--primary-color);
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.input-group {
  width: 100%;
}

.login-input {
  width: 100%;
  padding: 15px;
  font-size: 15px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  outline: none;
  transition: border-color 0.3s;
  font-family: inherit;
}

.login-input:focus {
  border-color: var(--accent-color);
}

.error-msg {
  color: #d9534f;
  font-size: 13px;
  margin-top: -5px;
  margin-bottom: 5px;
}

.btn-login {
  width: 100%;
  padding: 15px;
  background-color: var(--primary-color);
  color: #ffffff;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  font-weight: 500;
  margin-top: 10px;
  transition: background-color 0.3s;
}

.btn-login:hover {
  background-color: #333333;
}

.divider {
  height: 1px;
  background-color: var(--border-color);
  margin: 30px 0;
}

.social-login {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.btn-social {
  width: 100%;
  padding: 14px;
  border-radius: 4px;
  font-size: 15px;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border: 1px solid var(--border-color);
  transition: opacity 0.3s;
  cursor: pointer;
}

.btn-social:hover {
  opacity: 0.8;
}

.btn-google {
  background-color: #ffffff;
  color: var(--text-color);
}

.btn-kakao {
  background-color: #FEE500;
  border-color: #FEE500;
  color: #000000;
}

.social-icon {
  width: 18px;
  height: 18px;
}

.login-links {
  margin-top: 25px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--text-muted);
}

.login-links a {
  color: var(--text-muted);
}

.login-links a:hover {
  color: var(--accent-color);
}

.separator {
  color: var(--border-color);
}
</style>
