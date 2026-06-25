<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { categories } from '@/data/categories'
import AppBanner from '@/components/common/AppBanner.vue'
import { commerceApi } from '@/api/commerce'

const route = useRoute()

// State for active category selections
const selectedMainCategory = ref(categories[0])
const selectedSubCategory = ref(null)
const selectedKeyword = ref(null) // 단일 선택용
const customSearchQuery = ref('') // 자유 검색어

// Sort & View state
const sortOption = ref('sim') // sim, date, asc, dsc
const viewType = ref('grid') // 'grid' or 'list'

// Products state
const products = ref([])
const isLoading = ref(false)
const error = ref(null)

// Infinite Scroll state
const currentStart = ref(1)
const isFinished = ref(false)
const loadMoreTrigger = ref(null)

// Handlers
const fetchProducts = async (isLoadMore = false) => {
  // Determine the search query
  let query = ''
  if (customSearchQuery.value) {
    query = customSearchQuery.value
  } else if (selectedKeyword.value) {
    // 키워드(칩)를 클릭했을 경우 해당 키워드만 검색어로 사용
    query = selectedKeyword.value
  } else if (selectedSubCategory.value) {
    // 소분류 선택 시, 첫 번째 키워드를 기본으로 사용
    query = selectedSubCategory.value.items[0] || selectedSubCategory.value.name
  } else if (selectedMainCategory.value) {
    // 대분류만 선택 시, 대분류 이름을 검색어로 사용하되 불필요한 특수문자 제거
    query = selectedMainCategory.value.name.replace(/[^a-zA-Z가-힣0-9 ]/g, '')
  }

  if (!query) return
  if (isFinished.value && isLoadMore) return

  try {
    isLoading.value = true
    error.value = null
    // 네이버 쇼핑 API 호출 (검색어, 가져올 개수, 시작위치, 정렬 옵션)
    const result = await commerceApi.searchProducts(query, 10, currentStart.value, sortOption.value)
    
    if (result.length === 0) {
      isFinished.value = true
      return
    }

    if (isLoadMore) {
      products.value = [...products.value, ...result]
    } else {
      products.value = result
    }
  } catch (e) {
    console.error(e)
    if (!isLoadMore) {
      error.value = '상품을 불러오는데 실패했습니다.'
      products.value = []
    }
  } finally {
    isLoading.value = false
  }
}

const resetAndFetch = () => {
  products.value = []
  currentStart.value = 1
  isFinished.value = false
  fetchProducts()
}

const selectMainCategory = (category) => {
  if (selectedMainCategory.value?.id === category.id && !customSearchQuery.value) return
  customSearchQuery.value = ''
  selectedMainCategory.value = category
  selectedSubCategory.value = null
  selectedKeyword.value = null
  resetAndFetch()
}

const selectSubCategory = (sub) => {
  if (selectedSubCategory.value?.id === sub.id && !customSearchQuery.value) return
  customSearchQuery.value = ''
  selectedSubCategory.value = sub
  selectedKeyword.value = null
  resetAndFetch()
}

const selectKeyword = (keyword) => {
  if (selectedKeyword.value === keyword && !customSearchQuery.value) return
  customSearchQuery.value = ''
  selectedKeyword.value = keyword
  resetAndFetch()
}

const handleCustomSearch = (e) => {
  const val = e.target.value.trim()
  if (!val) return
  
  customSearchQuery.value = val
  selectedMainCategory.value = null
  selectedSubCategory.value = null
  selectedKeyword.value = null
  resetAndFetch()
}

// Watchers
watch(sortOption, () => {
  resetAndFetch()
})

watch(() => route.query.q, (newQ) => {
  if (newQ) {
    customSearchQuery.value = newQ
    selectedMainCategory.value = null
    selectedSubCategory.value = null
    selectedKeyword.value = null
    resetAndFetch()
  }
})

