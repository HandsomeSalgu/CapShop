<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import CustomSelect from '@/components/common/CustomSelect.vue'
import { categories } from '@/data/categories.js'

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

const isCodeSent = ref(false)
const verificationCode = ref('')
const timer = ref(0)
const timerStr = ref('05:00')
let timerInterval = null

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

const currentDate = new Date()
const currentYear = currentDate.getFullYear()
const currentMonth = currentDate.getMonth() + 1
const currentDay = currentDate.getDate()

const availableYears = Array.from({ length: 100 }, (_, i) => currentYear - i)

const availableMonths = computed(() => {
  if (birthYear.value === currentYear) {
    return Array.from({ length: currentMonth }, (_, i) => i + 1)
  }
  return Array.from({ length: 12 }, (_, i) => i + 1)
})

const availableDays = computed(() => {
  if (!birthMonth.value) {
    return Array.from({ length: 31 }, (_, i) => i + 1)
  }
  const yearForCalc = birthYear.value || 2024 // 년도를 아직 선택 안 했다면 29일이 포함되도록 2024년(윤년) 기준으로 일수 계산
  let days = new Date(yearForCalc, birthMonth.value, 0).getDate()
  
  if (birthYear.value === currentYear && birthMonth.value === currentMonth) {
    days = Math.min(days, currentDay)
  }
  return Array.from({ length: days }, (_, i) => i + 1)
})

watch([birthYear, birthMonth], () => {
  if (birthYear.value === currentYear && birthMonth.value > currentMonth) {
    birthMonth.value = ''
  }
  if (birthDay.value && birthDay.value > availableDays.value.length) {
    birthDay.value = ''
  }
})

const formErrorMsg = ref('')

const startTimer = () => {
  if (timerInterval) clearInterval(timerInterval)
  timer.value = 300 // 5 minutes in seconds
  updateTimerStr()
  
  timerInterval = setInterval(() => {
    timer.value--
    updateTimerStr()
    if (timer.value <= 0) {
      clearInterval(timerInterval)
      emailErrorMsg.value = '인증 시간이 만료되었습니다. 다시 요청해주세요.'
      isCodeSent.value = false
    }
  }, 1000)
}

