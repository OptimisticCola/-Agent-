# ============================================
# LangGraph 工作流图定义
#
# 工作流:
#   用户输入 → 意图识别 → 路由决策 → 工具调用 → 回答生成
# ============================================
import logging
from typing import AsyncGenerator, Dict, Any, List

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agent.state import AgentState, Intent
from agent.nodes import (
    recognize_intent,
    route_by_intent,
    search_knowledge_node,
    create_ticket_node,
    query_order_node,
    transfer_human_node,
    generate_answer_node,
)

logger = logging.getLogger(__name__)


class AgentGraph:
    """LangGraph Agent 工作流管理器"""

    def __init__(self):
        self.graph = self._build_graph()
        self.checkpointer = MemorySaver()

    def _build_graph(self) -> StateGraph:
        """构建工作流图"""
        workflow = StateGraph(AgentState)

        # 添加节点
        workflow.add_node("recognize_intent", recognize_intent)
        workflow.add_node("search_knowledge", search_knowledge_node)
        workflow.add_node("create_ticket", create_ticket_node)
        workflow.add_node("query_order", query_order_node)
        workflow.add_node("transfer_human", transfer_human_node)
        workflow.add_node("generate_answer", generate_answer_node)

        # 设置入口: 意图识别
        workflow.set_entry_point("recognize_intent")

        # 条件路由: 根据意图分发到不同节点
        workflow.add_conditional_edges(
            "recognize_intent",
            route_by_intent,
            {
                "search_knowledge": "search_knowledge",
                "create_ticket": "create_ticket",
                "query_order": "query_order",
                "transfer_human": "transfer_human",
                "generate_answer": "generate_answer",
            },
        )

        # 所有工具节点完成后 → 生成回答
        workflow.add_edge("search_knowledge", "generate_answer")
        workflow.add_edge("create_ticket", END)  # 工单创建后直接结束（已包含回答）
        workflow.add_edge("query_order", END)     # 订单查询后直接结束（已包含回答）
        workflow.add_edge("transfer_human", END)  # 转接后直接结束（已包含回答）
        workflow.add_edge("generate_answer", END)

        return workflow.compile()

    async def invoke(
        self,
        user_message: str,
        session_id: str,
        history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        非流式执行 Agent 工作流，返回完整结果。

        Returns:
            {
                "output": str,        # 完整回复文本
                "sources": list,      # 知识来源
                "tool_calls": list,   # 工具调用日志
                "intent": str,        # 识别到的意图
            }
        """
        output = ""
        sources = []
        tool_calls_log = []
        intent = "unknown"

        async for event in self.stream(user_message, session_id, history):
            event_type = event.get("type")
            event_data = event.get("data", {})

            if event_type == "chunk":
                output += event_data.get("content", "")
            elif event_type == "sources":
                sources = event_data.get("sources", [])
            elif event_type == "tool_call":
                tool_calls_log.append(event_data)
            elif event_type == "tool_result":
                # 将结果合并到最近的 tool_call
                if tool_calls_log:
                    tool_calls_log[-1]["result"] = event_data
            elif event_type == "thinking" and "intent" in event_data:
                intent = event_data["intent"]

        return {
            "output": output,
            "sources": sources,
            "tool_calls": tool_calls_log,
            "intent": intent,
        }

    async def stream(
        self,
        user_message: str,
        session_id: str,
        history: List[Dict[str, Any]],
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式执行 Agent 工作流

        Yields:
            {"type": "thinking", "data": {"status": "..."}}
            {"type": "tool_call", "data": {...}}
            {"type": "tool_result", "data": {...}}
            {"type": "chunk", "data": {"content": "..."}}
            {"type": "sources", "data": {"sources": [...]}}
        """
        # 1. 意图识别
        yield {
            "type": "thinking",
            "data": {"status": "正在识别您的意图..."},
        }

        intent_result = await recognize_intent(AgentState(
            session_id=session_id,
            user_message=user_message,
            history=history,
        ))

        intent = intent_result.get("intent", Intent.UNKNOWN)
        confidence = intent_result.get("intent_confidence", 0)

        intent_names = {
            Intent.KNOWLEDGE_SEARCH: "正在检索相关知识...",
            Intent.CREATE_TICKET: "正在为您创建工单...",
            Intent.QUERY_ORDER: "正在查询订单信息...",
            Intent.TRANSFER_HUMAN: "正在转接人工客服...",
            Intent.CHITCHAT: "正在为您准备回答...",
            Intent.UNKNOWN: "正在分析您的问题...",
        }

        yield {
            "type": "thinking",
            "data": {
                "status": intent_names.get(intent, "正在处理..."),
                "intent": intent.value,
                "confidence": confidence,
            },
        }

        # 2. 工具调用（根据意图）
        state = AgentState(
            session_id=session_id,
            user_message=user_message,
            history=history,
            intent=intent,
            intent_confidence=confidence,
        )

        tool_calls_made = []

        if intent == Intent.KNOWLEDGE_SEARCH:
            yield {
                "type": "tool_call",
                "data": {
                    "tool": "search_knowledge",
                    "status": "running",
                    "message": "正在搜索知识库...",
                },
            }
            result = await search_knowledge_node(state)
            tool_calls_made = result.get("tool_calls", [])
            for tc in tool_calls_made:
                yield {
                    "type": "tool_result",
                    "data": {
                        "tool": tc.tool_name,
                        "status": tc.status,
                        "preview": str(tc.result)[:200] if tc.result else "",
                    },
                }
            state = state.model_copy(update=result)

        elif intent == Intent.CREATE_TICKET:
            yield {
                "type": "tool_call",
                "data": {
                    "tool": "create_ticket",
                    "status": "running",
                    "message": "正在创建工单...",
                },
            }
            result = await create_ticket_node(state)
            tool_calls_made = result.get("tool_calls", [])
            for tc in tool_calls_made:
                yield {
                    "type": "tool_result",
                    "data": {
                        "tool": tc.tool_name,
                        "status": tc.status,
                        "ticket_id": tc.result,
                    },
                }
            state = state.model_copy(update=result)

        elif intent == Intent.QUERY_ORDER:
            yield {
                "type": "tool_call",
                "data": {
                    "tool": "query_order",
                    "status": "running",
                    "message": "正在查询订单...",
                },
            }
            result = await query_order_node(state)
            tool_calls_made = result.get("tool_calls", [])
            for tc in tool_calls_made:
                yield {
                    "type": "tool_result",
                    "data": {
                        "tool": tc.tool_name,
                        "status": tc.status,
                        "preview": str(tc.result)[:200] if tc.result else "",
                    },
                }
            state = state.model_copy(update=result)

        elif intent == Intent.TRANSFER_HUMAN:
            yield {
                "type": "tool_call",
                "data": {
                    "tool": "transfer_to_human",
                    "status": "running",
                    "message": "正在排队转接...",
                },
            }
            result = await transfer_human_node(state)
            tool_calls_made = result.get("tool_calls", [])
            for tc in tool_calls_made:
                yield {
                    "type": "tool_result",
                    "data": {
                        "tool": tc.tool_name,
                        "status": tc.status,
                    },
                }
            state = state.model_copy(update=result)

        # 3. 回答生成
        if not state.final_response:
            answer_result = await generate_answer_node(state)
            state = state.model_copy(update=answer_result)

        # 4. 流式输出回答（模拟打字机效果）
        if state.final_response:
            # 分块输出，模拟流式效果
            text = state.final_response
            chunk_size = 3  # 每块字符数
            for i in range(0, len(text), chunk_size):
                chunk = text[i:i + chunk_size]
                yield {
                    "type": "chunk",
                    "data": {"content": chunk},
                }
                import asyncio
                await asyncio.sleep(0.03)  # 模拟打字延迟

        # 5. 返回来源
        if state.sources:
            yield {
                "type": "sources",
                "data": {"sources": state.sources},
            }
