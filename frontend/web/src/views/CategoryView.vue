<script setup>
import { ref, computed } from 'vue'
import { categories } from '@/data/categories'

// State for active category selections
const selectedMainCategory = ref(categories[0])
const selectedSubCategory = ref(null)
const selectedItems = ref([]) // For the detailed filter

// Price filter state
const minPrice = ref(null)
const maxPrice = ref(null)

// Sort & View state
const sortOption = ref('popular')
const viewType = ref('grid') // 'grid' or 'list'

// Pagination state
const currentPage = ref(1)
const itemsPerPage = 12

// Mock Products Generator
const generateMockProducts = () => {
  const products = []
  for (let i = 1; i <= 50; i++) {
    products.push({
      id: i,
      title: `프리미엄 상품 테스트 ${i}`,
      price: Math.floor(Math.random() * 900 + 100) * 100, // 10,000 ~ 100,000
      imageUrl: `https://picsum.photos/seed/${i}/400/400`,
      brand: `브랜드 ${Math.floor(i % 5) + 1}`,
      isNew: i % 3 === 0
    })
  }
  return products
}

const allProducts = ref(generateMockProducts())

// Computed properties for UI
const filteredProducts = computed(() => {
  // In a real app, filtering happens here based on selected categories/price
  let filtered = [...allProducts.value]
  
  if (minPrice.value) {
    filtered = filtered.filter(p => p.price >= minPrice.value)
  }
  if (maxPrice.value) {
    filtered = filtered.filter(p => p.price <= maxPrice.value)
  }
  
  // Sort
  if (sortOption.value === 'price-high') {
    filtered.sort((a, b) => b.price - a.price)
  } else if (sortOption.value === 'price-low') {
    filtered.sort((a, b) => a.price - b.price)
  } else if (sortOption.value === 'newest') {
    filtered.sort((a, b) => b.isNew - a.isNew) // Simplistic
  }
  
  return filtered
})

const paginatedProducts = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  const end = start + itemsPerPage
  return filteredProducts.value.slice(start, end)
})

const totalPages = computed(() => {
  return Math.ceil(filteredProducts.value.length / itemsPerPage)
})

// Handlers
const selectMainCategory = (category) => {
  selectedMainCategory.value = category
  selectedSubCategory.value = null
  selectedItems.value = []
  currentPage.value = 1
}

const selectSubCategory = (sub) => {
  selectedSubCategory.value = sub
  selectedItems.value = []
  currentPage.value = 1
}

const toggleItemFilter = (item) => {
  const index = selectedItems.value.indexOf(item)
  if (index > -1) {
    selectedItems.value.splice(index, 1)
  } else {
    selectedItems.value.push(item)
  }
  currentPage.value = 1
}

const formatPrice = (price) => {
  return price.toLocaleString('ko-KR') + '원'
}
</script>

