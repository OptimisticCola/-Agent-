<!-- ============================================ -->
<!-- 聊天消息气泡 -->
<!-- ============================================ -->
<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import type { ChatMessage } from '@/types'
import ToolCallCard from './ToolCallCard.vue'
import SourceCard from './SourceCard.vue'

const props = defineProps<{
  message: ChatMessage
}>()

const isUser = computed(() => props.message.role === 'user')
const isStreaming = computed(() => props.message.isStreaming || false)

// Markdown 渲染
marked.setOptions({
  highlight(code: string, lang: string) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value
    }
    return hljs.highlightAuto(code).value
  },
  breaks: true,
  gfm: true,
})

const renderedContent = computed(() => {
  try {
    return marked.parse(props.message.content) as string
  } catch {
    return props.message.content
  }
})

const formattedTime = computed(() => {
  const d = new Date(props.message.timestamp)
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
})

const hasToolCalls = computed(() =>
  props.message.toolCalls && props.message.toolCalls.length > 0
)

const hasSources = computed(() =>
  props.message.sources && props.message.sources.length > 0
)
</script>

<template>
  <div class="message-item" :class="{ user: isUser, assistant: !isUser }">
    <!-- 头像 -->
    <div class="message-avatar">
      <span v-if="isUser">👤</span>
      <span v-else>🤖</span>
    </div>

    <!-- 消息主体 -->
    <div class="message-body">
      <!-- 工具调用卡片（助手消息的顶部） -->
      <div v-if="!isUser && hasToolCalls" class="tool-calls-section">
        <ToolCallCard
          v-for="tc in message.toolCalls"
          :key="tc.id"
          :tool-call="tc"
        />
      </div>

      <!-- 消息内容 -->
      <div class="message-bubble" :class="{ streaming: isStreaming }">
        <div
          v-if="isUser"
          class="message-text"
        >{{ message.content }}</div>
        <div
          v-else
          class="message-text markdown-body"
          v-html="renderedContent"
        />

        <!-- 打字光标 -->
        <span v-if="isStreaming" class="typing-cursor">|</span>
      </div>

      <!-- 来源展示（助手消息底部） -->
      <div v-if="!isUser && hasSources" class="sources-section">
        <SourceCard :sources="message.sources!" />
      </div>

      <!-- 时间戳 -->
      <div class="message-time">{{ formattedTime }}</div>
    </div>
  </div>
</template>

<style scoped>
.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  max-width: 90%;
}

.message-item.user {
  flex-direction: row-reverse;
  align-self: flex-end;
  margin-left: auto;
}

.message-item.assistant {
  align-self: flex-start;
}

/* 头像 */
.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
  background: var(--bg-avatar);
}

.message-item.user .message-avatar {
  background: var(--color-primary-light);
}

/* 消息主体 */
.message-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

/* 消息气泡 */
.message-bubble {
  padding: 12px 16px;
  border-radius: 16px;
  line-height: 1.6;
  word-break: break-word;
  position: relative;
}

.message-item.user .message-bubble {
  background: var(--color-primary);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message-item.assistant .message-bubble {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-bottom-left-radius: 4px;
}

.message-bubble.streaming {
  border-style: dashed;
}

/* 消息文本 */
.message-text {
  font-size: 14px;
  line-height: 1.7;
}

/* Markdown 内容样式 */
.markdown-body :deep(p) {
  margin: 0 0 8px;
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-body :deep(code) {
  background: var(--bg-code);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', monospace;
  font-size: 13px;
}

.markdown-body :deep(pre) {
  background: #1e1e2e;
  border-radius: 8px;
  padding: 16px;
  overflow-x: auto;
  margin: 8px 0;
}

.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 13px;
  color: #cdd6f4;
}

.markdown-body :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid var(--border-color);
  padding: 8px 12px;
  text-align: left;
  font-size: 13px;
}

.markdown-body :deep(th) {
  background: var(--bg-hover);
  font-weight: 600;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 4px 0;
  padding-left: 20px;
}

.markdown-body :deep(strong) {
  font-weight: 600;
}

.markdown-body :deep(blockquote) {
  border-left: 3px solid var(--color-primary);
  margin: 8px 0;
  padding: 4px 12px;
  color: var(--text-secondary);
}

/* 打字光标 */
.typing-cursor {
  display: inline-block;
  animation: blink 0.7s infinite;
  color: var(--color-primary);
  font-weight: bold;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* 时间戳 */
.message-time {
  font-size: 11px;
  color: var(--text-tertiary);
  padding: 0 4px;
}

.message-item.user .message-time {
  text-align: right;
}

/* 工具调用区域 */
.tool-calls-section {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 4px;
}

/* 来源区域 */
.sources-section {
  margin-top: 4px;
}

/* 响应式 */
@media (max-width: 768px) {
  .message-item {
    max-width: 95%;
  }

  .message-bubble {
    padding: 10px 14px;
  }
}
</style>
