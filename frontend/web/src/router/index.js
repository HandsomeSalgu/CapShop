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
          redirect: '/mypage/password-check'
        },
        {
          path: 'password-check',
          name: 'passwordCheck',
          component: () => import('../views/mypage/PasswordCheckView.vue'),
        },
        {
          path: 'profile',
          name: 'profileEdit',
          component: () => import('../views/mypage/ProfileEditView.vue'),
          beforeEnter: (to, from, next) => {
            if (sessionStorage.getItem('passwordVerified') === 'true') {
              next()
            } else {
              next('/mypage/password-check')
            }
          }
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

export default router