<template>
  <main class="category-page">
    <!-- Banner Area -->
    <section class="banner-section">
      <div class="banner-content">
        <h2>배너</h2>
        <p>시즌 한정 특가 및 기획전을 확인해보세요</p>
      </div>
    </section>

    <div class="container layout-container">
      <!-- Left Sidebar (Filters) -->
      <aside class="sidebar">
        <!-- 1. 카테고리 필터 -->
        <div class="filter-group">
          <h3 class="filter-title">1. 카테고리 제목</h3>
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

        <!-- 2. 가격 필터 -->
        <div class="filter-group">
          <h3 class="filter-title">2. 가격 필터</h3>
          <div class="price-inputs">
            <input type="number" v-model="minPrice" placeholder="최소 금액" />
            <span>~</span>
            <input type="number" v-model="maxPrice" placeholder="최대 금액" />
          </div>
        </div>

        <!-- 7. 브랜드 선택 및 부가 필터 -->
        <div class="filter-group detail-filter">
          <h3 class="filter-title">7. 브랜드 선택</h3>
          
          <div class="additional-filters">
            <h4 class="sub-title">상세 속성 필터</h4>
            <div class="filter-items-wrapper">
              <template v-if="selectedSubCategory">
                <label 
                  v-for="(item, idx) in selectedSubCategory.items" 
                  :key="idx" 
                  class="checkbox-label"
                >
                  <input 
                    type="checkbox" 
                    :value="item"
                    :checked="selectedItems.includes(item)"
                    @change="toggleItemFilter(item)"
                  />
                  <span class="custom-checkbox"></span>
                  <span class="label-text">{{ item }}</span>
                </label>
              </template>
              <template v-else-if="selectedMainCategory">
                <p class="empty-filter-msg">중분류를 선택하시면 상세 속성을 필터링 할 수 있습니다.</p>
              </template>
            </div>
          </div>
        </div>
      </aside>

      <!-- Right Main Content Area -->
      <section class="main-content">
        <!-- Header: Page Indicator, Sort, View Type -->
        <div class="content-header">
          <!-- 3. 페이지 표시 -->
          <div class="page-indicator">
            총 <strong>{{ filteredProducts.length }}</strong>개의 상품 
            <span>(페이지 {{ currentPage }}/{{ Math.max(1, totalPages) }})</span>
          </div>

          <div class="controls">
            <!-- 4. 정렬 옵션 -->
            <select v-model="sortOption" class="sort-select">
              <option value="popular">인기순</option>
              <option value="newest">최신순</option>
              <option value="price-low">가격 낮은 순</option>
              <option value="price-high">가격 높은 순</option>
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

        <!-- 6. 상품 리스트 영역 -->
        <div 
          class="product-list" 
          :class="viewType === 'grid' ? 'grid-view' : 'list-view'"
        >
          <div v-for="product in paginatedProducts" :key="product.id" class="product-card">
            <div class="image-wrapper">
              <img :src="product.imageUrl" :alt="product.title" loading="lazy" />
              <span v-if="product.isNew" class="badge-new">NEW</span>
            </div>
            <div class="product-info">
              <div class="brand">{{ product.brand }}</div>
              <h4 class="title">{{ product.title }}</h4>
              <div class="price">{{ formatPrice(product.price) }}</div>
            </div>
          </div>
        </div>

        <div v-if="paginatedProducts.length === 0" class="empty-state">
          조건에 맞는 상품이 없습니다.
        </div>

        <!-- 8. 페이지 버튼 (페이지네이션) -->
        <div class="pagination" v-if="totalPages > 1">
          <button 
            class="page-btn" 
            :disabled="currentPage === 1"
            @click="currentPage--"
          >
            <i class="fa-solid fa-chevron-left"></i>
          </button>
          
          <button 
            v-for="page in totalPages" 
            :key="page"
            class="page-num"
            :class="{ active: currentPage === page }"
            @click="currentPage = page"
          >
            {{ page }}
          </button>

          <button 
            class="page-btn" 
            :disabled="currentPage === totalPages"
            @click="currentPage++"
          >
            <i class="fa-solid fa-chevron-right"></i>
          </button>
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

/* Banner */
.banner-section {
  width: 100%;
  height: 250px;
  background: linear-gradient(135deg, #2c3e50, #3498db);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-bottom: 40px;
}

.banner-content {
  text-align: center;
}

.banner-content h2 {
  font-size: 48px;
  font-weight: 800;
  margin-bottom: 10px;
  letter-spacing: 2px;
}

.banner-content p {
  font-size: 16px;
  opacity: 0.9;
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

/* Price Filter */
.price-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
}

.price-inputs input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
}

.price-inputs input:focus {
  border-color: #3498db;
}

/* Detailed Filters */
.sub-title {
  font-size: 14px;
  font-weight: 600;
  color: #444;
  margin-bottom: 12px;
}

.filter-items-wrapper {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.empty-filter-msg {
  font-size: 12px;
  color: #999;
  line-height: 1.5;
}

.checkbox-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-size: 13px;
  color: #555;
  user-select: none;
}

.checkbox-label input {
  position: absolute;
  opacity: 0;
  cursor: pointer;
}

.custom-checkbox {
  width: 18px;
  height: 18px;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-right: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  background-color: white;
}

.checkbox-label input:checked ~ .custom-checkbox {
  background-color: #3498db;
  border-color: #3498db;
}

.checkbox-label input:checked ~ .custom-checkbox::after {
  content: '\f00c';
  font-family: 'Font Awesome 6 Free';
  font-weight: 900;
  color: white;
  font-size: 10px;
}

.checkbox-label:hover .custom-checkbox {
  border-color: #3498db;
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
  font-size: 14px;
  color: #555;
}

.page-indicator strong {
  color: #3498db;
  font-size: 16px;
}

.page-indicator span {
  color: #999;
  font-size: 13px;
  margin-left: 5px;
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

.badge-new {
  position: absolute;
  top: 10px;
  left: 10px;
  background: #e74c3c;
  color: white;
  font-size: 11px;
  font-weight: bold;
  padding: 4px 8px;
  border-radius: 4px;
  z-index: 1;
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

/* Empty State */
.empty-state {
  text-align: center;
  padding: 60px 0;
  color: #888;
  background: white;
  border-radius: 12px;
  font-size: 15px;
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  margin-top: 40px;
}

.page-btn, .page-num {
  border: 1px solid #ddd;
  background: white;
  border-radius: 6px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: #555;
  cursor: pointer;
  transition: all 0.2s;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #f9f9f9;
}

.page-btn:not(:disabled):hover, .page-num:hover {
  border-color: #3498db;
  color: #3498db;
}

.page-num.active {
  background: #3498db;
  border-color: #3498db;
  color: white;
  font-weight: bold;
}
</style>
