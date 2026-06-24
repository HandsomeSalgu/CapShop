<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import ProductCard from '@/components/product/ProductCard.vue'
import { recommendationApi } from '@/api/recommendation'

const router = useRouter()
const products = ref([])
const isLoading = ref(true)

onMounted(async () => {
  try {
    const data = await recommendationApi.getMyRecommendations(3)
    if (data && data.length > 0) {
      products.value = data.map(item => ({
        ...item,
        productId: item.productId || item.externalProductId,
        externalProductId: item.externalProductId,
        mallName: item.brand || '쇼핑몰',
        affiliateUrl: item.link || item.affiliateUrl || '',
        source: 'NAVER'
      }))
    } else {
      // Fallback dummy data if no recommendations returned
      products.value = [
        { productId: 1, title: 'AI 추천 상품이 없습니다.', price: 0, imagePlaceholder: '상품 없음' }
      ]
    }
  } catch (error) {
    console.error('Failed to load recommendations:', error)
    products.value = [
      { productId: 1, title: '추천 상품을 불러오지 못했습니다.', price: 0, imagePlaceholder: '오류' }
    ]
  } finally {
    isLoading.value = false
  }
})

const goToRecommendView = () => {
  router.push('/recommend')
}

const handleProductClick = (product) => {
  if (!product.productId && !product.externalProductId) return
  
  const targetId = product.externalProductId || product.productId
  if (String(targetId).startsWith('temp_')) return

  router.push({
    path: `/product/${targetId}`,
    state: {
      productData: JSON.stringify(product),
      sourcePage: 'MAIN_RECOMMENDATION'
    }
  })
}
</script>

<template>
  <section class="section">
    <div class="section-header">
      <h2>AI 추천 상품 리스트</h2>
      <p>사용자 활동 및 관심사를 분석하여 제공하는 맞춤 추천 서비스입니다.</p>
      <a href="#" class="more-btn" @click.prevent="goToRecommendView">더보기</a>
    </div>
    
    <div v-if="isLoading" class="loading-state">
      <div class="spinner"></div>
      <p>AI가 맞춤 상품을 분석 중입니다...</p>
    </div>
    
    <div v-else class="grid-3">
      <ProductCard 
        v-for="item in products" 
        :key="item.productId || item.externalProductId || item.title"
        :name="item.title"
        :price="item.price"
        :imageUrl="item.imageUrl"
        :link="item.link || item.affiliateUrl"
        :imagePlaceholder="item.imagePlaceholder || '이미지 준비중'"
        @click="handleProductClick(item)"
      />
    </div>
  </section>
</template>

<style scoped>
.section {
  margin-bottom: 120px;
}

.section-header {
  text-align: center;
  margin-bottom: 50px;
  position: relative;
}

.section-header h2 {
  font-size: 30px;
  font-weight: 600;
  color: var(--primary-color);
  margin-bottom: 10px;
}

.section-header p {
  font-size: 15px;
  color: var(--text-muted);
}

.more-btn {
  position: absolute;
  right: 0;
  bottom: 0;
  font-size: 13px;
  font-weight: 500;
  text-transform: uppercase;
  border-bottom: 1px solid var(--primary-color);
  padding-bottom: 2px;
}

.grid-3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 30px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 50px 0;
  color: var(--text-muted);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(0,0,0,0.1);
  border-left-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

:deep(.grid-3 .img-placeholder) {
  aspect-ratio: 1;
}
</style>
