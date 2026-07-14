// ============================================
// 聊天逻辑组合式函数（非流式版本）
// ============================================
import { computed } from 'vue'
import { useChatStore } from '@/stores/chat'
import { sendMessageSync } from '@/api/chat'
import type { Source } from '@/types'

export function useChat() {
  const store = useChatStore()
  let abortController: AbortController | null = null

  /** 直接使用 store 的响应式计算属性，避免 readonly(ref()) 断连问题 */
  const isLoading = computed(() => store.isLoading)
  const thinkingStatus = computed(() => store.thinkingStatus)

  function cleanupState() {
    store.setLoading(false)
    store.setThinking('')
    store.finishLastMessage()
  }

  async function sendMessage(content: string) {
    if (!content.trim() || store.isLoading) return

    // 添加用户消息
    store.addMessage({ role: 'user', content: content.trim() })
    store.setLoading(true)
    store.setThinking('正在思考...')

    // 添加助手消息占位
    store.addMessage({
      role: 'assistant',
      content: '',
      isStreaming: true,
    })

    // 创建 AbortController
    abortController = new AbortController()

    try {
      const result = await sendMessageSync(
        content.trim(),
        store.currentSessionId,
        abortController.signal,
      )

      // 更新 session_id（新会话时后端会返回）
      if (result.session_id && !store.currentSessionId) {
        store.currentSessionId = result.session_id
      }

      // 一次性设置完整的回复内容
      store.replaceLastMessage(result.content)
      store.finishLastMessage(result.sources)
      store.setThinking('')
      store.setLoading(false)
    } catch (err: any) {
      if (err.name === 'AbortError') {
        // 用户手动停止 — 保留占位消息并清理状态
        cleanupState()
        return
      }
      // 网络错误或服务端错误 — 在最后一条消息中显示错误
      const errMsg = err?.message ? String(err.message) : String(err)
      store.replaceLastMessage(`❌ ${errMsg}`)
      cleanupState()
    }
  }

  function stopGenerating() {
    abortController?.abort()
    cleanupState()
  }

  function clearChat() {
    store.initSession()
  }

  return {
    sendMessage,
    stopGenerating,
    clearChat,
    isLoading,
    thinkingStatus,
  }
}
