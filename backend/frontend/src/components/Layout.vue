<template>
  <el-container style="height: 100vh">
    <el-header class="header" style="display:flex;align-items:center;justify-content:space-between;background:#001529;color:#fff;padding:0 20px">
      <div style="display:flex;align-items:center;gap:12px">
        <el-icon :size="28"><Ship /></el-icon>
        <span style="font-size:18px;font-weight:600">GTCS 全球贸易通关系统</span>
      </div>
      <div style="display:flex;align-items:center;gap:16px">
        <el-tag size="small" type="warning" v-if="user?.role">{{ user.role }}</el-tag>
        <span>{{ user?.display_name || user?.username }}</span>
        <el-button size="small" type="danger" plain @click="logout">退出</el-button>
      </div>
    </el-header>
    <el-container style="height: calc(100vh - 60px)">
      <el-aside width="220px" style="background:#001529;overflow-y:auto">
        <el-menu :default-active="route.path" router background-color="#001529" text-color="#fff" active-text-color="#409EFF">
          <el-menu-item index="/dashboard"><el-icon><Monitor /></el-icon><span>工作台</span></el-menu-item>
          <el-menu-item index="/tariff"><el-icon><Search /></el-icon><span>税则查询</span></el-menu-item>
          <el-menu-item index="/fta"><el-icon><TrendCharts /></el-icon><span>FTA 优选</span></el-menu-item>
          <el-menu-item index="/cost"><el-icon><Money /></el-icon><span>成本模拟</span></el-menu-item>
          <el-menu-item index="/hs-classification"><el-icon><List /></el-icon><span>HS 归类</span></el-menu-item>
          <el-menu-item index="/price-risk"><el-icon><WarningFilled /></el-icon><span>价格风控</span></el-menu-item>
          <el-menu-item index="/origin"><el-icon><Connection /></el-icon><span>原产地评估</span></el-menu-item>
          <el-menu-item index="/declaration"><el-icon><Document /></el-icon><span>报关单</span></el-menu-item>
          <el-menu-item index="/enterprise"><el-icon><OfficeBuilding /></el-icon><span>企业管理</span></el-menu-item>
          <el-menu-item index="/product"><el-icon><Box /></el-icon><span>产品管理</span></el-menu-item>
          <el-menu-item index="/screening"><el-icon><Warning /></el-icon><span>受限制方筛查</span></el-menu-item>
          <el-menu-item index="/admin"><el-icon><Setting /></el-icon><span>系统设置</span></el-menu-item>
        </el-menu>
      </el-aside>
      <el-main style="background:#f0f2f5;overflow-y:auto;padding:20px">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../api/index.js'

const router = useRouter()
const route = useRoute()
const user = ref(null)

onMounted(async () => {
  try {
    const res = await api.profile()
    user.value = res.data
  } catch { }
})

function logout() {
  localStorage.removeItem('gtcs_token')
  router.push('/login')
}
</script>

<style scoped>
.el-menu { border-right: none; }
.el-menu-item { font-size: 14px; }
</style>
