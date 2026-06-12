<script setup>
import { ref, onMounted } from 'vue'
import { RouterView } from 'vue-router'
import AppHeader from './components/common/AppHeader.vue'
import AppFooter from './components/common/AppFooter.vue'
import SearchModal from './components/common/SearchModal.vue'
import { useAuthStore } from '@/stores/auth'

const isSearchModalOpen = ref(false)
const authStore = useAuthStore()

onMounted(() => {
  authStore.init()
})
</script>

<template>
  <AppHeader @open-search="isSearchModalOpen = true" />
  
  <RouterView />

  <AppFooter />

  <SearchModal v-model="isSearchModalOpen" />
</template>

<style scoped>
</style>
