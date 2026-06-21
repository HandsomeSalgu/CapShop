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
        <button type="button" class="btn-social btn-google" @click="alertPreparing">
          <img src="https://upload.wikimedia.org/wikipedia/commons/5/53/Google_%22G%22_Logo.svg" alt="Google" class="social-icon">
          구글 소셜 로그인
        </button>
        <button type="button" class="btn-social btn-kakao" @click="alertPreparing">
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
