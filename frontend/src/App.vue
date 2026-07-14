<!-- ============================================ -->
<!-- 根组件 -->
<!-- ============================================ -->
<script setup lang="ts">
import { onMounted } from 'vue'
import { useChatStore } from '@/stores/chat'
import Sidebar from '@/components/Sidebar.vue'
import ChatWindow from '@/components/ChatWindow.vue'
import ChatInput from '@/components/ChatInput.vue'
import { useChat } from '@/composables/useChat'

const store = useChatStore()
const { sendMessage, stopGenerating, isLoading } = useChat()

onMounted(() => {
  store.initSession()
})
</script>

<template>
  <div class="app-container" :class="{ dark: store.darkMode }">
    <!-- 顶部导航栏 -->
    <header class="app-header">
      <div class="header-left">
        <el-button
          :icon="store.sidebarCollapsed ? 'Expand' : 'Fold'"
          text
          @click="store.toggleSidebar()"
          class="menu-btn"
        />
        <div class="logo">
          <span class="logo-icon">🤖</span>
          <span class="logo-text">智能客服</span>
        </div>
      </div>
      <div class="header-right">
        <el-switch
          v-model="store.darkMode"
          :active-icon="'Moon'"
          :inactive-icon="'Sunny'"
          inline-prompt
          size="small"
        />
      </div>
    </header>

    <!-- 主体区域 -->
    <div class="app-body">
      <!-- 侧边栏 -->
      <aside class="app-sidebar" :class="{ collapsed: store.sidebarCollapsed }">
        <Sidebar />
      </aside>

      <!-- 聊天区域 -->
      <main class="app-main">
        <ChatWindow />

        <div class="input-area">
          <ChatInput
            @send="sendMessage"
            @stop="stopGenerating"
            :loading="isLoading"
            :disabled="false"
          />
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: background 0.3s, color 0.3s;
}

/* 顶部导航 */
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  padding: 0 16px;
  background: var(--bg-header);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.menu-btn {
  font-size: 20px;
  padding: 6px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo-icon {
  font-size: 24px;
}

.logo-text {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 主体布局 */
.app-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* 侧边栏 */
.app-sidebar {
  width: 280px;
  flex-shrink: 0;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-color);
  overflow-y: auto;
  transition: width 0.3s, opacity 0.3s;
}

.app-sidebar.collapsed {
  width: 0;
  overflow: hidden;
  border-right: none;
}

/* 聊天主区域 */
.app-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.input-area {
  padding: 16px 24px 24px;
  flex-shrink: 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .app-sidebar {
    position: fixed;
    top: 56px;
    left: 0;
    bottom: 0;
    z-index: 90;
    width: 280px;
    box-shadow: 4px 0 20px rgba(0, 0, 0, 0.15);
  }

  .app-sidebar.collapsed {
    width: 0;
  }

  .input-area {
    padding: 12px 12px 16px;
  }

  .logo-text {
    display: none;
  }
}
</style>
