<template>
  <div>
    <h2>报关单管理</h2>
    <div style="margin-bottom:12px;display:flex;gap:8px">
      <el-button type="primary" @click="showCreate = true">新建报关单</el-button>
      <el-select v-model="filterStatus" placeholder="状态筛选" clearable style="width:140px">
        <el-option v-for="s in ['draft','submitted','query_received','amended','cleared','closed']" :key="s" :label="s" :value="s" />
      </el-select>
      <el-button @click="loadList">刷新</el-button>
    </div>

    <el-table :data="declarations" border stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="declaration_no" label="报关单号" width="180" />
      <el-table-column prop="direction" label="方向" width="80">
        <template #default="{row}">
          <el-tag :type="row.direction === 'IMPORT' ? 'danger' : 'success'" size="small">{{ row.direction }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{row}">
          <el-tag :type="statusType(row.status)" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="total_value" label="总价值" width="120">
        <template #default="{row}">${{ row.total_value?.toFixed(2) }}</template>
      </el-table-column>
      <el-table-column prop="consignee" label="收货人" width="140" show-overflow-tooltip />
      <el-table-column label="可操作" width="200">
        <template #default="{row}">
          <el-button v-for="a in row.available_actions" :key="a.action" size="small" @click="transition(row.id, a.action)">{{ a.label }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showCreate" title="新建报关单" width="700px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="方向">
          <el-radio-group v-model="createForm.direction">
            <el-radio value="IMPORT">进口</el-radio>
            <el-radio value="EXPORT">出口</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="收货人"><el-input v-model="createForm.consignee" /></el-form-item>
        <el-form-item label="发货人"><el-input v-model="createForm.consignor" /></el-form-item>
        <el-form-item label="HS编码"><el-input v-model="createForm.hs_code" placeholder="如 8528420000" /></el-form-item>
        <el-form-item label="商品名称"><el-input v-model="createForm.name_cn" /></el-form-item>
        <el-form-item label="数量"><el-input-number v-model="createForm.qty" :min="1" /></el-form-item>
        <el-form-item label="单价($)"><el-input-number v-model="createForm.unit_price" :min="0" :step="10" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="createDeclaration">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api/index.js'

const declarations = ref([])
const showCreate = ref(false)
const filterStatus = ref('')
const createForm = ref({ direction: 'IMPORT', consignee: '', consignor: '', hs_code: '8528420000', name_cn: '电子产品', qty: 100, unit_price: 150 })

function statusType(s) {
  const m = { draft: 'info', submitted: 'primary', query_received: 'warning', amended: '', cleared: 'success', closed: '' }
  return m[s] || 'info'
}

async function loadList() {
  const res = await api.declarationList({ status: filterStatus.value || undefined })
  declarations.value = res.data.items
}

async function transition(id, action) {
  await api.declarationTransition(id, { action })
  ElMessage.success(`状态已变更为: ${action}`)
  loadList()
}

async function createDeclaration() {
  const f = createForm.value
  await api.declarationCreate({
    direction: f.direction,
    consignee: f.consignee,
    consignor: f.consignor,
    items: [{ hs_code: f.hs_code, name_cn: f.name_cn, qty: f.qty, unit_price: f.unit_price, total_price: f.qty * f.unit_price }],
  })
  ElMessage.success('创建成功')
  showCreate.value = false
  loadList()
}

watch(filterStatus, loadList)
loadList()
</script>
