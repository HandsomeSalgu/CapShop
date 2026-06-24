<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter, useRoute } from 'vue-router'
import logoImage from '@/assets/logo.png'

const emit = defineEmits(['open-search'])
const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()
const isDropdownOpen = ref(false)

const isHomePage = computed(() => route.path === '/')

const isSticky = ref(false)
const gnbRef = ref(null)
const gnbWrapperHeight = ref('auto')
const headerTopHeight = ref(0)

const calculateHeaderHeight = () => {
  const headerTop = document.querySelector('.header-top')
  if (headerTop) {
    headerTopHeight.value = headerTop.offsetHeight + 50 // header padding-top 50px
  } else {
    headerTopHeight.value = 125
  }
}

const handleScroll = () => {
  if (window.scrollY > headerTopHeight.value) {
    if (!isSticky.value) {
      gnbWrapperHeight.value = gnbRef.value ? `${gnbRef.value.offsetHeight}px` : 'auto'
      isSticky.value = true
    }
  } else {
    if (isSticky.value) {
      isSticky.value = false
      gnbWrapperHeight.value = 'auto'
    }
  }
}

onMounted(() => {
  calculateHeaderHeight()
  window.addEventListener('resize', calculateHeaderHeight)
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('resize', calculateHeaderHeight)
  window.removeEventListener('scroll', handleScroll)
})

const handleLogout = () => {
  authStore.logout()
  isDropdownOpen.value = false
  router.push('/')
}

const alertPreparing = () => {
  alert('준비 중입니다')
  isDropdownOpen.value = false
}

void alertPreparing

const goToMyPage = () => {
  isDropdownOpen.value = false
  router.push('/mypage/profile')
}

const goToAdminPage = () => {
  isDropdownOpen.value = false
  router.push('/admin/dashboard')
}
</script>

<template>
  <header :class="{ 'absolute-header': isHomePage }">
    <div class="container">
      <div class="header-top">
        <div class="welcome-msg">스크린샷으로 찾는 똑같은 상품 추천</div>
        <RouterLink to="/" class="logo" style="text-decoration: none;">
          <img :src="logoImage" alt="CapShop Logo" />
        </RouterLink>
        <div class="header-utils">
          <span @click="emit('open-search')" id="search-btn">
            <i class="fa-solid fa-magnifying-glass"></i> 검색
          </span>
          <RouterLink to="/mypage/history" class="cart-link">
            <i class="fa-solid fa-cart-shopping"></i> 장바구니
          </RouterLink>
          
          <template v-if="authStore.isLoggedIn">
            <div class="profile-container" @click="isDropdownOpen = !isDropdownOpen">
              <img 
                v-if="authStore.userInfo?.profileImageUrl" 
                :src="authStore.userInfo.profileImageUrl" 
                alt="Profile" 
                class="profile-img"
              />
              <div v-else class="profile-empty"></div>
              
              <div v-show="isDropdownOpen" class="profile-dropdown">
                <div class="dropdown-item" @click="goToMyPage">마이페이지</div>
                <div v-if="authStore.userInfo?.role === 'ADMIN'" class="dropdown-item text-primary fw-bold" @click="goToAdminPage">관리자 페이지</div>
                <div class="dropdown-item text-danger" @click="handleLogout">로그아웃</div>
              </div>
            </div>
          </template>
          
          <template v-else>
            <RouterLink to="/login" class="login-link">
              <i class="fa-regular fa-user"></i> 로그인
            </RouterLink>
          </template>
        </div>
      </div>
      <div class="gnb-wrapper" :style="{ height: gnbWrapperHeight }">
        <nav class="gnb" :class="{ sticky: isSticky }" ref="gnbRef">
          <RouterLink to="/best">베스트 상품리스트</RouterLink>
          <RouterLink to="/ai-recommend">AI 추천 상품리스트</RouterLink>
          <RouterLink to="/category">전체 카테고리</RouterLink>
          <a href="#">크롬 익스텐션 설치</a>
          <RouterLink to="/board">공지사항/FAQ</RouterLink>
          <a href="#">이벤트</a>
        </nav>
      </div>
    </div>
  </header>
</template>

<style scoped>
header {
  border-bottom: 1px solid var(--border-color);
  padding-top: 50px;
}

header.absolute-header {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  z-index: 100;
  border-bottom: none;
  background-color: transparent;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 40px;
}

.welcome-msg {
  flex: 1;
  font-size: 13px;
  color: var(--text-muted);
}

.logo {
  flex: 1;
  text-align: center;
  display: flex;
  justify-content: center;
  align-items: center;
}

.logo img {
  max-height: 35px;
  object-fit: contain;
}

.header-utils {
  flex: 1;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 25px;
  font-size: 14px;
  font-weight: 500;
}

.header-utils span,
.header-utils .login-link,
.header-utils .cart-link {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: color 0.3s;
  text-decoration: none;
  color: inherit;
}

.header-utils span:hover,
.header-utils .login-link:hover,
.header-utils .cart-link:hover {
  color: var(--accent-color);
}

.gnb {
  display: flex;
  justify-content: center;
  gap: 55px;
  padding: 20px 0;
}

.gnb a {
  font-size: 13px;
  font-weight: 500;
  position: relative;
}

.gnb a::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: -5px;
  width: 0;
  height: 2px;
  background-color: var(--primary-color);
  transition: width 0.3s;
}

.gnb a:hover::after {
  width: 100%;
}

.gnb.sticky {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  background-color: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  z-index: 1000;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
  animation: slideDown 0.3s ease-out;
  padding: 30px 0;
}

@keyframes slideDown {
  from { transform: translateY(-100%); }
  to { transform: translateY(0); }
}

.profile-container {
  position: relative;
  display: flex;
  align-items: center;
  cursor: pointer;
}

.profile-img, .profile-empty {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid var(--border-color);
}

.profile-empty {
  background-color: #ffffff;
}

.profile-dropdown {
  position: absolute;
  top: 45px;
  right: 0;
  width: 120px;
  background-color: #ffffff;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  z-index: 100;
  display: flex;
  flex-direction: column;
}

.dropdown-item {
  padding: 12px 15px;
  font-size: 13px;
  color: var(--text-color);
  transition: background-color 0.2s;
  text-align: center;
}

.dropdown-item:hover {
  background-color: #f5f5f5;
}

.text-danger {
  color: #d9534f;
}

.text-danger:hover {
  background-color: #ffeaea;
}

.text-primary {
  color: var(--primary-color, #4361ee);
}

.fw-bold {
  font-weight: bold;
}
</style>
