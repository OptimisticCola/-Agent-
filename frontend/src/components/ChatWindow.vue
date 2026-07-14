<!-- ============================================ -->
<!-- 聊天消息窗口 -->
<!-- ============================================ -->
<script setup lang="ts">
import { ref, watch, nextTick, onMounted } from 'vue'
import { useChatStore } from '@/stores/chat'
import ChatMessage from './ChatMessage.vue'

const store = useChatStore()
const messageList = ref<HTMLDivElement>()
const welcomeVisible = ref(true)

watch(
  () => store.messages.length,
  async () => {
    await nextTick()
    scrollToBottom()
  },
)

watch(
  () => {
    const msgs = store.messages
    if (msgs.length > 0) {
      return msgs[msgs.length - 1].content
    }
    return ''
  },
  async () => {
    await nextTick()
    scrollToBottom()
  },
)

function scrollToBottom() {
  if (messageList.value) {
    messageList.value.scrollTop = messageList.value.scrollHeight
  }
}

onMounted(() => {
  scrollToBottom()
})
</script>

<template>
  <div class="chat-window" ref="messageList">
    <!-- 欢迎界面 -->
    <div v-if="store.messages.length === 0" class="welcome-container">
      <div class="welcome-icon">🤖</div>
      <h2 class="welcome-title">医院智能助手</h2>
      <p class="welcome-subtitle">我可以帮您查询医疗知识、就诊预约、查看预约和转接人工客服</p>

      <div class="suggestion-cards">
        <div class="suggestion-card" @click="$emit('suggestion', '我想预约挂号')">
          <span class="suggestion-icon">📅</span>
          <span>就诊预约</span>
        </div>
        <div class="suggestion-card" @click="$emit('suggestion', '我想查看我的预约记录')">
          <span class="suggestion-icon">📋</span>
          <span>查看预约</span>
        </div>
        <div class="suggestion-card" @click="$emit('suggestion', '高血压应该注意什么')">
          <span class="suggestion-icon">🩺</span>
          <span>医疗常识</span>
        </div>
        <div class="suggestion-card" @click="$emit('suggestion', '转人工客服')">
          <span class="suggestion-icon">👩‍⚕️</span>
          <span>转接人工客服</span>
        </div>
      </div>
    </div>

    <!-- 消息列表 -->
    <div v-else class="message-list">
      <ChatMessage
        v-for="msg in store.messages"
        :key="msg.id"
        :message="msg"
      />

      <!-- 加载指示器 -->
      <div v-if="store.isLoading && store.thinkingStatus" class="loading-indicator">
        <div class="typing-dots">
          <span></span><span></span><span></span>
        </div>
        <span class="loading-text">{{ store.thinkingStatus }}</span>
      </div>

      <div class="scroll-anchor" />
    </div>
  </div>
</template>

<style scoped>
.chat-window {
  flex: 1;
  overflow-y: auto;
  padding: 0 16px;
  scroll-behavior: smooth;
}

/* 欢迎界面 */
.welcome-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 48px 24px;
  text-align: center;
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.welcome-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 8px;
  color: var(--text-primary);
}

.welcome-subtitle {
  font-size: 15px;
  color: var(--text-secondary);
  margin: 0 0 32px;
  max-width: 480px;
}

.suggestion-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  max-width: 520px;
  width: 100%;
}

.suggestion-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
  color: var(--text-primary);
  text-align: left;
}

.suggestion-card:hover {
  background: var(--bg-hover);
  border-color: var(--color-primary);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.suggestion-icon {
  font-size: 22px;
  flex-shrink: 0;
}

/* 消息列表 */
.message-list {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px 0;
}

/* 加载指示器 */
.loading-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  margin: 8px 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.typing-dots {
  display: flex;
  gap: 4px;
}

.typing-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-primary);
  animation: typing-bounce 1.4s infinite ease-in-out both;
}

.typing-dots span:nth-child(1) { animation-delay: -0.32s; }
.typing-dots span:nth-child(2) { animation-delay: -0.16s; }
.typing-dots span:nth-child(3) { animation-delay: 0s; }

@keyframes typing-bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

.loading-text {
  color: var(--text-secondary);
}

.scroll-anchor {
  height: 1px;
}

/* 响应式 */
@media (max-width: 768px) {
  .welcome-title {
    font-size: 22px;
  }

  .suggestion-cards {
    grid-template-columns: 1fr;
  }

  .message-list {
    padding: 16px 0;
  }
}
</style>
