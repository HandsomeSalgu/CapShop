<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const userList = ref([])
const searchQuery = ref('')
const currentPage = ref(1)
const totalPages = ref(1)

const fetchUsers = async (page = 1) => {
  try {
    const token = localStorage.getItem('accessToken')
    const response = await axios.get('/api/admin/users', {
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
      userList.value = pageData.content.map(user => {
        return {
          id: user.id,
          createdAt: formatDate(user.createdAt),
          name: user.nickname, // 실명 대신 nickname 사용
          username: user.email, // username 대신 email 사용
          email: user.email,
          phone: user.phone || '없음',
          status: user.status === 'ACTIVE' ? '정상' : '삭제',
          role: user.role === 'ADMIN' ? '어드민' : '유저',
          rawStatus: user.status,
          rawRole: user.role
        }
      })
      currentPage.value = pageData.page
      totalPages.value = pageData.totalPages || 1
    }
  } catch (error) {
    console.error('Failed to fetch users:', error)
  }
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

const search = () => {
  fetchUsers(1)
}

const changePage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    fetchUsers(page)
  }
}

const updateUserStatus = async (userId, newStatus) => {
  try {
    const token = localStorage.getItem('accessToken')
    await axios.patch(`/api/admin/users/${userId}/status`, { status: newStatus }, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
    alert('계정 상태가 변경되었습니다.')
  } catch (error) {
    console.error('Failed to update status:', error)
    alert('상태 변경에 실패했습니다.')
    fetchUsers(currentPage.value) // 원래 상태로 되돌리기 위해 새로고침
  }
}

const updateUserRole = async (userId, newRole) => {
  try {
    const token = localStorage.getItem('accessToken')
    await axios.patch(`/api/admin/users/${userId}/role`, { role: newRole }, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
    alert('권한이 변경되었습니다.')
  } catch (error) {
    console.error('Failed to update role:', error)
    alert('권한 변경에 실패했습니다.')
    fetchUsers(currentPage.value)
  }
}

onMounted(() => {
  fetchUsers()
})

</script>

<template>
  <div class="admin-user">
    <div class="page-header">
      <h1 class="page-title">User</h1>
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
              placeholder="이름 또는 닉네임 검색" 
              v-model="searchQuery"
              @keyup.enter="search"
            />
          </div>
          <button class="btn-search" @click="search">검색</button>
        </div>
      </div>
      
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table">
            <thead>
              <tr>
                <th width="8%">ID</th>
                <th width="12%">Date</th>
                <th width="15%">User</th>
                <th width="15%">Username</th>
                <th width="20%">Email</th>
                <th width="15%">전화번호</th>
                <th width="8%" class="sortable">Account <i class="fa-solid fa-caret-down"></i></th>
                <th width="7%" class="sortable">Admin <i class="fa-solid fa-caret-down"></i></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in userList" :key="item.id" class="table-row-static">
                <td class="text-center font-weight-bold text-muted">#{{ item.id }}</td>
                <td class="text-muted">{{ item.createdAt }}</td>
                <td class="font-weight-bold text-dark">{{ item.name }}</td>
                <td class="text-muted">{{ item.username }}</td>
                <td class="text-muted">{{ item.email }}</td>
                <td class="text-muted">{{ item.phone }}</td>
                <td>
                  <select 
                    class="form-select-inline" 
                    v-model="item.rawStatus" 
                    @change="updateUserStatus(item.id, item.rawStatus)"
                    :disabled="item.id === authStore.userInfo?.userId"
                    :class="{
                      'text-success': item.rawStatus === 'ACTIVE',
                      'text-muted': item.rawStatus === 'INACTIVE',
                      'disabled-select': item.id === authStore.userInfo?.userId
                    }"
                  >
                    <option value="ACTIVE">정상</option>
                    <option value="INACTIVE">삭제</option>
                  </select>
                </td>
                <td>
                  <select 
                    class="form-select-inline" 
                    v-model="item.rawRole" 
                    @change="updateUserRole(item.id, item.rawRole)"
                    :disabled="item.id === authStore.userInfo?.userId"
                    :class="[
                      item.rawRole === 'ADMIN' ? 'text-primary' : 'text-muted',
                      { 'disabled-select': item.id === authStore.userInfo?.userId }
                    ]"
                  >
                    <option value="USER">유저</option>
                    <option value="ADMIN">어드민</option>
                  </select>
                </td>
              </tr>
              <tr v-if="userList.length === 0">
                <td colspan="8" class="text-center py-4 text-muted">검색 결과가 없습니다.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      
      <!-- 페이지네이션 -->
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
/* AdminBoardView와 유사한 스타일 통일감 제공 */
.admin-user {
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

.table-row-static {
  transition: background-color 0.2s;
}

.table-row-static:hover {
  background-color: #f8f9fe;
}

.table-row-static:last-child td {
  border-bottom: none;
}

/* Inline Select */
.form-select-inline {
  padding: 6px 30px 6px 12px;
  font-size: 13px;
  font-weight: 600;
  border: 1px solid #e1e1e1;
  border-radius: 6px;
  background-color: #f8f9fe;
  cursor: pointer;
  outline: none;
  appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 8px center;
  background-size: 14px;
}

.form-select-inline:focus {
  border-color: #3b4cb8;
  box-shadow: 0 0 0 2px rgba(59, 76, 184, 0.1);
}

.text-success { color: #2dc447 !important; }
.text-danger { color: #e74c3c !important; }
.text-primary { color: #4361ee !important; }

.disabled-select {
  background-color: #e9ecef;
  color: #6c757d !important;
  cursor: not-allowed;
  opacity: 0.7;
}

/* Text & Badges Helpers */
.text-center { text-align: center; }
.font-weight-bold { font-weight: 600; }
.text-muted { color: #888; }
.text-dark { color: #333; }
.py-4 { padding-top: 1.5rem; padding-bottom: 1.5rem; }

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
