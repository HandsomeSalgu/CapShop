<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: ''
  },
  options: {
    type: Array,
    required: true
  },
  placeholder: {
    type: String,
    default: '선택'
  },
  maxHeight: {
    type: String,
    default: '150px' // 드롭다운 높이를 기본보다 짧게 설정
  }
})

const emit = defineEmits(['update:modelValue'])

const isOpen = ref(false)
const selectRef = ref(null)

const toggleOpen = () => {
  isOpen.value = !isOpen.value
}

const selectOption = (option) => {
  emit('update:modelValue', option)
  isOpen.value = false
}

const handleClickOutside = (event) => {
  if (selectRef.value && !selectRef.value.contains(event.target)) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

const displayValue = computed(() => {
  return props.modelValue || props.placeholder
})
</script>

<template>
  <div class="custom-select" ref="selectRef">
    <div 
      class="select-trigger" 
      :class="{ 'is-open': isOpen, 'has-value': modelValue }"
      @click="toggleOpen"
    >
      <span class="select-value">{{ displayValue }}</span>
      <i class="fa-solid fa-chevron-down select-icon"></i>
    </div>
    
    <transition name="dropdown">
      <ul class="select-dropdown" v-if="isOpen" :style="{ maxHeight: maxHeight }">
        <li 
          v-for="option in options" 
          :key="option"
          class="select-option"
          :class="{ 'is-selected': modelValue === option }"
          @click="selectOption(option)"
        >
          {{ option }}
        </li>
      </ul>
    </transition>
  </div>
</template>

<style scoped>
.custom-select {
  position: relative;
  width: 100%;
  user-select: none;
}

.select-trigger {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 14px;
  font-size: 15px;
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 4px;
  background-color: #fff;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #888;
}

.select-trigger.has-value {
  color: var(--text-color, #333);
}

.select-trigger.is-open {
  border-color: var(--accent-color, #000);
}

.select-icon {
  font-size: 12px;
  transition: transform 0.3s ease;
}

.select-trigger.is-open .select-icon {
  transform: rotate(180deg);
}

.select-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  width: 100%;
  margin: 0;
  padding: 4px 0;
  list-style: none;
  background-color: #fff;
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
  z-index: 100;
  
  /* Scrollbar styling */
  scrollbar-width: thin;
  scrollbar-color: #bbb transparent;
}

.select-dropdown::-webkit-scrollbar {
  width: 6px;
}

.select-dropdown::-webkit-scrollbar-track {
  background: transparent;
}

.select-dropdown::-webkit-scrollbar-thumb {
  background-color: #bbb;
  border-radius: 3px;
}

.select-option {
  padding: 10px 14px;
  font-size: 14px;
  color: var(--text-color, #333);
  cursor: pointer;
  transition: background-color 0.2s;
  text-align: center;
}

.select-option:hover {
  background-color: #f5f5f5;
}

.select-option.is-selected {
  background-color: #f0f0f0;
  font-weight: 600;
}

/* Animations */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
