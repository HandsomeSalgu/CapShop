<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppBanner from '@/components/common/AppBanner.vue'
import { useAuthStore } from '@/stores/auth'
import { userEventApi } from '@/api/userEvent'
import { wishlistApi } from '@/api/wishlist'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const productId = route.params.id

// ==========================================
// 1. 상태 관리 (State)
// ==========================================
const product = ref(null)
const isLoading = ref(true)
const error = ref(null)

const selectedImage = ref('')

const relatedProducts = ref([])
const isWishlisted = ref(false)

// ==========================================
// 2. 임시 데이터 로드 함수 (API 연동 대체)
// ==========================================
const fetchProductDetail = async (id) => {
  isLoading.value = true
  error.value = null
  
  try {
    const stateData = history.state.productData
    if (stateData) {
      const parsed = JSON.parse(stateData)
      product.value = {
        id: parsed.externalProductId || parsed.productId || id,
        title: parsed.title || '상품명 없음',
        price: parsed.price || parsed.lprice || 0,
        summary: parsed.mallName || parsed.brand ? `${parsed.mallName || parsed.brand}에서 판매 중인 상품입니다.` : '해당 쇼핑몰에서 상품 상세 정보를 확인해보세요.',
        mainImage: parsed.imageUrl || parsed.image || 'https://via.placeholder.com/600',
        link: parsed.affiliateUrl || parsed.link || ''
      }
      selectedImage.value = product.value.mainImage
      
      // 로그 저장 및 내부 productId 확보
      if (authStore.isLoggedIn) {
        try {
          const res = await userEventApi.logProductDetailView({
            productId: product.value.id,
            product: parsed,
            sourcePage: history.state.sourcePage || 'PRODUCT_DETAIL'
          })
          if (res && res.data && res.data.productId) {
            product.value.id = res.data.productId
          }
          
          // 위시리스트 추가 여부 확인
          const wishRes = await wishlistApi.checkWishlist(product.value.id)
          if (wishRes && wishRes.data !== undefined) {
            isWishlisted.value = wishRes.data
          }
        } catch (err) {
          console.error('이벤트 로그 저장 실패:', err)
        }
      }
    } else {
      error.value = '상품 데이터를 불러올 수 없습니다. 카테고리 페이지를 통해 접근해주세요.'
    }
    
    // 관련 상품 Mock
    relatedProducts.value = [
      { id: 101, title: '고속 무선 충전 패드 15W', price: 25000, image: 'https://picsum.photos/300/300?random=10' },
      { id: 102, title: '알루미늄 노트북 거치대', price: 32000, image: 'https://picsum.photos/300/300?random=11' },
      { id: 103, title: '기계식 키보드 청축', price: 89000, image: 'https://picsum.photos/300/300?random=12' },
      { id: 104, title: '고급형 팜레스트 손목보호대', price: 15000, image: 'https://picsum.photos/300/300?random=13' },
    ]
  } catch (err) {
    console.error(err)
    error.value = '상품 정보를 불러오는 데 실패했습니다.'
  } finally {
    isLoading.value = false
  }
}

// ==========================================
// 3. 동작(Action) 함수
// ==========================================

const formatPrice = (price) => {
  return price.toLocaleString('ko-KR') + '원'
}

const toggleWishlist = async () => {
  if (!authStore.isLoggedIn) {
    alert('로그인이 필요한 서비스입니다.')
    router.push('/login')
    return
  }
  
  try {
    if (isWishlisted.value) {
      await wishlistApi.removeWishlist(product.value.id)
      isWishlisted.value = false
      alert('위시리스트에서 상품이 제거되었습니다.')
    } else {
      await wishlistApi.addWishlist(product.value.id)
      isWishlisted.value = true
      alert('위시리스트에 상품이 추가되었습니다.')
    }
  } catch (error) {
    console.error('위시리스트 처리 중 오류 발생:', error)
    if (error.response?.data?.message) {
      alert(error.response.data.message)
    } else {
      alert('위시리스트 처리에 실패했습니다. 다시 시도해주세요.')
    }
  }
}

const goToLink = () => {
  if (product.value.link) {
    window.open(product.value.link, '_blank')
  } else {
    alert('해당 상품의 외부 링크가 존재하지 않습니다.')
  }
}

onMounted(() => {
  window.scrollTo(0, 0)
  fetchProductDetail(productId)
})
</script>

