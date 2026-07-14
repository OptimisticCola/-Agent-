// ============================================
// Vue Router 路由配置
// ============================================
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/App.vue'),
    },
    {
      path: '/chat/:sessionId?',
      name: 'chat',
      component: () => import('@/App.vue'),
    },
  ],
})

export default router
