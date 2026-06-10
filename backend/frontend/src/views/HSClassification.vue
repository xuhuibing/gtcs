<template>
  <div>
    <h2>HS 归类工作台</h2>

    <el-row :gutter="24">
      <!-- 左栏：上游产品信息 -->
      <el-col :span="8">
        <el-card shadow="never" style="margin-bottom:12px">
          <template #header><span style="font-weight:600">产品信息录入</span></template>
          <el-form label-position="top" size="small">
            <el-form-item label="产品名称">
              <el-input v-model="form.product_name" placeholder="如：交互式智能平板" />
            </el-form-item>
            <el-form-item label="产品描述">
              <el-input v-model="form.product_description" type="textarea" :rows="2"
                placeholder="85英寸触摸屏，4K，WiFi，内置Android" />
            </el-form-item>
            <el-row :gutter="8">
              <el-col :span="12">
                <el-form-item label="品牌"><el-input v-model="form.brand" placeholder="如：华为" /></el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="型号"><el-input v-model="form.model" placeholder="如：IdeaHub S" /></el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="规格参数">
              <el-input v-model="form.specifications" type="textarea" :rows="1" placeholder="如：85寸/4K/8GB+64GB" />
            </el-form-item>
            <el-form-item label="材质构成">
              <el-input v-model="form.material_composition" placeholder="如：铝合金边框/玻璃面板" />
            </el-form-item>
            <el-form-item label="功能描述">
              <el-input v-model="form.function_description" type="textarea" :rows="2"
                placeholder="触控显示/无线投屏/视频会议/文件白板" />
            </el-form-item>
            <el-form-item label="用途说明">
              <el-input v-model="form.use_purpose" placeholder="如：企业会议室协作设备" />
            </el-form-item>
            <el-form-item label="目的国（进口国）">
              <el-select v-model="form.dest_country" filterable style="width:100%">
                <el-option v-for="c in countryList" :key="c.iso2"
                  :label="`${c.iso2} - ${c.name_cn}`" :value="c.iso2" />
              </el-select>
            </el-form-item>
            <el-button type="primary" style="width:100%" @click="recommend" :loading="recommending">
              推荐 HS 编码
            </el-button>
          </el-form>
        </el-card>

        <!-- 已有归类记录 -->
        <el-card shadow="never">
          <template #header><span style="font-weight:600">历史归类记录</span></template>
          <el-table :data="historyRecords" size="small" stripe max-height="300" v-loading="loadingHistory">
            <el-table-column prop="product_name_cn" label="产品" min-width="120" show-overflow-tooltip />
            <el-table-column prop="classified_hs_code" label="HS" width="80" />
            <el-table-column label="状态" width="70" align="center">
              <template #default="{row}">
                <el-tag :type="row.status === 'ACTIVE' ? 'success' : 'info'" size="small">
                  {{ row.status === 'ACTIVE' ? '有效' : row.status }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 右栏：HS 推荐 + 归类确认 -->
      <el-col :span="16">
        <!-- 空状态 -->
        <el-empty v-if="!recommendations.length && !recommending && !confirmed"
          description="左侧输入产品信息并点击「推荐 HS 编码」" :image-size="80" style="margin-top:60px" />

        <!-- 推荐列表 -->
        <template v-if="recommendations.length || recommending">
          <el-card shadow="never" style="margin-bottom:12px">
            <template #header>
              <div style="display:flex;justify-content:space-between;align-items:center">
                <span>
                  <span style="font-weight:600">HS 推荐结果</span>
                  <el-tag style="margin-left:8px" size="small">{{ recommendations.length }} 个候选</el-tag>
                  <el-tag type="success" size="small" v-if="recommendations.length" style="margin-left:4px">
                    推荐: {{ recommendations[0].hs_code }}
                  </el-tag>
                </span>
                <el-button type="success" size="small" :disabled="!selectedHs" @click="confirmClassification">
                  确认归类
                </el-button>
              </div>
            </template>

            <el-table :data="recommendations" border stripe size="small" highlight-current-row
              @row-click="selectRecommendation" max-height="360">
              <el-table-column type="index" label="#" width="40" />
              <el-table-column label="HS 编码" width="100">
                <template #default="{row}">
                  <strong style="color:#409eff">{{ row.hs_code }}</strong>
                </template>
              </el-table-column>
              <el-table-column label="商品描述" min-width="200" show-overflow-tooltip>
                <template #default="{row}">
                  <div>{{ row.description_cn }}</div>
                  <div style="font-size:11px;color:#909399">{{ row.description_en }}</div>
                </template>
              </el-table-column>
              <el-table-column label="MFN 税率" width="80" align="center">
                <template #default="{row}">
                  <el-tag v-if="row.mfn_rate != null" :type="row.mfn_rate > 5 ? 'danger' : 'success'" size="small">
                    {{ row.mfn_rate }}%
                  </el-tag>
                  <span v-else class="no-data">-</span>
                </template>
              </el-table-column>
              <el-table-column label="FTA 优惠" width="120">
                <template #default="{row}">
                  <div v-if="row.fta_rates?.length">
                    <el-tag v-for="f in row.fta_rates" :key="f.agreement" type="warning" size="small" style="margin:1px">
                      {{ f.agreement }} {{ f.rate_pct }}%
                    </el-tag>
                  </div>
                  <span v-else class="no-data">-</span>
                </template>
              </el-table-column>
              <el-table-column label="预裁定匹配" width="90" align="center">
                <template #default="{row}">
                  <el-tag v-if="row.matched_rulings?.length" type="primary" size="small">
                    {{ row.matched_rulings.length }}条
                  </el-tag>
                  <span v-else class="no-data">-</span>
                </template>
              </el-table-column>
            </el-table>
          </el-card>

          <!-- 选定 HS 的预裁定详情 -->
          <el-card v-if="selectedRulings.length" shadow="never" style="margin-bottom:12px">
            <template #header><span style="font-weight:600">匹配的海关预裁定</span></template>
            <el-collapse>
              <el-collapse-item v-for="r in selectedRulings" :key="r.ruling_number"
                :title="`${r.ruling_number} - ${r.issuing_authority} (${r.ruling_date})`">
                <el-descriptions :column="1" border size="small">
                  <el-descriptions-item label="裁定编号">{{ r.ruling_number }}</el-descriptions-item>
                  <el-descriptions-item label="产品名称">{{ r.product_name }}</el-descriptions-item>
                  <el-descriptions-item label="裁定结论">{{ r.decision }}</el-descriptions-item>
                  <el-descriptions-item label="归类依据/推理">{{ r.classification_reasoning }}</el-descriptions-item>
                </el-descriptions>
              </el-collapse-item>
            </el-collapse>
          </el-card>

          <!-- 选定 HS 的税率详情 -->
          <el-card v-if="selectedHsTariff" shadow="never">
            <template #header><span style="font-weight:600">选定 HS 编码：{{ selectedHs }} 海关税率</span></template>
            <el-descriptions :column="3" border size="small">
              <el-descriptions-item label="MFN 税率">
                <el-tag :type="(selectedHsTariff.mfn_rate || 0) > 5 ? 'danger' : 'success'">
                  {{ selectedHsTariff.mfn_rate || 0 }}%
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="综合有效税率">
                <el-tag :type="(selectedHsTariff.total_effective_rate || 0) > 5 ? 'danger' : 'warning'">
                  {{ selectedHsTariff.total_effective_rate || 0 }}%
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="FTA 优惠" v-if="selectedHsTariff.fta_rates?.length">
                <el-tag v-for="f in selectedHsTariff.fta_rates" :key="f.agreement" type="success" style="margin:1px">
                  {{ f.agreement }}: {{ f.rate_pct }}%
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item v-else label="FTA 优惠" />
            </el-descriptions>
          </el-card>
        </template>

        <!-- 确认归类成功 -->
        <el-result v-if="confirmed" status="success" :title="`归类确认成功: ${confirmedHs}`" style="padding:20px">
          <template #extra>
            <el-button type="primary" @click="resetAll">继续新归类</el-button>
            <el-button @click="$router.push('/cost')">进入成本分析</el-button>
          </template>
        </el-result>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.no-data { color: #c0c4cc; }
</style>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api/index.js'

const form = ref({
  product_name: '',
  product_description: '',
  brand: '',
  model: '',
  specifications: '',
  material_composition: '',
  function_description: '',
  use_purpose: '',
  dest_country: 'CN',
})
const countryList = ref([])
const loadingHistory = ref(false)
const historyRecords = ref([])
const recommending = ref(false)
const recommendations = ref([])
const selectedHs = ref('')
const selectedRulings = ref([])
const selectedHsTariff = ref(null)
const confirmed = ref(false)
const confirmedHs = ref('')

async function recommend() {
  if (!form.value.product_name && !form.value.product_description) {
    ElMessage.warning('请输入产品名称或描述')
    return
  }
  recommending.value = true
  recommendations.value = []
  selectedHs.value = ''
  selectedRulings.value = []
  selectedHsTariff.value = null
  confirmed.value = false
  try {
    const res = await api.hsEnterpriseRecommend(form.value)
    recommendations.value = res.data.recommendations || []
    if (!recommendations.value.length) {
      ElMessage.info('未找到匹配的 HS 编码')
    }
  } catch {
    recommendations.value = []
  }
  recommending.value = false
}

function selectRecommendation(row) {
  selectedHs.value = row.hs_code
  selectedRulings.value = row.matched_rulings || []
  selectedHsTariff.value = {
    mfn_rate: row.mfn_rate,
    fta_rates: row.fta_rates,
    total_effective_rate: row.total_effective_rate,
  }
}

async function confirmClassification() {
  if (!selectedHs.value) {
    ElMessage.warning('请先选择一条 HS 编码')
    return
  }
  try {
    await api.hsEnterpriseClassify({
      ...form.value,
      hs_code_candidate: selectedHs.value,
    })
    confirmedHs.value = selectedHs.value
    confirmed.value = true
    ElMessage.success(`归类确认成功：${selectedHs.value}`)
    loadHistory()
  } catch { /* handled by interceptor */ }
}

function resetAll() {
  form.value = {
    product_name: '', product_description: '', brand: '', model: '',
    specifications: '', material_composition: '', function_description: '',
    use_purpose: '', dest_country: 'CN',
  }
  recommendations.value = []
  selectedHs.value = ''
  selectedRulings.value = []
  selectedHsTariff.value = null
  confirmed.value = false
  confirmedHs.value = ''
}

async function loadCountries() {
  try {
    const res = await api.tariffCountries()
    countryList.value = res.data || []
  } catch { countryList.value = [] }
}

async function loadHistory() {
  loadingHistory.value = true
  try {
    const res = await api.hsClassHistory({ limit: 20 })
    historyRecords.value = res.data || []
  } catch { historyRecords.value = [] }
  loadingHistory.value = false
}

onMounted(() => {
  loadCountries()
  loadHistory()
})
</script>
