<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const boardList = ref([])
const searchQuery = ref('')
const currentPage = ref(1)
const totalPages = ref(1)
const activeDropdown = ref(null)

const getDropdownDirection = (index) => {
  if (boardList.value.length > 2 && index >= boardList.value.length - 2) {
    return 'up'
  }
  return 'down'
}

const toggleDropdown = (id, event) => {
  event.stopPropagation()
  if (activeDropdown.value === id) {
    activeDropdown.value = null
  } else {
    activeDropdown.value = id
  }
}

const closeDropdown = (event) => {
  if (!event.target.closest('.options-menu')) {
    activeDropdown.value = null
  }
}

const editPost = (id) => {
  router.push({ path: `/admin/board/edit/${id}` })
  activeDropdown.value = null
}

const deletePost = async (id) => {
  if (confirm('정말로 삭제하시겠습니까?')) {
    try {
      const token = localStorage.getItem('accessToken')
      await axios.delete(`/api/admin/posts/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
      alert('삭제되었습니다.')
      fetchPosts(currentPage.value)
    } catch (error) {
      console.error('Failed to delete post:', error)
      alert('삭제 중 오류가 발생했습니다.')
    }
  }
  activeDropdown.value = null
}

const restorePost = async (id) => {
  if (confirm('정말로 복구하시겠습니까?')) {
    try {
      const token = localStorage.getItem('accessToken')
      await axios.patch(`/api/admin/posts/${id}/restore`, {}, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
      alert('복구되었습니다.')
      fetchPosts(currentPage.value)
    } catch (error) {
      console.error('Failed to restore post:', error)
      alert('복구 중 오류가 발생했습니다.')
    }
  }
  activeDropdown.value = null
}

const fetchPosts = async (page = 1) => {
  try {
    const token = localStorage.getItem('accessToken')
    const response = await axios.get('/api/admin/posts', {
      params: {
        page: page,
        size: 10,
        keyword: searchQuery.value
      },
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
    
    if (response.data && response.data.data) {
      const pageData = response.data.data
      boardList.value = pageData.content.map(post => {
        return {
          id: post.postId,
          date: formatDate(post.createdAt),
          title: post.title,
          detail: post.content || '내용 없음',
          username: '관리자',
          status: post.visibleYn === 'Y' ? '정상' : '숨김',
          category: formatCategory(post.postType)
        }
      })
      currentPage.value = pageData.pageNumber
      totalPages.value = pageData.totalPages || 1
    }
  } catch (error) {
    console.error('Failed to fetch posts:', error)
  }
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

const formatCategory = (type) => {
  switch (type) {
    case 'NOTICE': return '공지사항'
    case 'EVENT': return '이벤트'
    case 'FAQ': return 'FAQ'
    default: return type
  }
}

const search = () => {
  fetchPosts(1)
}

const changePage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    fetchPosts(page)
  }
}

onMounted(() => {
  fetchPosts()
  document.addEventListener('click', closeDropdown)
})

onUnmounted(() => {
  document.removeEventListener('click', closeDropdown)
})

</script>

<template>
  <div class="admin-board">
    <div class="page-header">
      <h1 class="page-title">Board</h1>
    </div>

    <!-- 데이터 테이블 카드 -->
    <div class="card shadow-sm">
      <div class="card-header">
        <div class="search-area">
          <div class="search-input-wrapper">
            <i class="fa-solid fa-magnifying-glass search-icon"></i>
            <input 
              type="text" 
              class="form-control" 
              placeholder="제목 검색" 
              v-model="searchQuery"
            />
          </div>
          <button class="btn-search" @click="search">검색</button>
        </div>
        <div class="action-area">
          <button class="btn-primary" @click="$router.push('/admin/board/write')">
            <i class="fa-solid fa-pen-to-square"></i> 글 작성 버튼
          </button>
        </div>
      </div>
      
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table">
            <thead>
              <tr>
                <th width="8%">ID</th>
                <th width="12%">Date</th>
                <th width="25%">Title</th>
                <th width="25%">Detail</th>
                <th width="10%">Username</th>
                <th width="10%" class="sortable">Status <i class="fa-solid fa-caret-down"></i></th>
                <th width="10%" class="sortable">Category <i class="fa-solid fa-caret-down"></i></th>
                <th width="5%"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in boardList" :key="item.id" class="table-row">
                <td class="text-center font-weight-bold text-muted">#{{ item.id }}</td>
                <td class="text-muted">{{ item.date }}</td>
                <td class="font-weight-bold text-dark">{{ item.title }}</td>
                <td class="text-truncate text-muted">{{ item.detail }}</td>
                <td>
                  <span class="badge-user">{{ item.username }}</span>
                </td>
                <td>
                  <span class="status-indicator" :class="item.status === '정상' ? 'status-active' : 'status-danger'"></span>
                  {{ item.status }}
                </td>
                <td>
                  <span class="category-badge" :class="{
                    'bg-notice': item.category === '공지사항',
                    'bg-event': item.category === '이벤트',
                    'bg-faq': item.category === 'FAQ'
                  }">
                    {{ item.category }}
                  </span>
                </td>
                <td class="options-cell" @click.stop>
                  <div class="options-menu">
                    <button class="btn-icon" @click.stop="toggleDropdown(item.id, $event)">
                      <i class="fa-solid fa-ellipsis-vertical"></i>
                    </button>
                    <div class="dropdown-menu" :class="getDropdownDirection(index)" v-show="activeDropdown === item.id">
                      <template v-if="item.status === '정상'">
                        <a href="#" class="dropdown-item" @click.prevent="editPost(item.id)">
                          <i class="fa-solid fa-pen"></i> 수정
                        </a>
                        <a href="#" class="dropdown-item text-danger" @click.prevent="deletePost(item.id)">
                          <i class="fa-solid fa-trash"></i> 삭제
                        </a>
                      </template>
                      <template v-else>
                        <a href="#" class="dropdown-item text-success" @click.prevent="restorePost(item.id)">
                          <i class="fa-solid fa-arrow-rotate-left"></i> 복구
                        </a>
                      </template>
                    </div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      
      <!-- 페이지네이션 임시 UI -->
      <div class="card-footer">
        <div class="pagination-wrapper">
          <ul class="pagination">
            <li class="page-item" :class="{ disabled: currentPage === 1 }">
              <a class="page-link" href="#" @click.prevent="changePage(currentPage - 1)">이전</a>
            </li>
            <li class="page-item" v-for="page in totalPages" :key="page" :class="{ active: currentPage === page }">
              <a class="page-link" href="#" @click.prevent="changePage(page)">{{ page }}</a>
            </li>
            <li class="page-item" :class="{ disabled: currentPage === totalPages }">
              <a class="page-link" href="#" @click.prevent="changePage(currentPage + 1)">다음</a>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-board {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #2c2c2c;
  margin: 0;
}

/* Card UI */
.card {
  background-color: #ffffff;
  border-radius: 16px;
  border: none;
  display: flex;
  flex-direction: column;
}

.shadow-sm {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid #f2f2f2;
}

/* Search Area */
.search-area {
  display: flex;
  gap: 12px;
}

.search-input-wrapper {
  position: relative;
  width: 250px;
}

.search-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: #a0a0a0;
  font-size: 14px;
}

.form-control {
  width: 100%;
  padding: 10px 14px 10px 40px;
  border: 1px solid #e1e1e1;
  border-radius: 8px;
  font-size: 14px;
  color: #333;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.form-control:focus {
  outline: none;
  border-color: #3b4cb8;
}

/* Buttons */
.btn-search {
  padding: 10px 20px;
  background-color: #f0f2f5;
  color: #555;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-search:hover {
  background-color: #e4e6eb;
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background-color: #3b4cb8;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 4px 10px rgba(59, 76, 184, 0.2);
  transition: all 0.2s;
}

.btn-primary:hover {
  background-color: #2f3e9c;
  transform: translateY(-1px);
}

/* Table Styles */
.card-body.p-0 {
  padding: 0;
}

.table-responsive {
  width: 100%;
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.table th {
  padding: 16px 24px;
  font-size: 13px;
  font-weight: 600;
  color: #888;
  background-color: #fafbfc;
  border-bottom: 1px solid #f2f2f2;
}

.table th.sortable {
  cursor: pointer;
}

.table th.sortable:hover {
  color: #3b4cb8;
}

.table td {
  padding: 18px 24px;
  font-size: 14px;
  border-bottom: 1px solid #f2f2f2;
  vertical-align: middle;
}

.table-row {
  cursor: pointer;
  transition: background-color 0.2s;
}

.table-row:hover {
  background-color: #f8f9fe;
}

.table-row:last-child td {
  border-bottom: none;
}

/* Text & Badges Helpers */
.text-center { text-align: center; }
.font-weight-bold { font-weight: 600; }
.text-muted { color: #888; }
.text-dark { color: #333; }
.text-truncate {
  max-width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: inline-block;
}

.badge-user {
  display: inline-block;
  padding: 4px 10px;
  background-color: #f0f2f5;
  color: #555;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.status-indicator {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
}

.status-active { background-color: #2dc447; }
.status-danger { background-color: #e74c3c; }

.category-badge {
  display: inline-block;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.bg-notice { background-color: #eef2ff; color: #4361ee; }
.bg-event { background-color: #fff0f6; color: #eb2f96; }
.bg-faq { background-color: #f6ffed; color: #52c41a; }

/* Options Menu */
.options-cell {
  position: relative;
  text-align: right;
  padding-right: 40px !important;
}

.options-menu {
  position: relative;
  display: inline-block;
}

.btn-icon {
  background: none;
  border: none;
  color: #888;
  padding: 8px;
  cursor: pointer;
  border-radius: 50%;
  transition: background-color 0.2s, color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-icon:hover {
  background-color: #f0f2f5;
  color: #333;
}

.dropdown-menu {
  position: absolute;
  right: 0;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid #f2f2f2;
  min-width: 120px;
  z-index: 10;
  padding: 8px 0;
  display: flex;
  flex-direction: column;
}

.dropdown-menu.down {
  top: 100%;
  margin-top: 4px;
}

.dropdown-menu.up {
  bottom: 100%;
  margin-bottom: 4px;
}

.dropdown-item {
  padding: 8px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #555;
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  transition: background-color 0.2s;
}

.dropdown-item:hover {
  background-color: #f8f9fe;
  color: #3b4cb8;
}

.dropdown-item.text-danger {
  color: #e74c3c;
}

.dropdown-item.text-danger:hover {
  background-color: #fff0f0;
}

/* Pagination */
.card-footer {
  padding: 20px 24px;
  border-top: 1px solid #f2f2f2;
  display: flex;
  justify-content: flex-end;
}

.pagination {
  display: flex;
  list-style: none;
  padding: 0;
  margin: 0;
  gap: 8px;
}

.page-link {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background-color: #ffffff;
  border: 1px solid #e1e1e1;
  color: #555;
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s;
}

.page-link:hover {
  background-color: #f0f2f5;
}

.page-item.active .page-link {
  background-color: #3b4cb8;
  color: white;
  border-color: #3b4cb8;
}

.page-item.disabled .page-link {
  color: #ccc;
  background-color: #fafbfc;
  cursor: not-allowed;
}
</style>
