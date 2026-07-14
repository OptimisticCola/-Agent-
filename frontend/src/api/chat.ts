// ============================================
// 聊天 API — SSE 流式通信
// ============================================
import type { Source } from '@/types'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

export interface StreamCallbacks {
  onSession?: (sessionId: string) => void
  onThinking?: (status: string, intent?: string, confidence?: number) => void
  onToolCall?: (data: any) => void
  onToolResult?: (data: any) => void
  onChunk?: (content: string) => void
  onSources?: (sources: Source[]) => void
  onDone?: (data: any) => void
  onError?: (error: string) => void
}

/**
 * 解析单个 SSE 事件块（以 \n\n 分隔的完整 block）。
 * 返回 { eventType, data }，解析失败返回 null。
 *
 * 兼容两种场景：
 * 1. 标准 SSE：event: xxx + data: {...}
 * 2. 仅有 event 无 data（例如 bare "event: done"）——返回 data: {}
 */
function parseSSEBlock(block: string): { eventType: string; data: any } | null {
  let eventType = 'message' // SSE 默认事件类型
  let hasEventLine = false

  for (const line of block.split('\n')) {
    if (line.startsWith('event:')) {
      // 兼容 "event:xxx" 和 "event: xxx" 两种格式
      const raw = line.slice(6)
      eventType = raw.startsWith(' ') ? raw.slice(1).trim() : raw.trim()
      hasEventLine = true
    } else if (line.startsWith('data:')) {
      // 兼容 "data:{}" 和 "data: {}" 两种格式
      const raw = line.slice(5)
      const jsonStr = raw.startsWith(' ') ? raw.slice(1) : raw
      try {
        const data = JSON.parse(jsonStr)
        return { eventType, data }
      } catch {
        // JSON 解析失败 —— 不静默丢弃，返回原始文本便于排查
        return { eventType, data: { _raw: jsonStr, _parseError: true } }
      }
    }
    // 忽略注释行（以 : 开头）和其他未知字段（id、retry 等）
  }

  // 仅有 event 行没有 data 行（例如 bare "event: done"）→ 返回空 data
  if (hasEventLine) {
    return { eventType, data: {} }
  }

  return null
}

/**
 * 分发已解析的 SSE 事件到对应回调。
 */
function dispatchEvent(
  eventType: string,
  data: any,
  callbacks: StreamCallbacks,
) {
  // JSON 解析失败的事件 —— 转发为 error 回调
  if (data?._parseError) {
    callbacks.onError?.(`SSE 数据解析失败: ${data._raw}`)
    return
  }

  switch (eventType) {
    case 'session':
      callbacks.onSession?.(data.session_id)
      break
    case 'thinking':
      callbacks.onThinking?.(data.status, data.intent, data.confidence)
      break
    case 'tool_call':
      callbacks.onToolCall?.(data)
      break
    case 'tool_result':
      callbacks.onToolResult?.(data)
      break
    case 'chunk':
      // 安全提取 content，避免将非 chunk 事件误解析
      if (typeof data.content === 'string') {
        callbacks.onChunk?.(data.content)
      }
      break
    case 'sources':
      callbacks.onSources?.(data.sources)
      break
    case 'done':
      callbacks.onDone?.(data)
      break
    case 'error':
      callbacks.onError?.(data.error)
      break
    case 'message':
      // SSE 默认事件类型 —— 尝试按 chunk 处理
      if (typeof data.content === 'string') {
        callbacks.onChunk?.(data.content)
      }
      break
    default:
      // 未知事件类型，安全忽略
      break
  }
}

/**
 * 发送消息并获取 SSE 流式响应。
 *
 * 使用标准 SSE 解析：按 \n\n 切分完整事件块，
 * 每个块内独立解析 event: / data: 行，不依赖跨块回溯。
 */
export async function sendChatMessage(
  request: ChatRequest,
  callbacks: StreamCallbacks,
  abortSignal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
    signal: abortSignal,
  })

  if (!response.ok) {
    const err = await response.text()
    callbacks.onError?.(`HTTP ${response.status}: ${err}`)
    return
  }

  const reader = response.body?.getReader()
  if (!reader) {
    callbacks.onError?.('无法读取响应流')
    return
  }

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })

    // 按 \n\n 切分完整事件块
    const parts = buffer.split('\n\n')
    // 最后一段可能是不完整的块，保留到下一次
    buffer = parts.pop() || ''

    for (const block of parts) {
      if (!block.trim()) continue
      const parsed = parseSSEBlock(block)
      if (parsed) {
        dispatchEvent(parsed.eventType, parsed.data, callbacks)
      }
    }
  }

  // 流结束后处理残留的 buffer（最后一个事件块）
  if (buffer.trim()) {
    const parsed = parseSSEBlock(buffer)
    if (parsed) {
      dispatchEvent(parsed.eventType, parsed.data, callbacks)
    }
  }
}

/**
 * 非流式发送消息 —— 等待完整回复后返回。
 * 用于替代 SSE 流式接口，解决流式解析不稳定导致 UI 卡死的问题。
 */
export async function sendMessageSync(
  message: string,
  sessionId: string,
  abortSignal?: AbortSignal,
): Promise<{ session_id: string; content: string; sources: Source[]; tool_calls: any[] }> {
  const response = await fetch(`${API_BASE}/api/chat/sync`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
    signal: abortSignal,
  })

  if (!response.ok) {
    const errText = await response.text().catch(() => '')
    throw new Error(`请求失败 (${response.status}): ${errText}`)
  }

  return response.json()
}

export interface ChatRequest {
  message: string
  session_id: string
}

/**
 * 获取会话历史
 */
export async function getChatHistory(sessionId: string) {
  const res = await fetch(`${API_BASE}/api/chat/history/${sessionId}`)
  return res.json()
}

/**
 * 创建新会话
 */
export async function createSession(title: string = '新对话') {
  const res = await fetch(`${API_BASE}/api/chat/session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  })
  return res.json()
}

/**
 * 获取会话列表
 */
export async function getSessions() {
  const res = await fetch(`${API_BASE}/api/chat/sessions`)
  return res.json()
}

/**
 * 获取工具列表
 */
export async function getTools() {
  const res = await fetch(`${API_BASE}/api/tools`)
  return res.json()
}

/**
 * 健康检查
 */
export async function healthCheck() {
  const res = await fetch(`${API_BASE}/api/health`)
  return res.json()
}
