// ============================================
// TypeScript 类型定义
// ============================================

/** 消息角色 */
export type MessageRole = 'user' | 'assistant' | 'system'

/** 工具调用状态 */
export type ToolCallStatus = 'pending' | 'running' | 'completed' | 'error'

/** 聊天消息 */
export interface ChatMessage {
  id: string
  role: MessageRole
  content: string
  timestamp: number
  toolCalls?: ToolCall[]
  sources?: Source[]
  isStreaming?: boolean
}

/** 工具调用 */
export interface ToolCall {
  id: string
  tool: string
  status: ToolCallStatus
  message?: string
  preview?: string
  ticketId?: string
  result?: any
}

/** 知识来源 */
export interface Source {
  source: string
  score: number
  content?: string
}

/** 会话 */
export interface Session {
  id: string
  title: string
  messageCount: number
  lastMessage: string
  createdAt: string
}

/** SSE 事件类型 */
export enum SSEEventType {
  SESSION = 'session',
  THINKING = 'thinking',
  TOOL_CALL = 'tool_call',
  TOOL_RESULT = 'tool_result',
  CHUNK = 'chunk',
  SOURCES = 'sources',
  DONE = 'done',
  ERROR = 'error',
}

/** SSE 事件数据 */
export interface SSEEvent {
  type: SSEEventType
  data: any
}

/** 工具信息 */
export interface ToolInfo {
  name: string
  description: string
  server: string
  parameters: Record<string, any>
}

/** 发送消息请求 */
export interface ChatRequest {
  message: string
  session_id: string
}

/** 聊天响应 */
export interface ChatResponse {
  session_id: string
  sources?: Source[]
}

/** 会话历史响应 */
export interface HistoryResponse {
  session_id: string
  messages: ChatMessage[]
  total: number
}
