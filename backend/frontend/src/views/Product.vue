<template>
  <div>
    <h2>商品管理</h2>

    <el-card shadow="never">
      <template #header>
        <span>商品列表</span>
        <el-button type="primary" size="small" style="float:right" @click="showDialog = true">新建商品</el-button>
      </template>

      <el-form :inline="true" style="margin-bottom:12px">
        <el-form-item label="企业">
          <el-select v-model="filterEnterprise" filterable clearable style="width:200px" @change="load">
            <el-option v-for="e in enterprises" :key="e.id" :label="e.name_cn" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input v-model="filterQuery" placeholder="产品代码/名称" clearable @keyup.enter="load" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="load">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="products" border stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="product_code" label="产品代码" width="150" />
        <el-table-column prop="name_cn" label="中文名称" width="200" show-overflow-tooltip />
        <el-table-column prop="name_en" label="英文名称" width="200" show-overflow-tooltip />
        <el-table-column prop="brand" label="品牌" width="120" />
        <el-table-column prop="model" label="型号" width="120" />
        <el-table-column prop="unit" label="单位" width="80" />
      </el-table>

      <el-empty v-if="!products.length && !loading" description="暂无商品数据" />
    </el-card>

    <el-dialog v-model="showDialog" title="新建商品" width="550px">
      <el-form :model="form" label-width="120px">
        <el-form-item label="所属企业" required>
          <el-select v-model="form.enterprise_id" filterable style="width:100%">
            <el-option v-for="e in enterprises" :key="e.id" :label="e.name_cn" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="产品代码" required>
          <el-input v-model="form.product_code" placeholder="如 PROD-001" />
        </el-form-item>
        <el-form-item label="中文名称" required>
          <el-input v-model="form.name_cn" />
        </el-form-item>
        <el-form-item label="英文名称">
          <el-input v-model="form.name_en" />
        </el-form-item>
        <el-form-item label="品牌">
          <el-input v-model="form.brand" />
        </el-form-item>
        <el-form-item label="型号">
          <el-input v-model="form.model" />
        </el-form-item>
        <el-form-item label="规格">
          <el-input v-model="form.specifications" />
        </el-form-item>
        <el-form-item label="单位">
          <el-select v-model="form.unit" style="width:100%">
            <el-option label="件 (PCS)" value="PCS" />
            <el-option label="千克 (KG)" value="KG" />
            <el-option label="吨 (TON)" value="TON" />
            <el-option label="升 (LTR)" value="LTR" />
            <el-option label="平方米 (M2)" value="M2" />
            <el-option label="米 (MTR)" value="MTR" />
            <el-option label="套 (SET)" value="SET" />
          </el-select>
        </el-form-item>
        <el-form-item label="单价(USD)">
          <el-input-number v-model="form.unit_price" :min="0" :step="0.01" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="create" :loading="creating">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api/index.js'

const products = ref([])
const enterprises = ref([])
const loading = ref(false)
const showDialog = ref(false)
const creating = ref(false)
const filterEnterprise = ref(null)
const filterQuery = ref('')

const form = ref({
  enterprise_id: null, product_code: '', name_cn: '', name_en: '',
  brand: '', model: '', specifications: '', unit: 'PCS', unit_price: null,
})

async function load() {
  loading.value = true
  try {
    const params = { limit: 50 }
    if (filterEnterprise.value) params.enterprise_id = filterEnterprise.value
    if (filterQuery.value) params.query = filterQuery.value
    const res = await api.productList(params)
    products.value = res.data?.items || res.data || []
  } catch {
    products.value = []
  }
  loading.value = false
}

async function loadEnterprises() {
  try {
    const res = await api.enterpriseList({ limit: 100 })
    enterprises.value = res.data?.items || res.data || []
  } catch {
    enterprises.value = []
  }
}

async function create() {
  if (!form.value.enterprise_id) {
    ElMessage.warning('请选择所属企业')
    return
  }
  if (!form.value.product_code) {
    ElMessage.warning('请输入产品代码')
    return
  }
  if (!form.value.name_cn) {
    ElMessage.warning('请输入产品中文名称')
    return
  }
  creating.value = true
  try {
    await api.productCreate(form.value)
    ElMessage.success('创建成功')
    showDialog.value = false
    form.value = { enterprise_id: null, product_code: '', name_cn: '', name_en: '', brand: '', model: '', specifications: '', unit: 'PCS', unit_price: null }
    load()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '创建失败')
  }
  creating.value = false
}

onMounted(() => {
  loadEnterprises()
  load()
})
</script>
