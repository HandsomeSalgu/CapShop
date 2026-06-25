<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])
const router = useRouter()
const searchKeyword = ref('')

const close = () => {
  emit('update:modelValue', false)
  searchKeyword.value = ''
}

const performSearch = () => {
  if (!searchKeyword.value.trim()) return
  router.push({ path: '/category', query: { q: searchKeyword.value.trim() } })
  close()
}
</script>

<template>
  <div 
    class="modal-overlay" 
    :class="{ active: modelValue }"
    @click.self="close"
  >
    <div class="modal-content">
      <button class="modal-close" @click="close">&times;</button>
      <h3>원하는 상품을 검색할 수 있습니다.</h3>
      <div class="search-form">
        <input 
          type="text" 
          placeholder="검색어를 입력해주세요..."
          v-model="searchKeyword"
          @keyup.enter="performSearch"
        >
        <button type="button" @click="performSearch"><i class="fa-solid fa-magnifying-glass"></i></button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  display: none;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  opacity: 0;
  transition: opacity 0.3s;
}

.modal-overlay.active {
  display: flex;
  opacity: 1;
}

.modal-content {
  background: #ffffff;
  padding: 50px;
  width: 90%;
  max-width: 600px;
  position: relative;
  text-align: center;
  border-radius: 4px;
}

.modal-close {
  position: absolute;
  top: 20px;
  right: 25px;
  font-size: 28px;
  background: none;
  border: none;
  cursor: pointer;
  color: #999999;
}

.modal-close:hover {
  color: var(--primary-color);
}

.modal-content h3 {
  font-size: 24px;
  font-weight: 500;
  margin-bottom: 30px;
}

.search-form {
  display: flex;
  border-bottom: 2px solid var(--primary-color);
  padding-bottom: 5px;
}

.search-form input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 18px;
  padding: 10px;
  font-family: inherit;
}

.search-form button {
  background: none;
  border: none;
  font-size: 20px;
  padding: 0 10px;
  color: var(--primary-color);
}
</style>
