<!-- ============================================ -->
<!-- 聊天输入框 -->
<!-- ============================================ -->
<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'

const props = defineProps<{
  loading: boolean
  disabled: boolean
}>()

const emit = defineEmits<{
  send: [message: string]
  stop: []
}>()

const inputText = ref('')
const textareaRef = ref<HTMLTextAreaElement>()

function handleSend() {
  const text = inputText.value.trim()
  if (!text || props.loading) return

  emit('send', text)
  inputText.value = ''
  nextTick(() => adjustHeight())
}

function handleKeydown(e: KeyboardEvent) {
  // Enter 发送，Shift+Enter 换行
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

function handleStop() {
  emit('stop')
}

function adjustHeight() {
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
    textareaRef.value.style.height = Math.min(textareaRef.value.scrollHeight, 150) + 'px'
  }
}

onMounted(() => {
  textareaRef.value?.focus()
})
</script>

<template>
  <div class="chat-input-container">
    <div class="input-wrapper">
      <textarea
        ref="textareaRef"
        v-model="inputText"
        :disabled="disabled"
        class="chat-textarea"
        :class="{ loading: loading }"
        placeholder="输入您的问题... (Enter 发送，Shift+Enter 换行)"
        rows="1"
        @keydown="handleKeydown"
        @input="adjustHeight"
      />

      <div class="input-actions">
        <div class="input-hint">
          <span class="hint-text">{{ loading ? '正在回复...' : 'Enter 发送' }}</span>
        </div>

        <div class="input-buttons">
          <el-button
            v-if="loading"
            type="danger"
            size="small"
            round
            @click="handleStop"
          >
            停止
          </el-button>

          <el-button
            v-else
            type="primary"
            size="small"
            round
            :disabled="!inputText.trim() || disabled"
            @click="handleSend"
          >
            <el-icon><Promotion /></el-icon>
            发送
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-input-container {
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
}

.input-wrapper {
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 8px 12px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.input-wrapper:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-alpha);
}

.chat-textarea {
  width: 100%;
  border: none;
  outline: none;
  resize: none;
  font-size: 14px;
  line-height: 1.6;
  padding: 6px 4px;
  background: transparent;
  color: var(--text-primary);
  font-family: inherit;
  min-height: 24px;
  max-height: 150px;
}

.chat-textarea::placeholder {
  color: var(--text-tertiary);
}

.chat-textarea:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 4px;
}

.input-hint {
  font-size: 11px;
  color: var(--text-tertiary);
}

.input-buttons {
  display: flex;
  gap: 6px;
}

/* 响应式 */
@media (max-width: 768px) {
  .chat-input-container {
    padding: 0;
  }

  .input-wrapper {
    border-radius: 12px;
  }
}
</style>
