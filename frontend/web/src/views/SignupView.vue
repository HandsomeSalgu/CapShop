<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const step = ref(1)

const signupToken = ref('')
const isSocialSignup = ref(false)

onMounted(() => {
  if (route.query.signupToken) {
    signupToken.value = route.query.signupToken
    try {
      const payloadBase64 = signupToken.value.split('.')[1]
      // Use atob to decode base64, then decodeURIComponent to handle UTF-8 characters properly
      const payloadString = decodeURIComponent(escape(atob(payloadBase64)))
      const payload = JSON.parse(payloadString)
      
      email.value = payload.email || ''
      name.value = payload.nickname || ''
      isEmailVerified.value = true
      isSocialSignup.value = true
      emailSuccessMsg.value = '소셜 인증된 이메일입니다.'
    } catch (e) {
      console.error('Invalid signupToken', e)
    }
  }
})

// --- Step 1: Terms ---
const termsService = ref(false)
const termsPrivacy = ref(false)
const termsCustom = ref(false)
const termsError = ref(false)

const goNextFromTerms = () => {
  if (!termsService.value || !termsPrivacy.value) {
    termsError.value = true
    return
  }
  termsError.value = false
  step.value = 2
}

const goCancel = () => {
  router.push('/login')
}

// --- Step 2: Form ---
const email = ref('')
const isEmailVerified = ref(false)
const emailErrorMsg = ref('')
const emailSuccessMsg = ref('')

const password = ref('')
const passwordMsg = ref('')
const passwordMsgType = ref('')

const passwordConfirm = ref('')
const passwordConfirmMsg = ref('')
const passwordConfirmMsgType = ref('')

const name = ref('')
const phone = ref('')
const birthYear = ref('')
const birthMonth = ref('')
const birthDay = ref('')

const formErrorMsg = ref('')

const checkEmail = async () => {
  if (!email.value) {
    emailErrorMsg.value = '이메일을 입력해주세요.'
    emailSuccessMsg.value = ''
    return
  }
  
  const emailRegex = /^[a-zA-Z0-9+-_.]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/
  if (!emailRegex.test(email.value)) {
    emailErrorMsg.value = '올바른 이메일 형식이 아닙니다.'
    emailSuccessMsg.value = ''
    return
  }

  try {
    const res = await axios.get('/api/auth/check-email', { params: { email: email.value } })
    if (res.data.data === true) {
      isEmailVerified.value = true
      emailSuccessMsg.value = '사용할 수 있는 이메일입니다.'
      emailErrorMsg.value = ''
    } else {
      isEmailVerified.value = false
      emailErrorMsg.value = '사용할 수 없는 이메일입니다.'
      emailSuccessMsg.value = ''
    }
  } catch {
    emailErrorMsg.value = '이메일 확인 중 오류가 발생했습니다.'
    emailSuccessMsg.value = ''
  }
}

