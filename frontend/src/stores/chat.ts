// ============================================
// Pinia 聊天状态管理
// ============================================
import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import type { ChatMessage, Session, ToolCall, Source } from '@/types'
import { v4 as uuidv4 } from 'uuid'
import { getChatHistory } from '@/api/chat'

export const useChatStore = defineStore('chat', () => {
  // --- 状态 ---
  const sessions = ref<Session[]>([])
  const currentSessionId = ref<string>('')
  const messages = ref<ChatMessage[]>([])
  const isLoading = ref(false)
  const thinkingStatus = ref('')
  const activeToolCalls = ref<Map<string, ToolCall>>(new Map())
  const darkMode = ref(false)
  const sidebarCollapsed = ref(false)

  // --- 计算属性 ---
  const currentMessages = computed(() => messages.value)
  const hasMessages = computed(() => messages.value.length > 0)

  // --- 方法 ---
  function initSession(sessionId?: string) {
    if (sessionId) {
      currentSessionId.value = sessionId
    } else {
      currentSessionId.value = uuidv4()
    }
    messages.value = []
    activeToolCalls.value = new Map()
    thinkingStatus.value = ''
  }

  function addMessage(message: Partial<ChatMessage> & { role: ChatMessage['role']; content: string }) {
    const msg: ChatMessage = {
      id: uuidv4(),
      role: message.role,
      content: message.content,
      timestamp: Date.now(),
      toolCalls: message.toolCalls || [],
      sources: message.sources || [],
      isStreaming: message.isStreaming || false,
    }
    messages.value.push(msg)
    return msg
  }

  function appendToLastMessage(content: string) {
    // 防御：忽略非字符串内容（如被错误路由的 done 事件数据、null、undefined）
    if (typeof content !== 'string' || !content) return
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg && lastMsg.role === 'assistant') {
      lastMsg.content += content
    }
  }

  /** 替换最后一条助手消息的完整内容（非流式模式使用） */
  function replaceLastMessage(content: string) {
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg && lastMsg.role === 'assistant') {
      lastMsg.content = typeof content === 'string' ? content : String(content || '')
    }
  }

  function finishLastMessage(sources?: Source[]) {
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg && lastMsg.role === 'assistant') {
      lastMsg.isStreaming = false
      if (Array.isArray(sources) && sources.length > 0) {
        lastMsg.sources = sources
      }
    }
  }

  function addToolCall(tool: string, status: string = 'running', message?: string) {
    const tc: ToolCall = {
      id: uuidv4(),
      tool,
      status: status as ToolCall['status'],
      message,
    }
    activeToolCalls.value.set(tc.id, tc)

    // 同时添加到当前消息
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg && lastMsg.role === 'assistant') {
      if (!lastMsg.toolCalls) lastMsg.toolCalls = []
      lastMsg.toolCalls.push(tc)
    }

    return tc
  }

  function updateToolCall(id: string, updates: Partial<ToolCall>) {
    const tc = activeToolCalls.value.get(id)
    if (tc) {
      Object.assign(tc, updates)
    }
  }

  function removeToolCall(id: string) {
    activeToolCalls.value.delete(id)
  }

  function setThinking(status: string) {
    thinkingStatus.value = status
  }

  function setLoading(val: boolean) {
    isLoading.value = val
  }

  // 监听 darkMode 变化，自动切换 CSS class
  watch(darkMode, (val) => {
    document.documentElement.classList.toggle('dark', val)
  })

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  async function loadSession(sessionId: string) {
    currentSessionId.value = sessionId
    try {
      const data = await getChatHistory(sessionId)
      messages.value = (data.messages || []).map((msg: any) => ({
        id: uuidv4(),
        role: msg.role,
        content: msg.content,
        timestamp: Date.now(),
        toolCalls: msg.tool_calls || [],
        sources: msg.sources || [],
        isStreaming: false,
      }))
    } catch {
      messages.value = []
    }
    activeToolCalls.value = new Map()
    thinkingStatus.value = ''
  }

  return {
    // 状态
    sessions,
    currentSessionId,
    messages,
    isLoading,
    thinkingStatus,
    activeToolCalls,
    darkMode,
    sidebarCollapsed,
    // 计算属性
    currentMessages,
    hasMessages,
    // 方法
    initSession,
    addMessage,
    appendToLastMessage,
    replaceLastMessage,
    finishLastMessage,
    addToolCall,
    updateToolCall,
    removeToolCall,
    setThinking,
    setLoading,
    toggleSidebar,
    loadSession,
  }
})
