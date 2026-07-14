<!-- ============================================ -->
<!-- 侧边栏 — 会话管理 -->
<!-- ============================================ -->
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useChatStore } from '@/stores/chat'
import { createSession, getSessions } from '@/api/chat'
import type { Session } from '@/types'

const store = useChatStore()
const sessions = ref<Session[]>([])
const loading = ref(false)

onMounted(async () => {
  await loadSessions()
})

async function loadSessions() {
  loading.value = true
  try {
    const data = await getSessions()
    sessions.value = data.sessions || []
    store.sessions = sessions.value
  } catch {
    // 后端不可用时使用本地数据
    sessions.value = store.sessions || []
  } finally {
    loading.value = false
  }
}

async function handleNewChat() {
  try {
    const data = await createSession('新对话')
    store.initSession(data.session_id)
    await loadSessions()
  } catch {
    // 离线模式
    store.initSession()
  }
}

async function selectSession(session: Session) {
  await store.loadSession(session.id)
}
</script>

<template>
  <div class="sidebar">
    <!-- 新建对话 -->
    <div class="sidebar-header">
      <el-button
        type="primary"
        :icon="'Plus'"
        block
        size="large"
        @click="handleNewChat"
      >
        新对话
      </el-button>
    </div>

    <!-- 会话列表 -->
    <div class="session-list">
      <div class="section-title">历史会话</div>

      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>加载中...</span>
      </div>

      <div v-else-if="sessions.length === 0" class="empty-state">
        <span class="empty-icon">💬</span>
        <p>暂无历史会话</p>
        <p class="empty-hint">点击上方按钮开始新对话</p>
      </div>

      <div
        v-for="session in sessions"
        :key="session.id"
        class="session-item"
        :class="{ active: session.id === store.currentSessionId }"
        @click="selectSession(session)"
      >
        <div class="session-icon">💬</div>
        <div class="session-info">
          <div class="session-title">{{ session.title }}</div>
          <div class="session-meta">
            <span v-if="session.messageCount">{{ session.messageCount }} 条消息</span>
          </div>
          <div class="session-preview">{{ session.lastMessage || '' }}</div>
        </div>
      </div>
    </div>

    <!-- 底部 -->
    <div class="sidebar-footer">
      <el-button text size="small" @click="loadSessions">
        <el-icon><Refresh /></el-icon>
        刷新列表
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 12px;
}

/* 头部 */
.sidebar-header {
  padding: 8px 0 16px;
}

/* 会话列表 */
.session-list {
  flex: 1;
  overflow-y: auto;
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 8px 4px;
  margin-bottom: 4px;
}

.loading-state {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  color: var(--text-secondary);
  font-size: 13px;
  justify-content: center;
}

.empty-state {
  text-align: center;
  padding: 32px 16px;
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 40px;
  opacity: 0.5;
}

.empty-state p {
  margin: 8px 0 0;
  font-size: 13px;
}

.empty-hint {
  font-size: 11px !important;
  color: var(--text-tertiary);
}

/* 会话卡片 */
.session-item {
  display: flex;
  gap: 10px;
  padding: 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 2px;
}

.session-item:hover {
  background: var(--bg-hover);
}

.session-item.active {
  background: var(--color-primary-alpha);
  border: 1px solid var(--color-primary-light);
}

.session-icon {
  font-size: 18px;
  flex-shrink: 0;
  margin-top: 2px;
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-meta {
  font-size: 11px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

.session-preview {
  font-size: 12px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-top: 2px;
}

/* 底部 */
.sidebar-footer {
  padding: 12px 0 4px;
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: center;
}
</style>