const validatePassword = () => {
  const pwdRegex = /^(?=.*[a-zA-Z])(?=.*\d)(?=.*[!@#$%^&*])[a-zA-Z\d!@#$%^&*]{8,20}$/
  if (!password.value) {
    passwordMsg.value = ''
    passwordMsgType.value = ''
    return
  }
  if (!pwdRegex.test(password.value)) {
    passwordMsg.value = '20자 이내의 비밀번호를 입력해주세요 (영문, 숫자, 특수문자 포함 8~20자)'
    passwordMsgType.value = 'error'
  } else {
    passwordMsg.value = '해당 비밀번호 사용이 가능합니다'
    passwordMsgType.value = 'success'
  }
  
  // 비밀번호 확인도 같이 재검증
  if (passwordConfirm.value) {
    validatePasswordConfirm()
  }
}

const validatePasswordConfirm = () => {
  if (!passwordConfirm.value) {
    passwordConfirmMsg.value = ''
    return
  }
  if (password.value !== passwordConfirm.value) {
    passwordConfirmMsg.value = '비밀번호가 일치하지 않습니다'
    passwordConfirmMsgType.value = 'error'
  } else {
    passwordConfirmMsg.value = '비밀번호가 일치합니다'
    passwordConfirmMsgType.value = 'success'
  }
}

const submitSignup = async () => {
  if (!isEmailVerified.value) {
    formErrorMsg.value = '이메일 중복 확인을 진행해주세요.'
    return
  }
  if (passwordMsgType.value !== 'success' || passwordConfirmMsgType.value !== 'success') {
    formErrorMsg.value = '비밀번호를 올바르게 입력해주세요.'
    return
  }
  if (!name.value || !phone.value || !birthYear.value || !birthMonth.value || !birthDay.value) {
    formErrorMsg.value = '모든 항목을 입력해주세요.'
    return
  }
  
  // 간단한 날짜 조합 로직
  const paddedMonth = birthMonth.value.padStart(2, '0')
  const paddedDay = birthDay.value.padStart(2, '0')
  const birthDateStr = `${birthYear.value}-${paddedMonth}-${paddedDay}`

  try {
    const payload = {
      email: email.value,
      password: password.value,
      nickname: name.value,
      phone: phone.value,
      birthDate: birthDateStr
    }
    
    if (signupToken.value) {
      payload.signupToken = signupToken.value
    }

    await axios.post('/api/auth/signup', payload)
    step.value = 3
  } catch (error) {
    if (error.response && error.response.data && error.response.data.message) {
      formErrorMsg.value = error.response.data.message
    } else {
      formErrorMsg.value = '회원가입 중 오류가 발생했습니다.'
    }
  }
}

// --- Step 3: Complete ---
const goLogin = () => {
  router.push('/login')
}
</script>

<template>
  <main class="signup-container">
    <!-- Step 1: Terms -->
    <div v-if="step === 1" class="signup-card">
      <div class="signup-header">
        <h2>약관 동의</h2>
        <p class="subtitle">가입 전 약관을 확인해주세요</p>
      </div>
      
      <div v-if="termsError" class="error-msg top-error">
        필수 약관에 동의해 주세요
      </div>

      <div class="terms-group">
        <label class="terms-label">
          <input type="checkbox" v-model="termsService">
          <span>[필수] 서비스 이용 약관</span>
        </label>
        <div class="terms-box">
          제 1 조 (목적) 본 약관은 [회사명]이 제공하는 서비스의 이용과 관련하여 회사와 회원 간의 권리, 의무 및 책임사항을 규정함을 목적으로 합니다.
          제 2 조 (정의) 1. "서비스"란 회사가 제공하는 모든 서비스를 의미합니다.
          ...
        </div>
      </div>

      <div class="terms-group">
        <label class="terms-label">
          <input type="checkbox" v-model="termsPrivacy">
          <span>[필수] 개인정보 수집 및 이용 동의</span>
        </label>
        <div class="terms-box">
          [회사명]은 회원가입 및 원활한 서비스 제공을 위해 아래와 같이 최소한의 개인정보를 수집 및 이용합니다.
          1. 수집하는 개인정보 항목: 이메일, 비밀번호, 이름, 전화번호, 생년월일
          ...
        </div>
      </div>

      <div class="terms-group">
        <label class="terms-label">
          <input type="checkbox" v-model="termsCustom">
          <span>[선택] 맞춤형 상품 추천을 위한 데이터 수집 및 이용 동의</span>
        </label>
        <div class="terms-box">
          AI 추천 모델 고도화 등 개인화 서비스 제공을 위하여 다음과 같이 데이터를 수집하고 이용합니다.
          동의를 거부하셔도 기본 회원가입 및 서비스 이용은 가능합니다.
          ...
        </div>
      </div>

      <div class="btn-group">
        <button class="btn-outline" @click="goCancel">가입취소</button>
        <button class="btn-primary" @click="goNextFromTerms">다음으로</button>
      </div>
    </div>

    <!-- Step 2: Form -->
    <div v-else-if="step === 2" class="signup-card">
      <div class="signup-header">
        <h2>회원가입</h2>
        <p class="subtitle">회원이 되어 다양한 혜택을 경험해보세요</p>
      </div>

      <div class="form-group">
        <div class="label-row">
          <label>이메일</label>
          <span v-if="emailErrorMsg" class="msg-error">{{ emailErrorMsg }}</span>
          <span v-if="emailSuccessMsg" class="msg-success">{{ emailSuccessMsg }}</span>
        </div>
        <div class="input-with-btn">
          <input type="text" v-model="email" placeholder="아이디 입력(6~20자)" class="form-input" @input="isEmailVerified = false" :readonly="isSocialSignup">
          <button type="button" class="btn-check" @click="checkEmail" :disabled="isSocialSignup">이메일 확인</button>
        </div>
      </div>

      <div class="form-group">
        <div class="label-row">
          <label>비밀번호</label>
          <span v-if="passwordMsg" :class="passwordMsgType === 'error' ? 'msg-error' : 'msg-success'">
            {{ passwordMsg }}
          </span>
        </div>
        <input type="password" v-model="password" @blur="validatePassword" placeholder="비밀번호 입력(문자, 숫자, 특수문자 포함 8~20자)" class="form-input">
      </div>

      <div class="form-group">
        <div class="label-row">
          <label>비밀번호 확인</label>
          <span v-if="passwordConfirmMsg" :class="passwordConfirmMsgType === 'error' ? 'msg-error' : 'msg-success'">
            {{ passwordConfirmMsg }}
          </span>
        </div>
        <input type="password" v-model="passwordConfirm" @blur="validatePasswordConfirm" placeholder="비밀번호 재입력" class="form-input">
      </div>

      <div class="form-group">
        <label>이름</label>
        <input type="text" v-model="name" placeholder="이름을 입력하세요" class="form-input">
      </div>

      <div class="form-group">
        <label>전화번호</label>
        <input type="text" v-model="phone" placeholder="휴대폰 번호 입력('-' 제외 11자리 입력)" class="form-input" maxlength="11">
      </div>

      <div class="form-group">
        <label>생년월일</label>
        <div class="birth-inputs">
          <input type="text" v-model="birthYear" placeholder="년도" class="form-input" maxlength="4">
          <input type="text" v-model="birthMonth" placeholder="월" class="form-input" maxlength="2">
          <input type="text" v-model="birthDay" placeholder="일" class="form-input" maxlength="2">
        </div>
      </div>

      <div v-if="formErrorMsg" class="error-msg">
        {{ formErrorMsg }}
      </div>

      <div class="btn-group">
        <button class="btn-outline" @click="step = 1">뒤로가기</button>
        <button class="btn-primary" @click="submitSignup">다음으로</button>
      </div>
    </div>

    <!-- Step 3: Complete -->
    <div v-else-if="step === 3" class="signup-card center-card">
      <div class="complete-icon">
        <i class="fa-solid fa-circle-check"></i>
      </div>
      <h2>회원가입이 완료되었습니다!</h2>
      <p class="subtitle">로그인을 하여 다양한 서비스 및 혜택을 누려보세요!</p>
      
      <button class="btn-primary btn-large" @click="goLogin">로그인 하러가기</button>
    </div>
  </main>
</template>

<style scoped>
.signup-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 800px;
  padding: 60px 20px;
  background-color: var(--bg-body);
}

.signup-card {
  width: 100%;
  max-width: 500px;
  padding: 40px;
  border: 1px solid var(--border-color);
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.signup-header {
  text-align: center;
  margin-bottom: 30px;
}

.signup-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: var(--primary-color);
  margin-bottom: 8px;
}

.subtitle {
  font-size: 14px;
  color: var(--text-muted);
}

.terms-group {
  margin-bottom: 20px;
}

.terms-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  margin-bottom: 8px;
  cursor: pointer;
}

