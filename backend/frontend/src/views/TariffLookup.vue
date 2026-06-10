<template>
  <div>
    <h2>税则查询与浏览</h2>
    <el-tabs v-model="activeTab" type="border-card">
      <!-- Tab 1: Lookup -->
      <el-tab-pane label="税率查询" name="lookup">
        <el-card shadow="never" style="margin-bottom:16px">
          <el-form :inline="true" :model="form" label-width="80px">
            <el-form-item label="HS编码">
              <el-input v-model="form.hs_code" placeholder="如 8528420000 或 8528.52" style="width:200px" />
            </el-form-item>
            <el-form-item label="目的国">
              <el-select v-model="form.dest_country" style="width:160px" filterable>
                <el-option v-for="c in countryList" :key="c.iso2"
                  :label="`${c.iso2} - ${c.name_en}`" :value="c.iso2" />
              </el-select>
            </el-form-item>
            <el-form-item label="原产国">
              <el-select v-model="form.origin_country" style="width:160px" filterable>
                <el-option v-for="c in countryList" :key="c.iso2"
                  :label="`${c.iso2} - ${c.name_en}`" :value="c.iso2" />
              </el-select>
            </el-form-item>
            <el-form-item label="货值(USD)">
              <el-input-number v-model="form.value_usd" :min="0" :step="100" style="width:150px" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="lookup" :loading="lookingUp">查询</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card v-if="result" shadow="never" style="margin-bottom:16px">
          <template #header>
            <span>
              <strong>{{ result.local_code }}</strong>
              <el-tag style="margin-left:8px" size="small">{{ result.country }}</el-tag>
              <span style="margin-left:12px;font-weight:normal;font-size:13px;color:#606266">{{ result.description_cn || result.description || '' }}</span>
            </span>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="商品描述" :span="2">{{ result.description || '-' }}</el-descriptions-item>
            <el-descriptions-item label="中文名称" :span="2">{{ result.description_cn || '-' }}</el-descriptions-item>
            <el-descriptions-item label="MFN 税率">
              <el-tag :type="mfnRate > 0 ? 'danger' : 'success'" v-if="result.mfn_rate != null">{{ result.mfn_rate }}%</el-tag>
              <span v-else>-</span>
            </el-descriptions-item>
            <el-descriptions-item label="Column 2 税率">
              <el-tag type="warning" v-if="result.column2_rate != null">{{ result.column2_rate }}%</el-tag>
              <span v-else>-</span>
            </el-descriptions-item>
            <el-descriptions-item label="附加税合计">
              <el-tag type="danger" v-if="result.additional_duties?.length">{{ totalAdditional }}%</el-tag>
              <span v-else>0%</span>
            </el-descriptions-item>
            <el-descriptions-item label="计量单位">{{ result.unit || '-' }}</el-descriptions-item>
            <el-descriptions-item label="综合有效税率">
              <el-tag :type="result.total_effective_rate > 5 ? 'danger' : 'success'" size="large">
                {{ result.total_effective_rate }}%
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="预估关税 (USD)" v-if="result.estimated_duty != null">
              <strong style="font-size:16px;color:#f56c6c">${{ result.estimated_duty }}</strong>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card v-if="result?.fta_rates?.length" shadow="never" style="margin-bottom:16px">
          <template #header><span>自贸协定优惠税率（{{ result.fta_rates.length }}项）</span></template>
          <el-table :data="result.fta_rates" border size="small">
            <el-table-column prop="agreement" label="协定" width="120" />
            <el-table-column prop="rate_pct" label="优惠税率%" width="100" />
            <el-table-column prop="origin_scope" label="适用范围" />
          </el-table>
        </el-card>

        <el-card v-if="result?.additional_duties?.length" shadow="never">
          <template #header><span>附加税明细（{{ result.additional_duties.length }}项）</span></template>
          <el-table :data="result.additional_duties" border size="small">
            <el-table-column prop="duty_type" label="类型" width="120" />
            <el-table-column prop="rate_pct" label="税率%" width="100" />
            <el-table-column prop="target_origin" label="针对原产国" width="120" />
            <el-table-column prop="legal_basis" label="法律依据" />
          </el-table>
        </el-card>

        <el-empty v-if="!lookingUp && lookedUp && !result" description="未查询到该HS编码的税则数据" />
      </el-tab-pane>

      <!-- Tab 2: Browse -->
      <el-tab-pane label="税则浏览" name="browse">
        <el-row :gutter="16">
          <el-col :span="7">
            <el-card shadow="never">
              <template #header>
                <span>选择国家与章节</span>
              </template>
              <el-select v-model="browseCountry" filterable style="width:100%" @change="loadChapters">
                <el-option v-for="c in countryList" :key="c.iso2"
                  :label="`${c.iso2} - ${c.name_en}（${(c.line_count || 0).toLocaleString()}条）`" :value="c.iso2" />
              </el-select>
              <el-input v-model="chapterFilter" placeholder="搜索章节..." clearable style="margin-top:8px" @input="filterChapters" />
              <div style="margin-top:8px;max-height:550px;overflow-y:auto">
                <div v-for="ch in filteredChapters" :key="ch.chapter"
                  @click="selectChapter(ch.chapter)"
                  :class="['chapter-item', { active: selectedChapter === ch.chapter }]">
                  <div class="chapter-info">
                    <span class="chapter-code">第{{ ch.chapter }}章</span>
                    <span class="chapter-title">{{ ch.title_cn || ch.title_en || '' }}</span>
                  </div>
                  <span class="chapter-count">{{ (ch.count || 0).toLocaleString() }}</span>
                </div>
                <el-empty v-if="!filteredChapters.length" description="暂无章节数据" :image-size="50" />
              </div>
            </el-card>
          </el-col>
          <el-col :span="17">
            <el-card shadow="never">
              <template #header>
                <span v-if="selectedChapter && chapterTitle">{{ chapterTitle }}</span>
                <span v-else>{{ browseCountry }} 税则数据</span>
                <span style="margin-left:8px;font-weight:normal;font-size:12px;color:#909399">
                  ({{ browseTotal }}条)
                </span>
              </template>
              <el-row :gutter="8" style="margin-bottom:12px">
                <el-col :span="10">
                  <el-input v-model="browseQuery" placeholder="搜索HS编码或商品名称（中/英文）" clearable @clear="loadBrowse" @keyup.enter="loadBrowse">
                    <template #prefix><el-icon><Search /></el-icon></template>
                  </el-input>
                </el-col>
                <el-col :span="4">
                  <el-button type="primary" @click="loadBrowse">搜索</el-button>
                </el-col>
              </el-row>

              <el-table :data="browseItems" border stripe size="small" max-height="560"
                @row-click="selectLine" highlight-current-row>
                <el-table-column type="index" label="序号" width="55" />
                <el-table-column prop="local_code" label="HS编码" width="140" fixed />
                <el-table-column prop="description_cn" label="中文名称" width="200" show-overflow-tooltip />
                <el-table-column prop="description_en" label="英文描述" min-width="280" show-overflow-tooltip />
                <el-table-column prop="mfn_rate" label="MFN%" width="80" align="center">
                  <template #default="{row}">
                    <el-tag v-if="row.mfn_rate != null" :type="row.mfn_rate > 5 ? 'danger' : (row.mfn_rate > 0 ? 'warning' : 'success')" size="small">
                      {{ Number(row.mfn_rate).toFixed(2) }}%
                    </el-tag>
                    <span v-else class="no-data">-</span>
                  </template>
                </el-table-column>
                <el-table-column prop="unit" label="单位" width="65" />
                <el-table-column label="操作" width="80" align="center">
                  <template #default="{row}">
                    <el-button type="primary" link size="small" @click.stop="quickLookup(row)">
                      查税率
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>

              <el-pagination
                v-if="totalPages > 1"
                v-model:current-page="browsePage"
                :page-size="browsePageSize"
                :total="browseTotal"
                layout="total, prev, pager, next, jumper"
                background
                style="margin-top:12px;justify-content:center"
                @current-change="loadBrowse"
              />

              <el-empty v-if="!browseItems.length && browseLoaded" description="无匹配数据" :image-size="60" />
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped>
.chapter-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  cursor: pointer;
  border-radius: 4px;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.15s;
}
.chapter-item:hover {
  background: #ecf5ff;
}
.chapter-item.active {
  background: #409eff;
  color: #fff;
}
.chapter-info {
  flex: 1;
  min-width: 0;
}
.chapter-code {
  font-size: 12px;
  font-weight: 600;
  display: block;
}
.chapter-title {
  font-size: 11px;
  color: #909399;
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 170px;
}
.chapter-item.active .chapter-title {
  color: rgba(255,255,255,0.8);
}
.chapter-count {
  font-size: 11px;
  color: #909399;
  white-space: nowrap;
  margin-left: 4px;
}
.chapter-item.active .chapter-count {
  color: rgba(255,255,255,0.85);
}
.no-data {
  color: #c0c4cc;
}
</style>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api/index.js'

