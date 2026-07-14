# ============================================
# Agent 工具封装 — 对接 MCP Server
# ============================================
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import httpx

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class MCPTool:
    name: str
    description: str
    server_url: str
    parameters: Dict[str, Any]


# 工具注册表
TOOLS_REGISTRY: Dict[str, MCPTool] = {
    "search_knowledge": MCPTool(
        name="search_knowledge",
        description="检索知识库，获取产品文档、政策、FAQ 等信息",
        server_url=f"http://localhost:{settings.mcp_knowledge_port}/tools/search",
        parameters={
            "query": {"type": "string", "description": "搜索查询"},
            "top_k": {"type": "integer", "default": 5},
        },
    ),
    "create_ticket": MCPTool(
        name="create_ticket",
        description="创建工单，用于记录用户问题和跟踪处理进度",
        server_url=f"http://localhost:{settings.mcp_ticket_port}/tools/create",
        parameters={
            "title": {"type": "string", "description": "工单标题"},
            "description": {"type": "string", "description": "问题详细描述"},
            "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
        },
    ),
    "query_order": MCPTool(
        name="query_order",
        description="查询订单信息，包括订单状态、物流信息等",
        server_url=f"http://localhost:{settings.mcp_order_port}/tools/query",
        parameters={
            "order_id": {"type": "string", "description": "订单号"},
        },
    ),
    "transfer_to_human": MCPTool(
        name="transfer_to_human",
        description="转接人工客服",
        server_url=f"http://localhost:{settings.mcp_human_port}/tools/transfer",
        parameters={
            "reason": {"type": "string", "description": "转接原因"},
            "summary": {"type": "string", "description": "问题摘要"},
        },
    ),
}


async def call_mcp_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """
    调用 MCP Server 工具

    Args:
        tool_name: 工具名称
        arguments: 工具参数
        timeout: 超时时间

    Returns:
        工具执行结果
    """
    tool = TOOLS_REGISTRY.get(tool_name)
    if not tool:
        return {"error": f"未知工具: {tool_name}"}

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                tool.server_url,
                json={"arguments": arguments},
            )
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        logger.error(f"MCP 调用超时: {tool_name}")
        return {"error": f"工具 {tool_name} 调用超时"}
    except httpx.ConnectError:
        logger.warning(f"MCP Server 不可达: {tool.server_url}")
        # 返回模拟结果用于开发调试
        return {"result": f"[模拟] {tool_name} 执行成功", "arguments": arguments}
    except Exception as e:
        logger.error(f"MCP 调用异常: {tool_name} - {e}")
        return {"error": str(e)}


def get_tools_for_llm() -> List[Dict[str, Any]]:
    """
    生成 LLM function calling 格式的工具列表
    兼容 OpenAI function calling 格式
    """
    tools = []
    for name, tool in TOOLS_REGISTRY.items():
        tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        k: {
                            "type": v.get("type", "string"),
                            "description": v.get("description", ""),
                        }
                        for k, v in tool.parameters.items()
                    },
                    "required": [
                        k for k, v in tool.parameters.items()
                        if "default" not in v
                    ],
                },
            },
        })
    return tools
