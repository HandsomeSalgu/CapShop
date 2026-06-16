<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const password = ref('')
const errorMessage = ref('')
const isLoading = ref(false)

const confirmPassword = async () => {
  if (!password.value) {
    errorMessage.value = '비밀번호를 입력해주세요.'
    return
  }
  
  isLoading.value = true
  errorMessage.value = ''
  
  try {
    const token = localStorage.getItem('accessToken')
    const res = await axios.post('/api/users/me/password/verify', {
      password: password.value
    }, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
    
    if (res.data.data === true) {
      sessionStorage.setItem('passwordVerified', 'true')
      router.push('/mypage/profile')
    } else {
      errorMessage.value = '비밀번호가 일치하지 않습니다.'
    }
  } catch (error) {
    if (error.response && error.response.data && error.response.data.message) {
      errorMessage.value = error.response.data.message
    } else {
      errorMessage.value = '비밀번호 확인 중 오류가 발생했습니다.'
    }
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="profile-edit-card">
    <div class="signup-header">
      <h2>회원 정보 수정 전 비밀번호 확인</h2>
    </div>

    <div class="form-group">
      <div class="label-row">
        <label>현재 비밀번호 입력</label>
      </div>
      <input type="password" v-model="password" @keyup.enter="confirmPassword" placeholder="비밀번호 입력(문자, 숫자, 특수문자 포함 8~20자)" class="form-input">
    </div>

    <div v-if="errorMessage" class="error-msg">
      {{ errorMessage }}
    </div>

    <div class="btn-group">
      <button class="btn-primary" @click="confirmPassword" :disabled="isLoading">
        {{ isLoading ? '확인 중...' : '다음' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.profile-edit-card {
  background: white;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.03);
}

.signup-header {
  text-align: left;
  margin-bottom: 30px;
  border-bottom: 1px solid #eee;
  padding-bottom: 15px;
}

.signup-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: var(--primary-color, #2c3e50);
  margin-bottom: 8px;
}

.form-group {
  margin-bottom: 24px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #444;
}

.label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.label-row label {
  margin-bottom: 0;
}

.form-input {
  width: 100%;
  padding: 14px;
  font-size: 15px;
  border: 1px solid #ddd;
  border-radius: 6px;
  outline: none;
  transition: border-color 0.3s;
  font-family: inherit;
}

.form-input:focus {
  border-color: #3498db;
}

.btn-group {
  display: flex;
  gap: 15px;
  margin-top: 40px;
  justify-content: center;
}

.btn-primary {
  padding: 14px 40px;
  background-color: #3498db;
  color: #ffffff;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-primary:hover {
  background-color: #2980b9;
}

.error-msg {
  color: #d9534f;
  font-size: 14px;
  text-align: center;
  margin-top: 15px;
}
</style>
