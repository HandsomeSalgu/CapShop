<script setup>
import { useRoute, useRouter } from 'vue-router'
import AppBanner from '@/components/common/AppBanner.vue'

const route = useRoute()
const router = useRouter()

const menus = [
  { path: '/mypage/password-check', activePaths: ['/mypage/password-check', '/mypage/profile'], name: '회원 정보 수정' },
  { path: '/mypage/history', activePaths: ['/mypage/history'], name: '위시리스트/상품확인기록' }
]

const handleMenuClick = (path) => {
  if (path === '/mypage/history') {
    alert('준비 중입니다')
    return
  }
  router.push(path)
}
</script>

<template>
  <main class="mypage-layout">
    <AppBanner title="마이페이지" subtitle="나만의 쇼핑 정보를 확인하세요" bgImage="https://picsum.photos/1200/251" />

    <div class="container layout-container">
      <aside class="sidebar">
        <div class="filter-group">
          <h3 class="filter-title">마이페이지 메뉴</h3>
          <ul class="main-category-list">
            <li 
              v-for="menu in menus" 
              :key="menu.path"
              :class="{ active: menu.activePaths.includes(route.path) }"
              @click="handleMenuClick(menu.path)"
            >
              {{ menu.name }}
            </li>
          </ul>
        </div>
      </aside>

      <section class="main-content">
        <router-view></router-view>
      </section>
    </div>
  </main>
</template>

<style scoped>
/* Page Layout */
.mypage-layout {
  background-color: var(--background-color, #f8f9fa);
  min-height: 100vh;
  padding-bottom: 60px;
}

/* Container */
.layout-container {
  display: flex;
  gap: 30px;
  align-items: flex-start;
}

/* Sidebar */
.sidebar {
  width: 250px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.filter-group {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.03);
}

.filter-title {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 16px;
  color: #333;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

/* Menu List */
.main-category-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.main-category-list li {
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 6px;
  font-size: 14px;
  color: #555;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.main-category-list li:hover {
  background-color: #f0f4f8;
  color: #3498db;
}

.main-category-list li.active {
  background-color: #3498db;
  color: white;
  font-weight: 600;
}

/* Main Content Area */
.main-content {
  flex: 1;
  min-width: 0;
}
</style>
