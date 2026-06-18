<script setup>
import { ref, onMounted, watch } from 'vue'
import AppBanner from '@/components/common/AppBanner.vue'
import { boardApi } from '@/api/board'

const activeTab = ref('notices')
const boardItems = ref([])
const isLoading = ref(false)
const currentPage = ref(1)
const totalPages = ref(1)

// 탭 목록: 'notices', 'faqs', 'events'
const tabs = [
  { id: 'notices', name: '공지사항' },
  { id: 'faqs', name: 'FAQ' },
  { id: 'events', name: '이벤트' }
]

const loadBoardData = async (page = 1) => {
  isLoading.value = true
  try {
    let res = null
    if (activeTab.value === 'notices') {
      res = await boardApi.getNotices(page, 10)
    } else if (activeTab.value === 'faqs') {
      res = await boardApi.getFaqs(page, 10)
    } else if (activeTab.value === 'events') {
      res = await boardApi.getEvents(page, 10)
    }
    
    if (res && res.data) {
      const pageData = res.data
      boardItems.value = pageData.content.map(item => ({
        ...item,
        isExpanded: false,
        detailContent: null // 상세 내용을 저장할 속성
      }))
      currentPage.value = pageData.page
      totalPages.value = pageData.totalPages
    }
  } catch (error) {
    console.error('Failed to load board data:', error)
  } finally {
    isLoading.value = false
  }
}

const toggleAccordion = async (item) => {
  // 이미 로드된 경우 토글만 처리
  if (item.detailContent !== null) {
    item.isExpanded = !item.isExpanded
    return
  }

  // 상세 내용이 없으면 API 호출하여 가져오기
  try {
    const res = await boardApi.getPostDetail(item.postId)
    if (res && res.data) {
      item.detailContent = res.data.content
      item.isExpanded = true
    }
  } catch (error) {
    console.error('Failed to load post detail:', error)
    alert('상세 내용을 불러오는데 실패했습니다.')
  }
}

const changeTab = (tabId) => {
  activeTab.value = tabId
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return `${date.getFullYear()}.${String(date.getMonth() + 1).padStart(2, '0')}.${String(date.getDate()).padStart(2, '0')}`
}

const getTypeName = (type) => {
  if (type === 'NOTICE') return '공지사항'
  if (type === 'FAQ') return 'FAQ'
  if (type === 'EVENT') return '이벤트'
  return type
}

onMounted(() => {
  loadBoardData(1)
})

watch(activeTab, () => {
  loadBoardData(1)
})
</script>

<template>
  <main class="board-view">
    <AppBanner title="고객센터" subtitle="공지사항 및 자주 묻는 질문을 확인하세요" bgImage="" />
    
    <div class="container board-container">
      <div class="board-header">
        <h1 class="page-title">공지사항/FAQ</h1>
        <div class="tab-menu">
          <button 
            v-for="tab in tabs" 
            :key="tab.id"
            :class="['tab-btn', { active: activeTab === tab.id }]" 
            @click="changeTab(tab.id)"
          >{{ tab.name }}</button>
        </div>
      </div>

      <div class="board-content">
        <div class="list-header">
          <div class="col-type">분류</div>
          <div class="col-title">게시글 제목</div>
          <div class="col-date">등록일</div>
          <div class="col-icon"></div>
        </div>
        
        <div v-if="isLoading" class="loading-state">
          데이터를 불러오는 중입니다...
        </div>
        <div v-else-if="boardItems.length === 0" class="empty-state">
          등록된 게시글이 없습니다.
        </div>
        <div v-else class="list-body">
          <template v-for="item in boardItems" :key="item.postId">
            <div class="list-item" @click="toggleAccordion(item)">
              <div class="col-type">{{ getTypeName(item.postType) }}</div>
              <div class="col-title">{{ item.title }}</div>
              <div class="col-date">{{ formatDate(item.createdAt) }}</div>
              <div class="col-icon">
                <i :class="['fa-solid', item.isExpanded ? 'fa-minus' : 'fa-plus']"></i>
              </div>
            </div>
            <div class="list-detail" v-show="item.isExpanded">
              <div class="detail-content" v-html="item.detailContent"></div>
            </div>
          </template>
        </div>
        
        <!-- Pagination -->
        <div class="pagination" v-if="totalPages > 1 && !isLoading">
          <button 
            class="page-btn" 
            :disabled="currentPage === 1" 
            @click="loadBoardData(currentPage - 1)"
          >&lt;</button>
          <button 
            v-for="page in totalPages" 
            :key="page"
            :class="['page-btn', { active: currentPage === page }]"
            @click="loadBoardData(page)"
          >{{ page }}</button>
          <button 
            class="page-btn" 
            :disabled="currentPage === totalPages" 
            @click="loadBoardData(currentPage + 1)"
          >&gt;</button>
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
.board-view {
  min-height: calc(100vh - 200px);
  padding-bottom: 60px;
}

.board-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 20px;
}

.board-header {
  margin-bottom: 40px;
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  text-align: center;
  margin-bottom: 30px;
  color: var(--text-color);
}

.tab-menu {
  display: flex;
  justify-content: center;
  gap: 10px;
}

.tab-btn {
  padding: 10px 30px;
  font-size: 16px;
  font-weight: 600;
  border: 1px solid var(--border-color);
  background-color: #fff;
  color: var(--text-muted);
  border-radius: 25px;
  cursor: pointer;
  transition: all 0.3s;
}

.tab-btn:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.tab-btn.active {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
  color: #fff;
}

.list-header {
  display: flex;
  align-items: center;
  padding: 15px 0;
  border-top: 2px solid var(--text-color);
  border-bottom: 1px solid var(--border-color);
  font-weight: 600;
  font-size: 15px;
  color: var(--text-color);
}

.list-item {
  display: flex;
  align-items: center;
  padding: 20px 0;
  border-bottom: 1px solid var(--border-color);
  cursor: pointer;
  transition: background-color 0.2s;
}

.list-item:hover {
  background-color: #f9f9f9;
}

.col-type {
  width: 120px;
  text-align: center;
  color: var(--text-muted);
}

.col-title {
  flex: 1;
  padding: 0 20px;
  font-weight: 500;
}

.col-date {
  width: 120px;
  text-align: center;
  color: var(--text-muted);
}

.col-icon {
  width: 50px;
  text-align: center;
  font-size: 18px;
  color: var(--text-muted);
}

.list-detail {
  background-color: #f8f9fa;
  border-bottom: 1px solid var(--border-color);
  padding: 40px;
}

.detail-content {
  line-height: 1.6;
  color: var(--text-color);
  white-space: pre-wrap;
}

.loading-state, .empty-state {
  text-align: center;
  padding: 60px 0;
  color: var(--text-muted);
}

.pagination {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 40px;
}

.page-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border-color);
  background-color: #fff;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.page-btn.active {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
  color: #fff;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
