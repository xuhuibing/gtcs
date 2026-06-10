import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
  {
    path: '/',
    component: () => import('../components/Layout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
      { path: 'tariff', name: 'Tariff', component: () => import('../views/TariffLookup.vue') },
      { path: 'fta', name: 'FTA', component: () => import('../views/FTAOptimizer.vue') },
      { path: 'cost', name: 'Cost', component: () => import('../views/CostSimulator.vue') },
      { path: 'hs-classification', name: 'HSClassification', component: () => import('../views/HSClassification.vue') },
      { path: 'price-risk', name: 'PriceRisk', component: () => import('../views/PriceRisk.vue') },
      { path: 'origin', name: 'Origin', component: () => import('../views/OriginAssessment.vue') },
      { path: 'declaration', name: 'Declaration', component: () => import('../views/Declaration.vue') },
      { path: 'enterprise', name: 'Enterprise', component: () => import('../views/Enterprise.vue') },
      { path: 'product', name: 'Product', component: () => import('../views/Product.vue') },
      { path: 'screening', name: 'Screening', component: () => import('../views/Screening.vue') },
      { path: 'admin', name: 'Admin', component: () => import('../views/Admin.vue') },
    ],
  },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('gtcs_token')
  if (to.name !== 'Login' && !token) next({ name: 'Login' })
  else next()
})

export default router