onMounted(() => {
  if (route.query.q) {
    customSearchQuery.value = route.query.q
    selectedMainCategory.value = null
    selectedSubCategory.value = null
    selectedKeyword.value = null
  }

  // 초기 로드 시 상품 가져오기
  resetAndFetch()

  // IntersectionObserver 설정
  const observer = new IntersectionObserver((entries) => {
    const entry = entries[0]
    if (entry.isIntersecting && !isLoading.value && !isFinished.value && products.value.length > 0) {
      currentStart.value += 10
      fetchProducts(true)
    }
  }, {
    rootMargin: '100px'
  })

  if (loadMoreTrigger.value) {
    observer.observe(loadMoreTrigger.value)
  }
})

const formatPrice = (price) => {
  if (!price) return '가격 정보 없음'
  return price.toLocaleString('ko-KR') + '원'
}

const router = useRouter()
const goToDetail = (product) => {
  const productId = product.externalProductId || product.productId
  if (!productId) return
  
  router.push({
    path: `/product/${productId}`,
    state: {
      productData: JSON.stringify(product),
      sourcePage: 'PRODUCT_LIST'
    }
  })
}
</script>

<template>
  <main class="category-page">
    <!-- Banner Area -->
    <AppBanner title="배너" subtitle="시즌 한정 특가 및 기획전을 확인해보세요" bgImage="https://picsum.photos/1200/250" />

    <div class="container layout-container">
      <!-- Left Sidebar (Filters) -->
      <aside class="sidebar">
        <!-- 1. 카테고리 필터 -->
        <div class="filter-group">
          <h3 class="filter-title">카테고리</h3>
          <ul class="main-category-list">
            <li 
              v-for="cat in categories" 
              :key="cat.id"
              :class="{ active: selectedMainCategory?.id === cat.id }"
              @click="selectMainCategory(cat)"
            >
              {{ cat.name }}
            </li>
          </ul>
          
          <div v-if="selectedMainCategory" class="sub-category-list">
            <div 
              v-for="sub in selectedMainCategory.subCategories" 
              :key="sub.id"
              class="sub-item"
              :class="{ active: selectedSubCategory?.id === sub.id }"
              @click="selectSubCategory(sub)"
            >
              {{ sub.name }}
            </div>
          </div>
        </div>

        <!-- 2. 상세 키워드 칩 (Chip) -->
        <div class="filter-group detail-filter">
          <h3 class="filter-title">상세 키워드</h3>
          
          <div class="additional-filters">
            <div class="chip-wrapper">
              <template v-if="selectedSubCategory">
                <button 
                  v-for="(item, idx) in selectedSubCategory.items" 
                  :key="idx" 
                  class="keyword-chip"
                  :class="{ active: (!selectedKeyword && idx === 0) || selectedKeyword === item }"
                  @click="selectKeyword(item)"
                >
                  {{ item }}
                </button>
              </template>
              <template v-else-if="selectedMainCategory">
                <p class="empty-filter-msg">소분류를 선택하시면 상세 키워드를 볼 수 있습니다.</p>
              </template>
            </div>
          </div>
        </div>
      </aside>

      <!-- Right Main Content Area -->
      <section class="main-content">
        <!-- Header: Page Indicator, Sort, View Type -->
        <div class="content-header">
          <!-- 3. 검색된 상품 표시 및 커스텀 검색 -->
          <div class="page-indicator">
            <div class="breadcrumb-container" style="font-size: 1.1rem; font-weight: 600; color: #333; margin-bottom: 0.5rem;" v-if="selectedMainCategory">
              <span>
                ( {{ selectedMainCategory.name }} 
                <span v-if="selectedSubCategory">> {{ selectedSubCategory.name }}</span>
                )
              </span>
            </div>
            <div class="custom-search-container">
              <input 
                type="text" 
                class="custom-search-input"
                placeholder="원하시는 상품을 검색해보세요" 
                :value="customSearchQuery || selectedKeyword || selectedSubCategory?.items?.[0] || selectedMainCategory?.name || ''"
                @keyup.enter="handleCustomSearch"
              />
              <i class="fa-solid fa-magnifying-glass search-icon"></i>
            </div>
          </div>

          <div class="controls">
            <!-- 4. 정렬 옵션 (네이버 API 기준) -->
            <select v-model="sortOption" class="sort-select">
              <option value="sim">정확도순</option>
              <option value="date">최신순</option>
              <option value="asc">가격 낮은 순</option>
              <option value="dsc">가격 높은 순</option>
            </select>

            <!-- 5. 뷰 타입 전환 -->
            <div class="view-type-toggle">
              <button 
                :class="{ active: viewType === 'grid' }" 
                @click="viewType = 'grid'"
                title="바둑판형"
              >
                <i class="fa-solid fa-table-cells-large"></i>
              </button>
              <button 
                :class="{ active: viewType === 'list' }" 
                @click="viewType = 'list'"
                title="리스트형"
              >
                <i class="fa-solid fa-list"></i>
              </button>
            </div>
          </div>
        </div>

        <!-- 초기 로딩 상태 (상품이 없을 때만) -->
        <div v-if="isLoading && products.length === 0" class="loading-state">
          <div class="spinner"></div>
          <p>상품을 불러오는 중입니다...</p>
        </div>

        <!-- 에러 상태 -->
        <div v-else-if="error && products.length === 0" class="error-state">
          {{ error }}
        </div>

        <!-- 6. 상품 리스트 영역 -->
        <div v-else
          class="product-list" 
          :class="viewType === 'grid' ? 'grid-view' : 'list-view'"
        >
          <div v-for="product in products" :key="product.externalProductId || product.productId" class="product-card" @click="goToDetail(product)">
            <div class="image-wrapper">
              <img :src="product.imageUrl" :alt="product.title" loading="lazy" />
            </div>
            <div class="product-info">
              <div class="brand">{{ product.brand || product.mallName || '쇼핑몰' }}</div>
              <h4 class="title">{{ product.title }}</h4>
              <div class="price">{{ formatPrice(product.price) }}</div>
            </div>
          </div>
        </div>

        <!-- Intersection Observer Trigger -->
        <div ref="loadMoreTrigger" class="load-more-trigger"></div>

        <div v-if="isLoading && products.length > 0" class="loading-more">
          <div class="spinner small"></div>
          <p>더 불러오는 중...</p>
        </div>

        <div v-if="isFinished && products.length > 0" class="finished-state">
          더 이상 상품이 없습니다.
        </div>

        <div v-if="!isLoading && !error && products.length === 0" class="empty-state">
          조건에 맞는 상품이 없습니다.
        </div>
      </section>
    </div>
  </main>
