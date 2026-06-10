<template>
  <div>
    <h2>价格风控</h2>
    <el-tabs v-model="tab">
      <el-tab-pane label="价格记录" name="record">
        <el-card>
          <el-form :inline="true" :model="recordForm">
            <el-form-item label="HS编码"><el-input v-model="recordForm.hs_code" style="width:140px" /></el-form-item>
            <el-form-item label="单价($)"><el-input-number v-model="recordForm.unit_price" :min="0" :step="1" /></el-form-item>
            <el-form-item label="品牌"><el-input v-model="recordForm.brand" style="width:120px" /></el-form-item>
            <el-form-item label="型号"><el-input v-model="recordForm.model" style="width:120px" /></el-form-item>
            <el-form-item><el-button type="primary" @click="addRecord">录入</el-button></el-form-item>
          </el-form>
          <el-tag v-if="lastRecord" :type="lastRecord.risk_flag === 'GREEN' ? 'success' : 'danger'" style="margin-top:8px">
            风险: {{ lastRecord.risk_flag }} — {{ lastRecord.risk_reason }}
          </el-tag>
        </el-card>
        <el-card style="margin-top:16px">
          <template #header><span>历史价格曲线</span></template>
          <el-form :inline="true">
            <el-form-item label="HS编码"><el-input v-model="historyForm.hs_code" style="width:140px" /></el-form-item>
            <el-form-item><el-button @click="loadHistory">查询</el-button></el-form-item>
          </el-form>
          <el-table :data="priceHistory" border size="small" max-height="300">
            <el-table-column prop="unit_price" label="单价" width="100" />
            <el-table-column prop="currency" label="币种" width="60" />
            <el-table-column prop="brand" label="品牌" width="100" />
            <el-table-column prop="model" label="型号" width="100" />
            <el-table-column prop="origin_country" label="原产国" width="80" />
            <el-table-column prop="declaration_date" label="申报日期" />
            <el-table-column prop="risk_flag" label="风险" width="80">
              <template #default="{row}">
                <el-tag :type="row.risk_flag === 'GREEN' ? 'success' : 'danger'" size="small">{{ row.risk_flag }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
      <el-tab-pane label="风险告警" name="alerts">
        <el-card>
          <el-table :data="alerts" border stripe>
            <el-table-column prop="hs_code" label="HS编码" width="120" />
            <el-table-column prop="alert_type" label="类型" width="140" />
            <el-table-column prop="severity" label="严重度" width="80">
              <template #default="{row}">
                <el-tag :type="row.severity === 'HIGH' ? 'danger' : row.severity === 'MEDIUM' ? 'warning' : 'info'" size="small">{{ row.severity }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="unit_price" label="当前单价" width="100" />
            <el-table-column prop="previous_price" label="前次价格" width="100" />
            <el-table-column prop="triggered_at" label="触发时间" width="160" />
            <el-table-column prop="customs_implication" label="海关风险提示" show-overflow-tooltip />
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import api from '../api/index.js'

const tab = ref('record')
const recordForm = reactive({ hs_code: '8528420000', unit_price: 150, brand: 'Samsung', model: 'XYZ' })
const lastRecord = ref(null)
const priceHistory = ref([])
const historyForm = ref({ hs_code: '8528420000' })
const alerts = ref([])

async function addRecord() {
  const res = await api.priceRiskRecord(recordForm)
  lastRecord.value = res.data
  loadAlerts()
}

async function loadHistory() {
  const res = await api.priceRiskHistory(historyForm.value)
  priceHistory.value = res.data
}

async function loadAlerts() {
  const res = await api.priceRiskAlerts({ limit: 20 })
  alerts.value = res.data
}

loadHistory()
loadAlerts()
</script>
