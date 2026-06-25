<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import ProductCard from '@/components/product/ProductCard.vue'

const hotProducts = ref([])
const scrollContainer = ref(null)
const isAtStart = ref(true)
const isAtEnd = ref(false)
const router = useRouter()

const goToDetail = (product) => {
  const targetId = product.externalProductId || product.productId
  if (!targetId) return
  router.push({
    path: `/product/${targetId}`,
    state: {
      productData: JSON.stringify(product),
      sourcePage: 'MAIN_HOT_ITEMS'
    }
  })
}

const checkScroll = () => {
  if (!scrollContainer.value) return
  const { scrollLeft, scrollWidth, clientWidth } = scrollContainer.value
  isAtStart.value = scrollLeft <= 0
  // Allow 1px margin of error for fractional pixels in layout
  isAtEnd.value = scrollLeft + clientWidth >= scrollWidth - 1
}

const scrollLeftBtn = () => {
  if (scrollContainer.value) {
    const cardWidth = scrollContainer.value.querySelector('.hot-item-wrapper').offsetWidth + 20
    scrollContainer.value.scrollBy({ left: -cardWidth, behavior: 'smooth' })
  }
}

const scrollRightBtn = () => {
  if (scrollContainer.value) {
    const cardWidth = scrollContainer.value.querySelector('.hot-item-wrapper').offsetWidth + 20
    scrollContainer.value.scrollBy({ left: cardWidth, behavior: 'smooth' })
  }
}

onMounted(async () => {
  try {
    const response = await axios.get('/api/products/best?limit=10')
    if (response.data.success) {
      hotProducts.value = response.data.data
      
      // Delay to allow DOM to render before checking scroll bounds
      setTimeout(checkScroll, 100)
      window.addEventListener('resize', checkScroll)
    }
  } catch (error) {
    console.error('Failed to fetch hot products:', error)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', checkScroll)
})
</script>

<template>
  <section class="section">
    <div class="section-header">
      <h2>HOT ITEMS TOP 10</h2>
      <p>전체 유저들의 조회를 반영한 핫한 랭킹 상품 노출</p>
      <a href="/best" class="more-btn">더보기</a>
    </div>
    
    <div class="carousel-container" v-if="hotProducts.length > 0">
      <button 
        class="nav-btn prev-btn" 
        @click="scrollLeftBtn" 
        v-show="!isAtStart"
        aria-label="이전"
      >
        &#10094;
      </button>

      <div class="horizontal-scroll" ref="scrollContainer" @scroll="checkScroll">
        <div 
          class="hot-item-wrapper" 
          v-for="(item, index) in hotProducts" 
          :key="item.productId"
          @click="goToDetail(item)"
        >
          <div class="rank-badge">BEST {{ index + 1 }}</div>
          <ProductCard
            :name="item.title"
            :price="item.price"
            :imageUrl="item.imageUrl"
          />
        </div>
      </div>

      <button 
        class="nav-btn next-btn" 
        @click="scrollRightBtn" 
        v-show="!isAtEnd"
        aria-label="다음"
      >
        &#10095;
      </button>
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

.carousel-container {
  position: relative;
  display: flex;
  align-items: center;
}

.nav-btn {
  position: absolute;
  top: 40%;
  transform: translateY(-50%);
  width: 44px;
  height: 44px;
  background-color: white;
  border: 1px solid #ddd;
  border-radius: 50%;
  font-size: 18px;
  color: #333;
  cursor: pointer;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  transition: all 0.2s ease;
}

.nav-btn:hover {
  background-color: #f8f9fa;
  box-shadow: 0 4px 16px rgba(0,0,0,0.2);
}

.prev-btn {
  left: -22px;
}

.next-btn {
  right: -22px;
}

.horizontal-scroll {
  display: flex;
  gap: 20px;
  overflow-x: auto;
  padding-bottom: 20px;
  padding-top: 5px;
  scroll-behavior: smooth;
  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;
  width: 100%;
  /* Hide scrollbar */
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.horizontal-scroll::-webkit-scrollbar {
  display: none;
}

.hot-item-wrapper {
  position: relative;
  flex: 0 0 calc(33.333% - 13.4px);
  scroll-snap-align: start;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.hot-item-wrapper:hover {
  transform: translateY(-2px);
}

:deep(.horizontal-scroll .img-placeholder), :deep(.horizontal-scroll .img-wrapper) {
  aspect-ratio: 1;
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

@media (max-width: 768px) {
  .hot-item-wrapper {
    flex: 0 0 calc(80%);
  }
  .nav-btn {
    display: none; /* Hide buttons on mobile, let them swipe */
  }
}
</style>
