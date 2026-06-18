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
      path: '/category',
      name: 'category',
      component: () => import('../views/CategoryView.vue'),
    },
    {
      path: '/product/:id',
      name: 'productDetail',
      component: () => import('../views/ProductDetailView.vue'),
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
    }
  ],
})

export default router
