# ============================================
# LangGraph Agent 状态定义
# ============================================
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class Intent(str, Enum):
    KNOWLEDGE_SEARCH = "knowledge_search"
    CREATE_TICKET = "create_ticket"
    QUERY_ORDER = "query_order"
    TRANSFER_HUMAN = "transfer_human"
    CHITCHAT = "chitchat"
    UNKNOWN = "unknown"


class Message(BaseModel):
    role: str = "user"
    content: str = ""


class ToolCall(BaseModel):
    tool_name: str = ""
    arguments: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[str] = None
    status: str = "pending"  # pending, running, completed, error


class AgentState(BaseModel):
    """Agent 工作流状态"""
    # 输入
    session_id: str = ""
    user_message: str = ""
    history: List[Dict[str, Any]] = Field(default_factory=list)

    # 中间状态
    intent: Intent = Intent.UNKNOWN
    intent_confidence: float = 0.0
    tool_calls: List[ToolCall] = Field(default_factory=list)
    knowledge_results: List[Dict[str, Any]] = Field(default_factory=list)

    # 输出
    final_response: str = ""
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    should_continue: bool = True
    error: Optional[str] = None
