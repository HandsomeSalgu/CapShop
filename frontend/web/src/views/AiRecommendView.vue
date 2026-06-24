<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppBanner from '@/components/common/AppBanner.vue'
import { recommendationApi } from '@/api/recommendation'

const router = useRouter()
const recommendations = ref([])
const isLoading = ref(true)
const error = ref(null)

// 임시 AI 추천 이유 데이터
const aiReasons = [
  "회원님의 최근 쇼핑/클릭 로그를 분석하여 취향과 가장 일치하는 제품을 찾아냈습니다.",
  "설정하신 관심 카테고리와 연관성이 매우 높으며, 최근 가장 트렌디하게 떠오르는 인기 아이템입니다.",
  "회원님의 활동 기록과 일치하며, 사용자 리뷰가 압도적으로 긍정적인 베스트 상품입니다.",
  "위시리스트에 담으신 관심사들을 토대로 AI가 분석한 최적의 맞춤형 제품입니다."
]

const fetchRecommendations = async () => {
  isLoading.value = true
  error.value = null
  try {
    const result = await recommendationApi.getMyRecommendations(10)
    
    recommendations.value = result.map((item, index) => ({
      productId: item.productId || item.externalProductId || `temp_${index}`,
      externalProductId: item.externalProductId,
      title: item.title,
      brand: item.brand || '쇼핑몰',
      mallName: item.brand || '쇼핑몰',
      price: item.price,
      imageUrl: item.imageUrl,
      link: item.link || item.affiliateUrl || '',
      affiliateUrl: item.link || item.affiliateUrl || '',
      categoryName: item.categoryName,
      source: 'NAVER',
      reason: item.reason || aiReasons[index % aiReasons.length]
    }))
  } catch (err) {
    console.error('Recommendation fetch failed:', err)
    error.value = '추천 상품을 불러오는 데 실패했습니다.'
  } finally {
    isLoading.value = false
  }
}

const formatPrice = (price) => {
  if (!price) return '가격 정보 없음'
  return price.toLocaleString('ko-KR') + '원'
}

const goToDetail = (product) => {
  if (!product.productId || String(product.productId).startsWith('temp_')) return
  
  router.push({
    path: `/product/${product.productId}`,
    state: {
      productData: JSON.stringify(product),
      sourcePage: 'RECOMMENDATION_PAGE'
    }
  })
}

onMounted(() => {
  fetchRecommendations()
})
</script>

<template>
  <main class="ai-recommend-page">
    <AppBanner 
      title="AI 추천 상품 리스트" 
      subtitle="사용자 맞춤형 인공지능 쇼핑 제안" 
      bgImage="https://picsum.photos/1200/250?random=20" 
    />

    <div class="container">
      <section class="intro-section">
        <h2 class="section-title">AI 맞춤 추천 서비스</h2>
        <p class="intro-text">
          사용자의 관심 카테고리 및 유튜브 시청 기록을 기반으로 분석된 개인 맞춤형 상품 추천 서비스입니다.<br/>
          지금 가장 필요하실 만한 특별한 상품들을 만나보세요.
        </p>
      </section>

      <section class="recommend-list-section">
        <div v-if="isLoading" class="loading-state">
          <div class="spinner"></div>
          <p>AI가 맞춤형 상품을 분석하고 있습니다...</p>
        </div>
        
        <div v-else-if="error" class="error-state">
          {{ error }}
        </div>

        <div v-else class="recommend-list">
          <div v-if="recommendations.length === 0" class="empty-state">추천해 드릴 상품이 없습니다.</div>
          
          <div 
            v-for="product in recommendations" 
            :key="product.productId" 
            class="product-item" 
            @click="goToDetail(product)"
          >
            <!-- 왼쪽 세로로 긴 이미지 영역 -->
            <div class="image-section">
              <img :src="product.imageUrl" :alt="product.title" loading="lazy" />
            </div>

            <!-- 오른쪽 정보 영역 -->
            <div class="info-section">
              <div class="product-basic-info">
                <div class="brand">{{ product.brand }}</div>
                <h4 class="title" v-html="product.title"></h4>
                <div class="price">{{ formatPrice(product.price) }}</div>
              </div>

              <div class="ai-reason-block">
                <div class="reason-title">
                  <i class="fa-solid fa-sparkles reason-icon"></i> AI 추천 이유
                </div>
                <p class="reason-text">{{ product.reason }}</p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </main>
</template>

<style scoped>
.ai-recommend-page {
  background-color: #ffffff; /* 깔끔하게 화이트 톤으로 변경 */
  min-height: 100vh;
  padding-bottom: 100px;
}

.container {
  max-width: 1000px; /* 리스트 집중을 위해 폭을 약간 줄임 */
  margin: 0 auto;
  padding: 0 20px;
}

/* Intro Section */
.intro-section {
  text-align: center;
  margin: 60px 0;
}

.section-title {
  font-size: 26px;
  font-weight: 700;
  color: #222;
  margin: 0 0 15px 0;
}

.intro-text {
  font-size: 15px;
  color: #666;
  line-height: 1.6;
  margin: 0;
}

/* Recommend List (표/선 제거, 배치 중심) */
.recommend-list {
  display: flex;
  flex-direction: column;
  gap: 80px; /* 상품 간격 넓게 확보 */
  margin-top: 40px;
}

.product-item {
  display: flex;
  gap: 50px;
  align-items: flex-start;
  cursor: pointer;
  transition: opacity 0.2s;
}

.product-item:hover {
  opacity: 0.8;
}

/* Image Section (세로로 길게) */
.image-section {
  width: 280px;
  aspect-ratio: 3 / 4; /* 세로로 긴 비율 */
  flex-shrink: 0;
  background-color: #f8f8f8;
  border: 1px solid #eaeaea; /* 설계도 느낌처럼 아주 연한 테두리 */
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-section img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Info Section */
.info-section {
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  padding-top: 20px;
  flex: 1;
}

.product-basic-info {
  margin-bottom: 40px;
}

.brand {
  font-size: 14px;
  color: #888;
  margin-bottom: 8px;
}

.title {
  font-size: 22px;
  font-weight: 600;
  color: #222;
  margin: 0 0 12px 0;
  line-height: 1.4;
  word-break: keep-all;
}

.price {
  font-size: 20px;
  font-weight: 700;
  color: #222;
}

/* AI Reason Block */
.ai-reason-block {
  margin-top: 20px;
}

.reason-title {
  font-size: 16px;
  font-weight: 700;
  color: #222;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.reason-icon {
  color: #ff3f3f; /* AI 강조 컬러 */
  font-size: 14px;
}

.reason-text {
  font-size: 15px;
  line-height: 1.6;
  color: #555;
  margin: 0;
  word-break: keep-all;
}

/* Loading & Error */
.loading-state, .error-state, .empty-state {
  text-align: center;
  padding: 100px 0;
  color: #777;
  font-size: 16px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #333;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Responsive */
@media (max-width: 768px) {
  .product-item {
    flex-direction: column;
    gap: 30px;
  }

  .image-section {
    width: 100%;
    max-width: 320px;
    margin: 0 auto;
  }
  
  .info-section {
    padding-top: 0;
    text-align: center;
    align-items: center;
  }
  
  .reason-title {
    justify-content: center;
  }
}
</style>
