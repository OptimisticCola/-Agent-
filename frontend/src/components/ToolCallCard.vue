<!-- ============================================ -->
<!-- 工具调用卡片 -->
<!-- ============================================ -->
<script setup lang="ts">
import { computed } from 'vue'
import type { ToolCall } from '@/types'

const props = defineProps<{
  toolCall: ToolCall
}>()

const iconMap: Record<string, string> = {
  search_knowledge: '🩺',
  create_ticket: '📅',
  query_order: '📋',
  transfer_to_human: '👩‍⚕️',
}

const toolIcon = computed(() => iconMap[props.toolCall.tool] || '🔧')

const toolLabel = computed(() => {
  const labels: Record<string, string> = {
    search_knowledge: '医疗知识检索',
    create_ticket: '就诊预约',
    query_order: '查看预约',
    transfer_to_human: '转接人工',
  }
  return labels[props.toolCall.tool] || props.toolCall.tool
})

const statusColor = computed(() => {
  switch (props.toolCall.status) {
    case 'running': return 'var(--color-warning)'
    case 'completed': return 'var(--color-success)'
    case 'error': return 'var(--color-danger)'
    default: return 'var(--text-tertiary)'
  }
})

const statusLabel = computed(() => {
  const labels: Record<string, string> = {
    pending: '等待中',
    running: '执行中',
    completed: '已完成',
    error: '出错',
  }
  return labels[props.toolCall.status] || props.toolCall.status
})
</script>

<template>
  <div class="tool-call-card" :class="toolCall.status">
    <div class="tool-header">
      <span class="tool-icon">{{ toolIcon }}</span>
      <span class="tool-name">{{ toolLabel }}</span>
      <span class="tool-status" :style="{ color: statusColor }">
        <span v-if="toolCall.status === 'running'" class="status-dot pulse" />
        <span v-else class="status-dot" />
        {{ statusLabel }}
      </span>
    </div>

    <div v-if="toolCall.message" class="tool-message">
      {{ toolCall.message }}
    </div>

    <div v-if="toolCall.preview" class="tool-preview">
      <code>{{ toolCall.preview }}</code>
    </div>
  </div>
</template>

<style scoped>
.tool-call-card {
  background: var(--bg-tool-call);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 12px;
  max-width: 320px;
}

.tool-call-card.running {
  border-color: var(--color-warning);
}

.tool-call-card.completed {
  border-color: var(--color-success);
  opacity: 0.9;
}

.tool-call-card.error {
  border-color: var(--color-danger);
}

.tool-header {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tool-icon {
  font-size: 14px;
}

.tool-name {
  font-weight: 600;
  color: var(--text-primary);
  flex: 1;
}

.tool-status {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.status-dot.pulse {
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.7); }
}

.tool-message {
  margin-top: 6px;
  color: var(--text-secondary);
  font-size: 11px;
}

.tool-preview {
  margin-top: 6px;
  background: var(--bg-code);
  border-radius: 4px;
  padding: 4px 8px;
  overflow-x: auto;
  max-height: 60px;
  overflow-y: auto;
}

.tool-preview code {
  font-size: 11px;
  font-family: 'Fira Code', monospace;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
