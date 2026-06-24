<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import ProductCard from '@/components/product/ProductCard.vue'

const router = useRouter()

// 필터 상태
const activeTab = ref('WISHLIST') // 'WISHLIST' | 'RECENT'
const searchKeyword = ref('')

// 데이터 상태
const products = ref([])
const isLoading = ref(false)
const currentPage = ref(1)
const hasMore = ref(true)

const fetchProducts = async (isLoadMore = false) => {
  if (isLoading.value) return
  if (!isLoadMore) {
    currentPage.value = 1
    products.value = []
    hasMore.value = true
  }
  
  if (!hasMore.value) return

  isLoading.value = true
  try {
    const endpoint = activeTab.value === 'WISHLIST' 
      ? '/api/users/me/wishlist'
      : '/api/users/me/view-history'

    const response = await axios.get(endpoint, {
      params: {
        keyword: searchKeyword.value || null,
        page: currentPage.value,
        size: 12
      },
      headers: {
        Authorization: `Bearer ${localStorage.getItem('accessToken')}`
      }
    })

    if (response.data.success) {
      const newItems = response.data.data.content
      if (isLoadMore) {
        products.value = [...products.value, ...newItems]
      } else {
        products.value = newItems
      }
      
      hasMore.value = !response.data.data.last
      if (hasMore.value) {
        currentPage.value += 1
      }
    }
  } catch (error) {
    console.error('Failed to fetch data:', error)
  } finally {
    isLoading.value = false
  }
}

const handleSearch = () => {
  fetchProducts(false)
}

const handleTabChange = (tab) => {
  activeTab.value = tab
  fetchProducts(false)
}

onMounted(() => {
  fetchProducts(false)
})

const formatPrice = (price) => {
  if (!price) return '가격 정보 없음'
  return price.toLocaleString('ko-KR') + '원'
}

const goToDetail = (product) => {
  const productId = product.productId
  if (!productId) return
  router.push(`/product/${productId}`)
}
</script>

<template>
  <div class="history-view">
    <!-- Filters Header -->
    <div class="filters-header">
      <div class="search-section">
        <div class="search-box">
          <input 
            type="text" 
            v-model="searchKeyword" 
            placeholder="상품명, 브랜드를 검색해보세요"
            @keyup.enter="handleSearch"
          />
          <i class="fa-solid fa-magnifying-glass" @click="handleSearch"></i>
        </div>
      </div>

      <div class="tab-section">
        <button 
          :class="{ active: activeTab === 'WISHLIST' }"
          @click="handleTabChange('WISHLIST')"
        >
          위시리스트
        </button>
        <button 
          :class="{ active: activeTab === 'RECENT' }"
          @click="handleTabChange('RECENT')"
        >
          최근 본 상품
        </button>
      </div>
    </div>

    <!-- Product List -->
    <div v-if="isLoading && products.length === 0" class="loading-state">
      <div class="spinner"></div>
      <p>목록을 불러오는 중입니다...</p>
    </div>

    <div v-else-if="products.length === 0" class="empty-state">
      <i class="fa-regular fa-folder-open"></i>
      <p>해당하는 내역이 없습니다.</p>
    </div>

    <div v-else class="product-grid">
      <ProductCard
        v-for="product in products"
        :key="product.productId"
        :name="product.title"
        :price="product.price"
        :imageUrl="product.imageUrl"
        @click="goToDetail(product)"
      />
    </div>

    <div v-if="hasMore && products.length > 0" class="load-more">
      <button class="btn-load-more" @click="fetchProducts(true)" :disabled="isLoading">
        {{ isLoading ? '불러오는 중...' : '더보기' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.history-view {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.03);
}

.filters-header {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eee;
}

.search-section {
  display: flex;
  gap: 15px;
}

.search-box {
  flex: 1;
  display: flex;
  align-items: center;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 0 15px;
  background: #f9f9f9;
}

.search-box input {
  flex: 1;
  border: none;
  background: transparent;
  padding: 12px 0;
  outline: none;
  font-size: 15px;
}

.search-box i {
  color: #888;
  cursor: pointer;
  padding: 10px;
}

.search-box i:hover {
  color: var(--primary-color);
}

.tab-section {
  display: flex;
  gap: 10px;
}

.tab-section button {
  flex: 1;
  padding: 12px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 500;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-section button.active {
  background: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

.tab-section button:hover:not(.active) {
  background: #f5f5f5;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.empty-state {
  text-align: center;
  padding: 80px 0;
  color: #888;
}

.empty-state i {
  font-size: 40px;
  margin-bottom: 15px;
  color: #ddd;
}

.loading-state {
  text-align: center;
  padding: 60px 0;
  color: #666;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.load-more {
  text-align: center;
  margin-top: 40px;
}

.btn-load-more {
  background: white;
  border: 1px solid #ddd;
  padding: 12px 40px;
  border-radius: 20px;
  font-size: 14px;
  color: #333;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-load-more:hover:not(:disabled) {
  background: #f9f9f9;
  border-color: #bbb;
}

.btn-load-more:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .product-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .search-section {
    flex-direction: column;
  }
}
</style>
