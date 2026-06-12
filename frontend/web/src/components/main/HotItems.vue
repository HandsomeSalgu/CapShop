<script setup>
import ProductCard from '@/components/product/ProductCard.vue'

const hotProduct1 = { name: '베스트 랭킹 1위 상품', price: '₩ 890,000', placeholder: '상품 1' }
const hotProducts = [
  { id: 2, name: '베스트 랭킹 2위 상품', price: '₩ 65,000', placeholder: '상품 2' },
  { id: 3, name: '베스트 랭킹 3위 상품', price: '₩ 42,000', placeholder: '상품 3' },
  { id: 4, name: '베스트 랭킹 4위 상품', price: '₩ 55,000', placeholder: '상품 4' }
]
</script>

<template>
  <section class="section">
    <div class="section-header">
      <h2>현재 제일 핫한 상품 리스트</h2>
      <p>카테고리 별 4위까지 가장 핫한 랭킹 상품 노출</p>
      <a href="#" class="more-btn">더보기</a>
    </div>
    <div class="grid-hot">
      <div class="hot-left">
        <ProductCard
          class="first-card"
          :name="hotProduct1.name"
          :price="hotProduct1.price"
          :imagePlaceholder="hotProduct1.placeholder"
        />
      </div>
      <div class="hot-right">
        <ProductCard
          class="other-card"
          v-for="item in hotProducts"
          :key="item.id"
          :name="item.name"
          :price="item.price"
          :imagePlaceholder="item.placeholder"
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
