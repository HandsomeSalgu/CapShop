<script setup>
import ProductCard from '@/components/product/ProductCard.vue'

const products = [
  { id: 1, name: 'AI 추천 상품 1', price: '₩ 120,000', placeholder: '상품 1' },
  { id: 2, name: 'AI 추천 상품 2', price: '₩ 85,000', placeholder: '상품 2' },
  { id: 3, name: 'AI 추천 상품 3', price: '₩ 230,000', placeholder: '상품 3' }
]
</script>

<template>
  <section class="section">
    <div class="section-header">
      <h2>AI 추천 상품 리스트</h2>
      <p>AI가 사용자 정보를 일부 수집해 추천하는 서비스입니다.</p>
      <a href="#" class="more-btn">더보기</a>
    </div>
    <div class="grid-3">
      <ProductCard 
        v-for="item in products" 
        :key="item.id"
        :name="item.name"
        :price="item.price"
        :imagePlaceholder="item.placeholder"
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

:deep(.grid-3 .img-placeholder) {
  aspect-ratio: 1;
}
</style>
