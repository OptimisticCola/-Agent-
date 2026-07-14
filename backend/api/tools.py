# ============================================
# 工具列表 API
# ============================================
from fastapi import APIRouter

router = APIRouter(tags=["工具"])


@router.get("/tools")
async def get_tools():
    """获取可用工具列表"""
    return {
        "tools": [
            {
                "name": "search_knowledge",
                "description": "检索知识库中的相关内容",
                "server": "knowledge_server",
                "parameters": {
                    "query": {"type": "string", "description": "搜索查询"},
                    "top_k": {"type": "integer", "description": "返回结果数", "default": 5},
                },
            },
            {
                "name": "create_ticket",
                "description": "创建工单",
                "server": "ticket_server",
                "parameters": {
                    "title": {"type": "string", "description": "工单标题"},
                    "description": {"type": "string", "description": "问题描述"},
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "urgent"],
                        "description": "优先级",
                    },
                    "category": {"type": "string", "description": "问题分类"},
                },
            },
            {
                "name": "query_order",
                "description": "查询订单信息",
                "server": "order_server",
                "parameters": {
                    "order_id": {"type": "string", "description": "订单号"},
                },
            },
            {
                "name": "transfer_to_human",
                "description": "转接人工客服",
                "server": "human_server",
                "parameters": {
                    "reason": {"type": "string", "description": "转接原因"},
                    "priority": {"type": "string", "description": "紧急程度"},
                    "summary": {"type": "string", "description": "问题摘要"},
                },
            },
        ]
    }
