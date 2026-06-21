<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const route = useRoute()

const isEditMode = computed(() => !!route.params.id)

const postData = ref({
  title: '',
  postType: 'NOTICE',
  content: '',
  visibleYn: 'Y'
})

const isSubmitting = ref(false)
const isLoading = ref(false)

onMounted(async () => {
  if (isEditMode.value) {
    isLoading.value = true
    try {
      const token = localStorage.getItem('accessToken')
      const response = await axios.get(`/api/admin/posts/${route.params.id}`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
      if (response.data && response.data.data) {
        const data = response.data.data
        postData.value = {
          title: data.title,
          postType: data.postType,
          content: data.content,
          visibleYn: data.visibleYn
        }
      }
    } catch (error) {
      console.error('Failed to fetch post details:', error)
      alert('게시글 정보를 불러오는 데 실패했습니다.')
      router.push('/admin/board')
    } finally {
      isLoading.value = false
    }
  }
})

const submitPost = async () => {
  if (!postData.value.title.trim()) {
    alert('제목을 입력해주세요.')
    return
  }
  if (!postData.value.content.trim()) {
    alert('내용을 입력해주세요.')
    return
  }

  isSubmitting.value = true
  try {
    const token = localStorage.getItem('accessToken')
    let response
    
    if (isEditMode.value) {
      response = await axios.put(`/api/admin/posts/${route.params.id}`, postData.value, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
    } else {
      response = await axios.post('/api/admin/posts', postData.value, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
    }
    
    if (response.data && response.data.success) {
      alert(isEditMode.value ? '게시글이 성공적으로 수정되었습니다.' : '게시글이 성공적으로 등록되었습니다.')
      router.push('/admin/board')
    } else {
      alert(isEditMode.value ? '게시글 수정에 실패했습니다.' : '게시글 등록에 실패했습니다.')
    }
  } catch (error) {
    console.error(isEditMode.value ? 'Failed to update post:' : 'Failed to create post:', error)
    alert(isEditMode.value ? '게시글 수정 중 오류가 발생했습니다.' : '게시글 등록 중 오류가 발생했습니다.')
  } finally {
    isSubmitting.value = false
  }
}

const cancel = () => {
  if (confirm('작성을 취소하시겠습니까? 작성 중인 내용은 저장되지 않습니다.')) {
    router.push('/admin/board')
  }
}
</script>

<template>
  <div class="admin-board-write">
    <div class="page-header">
      <h1 class="page-title">{{ isEditMode ? '글 수정' : '글 작성' }}</h1>
    </div>

    <div class="card shadow-sm">
      <div class="card-body" v-if="!isLoading">
        <form @submit.prevent="submitPost" class="write-form">
          <div class="form-group">
            <label for="postType" class="form-label">카테고리 <span class="required">*</span></label>
            <select id="postType" v-model="postData.postType" class="form-control form-select">
              <option value="NOTICE">공지사항</option>
              <option value="FAQ">FAQ</option>
              <option value="EVENT">이벤트</option>
            </select>
          </div>

          <div class="form-group">
            <label for="title" class="form-label">제목 <span class="required">*</span></label>
            <input 
              type="text" 
              id="title" 
              v-model="postData.title" 
              class="form-control" 
              placeholder="제목을 입력하세요 (최대 100자)" 
              maxlength="100"
            />
          </div>

          <div class="form-group">
            <label for="content" class="form-label">내용 <span class="required">*</span></label>
            <textarea 
              id="content" 
              v-model="postData.content" 
              class="form-control content-textarea" 
              placeholder="내용을 입력하세요"
              rows="15"
            ></textarea>
          </div>

          <div class="form-actions">
            <button type="button" class="btn-cancel" @click="cancel" :disabled="isSubmitting">취소</button>
            <button type="submit" class="btn-primary" :disabled="isSubmitting">
              <span v-if="isSubmitting">처리 중...</span>
              <span v-else>{{ isEditMode ? '수정하기' : '등록하기' }}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-board-write {
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

.card {
  background-color: #ffffff;
  border-radius: 16px;
  border: none;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
}

.card-body {
  padding: 32px;
}

.write-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.required {
  color: #e74c3c;
  margin-left: 4px;
}

.form-control {
  width: 100%;
  padding: 12px 16px;
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

.form-select {
  appearance: auto;
  cursor: pointer;
}

.content-textarea {
  resize: vertical;
  min-height: 300px;
  line-height: 1.6;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
  padding-top: 24px;
  border-top: 1px solid #f2f2f2;
}

.btn-cancel {
  padding: 12px 24px;
  background-color: #f0f2f5;
  color: #555;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-cancel:hover:not(:disabled) {
  background-color: #e4e6eb;
}

.btn-cancel:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-primary {
  padding: 12px 24px;
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

.btn-primary:hover:not(:disabled) {
  background-color: #2f3e9c;
  transform: translateY(-1px);
}

.btn-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}
</style>
