# ============================================
# 聊天 API — SSE 流式对话
# ============================================
import json
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agent.graph import AgentGraph
from agent.state import Message

router = APIRouter(tags=["聊天"])

# 全局 agent 实例 (生产环境建议用依赖注入)
agent_graph = AgentGraph()

# 会话存储 (生产环境应使用 Redis/数据库)
sessions: dict = {}
session_messages: dict = {}


class ChatRequest(BaseModel):
    message: str = Field(..., description="用户消息")
    session_id: str = Field(default="", description="会话 ID，空则新建")


class CreateSessionRequest(BaseModel):
    title: str = Field(default="新对话", description="会话标题")


class ChatEvent:
    """SSE 事件类型"""
    THINKING = "thinking"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    CHUNK = "chunk"
    SOURCES = "sources"
    DONE = "done"
    ERROR = "error"


@router.post("/chat")
async def chat(request: ChatRequest):
    """发送消息，SSE 流式返回"""
    session_id = request.session_id or str(uuid.uuid4())

    # 初始化会话
    if session_id not in session_messages:
        session_messages[session_id] = []
    if session_id not in sessions:
        sessions[session_id] = {
            "id": session_id, "title": "新对话",
            "created_at": __import__("datetime").datetime.now().isoformat(),
        }

    # 保存用户消息
    session_messages[session_id].append({
        "role": "user",
        "content": request.message,
    })

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            # 发送会话 ID
            yield f"event: session\ndata: {json.dumps({'session_id': session_id})}\n\n"

            # 发送思考状态
            yield f"event: {ChatEvent.THINKING}\ndata: {json.dumps({'status': '正在分析您的问题...'})}\n\n"

            # 调用 LangGraph Agent
            full_response = ""
            sources = []
            tool_calls_log = []

            async for event in agent_graph.stream(
                user_message=request.message,
                session_id=session_id,
                history=session_messages.get(session_id, [])[:-1],  # 不含当前消息
            ):
                event_type = event.get("type")
                event_data = event.get("data", {})

                if event_type == ChatEvent.THINKING:
                    yield f"event: {ChatEvent.THINKING}\ndata: {json.dumps(event_data, ensure_ascii=False)}\n\n"

                elif event_type == ChatEvent.TOOL_CALL:
                    tool_calls_log.append(event_data)
                    yield f"event: {ChatEvent.TOOL_CALL}\ndata: {json.dumps(event_data, ensure_ascii=False)}\n\n"

                elif event_type == ChatEvent.TOOL_RESULT:
                    yield f"event: {ChatEvent.TOOL_RESULT}\ndata: {json.dumps(event_data, ensure_ascii=False)}\n\n"

                elif event_type == ChatEvent.CHUNK:
                    full_response += event_data.get("content", "")
                    yield f"event: {ChatEvent.CHUNK}\ndata: {json.dumps(event_data, ensure_ascii=False)}\n\n"

                elif event_type == ChatEvent.SOURCES:
                    sources = event_data.get("sources", [])

            # 保存助手消息
            session_messages[session_id].append({
                "role": "assistant",
                "content": full_response,
                "tool_calls": tool_calls_log,
                "sources": sources,
            })

            # 发送完成事件
            yield f"event: {ChatEvent.DONE}\ndata: {json.dumps({'sources': sources, 'session_id': session_id}, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"event: {ChatEvent.ERROR}\ndata: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat/sync")
async def chat_sync(request: ChatRequest):
    """非流式聊天接口 —— 一次性返回完整回复"""
    session_id = request.session_id or str(uuid.uuid4())

    # 初始化会话
    if session_id not in session_messages:
        session_messages[session_id] = []
    if session_id not in sessions:
        sessions[session_id] = {
            "id": session_id, "title": "新对话",
            "created_at": __import__("datetime").datetime.now().isoformat(),
        }

    # 保存用户消息
    session_messages[session_id].append({
        "role": "user",
        "content": request.message,
    })

    try:
        result = await agent_graph.invoke(
            user_message=request.message,
            session_id=session_id,
            history=session_messages.get(session_id, [])[:-1],
        )

        output = result.get("output", "")
        sources = result.get("sources", [])
        tool_calls = result.get("tool_calls", [])

        # 保存助手消息
        session_messages[session_id].append({
            "role": "assistant",
            "content": output,
            "tool_calls": tool_calls,
            "sources": sources,
        })

        return {
            "session_id": session_id,
            "content": output,
            "sources": sources,
            "tool_calls": tool_calls,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/history/{session_id}")
async def get_history(session_id: str):
    """获取会话历史"""
    messages = session_messages.get(session_id, [])
    return {
        "session_id": session_id,
        "messages": messages,
        "total": len(messages),
    }


@router.post("/chat/session")
async def create_session(request: CreateSessionRequest):
    """创建新会话"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "id": session_id,
        "title": request.title,
        "created_at": __import__("datetime").datetime.now().isoformat(),
    }
    session_messages[session_id] = []
    return {"session_id": session_id, "title": request.title}


@router.get("/chat/sessions")
async def get_sessions():
    """获取所有会话列表（只返回有消息的会话）"""
    result = []
    for sid, msgs in session_messages.items():
        if not msgs:
            continue  # 跳过空会话
        msg_count = len(msgs)
        info = sessions.get(sid, {})
        last_msg = msgs[-1].get("content", "")[:50] if msgs else ""

        # 取第一条用户消息作为标题
        first_user = ""
        for m in msgs:
            if m.get("role") == "user":
                first_user = m.get("content", "")[:20]
                break

        result.append({
            "id": sid,
            "title": first_user or "新对话",
            "message_count": msg_count,
            "last_message": last_msg,
            "created_at": info.get("created_at", ""),
        })
    # 有消息的排前面，按最后更新时间倒序
    result.sort(key=lambda x: x.get("message_count", 0), reverse=True)
    return {"sessions": result}
