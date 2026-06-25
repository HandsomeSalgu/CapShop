<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, onBeforeRouteLeave } from 'vue-router'
import axios from 'axios'
import { Cropper } from 'vue-advanced-cropper'
import 'vue-advanced-cropper/dist/style.css'
import { useAuthStore } from '@/stores/auth'

onBeforeRouteLeave(() => {
  sessionStorage.removeItem('passwordVerified')
})

const router = useRouter()
const authStore = useAuthStore()

// Data for logged-in user
const isSocialLogin = ref(false)
const email = ref('')
const name = ref('')
const phone = ref('')
const birthYear = ref('')
const birthMonth = ref('')
const birthDay = ref('')

const profileImageUrl = ref(null)
const profileImageFile = ref(null)
const fileInput = ref(null)

const isCropperModalOpen = ref(false)
const rawImage = ref(null)
const cropperRef = ref(null)

const triggerFileInput = () => {
  if (!isSocialLogin.value) {
    fileInput.value.click()
  }
}

const onFileChange = (event) => {
  const file = event.target.files[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      rawImage.value = e.target.result
      isCropperModalOpen.value = true
    }
    reader.readAsDataURL(file)
  }
}

const applyCrop = () => {
  if (cropperRef.value) {
    const { canvas } = cropperRef.value.getResult()
    if (canvas) {
      profileImageUrl.value = canvas.toDataURL('image/jpeg')
      canvas.toBlob((blob) => {
        const file = new File([blob], 'profile.jpg', { type: 'image/jpeg' })
        profileImageFile.value = file
      }, 'image/jpeg')
    }
  }
  isCropperModalOpen.value = false
  // Reset input value to allow selecting same file again
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const cancelCrop = () => {
  isCropperModalOpen.value = false
  rawImage.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const password = ref('')
const passwordMsg = ref('')
const passwordMsgType = ref('')

const passwordConfirm = ref('')
const passwordConfirmMsg = ref('')
const passwordConfirmMsgType = ref('')

const formErrorMsg = ref('')

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

const fetchMyProfile = async () => {
  try {
    const token = localStorage.getItem('accessToken')
    const res = await axios.get('/api/users/me', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
    const data = res.data.data
    email.value = data.email
    name.value = data.nickname
    phone.value = data.phone
    isSocialLogin.value = data.provider !== 'LOCAL'
    profileImageUrl.value = data.profileImageUrl
    
    if (data.birthDate) {
      const [year, month, day] = data.birthDate.split('-')
      birthYear.value = year
      birthMonth.value = month
      birthDay.value = day
    }
  } catch (error) {
    console.error('Failed to fetch profile', error)
  }
}

onMounted(() => {
  fetchMyProfile()
})

const submitEdit = async () => {
  if (!isSocialLogin.value && password.value) {
    if (passwordMsgType.value !== 'success') {
      formErrorMsg.value = '새 비밀번호를 올바르게 입력해주세요.'
      return
    }
    if (passwordConfirmMsgType.value !== 'success') {
      formErrorMsg.value = '새 비밀번호가 일치하지 않습니다.'
      return
    }
  }

  if (!name.value || !phone.value || !birthYear.value || !birthMonth.value || !birthDay.value) {
    formErrorMsg.value = '모든 항목을 입력해주세요.'
    return
  }
  
  const paddedMonth = birthMonth.value.padStart(2, '0')
  const paddedDay = birthDay.value.padStart(2, '0')
  const birthDateStr = `${birthYear.value}-${paddedMonth}-${paddedDay}`

  const payload = {
    nickname: name.value,
    phone: phone.value,
    birthDate: birthDateStr,
    newPassword: password.value || null,
    confirmNewPassword: passwordConfirm.value || null
  }

  const formData = new FormData()
  formData.append('request', new Blob([JSON.stringify(payload)], { type: 'application/json' }))
  
  if (profileImageFile.value) {
    formData.append('profileImage', profileImageFile.value)
  }

  try {
    const token = localStorage.getItem('accessToken')
    const res = await axios.patch('/api/users/me', formData, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
    
    const updatedUser = res.data.data
    if (authStore.userInfo) {
      authStore.userInfo.nickname = updatedUser.nickname
      authStore.userInfo.profileImageUrl = updatedUser.profileImageUrl
      localStorage.setItem('userInfo', JSON.stringify(authStore.userInfo))
    }

    formErrorMsg.value = ''
    alert('회원정보가 성공적으로 수정되었습니다.')
    router.push('/')
  } catch (error) {
    if (error.response && error.response.data && error.response.data.message) {
      formErrorMsg.value = error.response.data.message
    } else {
      formErrorMsg.value = '회원정보 수정 중 오류가 발생했습니다.'
    }
  }
}

const cancelEdit = () => {
  if (confirm('수정을 취소하시겠습니까? 작성 중인 내용이 사라집니다.')) {
    router.push('/')
  }
}
</script>

<template>
  <div class="profile-edit-card">
    <div class="signup-header">
      <h2>회원 정보 수정</h2>
      <p class="subtitle">개인정보를 최신 상태로 유지해주세요</p>
    </div>

    <div class="profile-image-section">
      <div class="profile-image-wrapper" :class="{ 'clickable': !isSocialLogin }" @click="triggerFileInput">
        <img :src="profileImageUrl || '/src/assets/images/basic_image/Basic_image1.jpeg'" alt="Profile" class="profile-image">
        <div v-if="!isSocialLogin" class="camera-icon">
          <span>변경</span>
        </div>
      </div>
      <input type="file" ref="fileInput" @change="onFileChange" accept="image/*" style="display: none;">
      <p v-if="isSocialLogin" class="social-notice">소셜 로그인 계정은 프로필 사진을 변경할 수 없습니다.</p>
    </div>

    <div class="form-group">
      <div class="label-row">
        <label>이메일</label>
      </div>
      <input type="text" :value="email" disabled class="form-input readonly-input">
    </div>

    <div class="form-group" v-if="!isSocialLogin">
      <div class="label-row">
        <label>새 비밀번호</label>
        <span v-if="passwordMsg" :class="passwordMsgType === 'error' ? 'msg-error' : 'msg-success'">
          {{ passwordMsg }}
        </span>
      </div>
      <input type="password" v-model="password" @blur="validatePassword" placeholder="비밀번호 입력(문자, 숫자, 특수문자 포함 8~20자)" class="form-input">
    </div>

    <div class="form-group" v-if="!isSocialLogin">
      <div class="label-row">
        <label>새 비밀번호 확인</label>
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
      <input type="text" v-model="phone" placeholder="휴대폰 번호 입력('-' 제외 11자리 입력)" class="form-input" maxlength="11" oninput="this.value = this.value.replace(/[^0-9]/g, '')">
    </div>

    <div class="form-group">
      <label>생년월일</label>
      <div class="birth-inputs">
        <input type="text" v-model="birthYear" placeholder="년도" class="form-input" maxlength="4" oninput="this.value = this.value.replace(/[^0-9]/g, '')">
        <input type="text" v-model="birthMonth" placeholder="월" class="form-input" maxlength="2" oninput="this.value = this.value.replace(/[^0-9]/g, '')">
        <input type="text" v-model="birthDay" placeholder="일" class="form-input" maxlength="2" oninput="this.value = this.value.replace(/[^0-9]/g, '')">
      </div>
    </div>

    <div v-if="formErrorMsg" class="error-msg">
      {{ formErrorMsg }}
    </div>

    <div class="btn-group">
      <button class="btn-primary" @click="submitEdit">수정하기</button>
      <button class="btn-outline" @click="cancelEdit">수정취소</button>
    </div>

    <!-- Image Cropper Modal -->
    <div v-if="isCropperModalOpen" class="cropper-modal-overlay">
      <div class="cropper-modal-content">
        <h3>프로필 이미지 조정</h3>
        <div class="cropper-container">
          <Cropper
            ref="cropperRef"
            :src="rawImage"
            :stencil-props="{ aspectRatio: 1 }"
            class="cropper"
          />
        </div>
        <div class="cropper-actions">
          <button class="btn-outline" @click="cancelCrop">취소</button>
          <button class="btn-primary" @click="applyCrop">적용하기</button>
        </div>
      </div>
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

.subtitle {
  font-size: 14px;
  color: var(--text-muted, #888);
}

.profile-image-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 30px;
}

.profile-image-wrapper {
  position: relative;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid #eee;
}

.profile-image-wrapper.clickable {
  cursor: pointer;
  transition: opacity 0.2s;
}

.profile-image-wrapper.clickable:hover {
  opacity: 0.8;
}

.profile-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.camera-icon {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  background: rgba(0,0,0,0.5);
  color: white;
  text-align: center;
  padding: 6px 0;
  font-size: 13px;
  font-weight: 600;
}

.social-notice {
  margin-top: 12px;
  font-size: 13px;
  color: #888;
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
  border: 1px solid #ddd;
  border-radius: 6px;
  outline: none;
  transition: border-color 0.3s;
  font-family: inherit;
}

.form-input:focus {
  border-color: #3498db;
}

.readonly-input {
  background-color: #f5f5f5;
  color: #666;
  cursor: not-allowed;
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

.btn-outline {
  padding: 14px 40px;
  background-color: #ffffff;
  color: #555;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-outline:hover {
  background-color: #f5f5f5;
}

/* Cropper Modal Styles */
.cropper-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.cropper-modal-content {
  background: white;
  padding: 30px;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  text-align: center;
}

.cropper-modal-content h3 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #333;
}

.cropper-container {
  width: 100%;
  height: 350px;
  background: #f8f9fa;
  margin-bottom: 20px;
}

.cropper {
  height: 100%;
}

.cropper-actions {
  display: flex;
  justify-content: center;
  gap: 15px;
}
</style>