</template>

<style scoped>
/* Page Layout */
.category-page {
  background-color: var(--background-color, #f8f9fa);
  min-height: 100vh;
  padding-bottom: 60px;
}

/* Container */
.layout-container {
  display: flex;
  gap: 30px;
  align-items: flex-start;
}

/* Sidebar */
.sidebar {
  width: 250px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.filter-group {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.03);
}

.filter-title {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 16px;
  color: #333;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

/* Category Filter */
.main-category-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.main-category-list li {
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 6px;
  font-size: 14px;
  color: #555;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.main-category-list li:hover {
  background-color: #f0f4f8;
  color: #3498db;
}

.main-category-list li.active {
  background-color: #3498db;
  color: white;
  font-weight: 600;
}

.sub-category-list {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px dashed #eee;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sub-item {
  font-size: 13px;
  color: #666;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 4px;
  transition: all 0.2s;
  position: relative;
  padding-left: 20px;
}

.sub-item::before {
  content: '-';
  position: absolute;
  left: 8px;
  color: #ccc;
}

.sub-item:hover, .sub-item.active {
  color: #3498db;
  font-weight: 500;
}

/* Chips Filter */
.chip-wrapper {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.keyword-chip {
  padding: 6px 14px;
  background: #f1f3f5;
  border: 1px solid #e9ecef;
  border-radius: 20px;
  font-size: 13px;
  color: #555;
  cursor: pointer;
  transition: all 0.2s;
  outline: none;
}

.keyword-chip:hover {
  background: #e2e6ea;
  color: #333;
}

.keyword-chip.active {
  background: #3498db;
  border-color: #3498db;
  color: white;
  font-weight: 500;
}

.empty-filter-msg {
  font-size: 12px;
  color: #999;
  line-height: 1.5;
}

/* Main Content Area */
.main-content {
  flex: 1;
  min-width: 0;
}

/* Content Header */
.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  background: white;
  padding: 15px 20px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.03);
}

.page-indicator {
  flex: 1;
  margin-right: 20px;
}

.custom-search-container {
  position: relative;
  max-width: 400px;
}

.custom-search-input {
  width: 100%;
  padding: 10px 40px 10px 16px;
  border: 1px solid #ddd;
  border-radius: 20px;
  font-size: 15px;
  color: #333;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.custom-search-input:focus {
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

.search-icon {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: #999;
  pointer-events: none;
}

.controls {
  display: flex;
  align-items: center;
  gap: 15px;
}

.sort-select {
  padding: 8px 30px 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  color: #444;
  outline: none;
  appearance: none;
  background: url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2212%22%20height%3D%2212%22%20viewBox%3D%220%200%2012%2012%22%3E%3Cpath%20fill%3D%22%23999%22%20d%3D%22M10.293%203.293L6%207.586%201.707%203.293A1%201%200%2000.293%204.707l5%205a1%201%200%20001.414%200l5-5a1%201%200%2010-1.414-1.414z%22%2F%3E%3C%2Fsvg%3E') no-repeat right 10px center;
  background-color: white;
}

.view-type-toggle {
  display: flex;
  background: #f1f3f5;
  border-radius: 6px;
  padding: 3px;
}

.view-type-toggle button {
  border: none;
  background: transparent;
  width: 32px;
  height: 32px;
  border-radius: 4px;
  color: #888;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.view-type-toggle button.active {
  background: white;
  color: #3498db;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

/* Product List - Grid View */
.product-list.grid-view {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 24px;
}

.grid-view .product-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0,0,0,0.04);
  transition: transform 0.3s, box-shadow 0.3s;
  cursor: pointer;
  display: flex;
  flex-direction: column;
}

.grid-view .product-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0,0,0,0.08);
}