const updateTimerStr = () => {
  const m = Math.floor(timer.value / 60)
  const s = timer.value % 60
  timerStr.value = `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

const sendEmailCode = async () => {
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
    const res = await axios.post('/api/auth/email/send-code', { email: email.value })
    isCodeSent.value = true
    isEmailVerified.value = false
    emailSuccessMsg.value = '인증번호가 발송되었습니다. 이메일을 확인해주세요.'
    emailErrorMsg.value = ''
    startTimer()
  } catch (error) {
    if (error.response && error.response.data && error.response.data.message) {
      emailErrorMsg.value = error.response.data.message
    } else {
      emailErrorMsg.value = '인증번호 발송 중 오류가 발생했습니다.'
    }
    emailSuccessMsg.value = ''
  }
}

const verifyCode = async () => {
  if (!verificationCode.value) {
    emailErrorMsg.value = '인증번호를 입력해주세요.'
    emailSuccessMsg.value = ''
    return
  }

  try {
    const res = await axios.post('/api/auth/email/verify-code', { 
      email: email.value, 
      code: verificationCode.value 
    })
    
    isEmailVerified.value = true
    isCodeSent.value = false
    if (timerInterval) clearInterval(timerInterval)
    emailSuccessMsg.value = '이메일 인증이 완료되었습니다.'
    emailErrorMsg.value = ''
  } catch (error) {
    isEmailVerified.value = false
    if (error.response && error.response.data && error.response.data.message) {
      emailErrorMsg.value = error.response.data.message
    } else {
      emailErrorMsg.value = '인증번호가 올바르지 않습니다.'
    }
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

const goStep3 = () => {
  if (!isEmailVerified.value) {
    formErrorMsg.value = '이메일 중복 확인을 진행해주세요.'
    return
  }
  if (!isSocialSignup.value && (passwordMsgType.value !== 'success' || passwordConfirmMsgType.value !== 'success')) {
    formErrorMsg.value = '비밀번호를 올바르게 입력해주세요.'
    return
  }
  if (!name.value || !phone.value || !birthYear.value || !birthMonth.value || !birthDay.value) {
    formErrorMsg.value = '모든 항목을 입력해주세요.'
    return
  }
  
  step.value = 3
}

// --- Step 3: Category Selection ---
const selectedCategories = ref([
  { major: null, minor: null },
  { major: null, minor: null },
  { major: null, minor: null }
])

const activeSelection = ref({
  index: 0,
  type: 'major'
})

const currentCategoryList = computed(() => {
  if (activeSelection.value.type === 'major') {
    return categories.map(c => c.name)
  } else {
    const selectedMajorName = selectedCategories.value[activeSelection.value.index].major
    const majorObj = categories.find(c => c.name === selectedMajorName)
    if (majorObj) {
      return majorObj.subCategories.map(s => s.name)
    }
    return []
  }
})

const selectCategoryItem = (item) => {
  const { index, type } = activeSelection.value
  if (type === 'major') {
    selectedCategories.value[index].major = item
    selectedCategories.value[index].minor = null
    activeSelection.value.type = 'minor'
  } else {
    selectedCategories.value[index].minor = item
  }
}

const setActiveSelection = (index, type) => {
  activeSelection.value = { index, type }
}

const submitSignup = async () => {
  const hasSelectedAny = selectedCategories.value.some(cat => cat.major !== null)
  if (!hasSelectedAny) {
    const confirmProceed = confirm('아무것도 선택안하면 초반에 추천 시스템을 원활하게 이용할 수 없는데 괜찮으시겠습니까?')
    if (!confirmProceed) return
  }

  const paddedMonth = String(birthMonth.value).padStart(2, '0')
  const paddedDay = String(birthDay.value).padStart(2, '0')
  const birthDateStr = `${birthYear.value}-${paddedMonth}-${paddedDay}`

  const selectedMinorCategories = selectedCategories.value
    .filter(cat => cat.minor !== null)
    .map(cat => ({
      category1Name: cat.major,
      category2Name: cat.minor
    }))

  try {
    const payload = {
      email: email.value,
      password: isSocialSignup.value ? 'SocialDummyPass123!' : password.value,
      nickname: name.value,
      phone: phone.value,
      birthDate: birthDateStr,
      preferredCategories: selectedMinorCategories
    }
    
    if (signupToken.value) {
      payload.signupToken = signupToken.value
    }

    await axios.post('/api/auth/signup', payload)
    step.value = 4
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
          <input type="text" v-model="email" placeholder="이메일 입력(6~20자)" class="form-input" @input="isEmailVerified = false; isCodeSent = false" :readonly="isSocialSignup">
          <button type="button" class="btn-check" @click="sendEmailCode" :disabled="isSocialSignup">인증번호 발송</button>
        </div>
      </div>

      <div class="form-group" v-if="isCodeSent">
        <div class="label-row">
          <label>인증번호 ({{ timerStr }})</label>
        </div>
        <div class="input-with-btn">
          <input type="text" v-model="verificationCode" placeholder="인증번호 6자리 입력" class="form-input" maxlength="6">
          <button type="button" class="btn-check" @click="verifyCode">인증 확인</button>
        </div>
      </div>

      <div class="form-group" v-if="!isSocialSignup">
        <div class="label-row">
          <label>비밀번호</label>
          <span v-if="passwordMsg" :class="passwordMsgType === 'error' ? 'msg-error' : 'msg-success'">
            {{ passwordMsg }}
          </span>
        </div>
        <input type="password" v-model="password" @blur="validatePassword" placeholder="비밀번호 입력(문자, 숫자, 특수문자 포함 8~20자)" class="form-input">
      </div>

      <div class="form-group" v-if="!isSocialSignup">
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
          <CustomSelect v-model="birthYear" :options="availableYears" placeholder="년도" max-height="150px" />
          <CustomSelect v-model="birthMonth" :options="availableMonths" placeholder="월" max-height="150px" />
          <CustomSelect v-model="birthDay" :options="availableDays" placeholder="일" max-height="150px" />
        </div>
      </div>

      <div v-if="formErrorMsg" class="error-msg">
        {{ formErrorMsg }}
      </div>

      <div class="btn-group">
        <button class="btn-outline" @click="step = 1">뒤로가기</button>
        <button class="btn-primary" @click="goStep3">다음으로</button>
      </div>
    </div>

    <!-- Step 3: Categories -->
    <div v-else-if="step === 3" class="signup-card category-card">
      <div class="signup-header">
        <h2>관심 카테고리 선택</h2>
        <p class="subtitle">관심 카테고리를 선택해주세요</p>
      </div>

      <div class="category-selection-container">
        <!-- Left Panel: Selected Slots -->
        <div class="category-slots">
          <div 
            v-for="(cat, idx) in selectedCategories" 
            :key="idx" 
            class="category-slot"
          >
            <div class="slot-label">관심 카테고리 {{ idx + 1 }}</div>
            <div 
              class="slot-box" 
              :class="{ active: activeSelection.index === idx && activeSelection.type === 'major' }"
              @click="setActiveSelection(idx, 'major')"
            >
              {{ cat.major || '대분류 선택' }}
            </div>
            <div 
              class="slot-box minor" 
              :class="{ active: activeSelection.index === idx && activeSelection.type === 'minor', disabled: !cat.major }"
              @click="cat.major ? setActiveSelection(idx, 'minor') : null"
            >
              {{ cat.minor || '소분류 선택' }}
            </div>
          </div>
        </div>

        <!-- Right Panel: Selection List -->
        <div class="category-options-panel">
          <h3>
            {{ activeSelection.type === 'major' ? '대분류 선택창' : '소분류 선택창' }}
            <span v-if="activeSelection.type === 'minor' && selectedCategories[activeSelection.index].major">
              ({{ selectedCategories[activeSelection.index].major }})
            </span>
          </h3>
          <div class="options-grid">
            <button 
              v-for="item in currentCategoryList" 
              :key="item"
              class="option-btn"
              :class="{ selected: activeSelection.type === 'major' ? selectedCategories[activeSelection.index].major === item : selectedCategories[activeSelection.index].minor === item }"
              @click="selectCategoryItem(item)"
            >
              {{ item }}
            </button>
            <div v-if="currentCategoryList.length === 0" class="empty-options">
              대분류를 먼저 선택해주세요.
            </div>
          </div>
        </div>
      </div>

      <div class="btn-group">
        <button class="btn-outline" @click="step = 2">뒤로가기</button>
        <button class="btn-primary" @click="submitSignup">가입하기</button>
      </div>
    </div>

    <!-- Step 4: Complete -->
    <div v-else-if="step === 4" class="signup-card center-card">
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

.birth-inputs > * {
  flex: 1;
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

/* Category Selection UI */
.category-card {
  max-width: 800px;
}

.category-selection-container {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
  min-height: 350px;
}

.category-slots {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.category-slot {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.slot-label {
  font-size: 0.9rem;
  font-weight: bold;
  color: var(--text-color);
  margin-bottom: 5px;
}

.slot-box {
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  background-color: #f9f9f9;
  transition: all 0.2s;
  font-size: 0.95rem;
}

.slot-box:hover:not(.disabled) {
  border-color: var(--primary-color);
  background-color: #f0f7ff;
}

.slot-box.active {
  border-color: var(--primary-color);
  background-color: #e6f0ff;
  font-weight: bold;
  color: var(--primary-color);
}

.slot-box.minor {
  margin-top: 2px;
}

.slot-box.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background-color: #eee;
}

.category-options-panel {
  flex: 2;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  background-color: #fff;
  display: flex;
  flex-direction: column;
}

.category-options-panel h3 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 1.1rem;
  color: #333;
  text-align: center;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 10px;
  align-content: start;
  flex-grow: 1;
}

.option-btn {
  padding: 12px 10px;
  border: 1px solid #ccc;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.option-btn:hover {
  background-color: #f0f0f0;
}

.option-btn.selected {
  background-color: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

.empty-options {
  grid-column: 1 / -1;
  text-align: center;
  color: #888;
  margin-top: 40px;
}
</style>
