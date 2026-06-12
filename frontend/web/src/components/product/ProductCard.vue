<script setup>
defineProps({
  name: {
    type: String,
    required: true
  },
  price: {
    type: String,
    required: true
  },
  imagePlaceholder: {
    type: String,
    default: '상품 이미지'
  }
})
</script>

<template>
  <div class="product-card">
    <div class="img-placeholder">{{ imagePlaceholder }}</div>
    <div class="product-info">
      <div class="product-name">{{ name }}</div>
      <div class="product-price">{{ price }}</div>
    </div>
  </div>
</template>

<style scoped>
.product-card {
  cursor: pointer;
  display: flex;
  flex-direction: column;
}

.img-placeholder {
  background-color: var(--bg-light);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #bbb;
  font-size: 18px;
  transition: background-color 0.3s, transform 0.3s;
  margin-bottom: 20px;
  flex-grow: 1;
}

.product-card:hover .img-placeholder {
  background-color: #e8e9eb;
  transform: translateY(-5px);
}

.product-info {
  text-align: center;
}

.product-name {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 5px;
  color: var(--primary-color);
}

.product-price {
  font-size: 15px;
  color: var(--text-muted);
}
</style>
