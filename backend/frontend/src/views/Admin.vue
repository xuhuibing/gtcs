<template>
  <div>
    <h2>系统设置</h2>
    <el-row :gutter="16">
      <el-col :span="12">
        <el-card>
          <template #header><span>系统信息</span></template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="系统名称">GTCS 全球贸易通关系统</el-descriptions-item>
            <el-descriptions-item label="版本">v2.0.0</el-descriptions-item>
            <el-descriptions-item label="运行状态">
              <el-tag type="success">运行中</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="数据库规模">{{ dbSize }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span>数据概览</span></template>
          <el-table :data="stats" border size="small">
            <el-table-column prop="item" label="项目" />
            <el-table-column prop="value" label="数量" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top:16px">
      <template #header><span>API 测试</span></template>
      <el-space wrap>
        <el-button @click="testApi('/health')">健康检查</el-button>
        <el-button @click="testApi('/api/v1/tariff/lookup?hs_code=8528420000&dest_country=US')">税则查询</el-button>
        <el-button @click="testApi('/api/v1/fta/recommend?hs_code=8528420000&origin=CN&dest=US')">FTA推荐</el-button>
        <el-button @click="testApi('/api/v1/cost/simulate', 'post', {hs_code:'8528420000',origin_country:'CN',dest_country:'US',fob_unit_price:100,quantity:1000,freight:2000,insurance:500})">成本模拟</el-button>
        <el-button @click="testApi('/api/v1/origin/profiles')">原产地档案</el-button>
        <el-button @click="testApi('/api/v1/declaration/list')">报关单列表</el-button>
      </el-space>
      <pre v-if="apiResult" style="margin-top:12px;background:#f5f5f5;padding:12px;border-radius:4px;max-height:300px;overflow:auto;font-size:12px">{{ JSON.stringify(apiResult, null, 2) }}</pre>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const stats = ref([])
const dbSize = ref('--')
const apiResult = ref(null)

async function testApi(url, method = 'get', data = null) {
  try {
    const token = localStorage.getItem('gtcs_token')
    const config = { headers: token ? { Authorization: `Bearer ${token}` } : {} }
    let res
    if (method === 'post') res = await axios.post(url, data, config)
    else res = await axios.get(url, config)
    apiResult.value = res.data
  } catch (e) {
    apiResult.value = { error: e.message, detail: e.response?.data }
  }
}

onMounted(async () => {
  stats.value = [
    { item: '国家', value: '15' },
    { item: 'FTA协定', value: '8' },
    { item: '关税税目', value: '71,960+' },
    { item: '税种记录', value: '36,862+' },
  ]
  try {
    const res = await axios.get('/health')
    dbSize.value = `运行中 | API v${res.data.version}`
  } catch { }
})
</script>