const activeTab = ref('lookup')

// ========== Lookup Tab ==========
const form = ref({ hs_code: '8528420000', dest_country: 'US', origin_country: 'CN', value_usd: null })
const lookingUp = ref(false)
const lookedUp = ref(false)
const result = ref(null)
const countryList = ref([])

const mfnRate = computed(() => parseFloat(result.value?.mfn_rate || 0))
const totalAdditional = computed(() => {
  if (!result.value?.additional_duties) return 0
  return result.value.additional_duties.reduce((s, d) => s + parseFloat(d.rate_pct || 0), 0)
})

async function lookup() {
  lookingUp.value = true
  lookedUp.value = true
  try {
    const res = await api.tariffLookup({
      hs_code: form.value.hs_code,
      dest_country: form.value.dest_country,
      origin_country: form.value.origin_country,
      value_usd: form.value.value_usd || undefined,
    })
    result.value = res.data
  } catch {
    result.value = null
  }
  lookingUp.value = false
}

// ========== Browse Tab ==========
const browseCountry = ref('US')
const chaptersRaw = ref([])
const filteredChapters = ref([])
const chapterFilter = ref('')
const selectedChapter = ref('')
const browseQuery = ref('')
const browseItems = ref([])
const browsePage = ref(1)
const browsePageSize = 50
const browseTotal = ref(0)
const browseLoaded = ref(false)

