<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const activeTab = ref('email') // 'email' or 'password'

// Find Email state
const findEmailName = ref('')
const findEmailPhone = ref('')
const findEmailResult = ref('')
const findEmailError = ref('')

// Find Password state
const findPwEmail = ref('')
const findPwName = ref('')
const findPwPhone = ref('')
const findPwResult = ref('')
const findPwError = ref('')

const handleFindEmail = async () => {
  findEmailResult.value = ''
  findEmailError.value = ''
  
  if (!findEmailName.value || !findEmailPhone.value) {
    findEmailError.value = '이름과 전화번호를 모두 입력해주세요.'
    return
  }

  try {
    const response = await axios.post('/api/auth/find-email', {
      nickname: findEmailName.value,
      phone: findEmailPhone.value
    })
    findEmailResult.value = `회원님의 이메일은 ${response.data.data} 입니다.`
  } catch (error) {
    findEmailError.value = error.response?.data?.message || '이메일 찾기 중 오류가 발생했습니다.'
  }
}

const handleFindPassword = async () => {
  findPwResult.value = ''
  findPwError.value = ''

  if (!findPwEmail.value || !findPwName.value || !findPwPhone.value) {
    findPwError.value = '모든 정보를 입력해주세요.'
    return
  }

  try {
    const response = await axios.post('/api/auth/find-password', {
      email: findPwEmail.value,
      nickname: findPwName.value,
      phone: findPwPhone.value
    })
    
    findPwResult.value = response.data.message || '등록된 이메일로 임시 비밀번호가 발송되었습니다.'
  } catch (error) {
    findPwError.value = error.response?.data?.message || '비밀번호 찾기 중 오류가 발생했습니다.'
  }
}
</script>

<template>
  <main class="find-account-container">
    <div class="find-account-card">
      <div class="tabs">
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'email' }" 
          @click="activeTab = 'email'; findEmailResult=''; findEmailError='';"
        >
          이메일 찾기
        </button>
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'password' }" 
          @click="activeTab = 'password'; findPwResult=''; findPwError='';"
        >
          비밀번호 찾기
        </button>
      </div>

      <!-- 이메일 찾기 폼 -->
      <div v-if="activeTab === 'email'" class="form-content">
        <div class="form-header">
          <h2>이메일 찾기</h2>
          <p class="subtitle">가입 시 등록한 이름과 전화번호를 입력해주세요.</p>
        </div>

        <form @submit.prevent="handleFindEmail" class="find-form">
          <div class="form-group">
            <label>이름</label>
            <input type="text" v-model="findEmailName" placeholder="이름을 입력하세요" class="form-input">
          </div>
          <div class="form-group">
            <label>전화번호</label>
            <input type="text" v-model="findEmailPhone" placeholder="휴대폰 번호 입력('-' 제외)" class="form-input" maxlength="11">
          </div>

          <div v-if="findEmailError" class="error-msg">{{ findEmailError }}</div>
          <div v-if="findEmailResult" class="success-msg">{{ findEmailResult }}</div>

          <button type="submit" class="btn-submit">이메일 찾기</button>
        </form>
      </div>

      <!-- 비밀번호 찾기 폼 -->
      <div v-if="activeTab === 'password'" class="form-content">
        <div class="form-header">
          <h2>비밀번호 찾기</h2>
          <p class="subtitle">가입 시 등록한 이메일, 이름, 전화번호를 입력해주세요.</p>
        </div>

        <form @submit.prevent="handleFindPassword" class="find-form">
          <div class="form-group">
            <label>이메일</label>
            <input type="text" v-model="findPwEmail" placeholder="이메일 주소를 입력하세요" class="form-input">
          </div>
          <div class="form-group">
            <label>이름</label>
            <input type="text" v-model="findPwName" placeholder="이름을 입력하세요" class="form-input">
          </div>
          <div class="form-group">
            <label>전화번호</label>
            <input type="text" v-model="findPwPhone" placeholder="휴대폰 번호 입력('-' 제외)" class="form-input" maxlength="11">
          </div>

          <div v-if="findPwError" class="error-msg">{{ findPwError }}</div>
          <div v-if="findPwResult" class="success-msg">{{ findPwResult }}</div>

          <button type="submit" class="btn-submit">임시 비밀번호 발송</button>
        </form>
      </div>

      <div class="login-links">
        <a href="#" @click.prevent="router.push('/login')">로그인으로 돌아가기</a>
      </div>
    </div>
  </main>
</template>

<style scoped>
.find-account-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 600px;
  padding: 60px 20px;
  background-color: var(--bg-body);
}

.find-account-card {
  width: 100%;
  max-width: 450px;
  padding: 40px;
  border: 1px solid var(--border-color);
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.tabs {
  display: flex;
  margin-bottom: 30px;
  border-bottom: 1px solid var(--border-color);
}

.tab-btn {
  flex: 1;
  padding: 15px;
  background: none;
  border: none;
  font-size: 16px;
  font-weight: 500;
  color: var(--text-muted);
  cursor: pointer;
  border-bottom: 3px solid transparent;
  transition: all 0.3s;
}

.tab-btn:hover {
  color: var(--text-color);
}

.tab-btn.active {
  color: var(--primary-color);
  border-bottom-color: var(--primary-color);
}

.form-header {
  text-align: center;
  margin-bottom: 25px;
}

.form-header h2 {
  font-size: 22px;
  font-weight: 600;
  color: var(--primary-color);
  margin-bottom: 8px;
}

.subtitle {
  font-size: 14px;
  color: var(--text-muted);
}

.find-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
}

.form-input {
  width: 100%;
  padding: 14px;
  font-size: 15px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  outline: none;
  transition: border-color 0.3s;
  font-family: inherit;
}

.form-input:focus {
  border-color: var(--accent-color);
}

.error-msg {
  color: #d9534f;
  font-size: 13px;
  text-align: center;
  margin-top: 5px;
}

.success-msg {
  color: #5cb85c;
  font-size: 14px;
  text-align: center;
  margin-top: 5px;
  font-weight: 500;
}

.btn-submit {
  width: 100%;
  padding: 15px;
  background-color: var(--primary-color);
  color: #ffffff;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  font-weight: 500;
  margin-top: 10px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-submit:hover {
  background-color: #333333;
}

.login-links {
  margin-top: 25px;
  display: flex;
  justify-content: center;
  font-size: 14px;
}

.login-links a {
  color: var(--text-muted);
  text-decoration: none;
  transition: color 0.3s;
}

.login-links a:hover {
  color: var(--accent-color);
}
</style>
