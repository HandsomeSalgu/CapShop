<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goBackToMain = () => {
  router.push('/')
}
</script>

<template>
  <div class="admin-dashboard">
    <!-- LNB (Left Navigation Bar) -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <h2 class="logo-text">Fillow.</h2>
        <span class="logo-sub">Super Admin Dashboard</span>
      </div>
      
      <nav class="sidebar-nav">
        <ul>
          <li class="menu-item">
            <a href="#" class="menu-link" @click.prevent>
              <i class="fa-solid fa-chart-pie menu-icon"></i>
              <span>Dashboard</span>
            </a>
          </li>
          <li class="menu-item">
            <a href="#" class="menu-link" @click.prevent>
              <i class="fa-regular fa-user menu-icon"></i>
              <span>User</span>
            </a>
          </li>
          <li class="menu-item active">
            <RouterLink to="/admin/board" class="menu-link">
              <i class="fa-solid fa-list menu-icon"></i>
              <span>Board Post</span>
            </RouterLink>
          </li>
        </ul>
      </nav>
    </aside>

    <!-- Main Content Area -->
    <div class="main-content">
      <!-- Top Bar -->
      <header class="top-bar">
        <div class="header-left">
          <button class="hamburger-btn">
            <i class="fa-solid fa-bars"></i>
          </button>
        </div>
        <div class="header-right">
          <button class="return-btn" @click="goBackToMain">
            <i class="fa-solid fa-house"></i> 기존 서비스 화면으로 이동
          </button>
        </div>
      </header>

      <!-- Page Content -->
      <main class="page-wrapper">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.admin-dashboard {
  display: flex;
  height: 100vh;
  background-color: #f4f5f9; /* Fillow 레퍼런스 스타일의 밝은 배경 */
  font-family: 'Inter', sans-serif;
  overflow: hidden;
}

/* Sidebar Styles */
.sidebar {
  width: 260px;
  background-color: #ffffff;
  box-shadow: 0 0 15px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  z-index: 10;
}

.sidebar-header {
  padding: 30px 25px;
  border-bottom: 1px solid #f0f0f0;
}

.logo-text {
  font-size: 28px;
  font-weight: 800;
  color: #3b4cb8; /* 메인 테마 색상 */
  margin: 0;
  letter-spacing: -0.5px;
}

.logo-sub {
  font-size: 11px;
  color: #888;
  font-weight: 500;
}

.sidebar-nav {
  padding: 20px 0;
  flex: 1;
  overflow-y: auto;
}

.sidebar-nav ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.menu-item {
  margin-bottom: 5px;
}

.menu-link {
  display: flex;
  align-items: center;
  padding: 15px 30px;
  color: #6e6e6e;
  text-decoration: none;
  font-size: 15px;
  font-weight: 500;
  transition: all 0.3s;
  border-left: 4px solid transparent;
}

.menu-link:hover {
  color: #3b4cb8;
  background-color: #f8f9fe;
}

.menu-icon {
  width: 24px;
  margin-right: 15px;
  font-size: 18px;
}

.menu-item.active .menu-link {
  color: #3b4cb8;
  background-color: #f8f9fe;
  border-left-color: #3b4cb8;
  font-weight: 600;
}

/* Main Content Styles */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Top Bar Styles */
.top-bar {
  height: 70px;
  background-color: #ffffff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 30px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.02);
  z-index: 5;
}

.hamburger-btn {
  background: none;
  border: none;
  font-size: 20px;
  color: #555;
  cursor: pointer;
}

.return-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background-color: #f0f2f5;
  color: #333;
  border: 1px solid #e1e3e8;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.return-btn:hover {
  background-color: #e4e6eb;
}

.page-wrapper {
  flex: 1;
  padding: 30px;
  overflow-y: auto;
}
</style>