<template>
  <main class="product-detail-page">
    <!-- 상단 배너 영역 -->
    <AppBanner title="상품 상세" subtitle="선택하신 상품의 상세 정보를 확인하세요" bgImage="https://picsum.photos/1200/250?blur=2" />

    <div class="container layout-container">
      
      <!-- 로딩 상태 -->
      <div v-if="isLoading" class="loading-state">
        <div class="spinner"></div>
        <p>상품 정보를 불러오는 중입니다...</p>
      </div>

      <!-- 에러 상태 -->
      <div v-else-if="error" class="error-state">
        <p>{{ error }}</p>
      </div>

      <!-- 상단: 상품 기본 정보 (이미지 + 구매 옵션) -->
      <template v-else-if="product">
        <section class="product-intro">
        
        <!-- 좌측: 상품 이미지 영역 -->
        <div class="image-section">
          <!-- 메인 상품 이미지 -->
          <div class="main-image">
            <img :src="selectedImage" :alt="product.title" />
          </div>
        </div>

        <!-- 우측: 상품 상세 정보 및 구매 옵션 -->
        <div class="info-section">
          <!-- 상품 제목 -->
          <h2 class="product-title">{{ product.title }}</h2>
          
          <!-- 상품 가격 -->
          <div class="product-price">
            {{ formatPrice(product.price) }}
          </div>
          
          <!-- 상품 요약 설명 -->
          <p class="product-summary">
            {{ product.summary }}
          </p>
          
          <!-- 액션 버튼 -->
          <div class="action-buttons">
            <button class="btn-cart" @click="toggleWishlist">
              <i :class="isWishlisted ? 'fa-solid fa-heart' : 'fa-regular fa-heart'" :style="isWishlisted ? 'color: #e74c3c;' : ''"></i> 
              {{ isWishlisted ? '위시리스트 제거' : '위시리스트 추가' }}
            </button>
            <button class="btn-buy" @click="goToLink">해당 상품 링크로 이동</button>
          </div>
        </div>
      </section>



      <!-- 12. 관련 상품 추천 목록 -->
      <section class="related-products" v-if="product">
        <h3 class="section-title">관련된 상품</h3>
        <div class="related-list">
          <div class="related-card" v-for="item in relatedProducts" :key="item.id" @click="$router.push(`/product/${item.id}`)">
            <div class="related-image">
              <img :src="item.image" :alt="item.title" />
            </div>
            <div class="related-info">
              <h4 class="related-title">{{ item.title }}</h4>
              <div class="related-price">{{ formatPrice(item.price) }}</div>
            </div>
          </div>
        </div>
      </section>
      </template>

    </div>
  </main>
</template>

<style scoped>
/* Page Layout */
.product-detail-page {
  background-color: var(--background-color, #f8f9fa);
  min-height: 100vh;
  padding-bottom: 80px;
}

.layout-container {
  display: flex;
  flex-direction: column;
  gap: 50px;
  margin-top: 30px;
  background: white;
  padding: 40px;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.04);
}

/* ----------------------------
   Top Section: Intro
---------------------------- */
.product-intro {
  display: flex;
  gap: 50px;
  align-items: flex-start;
}

/* Left: Images */
.image-section {
  display: flex;
  gap: 20px;
  flex: 1;
  max-width: 55%;
}

.thumbnail-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 80px;
}

.thumbnail-item {
  width: 80px;
  height: 80px;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
  background-color: #f1f3f5;
}

.thumbnail-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumbnail-item.active {
  border-color: #3498db;
}

.thumbnail-item:hover {
  opacity: 0.8;
}

