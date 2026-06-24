<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import ProductCard from '@/components/product/ProductCard.vue'

const hotProducts = ref([])

onMounted(async () => {
  try {
    const response = await axios.get('http://localhost:8080/api/products/hot?limit=4')
    if (response.data.status === 'SUCCESS') {
      hotProducts.value = response.data.data
    }
  } catch (error) {
    console.error('Failed to fetch hot products:', error)
  }
})

const hotProduct1 = computed(() => hotProducts.value[0] || null)
const otherHotProducts = computed(() => hotProducts.value.slice(1, 4))
</script>

<template>
  <section class="section">
    <div class="section-header">
      <h2>현재 제일 핫한 상품 리스트</h2>
      <p>조회수와 저장수를 반영한 핫한 랭킹 상품 노출</p>
      <a href="/products?sort=popular" class="more-btn">더보기</a>
    </div>
    <div class="grid-hot" v-if="hotProducts.length > 0">
      <div class="hot-left" v-if="hotProduct1">
        <ProductCard
          class="first-card"
          :name="hotProduct1.title"
          :price="hotProduct1.price"
          :imageUrl="hotProduct1.imageUrl"
        />
      </div>
      <div class="hot-right">
        <ProductCard
          class="other-card"
          v-for="item in otherHotProducts"
          :key="item.productId"
          :name="item.title"
          :price="item.price"
          :imageUrl="item.imageUrl"
        />
      </div>
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

.grid-hot {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
}

.hot-left {
  display: flex;
  flex-direction: column;
}

:deep(.first-card) {
  flex-grow: 1;
}

:deep(.first-card .img-placeholder) {
  flex-grow: 1;
  min-height: 500px;
  margin-bottom: 20px;
}

.hot-right {
  display: grid;
  grid-template-rows: repeat(3, 1fr);
  gap: 30px;
}

:deep(.other-card .img-placeholder) {
  aspect-ratio: 2/1;
  margin-bottom: 15px;
}
</style>