.terms-box {
  border: 1px solid var(--border-color);
  border-radius: 4px;
  height: 100px;
  overflow-y: auto;
  padding: 12px;
  font-size: 13px;
  color: #555;
  background-color: #f9f9f9;
  line-height: 1.5;
}

.btn-group {
  display: flex;
  gap: 10px;
  margin-top: 30px;
}

.btn-primary {
  flex: 1;
  padding: 15px;
  background-color: var(--primary-color);
  color: #ffffff;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-primary:hover {
  background-color: #333;
}

.btn-outline {
  flex: 1;
  padding: 15px;
  background-color: #ffffff;
  color: var(--text-color);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-outline:hover {
  background-color: #f5f5f5;
}

.form-group {
  margin-bottom: 20px;
}

.label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.label-row label {
  font-size: 14px;
  font-weight: 500;
}

.msg-error {
  font-size: 12px;
  color: #d9534f;
}

.msg-success {
  font-size: 12px;
  color: #5cb85c;
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

.input-with-btn {
  display: flex;
  gap: 10px;
}

.btn-check {
  width: 120px;
  background-color: #f5f5f5;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-check:hover {
  background-color: #e9e9e9;
}

.birth-inputs {
  display: flex;
  gap: 10px;
}

.birth-inputs input {
  flex: 1;
  text-align: center;
}

.error-msg {
  color: #d9534f;
  font-size: 14px;
  text-align: center;
  margin-top: 15px;
}

.top-error {
  margin-top: 0;
  margin-bottom: 20px;
}

/* Step 3 Styles */
.center-card {
  text-align: center;
  padding: 60px 40px;
}

.complete-icon {
  font-size: 60px;
  color: #5cb85c;
  margin-bottom: 20px;
}

.center-card h2 {
  font-size: 24px;
  font-weight: 600;
  color: var(--primary-color);
  margin-bottom: 15px;
}

.center-card .subtitle {
  margin-bottom: 40px;
}

.btn-large {
  width: 100%;
}
</style>
