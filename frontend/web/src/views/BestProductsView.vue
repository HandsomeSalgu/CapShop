<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import AppBanner from '@/components/common/AppBanner.vue'
import axios from 'axios'

const router = useRouter()

// State
const bestProducts = ref([])
const isLoading = ref(false)
const error = ref(null)

const top3Products = computed(() => bestProducts.value.slice(0, 3))
const rankingProducts = computed(() => bestProducts.value.slice(3, 20))

// Handlers
const formatPrice = (price) => {
  if (!price) return '가격 정보 없음'
  return price.toLocaleString('ko-KR') + '원'
}

const goToDetail = (product) => {
  const productId = product.externalProductId || product.productId
  if (!productId) return
  
  router.push({
    path: `/product/${productId}`,
    state: {
      productData: JSON.stringify(product),
      sourcePage: 'BEST_PRODUCTS'
    }
  })
}

const fetchBestProducts = async () => {
  isLoading.value = true
  error.value = null
  try {
    const response = await axios.get('http://localhost:8080/api/products/best?limit=20')
    if (response.data.success) {
      bestProducts.value = response.data.data
    }
  } catch (err) {
    console.error(err)
    error.value = '베스트 상품을 불러오는데 실패했습니다.'
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchBestProducts()
})

</script>

<template>
  <main class="best-products-page">
    <AppBanner title="베스트" subtitle="지금 가장 사랑받는 핫한 상품들을 만나보세요" bgImage="https://picsum.photos/1200/250?random=10" />

    <div class="container">
      <!-- 이달의 제일 핫한 제품 TOP 3 -->
      <section class="top3-section">
        <h2 class="section-title">
          이달의 핫한 제품 TOP 3
        </h2>
        
        <div v-if="isLoading" class="loading-state">
          <div class="spinner"></div>
          <p>이달의 핫한 제품을 불러오는 중입니다...</p>
        </div>
        
        <div v-else-if="error" class="error-state">
          {{ error }}
        </div>
        
        <div v-else class="top3-grid">
          <div v-for="(product, index) in top3Products" :key="product.externalProductId || product.productId" class="product-card" @click="goToDetail(product)">
            <div class="rank-badge">BEST {{ index + 1 }}</div>
            <div class="image-wrapper">
              <img :src="product.imageUrl" :alt="product.title" loading="lazy" />
            </div>
            <div class="product-info">
              <div class="brand">{{ product.brand || product.mallName || '쇼핑몰' }}</div>
              <h4 class="title" v-html="product.title"></h4>
              <div class="price">{{ formatPrice(product.price) }}</div>
            </div>
          </div>
        </div>
      </section>

      <!-- 순위 리스트 (4위 ~ 20위) -->
      <section class="top10-section">
        <h2 class="section-title">
          월간 베스트 랭킹
        </h2>
        <div class="list-header">
          <div class="col-rank">순위</div>
          <div class="col-info">상품 정보</div>
        </div>

        <div v-if="isLoading" class="loading-state">
          <div class="spinner"></div>
          <p>상품 랭킹을 불러오는 중입니다...</p>
        </div>
        
        <div v-else-if="error" class="error-state">
          {{ error }}
        </div>
        
        <div v-else class="top10-list">
          <div v-if="rankingProducts.length === 0" class="empty-state">해당 상품 랭킹 데이터가 없습니다.</div>
          
          <div v-for="(product, index) in rankingProducts" :key="product.externalProductId || product.productId" class="list-row" @click="goToDetail(product)">
            <div class="col-rank">
              <span class="rank-number">{{ index + 4 }}</span>
            </div>
            <div class="col-info">
              <div class="list-image-wrapper">
                <img :src="product.imageUrl" :alt="product.title" loading="lazy" />
              </div>
              <div class="list-product-details">
                <div class="brand">{{ product.brand || product.mallName || '쇼핑몰' }}</div>
                <h4 class="title" v-html="product.title"></h4>
                <div class="price">{{ formatPrice(product.price) }}</div>
                <p class="description">{{ product.category1Name }} <span v-if="product.category2Name">> {{ product.category2Name }}</span></p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </main>
</template>

<style scoped>
.best-products-page {
  background-color: var(--background-color, #f8f9fa);
  min-height: 100vh;
  padding-bottom: 80px;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.section-title {
  font-size: 24px;
  font-weight: 700;
  color: #333;
  margin: 60px 0 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: 10px;
}

.badge {
  background-color: #e74c3c;
  color: white;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: bold;
}

/* TOP 3 Section */
.top3-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 30px;
}

.product-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0,0,0,0.05);
  transition: transform 0.3s, box-shadow 0.3s;
  cursor: pointer;
  position: relative;
  display: flex;
  flex-direction: column;
}

.product-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 25px rgba(0,0,0,0.1);
}

.rank-badge {
  position: absolute;
  top: 15px;
  left: 15px;
  background: rgba(231, 76, 60, 0.9);
  color: white;
  padding: 6px 12px;
  border-radius: 20px;
  font-weight: bold;
  font-size: 14px;
  z-index: 10;
  box-shadow: 0 2px 5px rgba(0,0,0,0.2);
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

.product-card:hover .image-wrapper img {
  transform: scale(1.05);
}

.product-info {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}

.brand {
  font-size: 13px;
  color: #888;
}

.title {
  font-size: 16px;
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
  font-size: 20px;
  font-weight: 700;
  color: #e74c3c;
  margin-top: auto;
}

/* TOP Ranking List Section */
.list-header {
  display: flex;
  padding: 15px 20px;
  background: white;
  border-top: 2px solid #333;
  border-bottom: 1px solid #ddd;
  font-weight: bold;
  color: #333;
  font-size: 15px;
}

.col-rank {
  width: 100px;
  text-align: center;
  flex-shrink: 0;
}

.col-info {
  flex: 1;
  padding-left: 20px;
}

.top10-list {
  background: white;
  border-bottom: 1px solid #ddd;
}

.list-row {
  display: flex;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
  transition: background-color 0.2s;
  cursor: pointer;
}

.list-row:last-child {
  border-bottom: none;
}

.list-row:hover {
  background-color: #f8f9fa;
}

.rank-number {
  font-size: 24px;
  font-weight: 800;
  color: #999;
  font-style: italic;
}

.list-image-wrapper {
  width: 120px;
  height: 120px;
  border-radius: 8px;
  overflow: hidden;
  background: #f8f9fa;
  flex-shrink: 0;
}

.list-image-wrapper img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.col-info {
  display: flex;
  gap: 20px;
  align-items: center;
}

.list-product-details {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.list-product-details .title {
  font-size: 18px;
  -webkit-line-clamp: 1;
}

.list-product-details .price {
  font-size: 18px;
  margin-top: 5px;
}

.description {
  font-size: 13px;
  color: #888;
  margin: 0;
  margin-top: 5px;
}

/* Loading & Error States */
.loading-state, .error-state, .empty-state {
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

@media (max-width: 768px) {
  .top3-grid {
    grid-template-columns: 1fr;
  }
  
  .col-rank {
    width: 60px;
  }
  
  .list-image-wrapper {
    width: 80px;
    height: 80px;
  }
  
  .list-product-details .title {
    font-size: 15px;
  }
}
</style>
