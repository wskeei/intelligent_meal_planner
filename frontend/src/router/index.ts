import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue')
    },
    {
      path: '/meal-plan',
      name: 'meal-plan',
      component: () => import('@/views/MealPlanView.vue')
    },
    {
      path: '/recipes',
      name: 'recipes',
      component: () => import('@/views/RecipesView.vue')
    },
    {
      path: '/shopping-list',
      name: 'shopping-list',
      component: () => import('@/views/ShoppingListView.vue')
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/ProfileView.vue')
    },
    {
      path: '/history',
      name: 'history',
      component: () => import('@/views/HistoryView.vue')
    }
  ]
})

export default router