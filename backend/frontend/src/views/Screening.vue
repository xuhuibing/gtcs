<template>
  <div>
    <h2>受限制方筛查</h2>
    <el-alert title="贸易合规底线要求：所有贸易伙伴（客户、供应商、中间商、收货人、最终用户）必须在交易前完成受限制方筛查。" type="warning" show-icon :closable="false" style="margin-bottom:16px" />

    <el-row :gutter="16" style="margin-bottom:16px">
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card">
            <div class="stat-value">{{ listStats.length }}</div>
            <div class="stat-label">制裁名单类型</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card">
            <div class="stat-value">{{ totalListed }}</div>
            <div class="stat-label">受限制方总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card">
            <div class="stat-value" style="color:#e6a23c">{{ highRiskCount }}</div>
            <div class="stat-label">高风险命中</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card">
            <div class="stat-value" style="color:#67c23a">{{ cleanCount }}</div>
            <div class="stat-label">筛查次数</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- 筛查 Tab -->
      <el-tab-pane label="单名称筛查" name="single">
        <el-card shadow="never">
          <el-form :model="checkForm" label-width="100px">
            <el-form-item label="名称（英文）" required>
              <el-input v-model="checkForm.name" placeholder="Enter name to screen...">
                <template #append>
                  <el-button @click="handleCheck" :loading="checking" type="primary">筛查</el-button>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item label="名称（中文）">
              <el-input v-model="checkForm.name_cn" placeholder="输入中文名称进行匹配" />
            </el-form-item>
            <el-form-item label="筛查类型">
              <el-select v-model="checkForm.screened_type" style="width:200px">
                <el-option label="客户 (CUSTOMER)" value="CUSTOMER" />
                <el-option label="供应商 (SUPPLIER)" value="SUPPLIER" />
                <el-option label="员工 (EMPLOYEE)" value="EMPLOYEE" />
                <el-option label="其他 (OTHER)" value="OTHER" />
              </el-select>
            </el-form-item>
            <el-form-item label="匹配阈值">
              <el-slider v-model="checkForm.min_score" :min="50" :max="99" :step="5" show-input style="width:300px" />
            </el-form-item>
            <el-form-item label="制裁清单">
              <el-checkbox-group v-model="checkForm.list_types">
                <el-checkbox label="OFAC">OFAC SDN</el-checkbox>
                <el-checkbox label="BIS">BIS 实体清单</el-checkbox>
                <el-checkbox label="EU">EU 制裁</el-checkbox>
                <el-checkbox label="UN">UN 制裁</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 筛查结果 -->
        <el-card v-if="checkResult" shadow="never" style="margin-top:16px">
          <template #header>
            <span>
              筛查结果：
              <el-tag v-if="checkResult.risk_level === 'CLEAN'" type="success" size="large">CLEAN - 无匹配</el-tag>
              <el-tag v-else-if="checkResult.risk_level === 'HIGH'" type="danger" size="large">HIGH - 高危命中</el-tag>
              <el-tag v-else-if="checkResult.risk_level === 'MEDIUM'" type="warning" size="large">MEDIUM - 中等风险</el-tag>
              <el-tag v-else type="info" size="large">{{ checkResult.risk_level }}</el-tag>
              <span style="margin-left:12px;font-size:13px;color:#909399">匹配 {{ checkResult.match_count }} 条</span>
            </span>
          </template>

          <el-table v-if="checkResult.matches?.length" :data="checkResult.matches" border stripe size="small">
            <el-table-column label="得分" width="80" align="center">
              <template #default="{row}">
                <el-tag :type="row.score >= 90 ? 'danger' : (row.score >= 75 ? 'warning' : 'info')" size="small">
                  {{ row.score }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="list_type" label="清单" width="80" />
            <el-table-column prop="id_type" label="类型" width="80" />
            <el-table-column prop="match_name" label="命中名称" min-width="250" show-overflow-tooltip />
            <el-table-column prop="match_name_cn" label="中文名" width="180" show-overflow-tooltip />
            <el-table-column prop="country" label="国家" width="60" />
            <el-table-column prop="program" label="制裁项目" width="120" />
            <el-table-column prop="reason" label="理由" min-width="200" show-overflow-tooltip />
          </el-table>
          <el-empty v-else description="未发现匹配" :image-size="60" />
        </el-card>
      </el-tab-pane>

      <!-- 批量筛查 Tab -->
      <el-tab-pane label="批量筛查" name="batch">
        <el-card shadow="never">
          <el-form>
            <el-form-item label="输入名称">
              <el-input v-model="batchInput" type="textarea" :rows="8"
                placeholder="每行一个名称&#10;例如:&#10;John Smith&#10;ABC Trading Co., Ltd.&#10;伊朗航运公司" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleBatch" :loading="batchChecking">批量筛查</el-button>
            </el-form-item>
          </el-form>

          <el-table v-if="batchResults.length" :data="batchResults" border stripe size="small" style="margin-top:12px">
            <el-table-column prop="screened_name" label="被筛查名称" min-width="250" show-overflow-tooltip />
            <el-table-column prop="match_count" label="匹配数" width="80" align="center" />
            <el-table-column prop="risk_level" label="风险等级" width="120" align="center">
              <template #default="{row}">
                <el-tag :type="row.risk_level === 'CLEAN' ? 'success' : (row.risk_level === 'HIGH' ? 'danger' : 'warning')" size="small">
                  {{ row.risk_level }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 筛查历史 Tab -->
      <el-tab-pane label="筛查历史" name="history">
        <el-card shadow="never">
          <el-row :gutter="8" style="margin-bottom:12px">
            <el-col :span="6">
              <el-select v-model="historyFilter.risk_level" clearable placeholder="风险等级" style="width:100%" @change="loadHistory">
                <el-option label="高风险" value="HIGH" />
                <el-option label="中等风险" value="MEDIUM" />
                <el-option label="低风险" value="LOW" />
                <el-option label="清洁" value="CLEAN" />
              </el-select>
            </el-col>
            <el-col :span="6">
              <el-select v-model="historyFilter.status" clearable placeholder="状态" style="width:100%" @change="loadHistory">
                <el-option label="已完成" value="COMPLETED" />
                <el-option label="待复核" value="PENDING_REVIEW" />
              </el-select>
            </el-col>
          </el-row>

          <el-table :data="screeningHistory" border stripe size="small" v-loading="loadingHistory">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="screened_name" label="被筛查名称" min-width="200" show-overflow-tooltip />
            <el-table-column prop="screened_type" label="类型" width="120" />
            <el-table-column prop="match_count" label="匹配" width="60" align="center" />
            <el-table-column prop="risk_level" label="风险等级" width="100" align="center">
              <template #default="{row}">
                <el-tag :type="row.risk_level === 'CLEAN' ? 'success' : (row.risk_level === 'HIGH' ? 'danger' : 'warning')" size="small">
                  {{ row.risk_level }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="screened_by" label="筛查人" width="120" />
            <el-table-column prop="created_at" label="筛查时间" width="180" />
          </el-table>
          <el-empty v-if="!screeningHistory.length && !loadingHistory" description="暂无筛查记录" :image-size="60" />
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped>
.stat-card {
  text-align: center;
  padding: 8px 0;
}
.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #409eff;
}
.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}
</style>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api/index.js'

const activeTab = ref('single')

// Stats
const listStats = ref([])
const screeningHistory = ref([])
const loadingHistory = ref(false)
const totalListed = computed(() => listStats.value.reduce((s, l) => s + (l.count || 0), 0))
const highRiskCount = computed(() => screeningHistory.value.filter(h => h.risk_level === 'HIGH').length)
const cleanCount = computed(() => screeningHistory.value.length)

// Single check
const checkForm = ref({
  name: '',
  name_cn: '',
  screened_type: 'OTHER',
  min_score: 60,
  list_types: [],
})
const checking = ref(false)
const checkResult = ref(null)

async function handleCheck() {
  if (!checkForm.value.name.trim()) {
    ElMessage.warning('请输入要筛查的名称')
    return
  }
  checking.value = true
  try {
    const res = await api.screeningCheck(checkForm.value)
    checkResult.value = res.data
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '筛查失败')
    checkResult.value = null
  }
  checking.value = false
  loadHistory()
}

