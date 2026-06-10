import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({ baseURL: '/api/v1' })

api.interceptors.request.use(config => {
  const token = localStorage.getItem('gtcs_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  resp => resp,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('gtcs_token')
      window.location.href = '/login'
    }
    ElMessage.error(error.response?.data?.detail || error.message)
    return Promise.reject(error)
  }
)

export default {
  // Auth
  login: data => api.post('/auth/login', data),
  register: data => api.post('/auth/register', data),
  profile: () => api.get('/auth/profile'),

  // Tariff
  tariffLookup: params => api.get('/tariff/lookup', { params }),
  tariffSearch: params => api.get('/tariff/search', { params: { q: params.query, country: params.country, limit: params.limit } }),
  tariffCountries: () => api.get('/tariff/countries'),
  tariffChapters: params => api.get('/tariff/chapters', { params }),
  tariffBrowse: params => api.get('/tariff/browse', { params }),

  // FTA
  ftaRecommend: params => api.get('/fta/recommend', { params }),
  ftaCompareOrigins: params => api.get('/fta/compare-origins', { params }),

  // Cost
  costSimulate: data => api.post('/cost/simulate', data),
  costEnterpriseSimulate: data => api.post('/cost/enterprise-simulate', data),
  costVatConfig: params => api.get('/cost/vat-config', { params }),
  costRequirements: params => api.get('/cost/requirements', { params }),

  // Additional Duty
  additionalDutyLookup: params => api.get('/additional-duty/lookup', { params }),

  // Price Risk
  priceRiskRecord: data => api.post('/price-risk/record', data),
  priceRiskBatch: data => api.post('/price-risk/batch', data),
  priceRiskHistory: params => api.get('/price-risk/history', { params }),
  priceRiskAlerts: params => api.get('/price-risk/alerts', { params }),
  priceRiskRecalculate: params => api.post('/price-risk/baseline/recalculate', null, { params }),

  // HS Classification
  hsClassCreate: data => api.post('/hs-classification/classify', data),
  hsClassSearch: params => api.get('/hs-classification/search', { params }),
  hsClassHistory: params => api.get('/hs-classification/history', { params }),
  hsRulingsSearch: params => api.get('/hs-classification/rulings', { params }),
  hsConsistencyCheck: params => api.get('/hs-classification/consistency-check', { params }),
  hsEnterpriseRecommend: data => api.post('/hs-classification/enterprise/recommend', data),
  hsEnterpriseClassify: data => api.post('/hs-classification/enterprise/classify', data),

  // Origin
  originAssess: params => api.get('/origin/assess', { params }),
  originProfiles: params => api.get('/origin/profiles', { params }),
  originRvcCalculate: profileId => api.post(`/origin/rvc/calculate/${profileId}`),
  originFullAssessment: profileId => api.post(`/origin/assess/${profileId}`),
  originAgreements: profileId => api.get(`/origin/assess/${profileId}/agreements`),
  originCtcCheck: params => api.post('/origin/ctc/check', null, { params }),

  // Declaration
  declarationCreate: data => api.post('/declaration/create', data),
  declarationList: params => api.get('/declaration/list', { params }),
  declarationGet: id => api.get(`/declaration/${id}`),
  declarationTransition: (id, params) => api.post(`/declaration/${id}/transition`, null, { params }),
  declarationActions: id => api.get(`/declaration/${id}/actions`),
  declarationCheck: id => api.post(`/declaration/${id}/check`),

  // Enterprise
  enterpriseList: params => api.get('/enterprise/list', { params }),
  enterpriseCreate: data => api.post('/enterprise/create', data),
  enterpriseGet: id => api.get(`/enterprise/${id}`),
  enterpriseUpdate: (id, data) => api.put(`/enterprise/${id}`, data),

  // Product
  productList: params => api.get('/product/list', { params }),
  productCreate: data => api.post('/product/create', data),
  productGet: id => api.get(`/product/${id}`),

  // Dashboard
  dashboardStats: () => api.get('/dashboard/stats'),

  // Audit
  auditLogs: params => api.get('/audit/logs', { params }),

  // Screening
  screeningCheck: data => api.post('/screening/check', data),
  screeningBatch: data => api.post('/screening/batch', data),
  screeningLists: () => api.get('/screening/lists'),
  screeningHistory: params => api.get('/screening/history', { params }),
}