const totalPages = computed(() => Math.ceil(browseTotal.value / browsePageSize))

const chapterTitle = computed(() => {
  const ch = chaptersRaw.value.find(c => c.chapter === selectedChapter.value)
  if (!ch) return ''
  return `第${ch.chapter}章 ${ch.title_cn || ch.title_en || ''}`
})

function filterChapters() {
  const q = (chapterFilter.value || '').toLowerCase()
  if (!q) {
    filteredChapters.value = [...chaptersRaw.value]
    return
  }
  filteredChapters.value = chaptersRaw.value.filter(c =>
    c.chapter.includes(q) ||
    (c.title_cn || '').toLowerCase().includes(q) ||
    (c.title_en || '').toLowerCase().includes(q)
  )
}

async function loadChapters() {
  selectedChapter.value = ''
  browsePage.value = 1
  try {
    const res = await api.tariffChapters({ country: browseCountry.value })
    chaptersRaw.value = res.data || []
    filterChapters()
  } catch {
    chaptersRaw.value = []
    filteredChapters.value = []
  }
  loadBrowse()
}

function selectChapter(ch) {
  selectedChapter.value = ch
  browsePage.value = 1
  browseQuery.value = ''
  loadBrowse()
}

async function loadBrowse() {
  browseLoaded.value = false
  try {
    const params = {
      country: browseCountry.value,
      page: browsePage.value,
      page_size: browsePageSize,
    }
    if (selectedChapter.value) params.prefix = selectedChapter.value
    if (browseQuery.value) params.q = browseQuery.value
    const res = await api.tariffBrowse(params)
    browseItems.value = res.data.items || []
    browseTotal.value = res.data.total || 0
  } catch {
    browseItems.value = []
    browseTotal.value = 0
  }
  browseLoaded.value = true
}

function selectLine(row) {
  form.value.hs_code = row.local_code
  form.value.dest_country = browseCountry.value
  activeTab.value = 'lookup'
  lookup()
}

function quickLookup(row) {
  form.value.hs_code = row.local_code
  form.value.dest_country = browseCountry.value
  activeTab.value = 'lookup'
  lookup()
}

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