// Batch check
const batchInput = ref('')
const batchChecking = ref(false)
const batchResults = ref([])

async function handleBatch() {
  const lines = batchInput.value.split('\n').map(l => l.trim()).filter(Boolean)
  if (!lines.length) {
    ElMessage.warning('请输入要筛查的名称')
    return
  }
  batchChecking.value = true
  try {
    const res = await api.screeningBatch({
      names: lines.map(n => ({ name: n, screened_type: 'OTHER' })),
      min_score: 60,
    })
    batchResults.value = res.data.results || []
    ElMessage.success(`批量筛查完成，${res.data.total} 个名称`)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '批量筛查失败')
  }
  batchChecking.value = false
}

// History
const historyFilter = ref({ risk_level: null, status: null })

async function loadHistory() {
  loadingHistory.value = true
  try {
    const res = await api.screeningHistory({
      risk_level: historyFilter.value.risk_level || undefined,
      status: historyFilter.value.status || undefined,
      limit: 50,
    })
    screeningHistory.value = res.data || []
  } catch {
    screeningHistory.value = []
  }
  loadingHistory.value = false
}

async function loadStats() {
  try {
    const res = await api.screeningLists()
    listStats.value = res.data || []
  } catch {
    listStats.value = []
  }
}

onMounted(() => {
  loadStats()
  loadHistory()
})
</script>
