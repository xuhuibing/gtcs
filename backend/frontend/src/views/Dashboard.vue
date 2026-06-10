<template>
  <div>
    <h2>工作台</h2>

    <!-- KPI Cards -->
    <el-row :gutter="12" style="margin-bottom:12px">
      <el-col :span="4" v-for="c in kpiCards" :key="c.label">
        <el-card shadow="hover" :body-style="{padding:'12px'}">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div>
              <div style="font-size:22px;font-weight:700;color:#409EFF">{{ c.value }}</div>
              <div style="color:#999;font-size:12px;margin-top:2px">{{ c.label }}</div>
            </div>
            <el-icon :size="28" :color="c.color"><component :is="c.icon" /></el-icon>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="12">
      <!-- 各国税则数据 -->
      <el-col :span="12">
        <el-card shadow="never" style="margin-bottom:12px">
          <template #header><span style="font-weight:600">国家税则数据一览</span></template>
          <el-table :data="stats.tariff_by_country || []" size="small" stripe @row-click="goTariff">
            <el-table-column prop="iso2" label="代码" width="60" />
            <el-table-column prop="name_cn" label="国家" width="100" />
            <el-table-column prop="line_count" label="税则条目" align="right" />
            <el-table-column label="占比" width="120">
              <template #default="{row}">
                <el-progress :percentage="Math.round(row.line_count / totalTariffLines * 100)" :stroke-width="12" />
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12">
        <!-- 受限制方筛查概览 -->
        <el-card shadow="never" style="margin-bottom:12px">
          <template #header><span style="font-weight:600">受限制方筛查概览</span></template>
          <div style="display:flex;gap:24px;padding:8px 0" v-if="stats.screening_list_types">
            <div v-for="s in stats.screening_list_types" :key="s.list_type">
              <div style="font-size:22px;font-weight:700;color:#e6a23c">{{ s.count }}</div>
              <div style="font-size:12px;color:#909399">{{ s.list_type }}</div>
            </div>
            <div>
              <div style="font-size:22px;font-weight:700;color:#F56C6C">{{ stats.screening_high_risk || 0 }}</div>
              <div style="font-size:12px;color:#909399">高风险命中</div>
            </div>
            <div>
              <div style="font-size:22px;font-weight:700;color:#67C23A">{{ stats.screening_log_count || 0 }}</div>
              <div style="font-size:12px;color:#909399">总筛查次数</div>
            </div>
          </div>
        </el-card>

        <!-- 近期审计日志 -->
        <el-card shadow="never">
          <template #header><span style="font-weight:600">近期操作记录</span></template>
          <el-timeline v-if="(stats.recent_audit_logs || []).length">
            <el-timeline-item v-for="log in stats.recent_audit_logs" :key="log.id"
              :timestamp="log.created_at" placement="top" :color="log.action === 'LOGIN' ? '#409EFF' : '#67C23A'">
              <div style="font-size:13px">
                <el-tag size="small" :type="actionTagType(log.action)" style="margin-right:6px">{{ log.action }}</el-tag>
                {{ log.username }} — {{ log.detail || log.resource_type }}
              </div>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else description="暂无操作记录" :image-size="50" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/index.js'

const router = useRouter()
const stats = ref({})
const loading = ref(false)

const totalTariffLines = computed(() => {
  return (stats.value.tariff_by_country || []).reduce((s, c) => s + (c.line_count || 0), 0)
})

const kpiCards = computed(() => [
  { label: '税则数据总量', value: totalTariffLines.value.toLocaleString(), icon: 'Collection', color: '#409EFF' },
  { label: '受限制方总数', value: (stats.value.screening_list_types || []).reduce((s, c) => s + (c.count || 0), 0), icon: 'WarningFilled', color: '#E6A23C' },
  { label: '企业/产品', value: `${stats.value.enterprises || 0}/${stats.value.products || 0}`, icon: 'OfficeBuilding', color: '#67C23A' },
  { label: '报关单', value: stats.value.declarations || 0, icon: 'Document', color: '#409EFF' },
  { label: '活跃预警', value: stats.value.active_alerts || 0, icon: 'Bell', color: '#F56C6C' },
  { label: '国家/地区', value: stats.value.tariff_by_country?.length || 0, icon: 'Globe', color: '#67C23A' },
])

function actionTagType(action) {
  if (action === 'LOGIN') return 'primary'
  if (action === 'QUERY') return 'info'
  if (action === 'CREATE') return 'success'
  if (action === 'UPDATE') return 'warning'
  if (action === 'DELETE' || action === 'EXPORT') return 'danger'
  return 'info'
}

function goTariff(row) {
  router.push('/tariff')
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await api.dashboardStats()
    stats.value = res.data
  } catch { }
  loading.value = false
})
</script>
