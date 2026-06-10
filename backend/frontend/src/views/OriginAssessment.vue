<template>
  <div>
    <h2>原产地评估</h2>

    <el-card style="margin-bottom:16px">
      <template #header><span>CTC 税则改变检查</span></template>
      <el-form :inline="true" :model="ctcForm">
        <el-form-item label="成品HS"><el-input v-model="ctcForm.hs_code" style="width:140px" /></el-form-item>
        <el-form-item label="原料HS"><el-input v-model="ctcForm.material_hs_code" style="width:140px" /></el-form-item>
        <el-form-item label="级别">
          <el-select v-model="ctcForm.level" style="width:100px">
            <el-option label="CC(章)" value="CC" />
            <el-option label="CTH(品目)" value="CTH" />
            <el-option label="CTSH(子目)" value="CTSH" />
          </el-select>
        </el-form-item>
        <el-form-item><el-button type="primary" @click="checkCtc">检查</el-button></el-form-item>
      </el-form>
      <el-alert v-if="ctcResult !== null" :title="ctcResult ? '✓ 满足税则改变要求' : '✗ 不满足税则改变要求'" :type="ctcResult ? 'success' : 'error'" :closable="false" />
    </el-card>

    <el-card>
      <template #header><span>原产地档案列表</span></template>
      <el-table :data="profiles" border stripe size="small">
        <el-table-column prop="product_code" label="产品代码" width="120" />
        <el-table-column prop="product_name" label="产品名称" width="150" show-overflow-tooltip />
        <el-table-column prop="hs_code" label="HS编码" width="130" />
        <el-table-column prop="manufacturing_country" label="制造国" width="80" />
        <el-table-column prop="origin_status" label="状态" width="130">
          <template #default="{row}">
            <el-tag :type="row.origin_status === 'QUALIFIES' ? 'success' : 'danger'" size="small">{{ row.origin_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="rvc_calculated" label="RVC%" width="80" />
        <el-table-column label="操作" width="180">
          <template #default="{row}">
            <el-button size="small" type="primary" @click="runAssessment(row.id)" :loading="loadingId === row.id">评估</el-button>
            <el-button size="small" @click="showAgreements(row.id)">FTA</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="agreementDialog" title="FTA 资格评估" width="800px">
      <el-table :data="agreements" border size="small">
        <el-table-column prop="agreement_code" label="协定" width="100" />
        <el-table-column prop="qualified" label="资格" width="80">
          <template #default="{row}">
            <el-tag :type="row.qualified ? 'success' : 'info'" size="small">{{ row.qualified ? '合格' : '不合格' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="method_used" label="方法" width="80" />
        <el-table-column prop="rvc_calculated" label="RVC%" width="80" />
        <el-table-column prop="rvc_threshold" label="阈值%" width="80" />
        <el-table-column prop="ctc_met" label="CTC" width="60">
          <template #default="{row}">{{ row.ctc_met === true ? '✓' : row.ctc_met === false ? '✗' : '-' }}</template>
        </el-table-column>
        <el-table-column prop="reasons" label="说明" show-overflow-tooltip />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/index.js'

const ctcForm = ref({ hs_code: '8528420000', material_hs_code: '8471300000', level: 'CTH' })
const ctcResult = ref(null)
const profiles = ref([])
const loadingId = ref(null)
const agreementDialog = ref(false)
const agreements = ref([])

async function checkCtc() {
  const res = await api.originCtcCheck(ctcForm.value)
  ctcResult.value = res.data.shifted
}

async function runAssessment(id) {
  loadingId.value = id
  await api.originFullAssessment(id)
  await loadProfiles()
  loadingId.value = null
}

async function showAgreements(id) {
  const res = await api.originAgreements(id)
  agreements.value = res.data
  agreementDialog.value = true
}

async function loadProfiles() {
  try {
    const res = await api.originProfiles({ limit: 20 })
    profiles.value = res.data
  } catch { }
}

onMounted(loadProfiles)
</script>
