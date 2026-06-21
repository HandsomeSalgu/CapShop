<script setup>
import AppBanner from '@/components/common/AppBanner.vue'
import AiRecommend from '@/components/main/AiRecommend.vue'
import HotItems from '@/components/main/HotItems.vue'
</script>

<template>
  <main>
    <AppBanner />
    <div class="container">
      <AiRecommend />
      <HotItems />
    </div>
  </main>
</template>