.main-image {
  flex: 1;
  border-radius: 12px;
  overflow: hidden;
  background-color: #f8f9fa;
  aspect-ratio: 1 / 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.main-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Right: Info */
.info-section {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.product-title {
  font-size: 28px;
  font-weight: 700;
  color: #222;
  margin: 0 0 12px;
  line-height: 1.4;
}

.rating-review {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  font-size: 15px;
}

.stars {
  color: #f1c40f;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}

.stars span {
  color: #333;
}

.reviews {
  color: #666;
}

.reviews span {
  font-weight: 600;
  color: #3498db;
  text-decoration: underline;
  cursor: pointer;
}

.product-price {
  font-size: 32px;
  font-weight: 800;
  color: #e74c3c;
  margin-bottom: 20px;
}

.product-summary {
  font-size: 15px;
  color: #555;
  line-height: 1.6;
  margin-bottom: 30px;
  background: #f8f9fa;
  padding: 16px;
  border-radius: 8px;
}

.divider {
  height: 1px;
  background: #eee;
  margin: 0 0 30px;
}

.option-group {
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.option-group label {
  font-size: 14px;
  font-weight: 600;
  color: #444;
}

.custom-select {
  width: 100%;
  padding: 14px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 15px;
  color: #333;
  outline: none;
  appearance: none;
  background: url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2212%22%20height%3D%2212%22%20viewBox%3D%220%200%2012%2012%22%3E%3Cpath%20fill%3D%22%23999%22%20d%3D%22M10.293%203.293L6%207.586%201.707%203.293A1%201%200%2000.293%204.707l5%205a1%201%200%20001.414%200l5-5a1%201%200%2010-1.414-1.414z%22%2F%3E%3C%2Fsvg%3E') no-repeat right 16px center;
  background-color: white;
  transition: all 0.2s;
}

.custom-select:focus {
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

.action-buttons {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.btn-cart, .btn-buy {
  flex: 1;
  padding: 16px 0;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn-cart {
  background-color: #f1f3f5;
  color: #333;
}

.btn-cart:hover {
  background-color: #e2e6ea;
}

.btn-buy {
  background-color: #3498db;
  color: white;
}

.btn-buy:hover {
  background-color: #2980b9;
}

/* ----------------------------
   Bottom Section: Details
---------------------------- */
.product-details {
  border-top: 1px solid #eee;
  padding-top: 40px;
}

.tabs {
  display: flex;
  gap: 20px;
  border-bottom: 1px solid #ddd;
  margin-bottom: 30px;
}

.tab-btn {
  background: none;
  border: none;
  padding: 12px 20px;
  font-size: 18px;
  font-weight: 600;
  color: #888;
  cursor: pointer;
  position: relative;
  transition: color 0.2s;
}

.tab-btn:hover {
  color: #333;
}

.tab-btn.active {
  color: #333;
}

.tab-btn.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 3px;
  background-color: #333;
}

.tab-content {
  color: #444;
  line-height: 1.8;
  font-size: 16px;
}

.tab-content h3 {
  font-size: 22px;
  color: #222;
  margin-bottom: 20px;
}

.detail-images {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin: 30px 0;
}

.detail-images img {
  width: 100%;
  max-width: 800px;
  border-radius: 12px;
  margin: 0 auto;
  display: block;
}

.content-reviews .review-item {
  border-bottom: 1px solid #eee;
  padding: 20px 0;
}

.review-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 10px;
}

.reviewer {
  font-weight: 600;
  color: #333;
}

.review-stars {
  color: #f1c40f;
  font-size: 14px;
}

.review-text {
  color: #555;
}

/* ----------------------------
   Related Products
---------------------------- */
.related-products {
  border-top: 1px solid #eee;
  padding-top: 40px;
}

.section-title {
  font-size: 22px;
  font-weight: 700;
  color: #222;
  margin-bottom: 24px;
}

.related-list {
  display: flex;
  gap: 20px;
  overflow-x: auto;
  padding-bottom: 10px;
}

/* 스크롤바 숨기기 */
.related-list::-webkit-scrollbar {
  height: 6px;
}
.related-list::-webkit-scrollbar-track {
  background: #f1f1f1; 
  border-radius: 4px;
}
.related-list::-webkit-scrollbar-thumb {
  background: #ccc; 
  border-radius: 4px;
}

.related-card {
  min-width: 200px;
  background: #fff;
  border: 1px solid #eee;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.related-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 16px rgba(0,0,0,0.05);
}

.related-image {
  width: 100%;
  aspect-ratio: 1 / 1;
  background-color: #f8f9fa;
}

.related-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.related-info {
  padding: 15px;
}

.related-title {
  font-size: 14px;
  color: #333;
  margin: 0 0 8px;
  font-weight: 500;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.related-price {
  font-size: 16px;
  font-weight: 700;
  color: #e74c3c;
}

/* 반응형 처리 */
@media (max-width: 1024px) {
  .product-intro {
    flex-direction: column;
  }
  .image-section {
    max-width: 100%;
    width: 100%;
  }
}

@media (max-width: 768px) {
  .layout-container {
    padding: 20px;
  }
  .image-section {
    flex-direction: column-reverse;
  }
  .thumbnail-list {
    flex-direction: row;
    width: 100%;
    overflow-x: auto;
  }
  .thumbnail-item {
    flex-shrink: 0;
  }
}
</style>
