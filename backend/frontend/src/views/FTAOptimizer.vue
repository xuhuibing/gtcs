<template>
  <div>
    <h2>FTA 原产地优选</h2>
    <el-card style="margin-bottom:16px">
      <el-form :inline="true" :model="form">
        <el-form-item label="HS编码"><el-input v-model="form.hs_code" style="width:160px" /></el-form-item>
        <el-form-item label="原产国"><el-select v-model="form.origin" style="width:120px">
          <el-option v-for="c in ['CN','VN','TH','MY','ID','JP','KR','IN']" :key="c" :label="c" :value="c" />
        </el-select></el-form-item>
        <el-form-item label="目的国"><el-select v-model="form.dest" style="width:120px">
          <el-option v-for="c in ['US','CN','VN','TH','MY','JP','KR','EU']" :key="c" :label="c" :value="c" />
        </el-select></el-form-item>
        <el-form-item><el-button type="primary" @click="recommend">推荐</el-button></el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="result">
      <template #header>
        <span>{{ result.hs_code }} | {{ result.origin }} → {{ result.dest }}</span>
      </template>
      <el-alert v-if="result.notes" :title="result.notes" type="info" :closable="false" style="margin-bottom:16px" />
      <el-table :data="result.available_agreements" border stripe>
        <el-table-column prop="code" label="协定" width="100" />
        <el-table-column label="税率" width="100">
          <template #default="{row}">
            <el-tag :type="row.code === 'MFN' ? 'info' : 'success'">{{ row.rate }}%</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="savings_vs_mfn" label="节省%" width="100">
          <template #default="{row}">
            <span v-if="row.savings_vs_mfn > 0" style="color:#67C23A">-{{ row.savings_vs_mfn }}%</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="certificate" label="所需证书" />
        <el-table-column prop="roo_requirement" label="原产地规则" />
      </el-table>

      <el-card v-if="compareResult.length" style="margin-top:16px">
        <template #header><span>多原产国对比</span></template>
        <el-table :data="compareResult" border stripe size="small">
          <el-table-column prop="origin" label="原产国" width="100" />
          <el-table-column prop="best_agreement" label="最佳协定" width="120" />
          <el-table-column prop="best_rate" label="最优税率%" width="100" />
          <el-table-column prop="additional_duty" label="附加税%" width="100" />
          <el-table-column prop="total_effective" label="综合税率%" width="100">
            <template #default="{row}">
              <el-tag :type="row.total_effective > 5 ? 'danger' : 'success'">{{ row.total_effective }}%</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="certificate" label="证书" />
        </el-table>
      </el-card>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '../api/index.js'

const form = ref({ hs_code: '8528420000', origin: 'CN', dest: 'US' })
const result = ref(null)
const compareResult = ref([])

async function recommend() {
  const [rec, cmp] = await Promise.all([
    api.ftaRecommend(form.value),
    api.ftaCompareOrigins({ ...form.value, origins: ['CN', 'VN', 'TH', 'MY', 'ID'] }),
  ])
  result.value = rec.data
  compareResult.value = cmp.data
}
</script>
