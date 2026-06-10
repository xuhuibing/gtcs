<template>
  <div style="display:flex;justify-content:center;align-items:center;height:100vh;background:#001529">
    <el-card style="width:400px;padding:20px">
      <h2 style="text-align:center;margin-bottom:24px">GTCS 全球贸易通关系统</h2>
      <el-form :model="form" @submit.prevent="login">
        <el-form-item label="用户名">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading" style="width:100%">登录</el-button>
        </el-form-item>
      </el-form>
      <div style="text-align:center;color:#999;font-size:12px">默认: admin / admin123</div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api/index.js'

const router = useRouter()
const loading = ref(false)
const form = reactive({ username: 'admin', password: 'admin123' })

async function login() {
  loading.value = true
  try {
    const res = await api.login(form)
    localStorage.setItem('gtcs_token', res.data.access_token)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch { }
  loading.value = false
}
</script>
