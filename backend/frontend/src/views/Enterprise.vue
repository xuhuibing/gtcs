<template>
  <div>
    <h2>企业管理</h2>

    <el-card shadow="never">
      <template #header>
        <span>企业列表</span>
        <el-button type="primary" size="small" style="float:right" @click="showDialog = true">新建企业</el-button>
      </template>

      <el-table :data="enterprises" border stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name_cn" label="中文名称" width="200" show-overflow-tooltip />
        <el-table-column prop="name_en" label="英文名称" width="200" show-overflow-tooltip />
        <el-table-column prop="credit_code" label="统一信用代码" width="180" />
        <el-table-column prop="customs_code" label="海关编码" width="120" />
        <el-table-column prop="aeo_level" label="AEO等级" width="120">
          <template #default="{row}">
            <el-tag v-if="row.aeo_level" :type="row.aeo_level === 'ADVANCED' ? 'success' : 'warning'" size="small">
              {{ row.aeo_level }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="contact_person" label="联系人" width="120" />
      </el-table>

      <el-empty v-if="!enterprises.length && !loading" description="暂无企业数据" />
    </el-card>

    <el-dialog v-model="showDialog" title="新建企业" width="550px">
      <el-form :model="form" label-width="120px">
        <el-form-item label="中文名称" required>
          <el-input v-model="form.name_cn" />
        </el-form-item>
        <el-form-item label="英文名称">
          <el-input v-model="form.name_en" />
        </el-form-item>
        <el-form-item label="统一信用代码">
          <el-input v-model="form.credit_code" />
        </el-form-item>
        <el-form-item label="海关编码">
          <el-input v-model="form.customs_code" />
        </el-form-item>
        <el-form-item label="AEO等级">
          <el-select v-model="form.aeo_level" clearable style="width:100%">
            <el-option label="高级认证 (ADVANCED)" value="ADVANCED" />
            <el-option label="一般认证 (CERTIFIED)" value="CERTIFIED" />
            <el-option label="一般信用 (NORMAL)" value="NORMAL" />
          </el-select>
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="form.address" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="form.contact_person" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="form.contact_phone" />
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

const enterprises = ref([])
const loading = ref(false)
const showDialog = ref(false)
const creating = ref(false)
const form = ref({
  name_cn: '', name_en: '', credit_code: '', customs_code: '',
  aeo_level: '', address: '', contact_person: '', contact_phone: '',
})

async function load() {
  loading.value = true
  try {
    const res = await api.enterpriseList({ limit: 50 })
    enterprises.value = res.data?.items || res.data || []
  } catch {
    enterprises.value = []
  }
  loading.value = false
}

async function create() {
  if (!form.value.name_cn) {
    ElMessage.warning('请输入企业中文名称')
    return
  }
  creating.value = true
  try {
    await api.enterpriseCreate(form.value)
    ElMessage.success('创建成功')
    showDialog.value = false
    form.value = { name_cn: '', name_en: '', credit_code: '', customs_code: '', aeo_level: '', address: '', contact_person: '', contact_phone: '' }
    load()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '创建失败')
  }
  creating.value = false
}

onMounted(load)
</script>