.image-wrapper {
  position: relative;
  width: 100%;
  aspect-ratio: 1 / 1;
  background-color: #f8f9fa;
  overflow: hidden;
}

.image-wrapper img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s;
}

.grid-view .product-card:hover .image-wrapper img {
  transform: scale(1.05);
}

.product-info {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.brand {
  font-size: 12px;
  color: #888;
}

.title {
  font-size: 15px;
  color: #333;
  margin: 0;
  font-weight: 500;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.price {
  font-size: 18px;
  font-weight: 700;
  color: #e74c3c;
  margin-top: auto;
}

/* Product List - List View */
.product-list.list-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.list-view .product-card {
  display: flex;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0,0,0,0.04);
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
  height: 180px;
}

.list-view .product-card:hover {
  transform: translateX(5px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.06);
}

.list-view .image-wrapper {
  width: 180px;
  height: 100%;
  flex-shrink: 0;
}

.list-view .product-info {
  justify-content: center;
  padding: 24px;
}

.list-view .title {
  font-size: 18px;
  -webkit-line-clamp: 1;
}

.list-view .price {
  font-size: 20px;
  margin-top: 10px;
}

/* Empty/Loading/Error State */
.empty-state, .error-state, .loading-state {
  text-align: center;
  padding: 60px 0;
  color: #888;
  background: white;
  border-radius: 12px;
  font-size: 15px;
}

.error-state {
  color: #e74c3c;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 무한 스크롤용 */
.load-more-trigger {
  height: 20px;
  margin-top: 20px;
}

.loading-more {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px 0;
  color: #888;
  font-size: 14px;
}

.spinner.small {
  width: 24px;
  height: 24px;
  border-width: 3px;
  margin-bottom: 8px;
}

.finished-state {
  text-align: center;
  padding: 30px 0;
  color: #aaa;
  font-size: 14px;
}
</style>
