<!-- ============================================ -->
<!-- 溯源展示卡片 -->
<!-- ============================================ -->
<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Source } from '@/types'

const props = defineProps<{
  sources: Source[]
}>()

const expanded = ref(false)

const topSources = computed(() => props.sources.slice(0, 3))

function formatScore(score: number): string {
  return (score * 100).toFixed(0) + '%'
}
</script>

<template>
  <div v-if="sources.length > 0" class="source-card">
    <div class="source-header" @click="expanded = !expanded">
      <div class="source-title">
        <span>📖 参考来源 ({{ sources.length }})</span>
      </div>
      <el-icon>
        <ArrowDown v-if="!expanded" />
        <ArrowUp v-else />
      </el-icon>
    </div>

    <div v-if="expanded" class="source-list">
      <div
        v-for="(source, idx) in sources"
        :key="idx"
        class="source-item"
      >
        <div class="source-item-header">
          <span class="source-index">#{{ idx + 1 }}</span>
          <span class="source-name">{{ source.source }}</span>
          <el-tag size="small" :type="source.score > 0.8 ? 'success' : 'info'">
            相关度 {{ formatScore(source.score) }}
          </el-tag>
        </div>
        <div v-if="source.content" class="source-content">
          {{ source.content?.slice(0, 200) }}{{ source.content && source.content.length > 200 ? '...' : '' }}
        </div>
      </div>
    </div>

    <!-- 折叠时显示简要信息 -->
    <div v-else class="source-summary">
      <span
        v-for="(source, idx) in topSources"
        :key="idx"
        class="source-chip"
      >
        {{ source.source }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.source-card {
  background: var(--bg-tool-call);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
}

.source-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  cursor: pointer;
  transition: background 0.2s;
  user-select: none;
}

.source-header:hover {
  background: var(--bg-hover);
}

.source-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}

.source-list {
  border-top: 1px solid var(--border-color);
  padding: 8px 12px;
}

.source-item {
  padding: 6px 0;
  border-bottom: 1px solid var(--border-color-light);
}

.source-item:last-child {
  border-bottom: none;
}

.source-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.source-index {
  font-size: 11px;
  color: var(--text-tertiary);
  font-weight: 600;
}

.source-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  flex: 1;
}

.source-content {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
  padding: 4px 0 4px 20px;
}

.source-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 4px 12px 8px;
}

.source-chip {
  font-size: 11px;
  background: var(--bg-hover);
  padding: 2px 8px;
  border-radius: 4px;
  color: var(--text-secondary);
}
</style>
