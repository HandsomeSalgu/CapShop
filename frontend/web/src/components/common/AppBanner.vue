<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import mainBannerImage from '@/assets/images/coffee_lantern.jpeg'

const props = defineProps({
  title: {
    type: String,
    default: ''
  },
  subtitle: {
    type: String,
    default: ''
  },
  bgImage: {
    type: String,
    default: ''
  }
})

const route = useRoute()
const router = useRouter()
const isHomePage = computed(() => route.path === '/')

const bannerStyle = computed(() => {
  if (isHomePage.value) {
    return {
      backgroundImage: `url(${mainBannerImage})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      backgroundRepeat: 'no-repeat'
    }
  }

  if (props.bgImage) {
    return {
      backgroundImage: `linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5)), url(${props.bgImage})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      backgroundRepeat: 'no-repeat'
    }
  }
  // Default gradient if no image is provided
  return {
    background: 'linear-gradient(135deg, #2c3e50, #3498db)'
  }
})
</script>

<template>
  <section class="banner-section" :class="{ 'main-banner': isHomePage }" :style="bannerStyle">
    <div class="banner-content" v-if="!isHomePage">
      <h2>{{ title }}</h2>
      <p v-if="subtitle">{{ subtitle }}</p>
    </div>
    
    <div class="main-banner-content container" v-if="isHomePage">
      <div class="text-area">
        <h2>지금 가장 사랑받는<br/>베스트 상품들</h2>
        <p>고객님들이 가장 많이 찾고 만족하신 인기 상품들을 한 곳에서 만나보세요. 꼼꼼하게 엄선된 최고의 상품들이 준비되어 있습니다.</p>
        <button class="discover-btn" @click="router.push('/best')">베스트 상품리스트로 이동하기</button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.banner-section {
  width: 100%;
  height: 250px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-bottom: 40px;
}

.banner-section.main-banner {
  height: 950px; /* Adjust based on image aspect ratio */
  padding-top: 150px; /* Space for the absolute header */
  margin-bottom: 60px;
  align-items: flex-start;
  color: #333; /* Dark text for light background */
}

.banner-content {
  text-align: center;
  padding: 0 20px;
}

.banner-content h2 {
  font-size: 48px;
  font-weight: 800;
  margin-bottom: 10px;
  letter-spacing: 2px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.banner-content p {
  font-size: 16px;
  opacity: 0.9;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.main-banner-content {
  width: 100%;
  display: flex;
  justify-content: flex-start;
  padding: 0 20px;
  margin-top: 100px;
}

.main-banner-content .text-area {
  max-width: 500px;
  text-align: left;
}

.main-banner-content h2 {
  font-size: 52px;
  font-weight: 800;
  margin-bottom: 20px;
  line-height: 1.2;
  color: #333;
}

.main-banner-content p {
  font-size: 16px;
  line-height: 1.6;
  color: #666;
  margin-bottom: 40px;
}

.discover-btn {
  padding: 15px 40px;
  background: transparent;
  color: #333;
  border: 1px solid #333;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  letter-spacing: 1px;
}

.discover-btn:hover {
  background: #333;
  color: white;
}
</style>
