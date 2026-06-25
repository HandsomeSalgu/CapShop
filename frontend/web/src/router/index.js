import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
    },
    {
      path: '/signup',
      name: 'signup',
      component: () => import('../views/SignupView.vue'),
    },
    {
      path: '/oauth/callback',
      name: 'oauthCallback',
      component: () => import('../views/OAuthCallbackView.vue'),
    },
    {
      path: '/find-account',
      name: 'findAccount',
      component: () => import('../views/FindAccountView.vue'),
    },
    {
      path: '/best',
      name: 'best',
      component: () => import('../views/BestProductsView.vue'),
    },
    {
      path: '/category',
      name: 'category',
      component: () => import('../views/CategoryView.vue'),
    },
    {
      path: '/ai-recommend',
      name: 'aiRecommend',
      component: () => import('../views/AiRecommendView.vue'),
    },
    {
      path: '/product/:id',
      name: 'productDetail',
      component: () => import('../views/ProductDetailView.vue'),
    },
    {
      path: '/board',
      name: 'board',
      component: () => import('../views/BoardView.vue'),
    },
    {
      path: '/mypage',
      component: () => import('../views/MyPageView.vue'),
      children: [
        {
          path: '',
          redirect: '/mypage/profile'
        },
        {
          path: 'profile',
          name: 'profileEdit',
          component: () => import('../views/mypage/ProfileEditView.vue'),
        },
        {
          path: 'history',
          name: 'history',
          component: () => import('../views/mypage/HistoryView.vue'),
        }
      ]
    },
    {
      path: '/admin',
      component: () => import('../views/admin/AdminLayout.vue'),
      children: [
        {
          path: 'dashboard',
          name: 'adminDashboard',
          component: () => import('../views/admin/AdminDashboardView.vue'),
        },
        {
          path: 'board',
          name: 'adminBoard',
          component: () => import('../views/admin/AdminBoardView.vue'),
        },
        {
          path: 'board/write',
          name: 'adminBoardWrite',
          component: () => import('../views/admin/AdminBoardWriteView.vue'),
        },
        {
          path: 'board/edit/:id',
          name: 'adminBoardEdit',
          component: () => import('../views/admin/AdminBoardWriteView.vue'),
        },
        {
          path: 'user',
          name: 'adminUser',
          component: () => import('../views/admin/AdminUserView.vue'),
        }
      ]
    }
  ],
})

router.beforeEach((to, from, next) => {
  const isAuthenticated = !!localStorage.getItem('accessToken')
  
  const authRequiredRoutes = ['login', 'signup', 'findAccount']
  
  if (isAuthenticated && authRequiredRoutes.includes(to.name)) {
    next('/')
  } else {
    next()
  }
})

export default router
