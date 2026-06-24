<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: {
    type: String,
    required: true
  },
  price: {
    type: [String, Number],
    required: true
  },
  imagePlaceholder: {
    type: String,
    default: '상품 이미지'
  },
  imageUrl: {
    type: String,
    default: ''
  },
  link: {
    type: String,
    default: ''
  }
})

const formattedPrice = computed(() => {
  if (typeof props.price === 'number') {
    return '₩ ' + props.price.toLocaleString()
  }
  return props.price
})

const emit = defineEmits(['click'])

const handleClick = () => {
  emit('click')
}
</script>

<template>
  <div class="product-card" @click="handleClick">
    <div v-if="imageUrl" class="img-wrapper">
      <img :src="imageUrl" :alt="name" class="product-image" />
    </div>
    <div v-else class="img-placeholder">{{ imagePlaceholder }}</div>
    <div class="product-info">
      <div class="product-name">{{ name }}</div>
      <div class="product-price">{{ formattedPrice }}</div>
    </div>
  </div>
</template>

<style scoped>
.product-card {
  cursor: pointer;
  display: flex;
  flex-direction: column;
}

.img-wrapper {
  background-color: var(--bg-light);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  transition: transform 0.3s;
  margin-bottom: 20px;
  flex-grow: 1;
  aspect-ratio: 1;
}

.product-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
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
  aspect-ratio: 1;
}

.product-card:hover .img-placeholder,
.product-card:hover .img-wrapper {
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
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  min-height: 48px;
}

.product-price {
  font-size: 15px;
  color: var(--text-muted);
}
</style>
