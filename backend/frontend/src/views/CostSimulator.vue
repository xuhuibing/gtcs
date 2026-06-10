<template>
  <div>
    <h2>企业进口成本分析</h2>

    <el-row :gutter="24">
      <!-- 左栏：业务需求输入 -->
      <el-col :span="10">
        <!-- 产品信息 -->
        <el-card shadow="never" style="margin-bottom:12px">
          <template #header><span style="font-weight:600">产品信息</span></template>
          <el-form label-position="top" size="small">
            <el-form-item label="产品名称">
              <el-input v-model="form.product_name" placeholder="如：交互式智能平板" />
            </el-form-item>
            <el-form-item label="产品描述">
              <el-input v-model="form.product_description" type="textarea" :rows="2"
                placeholder="如：85英寸触摸显示屏，4K分辨率，含WiFi模块" />
            </el-form-item>
            <el-form-item label="HS 编码">
              <el-autocomplete
                v-model="form.hs_code"
                :fetch-suggestions="hsSearch"
                placeholder="输入HS编码或商品关键词搜索"
                clearable
                style="width:100%"
                @select="onHsSelect"
                value-key="local_code"
              >
                <template #default="{ item }">
                  <div style="display:flex;justify-content:space-between">
                    <span><strong>{{ item.local_code }}</strong> {{ item.description_cn || item.description_en }}</span>
                    <span style="color:#999;font-size:12px">{{ item.country }}</span>
                  </div>
                </template>
              </el-autocomplete>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 贸易条款 -->
        <el-card shadow="never" style="margin-bottom:12px">
          <template #header><span style="font-weight:600">贸易条款</span></template>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="目的国（进口国）" size="small">
                <el-select v-model="form.dest_country" filterable style="width:100%" @change="onDestCountryChange">
                  <el-option v-for="c in countryList" :key="c.iso2"
                    :label="`${c.iso2} - ${c.name_cn}（${(c.line_count||0).toLocaleString()}条）`" :value="c.iso2" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="贸易术语" size="small">
                <el-select v-model="form.incoterm" style="width:100%">
                  <el-option label="EXW 工厂交货" value="EXW" />
                  <el-option label="FOB 离岸价" value="FOB" />
                  <el-option label="CIF 到岸价" value="CIF" />
                  <el-option label="DAP 目的地交货" value="DAP" />
                  <el-option label="DDP 完税后交货" value="DDP" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="12">
            <el-col :span="8">
              <el-form-item label="数量" size="small">
                <el-input-number v-model="form.quantity" :min="1" :max="999999" style="width:100%" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="单价" size="small">
                <el-input-number v-model="form.unit_price" :min="0" :precision="2" :step="10" style="width:100%" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="币种" size="small">
                <el-select v-model="form.currency" style="width:100%">
                  <el-option label="USD 美元" value="USD" />
                  <el-option label="CNY 人民币" value="CNY" />
                  <el-option label="EUR 欧元" value="EUR" />
                  <el-option label="JPY 日元" value="JPY" />
                  <el-option label="VND 越南盾" value="VND" />
                  <el-option label="THB 泰铢" value="THB" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </el-card>

        <!-- 多原产国对比 -->
        <el-card shadow="never" style="margin-bottom:12px">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span style="font-weight:600">多原产国对比</span>
              <el-button size="small" type="primary" text @click="addOrigin">+ 添加原产国</el-button>
            </div>
          </template>
          <div v-for="(origin, idx) in form.origins" :key="idx"
            style="border:1px solid #e4e7ed;border-radius:6px;padding:12px;margin-bottom:8px;position:relative">
            <el-button size="small" type="danger" text style="position:absolute;top:4px;right:4px"
              @click="removeOrigin(idx)" v-if="form.origins.length > 1">
              <el-icon><Delete /></el-icon>
            </el-button>
            <el-row :gutter="8">
              <el-col :span="8">
                <el-form-item :label="`原产国 ${idx+1}`" size="small">
                  <el-select v-model="origin.origin_country" filterable style="width:100%">
                    <el-option v-for="c in countryList" :key="c.iso2"
                      :label="`${c.iso2} - ${c.name_cn}`" :value="c.iso2" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="运费" size="small">
                  <el-input-number v-model="origin.freight" :min="0" :precision="2" :step="100" style="width:100%" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="保险费" size="small">
                  <el-input-number v-model="origin.insurance" :min="0" :precision="2" :step="50" style="width:100%" />
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </el-card>

        <el-button type="primary" size="large" style="width:100%;margin-bottom:12px"
          @click="runSimulation" :loading="loading" :disabled="!form.dest_country || !form.origins.length">
          执行成本模拟
        </el-button>
      </el-col>

      <!-- 右栏：关务分析结果 -->
      <el-col :span="14">
        <!-- 空状态 -->
        <el-empty v-if="!result && !loading" description="在左侧输入业务信息并点击「执行成本模拟」" :image-size="80" style="margin-top:60px" />

        <!-- 加载状态 -->
        <div v-if="loading" style="text-align:center;padding:60px 0">
          <el-icon :size="40" class="is-loading"><Loading /></el-icon>
          <p style="color:#909399;margin-top:12px">正在分析...</p>
        </div>

        <!-- 结果 -->
        <template v-if="result && !loading">
          <!-- HS 编码确认卡片 -->
          <el-card shadow="never" style="margin-bottom:12px">
            <template #header>
              <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
                <span style="font-weight:600">关务分析结果</span>
                <el-tag type="primary" effect="dark">{{ result.incoterm }}</el-tag>
                <el-tag>{{ result.dest_country }} - {{ result.dest_name }}</el-tag>
                <el-tag type="success" v-if="result.recommendation">
                  推荐原产：{{ result.recommendation.best_origin }}
                  节省：\${{ formatMoney(result.recommendation.total_saving) }}
                </el-tag>
              </div>
            </template>
            <el-descriptions :column="3" border size="small">
              <el-descriptions-item label="确认 HS 编码" :span="1">
                <strong style="font-size:15px;color:#409eff">{{ result.hs_code_determined }}</strong>
              </el-descriptions-item>
              <el-descriptions-item label="商品描述" :span="2">{{ result.hs_description || result.product_name || '-' }}</el-descriptions-item>
            </el-descriptions>
          </el-card>

          <!-- VAT + 认证一行两张卡片 -->
          <el-row :gutter="12" style="margin-bottom:12px">
            <el-col :span="10">
              <el-card shadow="never">
                <template #header><span style="font-weight:600">VAT / 消费税</span></template>
                <el-descriptions :column="1" border size="small">
                  <el-descriptions-item label="税种">{{ result.vat_config.tax_name || result.vat_config.tax_type }}</el-descriptions-item>
                  <el-descriptions-item label="税率">
                    <el-tag type="warning" size="large">{{ result.vat_config.rate_pct }}</el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="说明">{{ result.vat_config.notes }}</el-descriptions-item>
                </el-descriptions>
              </el-card>
            </el-col>
            <el-col :span="14">
              <el-card shadow="never">
                <template #header><span style="font-weight:600">商品认证要求</span></template>
                <div v-if="result.certification_requirements?.length">
                  <el-tag v-for="req in result.certification_requirements" :key="req.type"
                    :type="req.is_mandatory ? 'danger' : 'info'"
                    style="margin:0 4px 4px 0" effect="plain">
                    {{ req.type }} - {{ req.name }}
                  </el-tag>
                </div>
                <el-empty v-else description="未找到特定认证要求" :image-size="40" />
              </el-card>
            </el-col>
          </el-row>

          <!-- 成本分解瀑布图（div 模拟） -->
          <el-card shadow="never" style="margin-bottom:12px">
            <template #header><span style="font-weight:600">成本构成（首个原产国示例）</span></template>
            <div v-if="result.comparisons?.[0]?.cost_breakdown">
              <div v-for="seg in result.comparisons[0].cost_breakdown" :key="seg.component"
                style="display:flex;align-items:center;margin-bottom:4px;gap:8px">
                <div style="width:100px;font-size:12px;text-align:right;color:#606266">{{ seg.label }}</div>
                <div style="flex:1;height:28px;background:#f0f2f5;border-radius:4px;overflow:hidden">
                  <div :style="{ width: seg.pct + '%', height:'100%', background: segColor(seg.component), borderRadius:'4px', display:'flex', alignItems:'center', justifyContent:'center', color:'#fff', fontSize:'11px', minWidth: seg.pct > 5 ? '50px' : '0', transition:'width 0.5s' }">
                    {{ seg.pct.toFixed(1) }}%
                  </div>
                </div>
                <div style="width:120px;font-size:12px;text-align:right;font-weight:600">
                  \${{ formatMoney(seg.amount) }}
                </div>
              </div>
              <div style="display:flex;align-items:center;margin-top:8px;padding-top:8px;border-top:2px solid #409eff;gap:8px">
                <div style="width:100px;font-size:12px;text-align:right;color:#409eff;font-weight:600">总到岸成本</div>
                <div style="flex:1;font-size:16px;font-weight:700;color:#409eff">
                  \${{ formatMoney(result.comparisons[0].total_landed_cost) }}
                </div>
              </div>
            </div>
          </el-card>

          <!-- 原产国对比表格 -->
          <el-card shadow="never" style="margin-bottom:12px">
            <template #header><span style="font-weight:600">原产国成本对比</span></template>
            <el-table :data="result.comparisons" border stripe size="small" style="width:100%">
              <el-table-column label="原产国" width="80">
                <template #default="{row}">
                  <el-tag :type="row.origin_country === result.recommendation?.best_origin ? 'success' : ''">
                    {{ row.origin_country }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="origin_name" label="国家" width="90" />
              <el-table-column label="FOB 总价" width="110" align="right">
                <template #default="{row}">\${{ formatMoney(row.fob_total) }}</template>
              </el-table-column>
              <el-table-column label="CIF 价值" width="110" align="right">
                <template #default="{row}">\${{ formatMoney(row.cif_value) }}</template>
              </el-table-column>
              <el-table-column label="关税" width="140">
                <template #default="{row}">
                  <div>
                    <span style="font-size:11px;color:#999">{{ row.tariff.selected_rate_pct }}</span>
                    <br>
                    <span :style="{ color: row.tariff.duty_amount > 0 ? '#f56c6c' : '#67c23a', fontWeight:600 }">
                      \${{ formatMoney(row.tariff.duty_amount) }}
                    </span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="VAT" width="110" align="right">
                <template #default="{row}">\${{ formatMoney(row.vat.amount) }}</template>
              </el-table-column>
              <el-table-column label="总到岸成本" width="130" align="right">
                <template #default="{row}">
                  <el-tag :type="row.origin_country === result.recommendation?.best_origin ? 'success' : 'warning'" size="large">
                    \${{ formatMoney(row.total_landed_cost) }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-card>

          <!-- 详细分解折叠面板 -->
          <el-card shadow="never">
            <template #header><span style="font-weight:600">各原产国详细分解</span></template>
            <el-collapse>
              <el-collapse-item v-for="cmp in result.comparisons" :key="cmp.origin_country"
                :title="`${cmp.origin_country} - ${cmp.origin_name}  |  总成本 \$ ${formatMoney(cmp.total_landed_cost)}`"
                :name="cmp.origin_country">
                <el-descriptions :column="2" border size="small">
                  <el-descriptions-item label="FOB 总价">\${{ formatMoney(cmp.fob_total) }}</el-descriptions-item>
                  <el-descriptions-item label="运费">\${{ formatMoney(cmp.freight) }}</el-descriptions-item>
                  <el-descriptions-item label="保险费">\${{ formatMoney(cmp.insurance) }}</el-descriptions-item>
                  <el-descriptions-item label="CIF 到岸价值">
                    <strong>\${{ formatMoney(cmp.cif_value) }}</strong>
                  </el-descriptions-item>
                  <el-descriptions-item label="MFN 税率">{{ cmp.tariff.mfn_rate_pct }}</el-descriptions-item>
                  <el-descriptions-item v-if="cmp.tariff.fta_rate?.available" label="FTA 优惠税率">
                    <el-tag type="success">{{ cmp.tariff.fta_rate.rate_pct }}（{{ cmp.tariff.fta_rate.agreement }}）</el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="附加税率">{{ cmp.tariff.additional_rate_pct }}</el-descriptions-item>
                  <el-descriptions-item label="适用总税率">
                    <el-tag :type="parseFloat(cmp.tariff.selected_rate_pct) > 5 ? 'danger' : 'success'">
                      {{ cmp.tariff.selected_rate_pct }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="关税金额">
                    <span :style="{ color: cmp.tariff.duty_amount > 0 ? '#f56c6c' : '#67c23a', fontWeight:600 }">
                      \${{ formatMoney(cmp.tariff.duty_amount) }}
                    </span>
                  </el-descriptions-item>
                  <el-descriptions-item label="VAT 税率">{{ cmp.vat.rate_pct }}</el-descriptions-item>
                  <el-descriptions-item label="VAT 税基">\${{ formatMoney(cmp.vat.taxable_base) }}</el-descriptions-item>
                  <el-descriptions-item label="VAT 金额">\${{ formatMoney(cmp.vat.amount) }}</el-descriptions-item>
                  <el-descriptions-item label="总到岸成本" :span="2">
                    <el-tag type="success" size="large" style="font-size:15px">
                      \${{ formatMoney(cmp.total_landed_cost) }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="关税 vs MFN 节省" :span="2" v-if="cmp.tariff.saving_vs_mfn">
                    <span style="color:#67c23a">节省 \${{ formatMoney(cmp.tariff.saving_vs_mfn) }}</span>
                  </el-descriptions-item>
                </el-descriptions>
              </el-collapse-item>
            </el-collapse>
          </el-card>
        </template>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api/index.js'

// ====== ====== ======
const form = reactive({
  product_name: '',
  product_description: '',
  hs_code: '',
  dest_country: 'VN',
  quantity: 100,
  unit_price: 850,
  currency: 'USD',
  incoterm: 'CIF',
  origins: [
    { origin_country: 'CN', freight: 2500, insurance: 500 },
  ],
})

const countryList = ref([])
const result = ref(null)
const loading = ref(false)

// ====== HS 编码搜索（Autocomplete） ======
let hsSearchTimer = null
async function hsSearch(queryString, cb) {
  if (!queryString || queryString.length < 2) return cb([])
  // 防抖 300ms
  clearTimeout(hsSearchTimer)
  hsSearchTimer = setTimeout(async () => {
    try {
      const res = await api.tariffSearch({ query: queryString, country: form.dest_country, limit: 15 })
      cb(res.data.map(item => ({
        local_code: item.local_code || item.hs_code,
        description_en: item.description_en,
        description_cn: item.description_cn,
        country: item.country || form.dest_country,
      })))
    } catch {
      cb([])
    }
  }, 300)
}

function onHsSelect(item) {
  form.hs_code = item.local_code
}

function onDestCountryChange() {
  // 自动切换本地选择
}

// ====== 多原产国管理 ======
function addOrigin() {
  form.origins.push({ origin_country: 'VN', freight: 0, insurance: 0 })
}
function removeOrigin(idx) {
  form.origins.splice(idx, 1)
}

// ====== 颜色 ======
function segColor(comp) {
  const map = { fob: '#409eff', freight: '#67c23a', insurance: '#e6a23c', duty: '#f56c6c', vat: '#909399' }
  return map[comp] || '#909399'
}

// ====== 格式化 ======
function formatMoney(val) {
  const num = parseFloat(val)
  if (isNaN(num)) return '0.00'
  return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function parseFloat(val) {
  if (typeof val === 'string') val = val.replace('%', '')
  return Number(val) || 0
}

// ====== 执行模拟 ======
async function runSimulation() {
  if (!form.dest_country) {
    ElMessage.warning('请选择目的国')
    return
  }
  loading.value = true
  result.value = null
  try {
    const payload = {
      product_name: form.product_name,
      product_description: form.product_description,
      hs_code: form.hs_code || undefined,
      dest_country: form.dest_country,
      quantity: form.quantity,
      unit_price: form.unit_price,
      currency: form.currency,
      incoterm: form.incoterm,
      origins: form.origins,
    }
    const res = await api.costEnterpriseSimulate(payload)
    result.value = res.data
  } catch (e) {
    result.value = null
  }
  loading.value = false
}

// ====== 初始化 ======
async function loadCountries() {
  try {
    const res = await api.tariffCountries()
    countryList.value = res.data || []
  } catch {
    countryList.value = []
  }
}

onMounted(() => {
  loadCountries()
})
</script>
