# ============================================
# MCP Server: 人工客服转接
# ============================================
import os
import sys
from typing import Dict, Any
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mcp_servers.base import MCPServerBase, MCPServerConfig


class HumanServer(MCPServerBase):
    """人工客服转接服务 — 转接医护人员"""

    def __init__(self):
        config = MCPServerConfig(
            name="human_server",
            description="人工客服转接 MCP Server — 将对话转接给医护人员",
            port=8004,
        )
        super().__init__(config)
        self.transfer_queue: list = []
        self.available_staff = [
            {"id": "SF-001", "name": "张护士长", "role": "护理主管", "department": "护理部", "status": "available"},
            {"id": "SF-002", "name": "李医生助理", "role": "医师助理", "department": "内科", "status": "available"},
            {"id": "SF-003", "name": "王导诊", "role": "导诊员", "department": "门诊部", "status": "busy"},
            {"id": "SF-004", "name": "赵客服", "role": "患者服务", "department": "患者服务中心", "status": "available"},
        ]
        self._transfer_counter = 0

    def list_tools(self) -> Dict[str, Any]:
        return {
            "transfer": {
                "description": "转接人工客服",
                "parameters": {
                    "reason": {"type": "string", "description": "转接原因"},
                    "priority": {"type": "string", "description": "紧急程度", "default": "normal"},
                    "summary": {"type": "string", "description": "问题摘要"},
                    "session_id": {"type": "string", "description": "会话 ID"},
                },
            },
            "get_queue_status": {
                "description": "获取排队状态",
                "parameters": {
                    "transfer_id": {"type": "string", "description": "转接编号"},
                },
            },
            "list_staff": {
                "description": "列出在线客服人员",
                "parameters": {},
            },
        }

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        if tool_name == "transfer":
            return await self._transfer(arguments)
        elif tool_name == "get_queue_status":
            return await self._get_queue_status(arguments)
        elif tool_name == "list_staff":
            return self.available_staff
        else:
            raise ValueError(f"未知工具: {tool_name}")

    async def _transfer(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        self._transfer_counter += 1
        transfer_id = f"TR-{self._transfer_counter:04d}"

        available = [a for a in self.available_staff if a["status"] == "available"]
        queue_position = max(0, len(self.transfer_queue))

        assigned = None
        if available:
            assigned = available[0]
            assigned["status"] = "busy"

        transfer = {
            "transfer_id": transfer_id,
            "reason": arguments.get("reason", "用户请求"),
            "priority": arguments.get("priority", "normal"),
            "summary": arguments.get("summary", ""),
            "session_id": arguments.get("session_id", ""),
            "status": "queued",
            "queue_position": queue_position,
            "estimated_wait": f"约 {queue_position * 2 + 1} 分钟",
            "assigned_staff": assigned,
            "created_at": datetime.now().isoformat(),
        }

        self.transfer_queue.append(transfer)
        print(f"✅ 转接请求已创建: {transfer_id} (队列位置: {queue_position})")

        return transfer

    async def _get_queue_status(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        transfer_id = arguments.get("transfer_id", "")
        for t in self.transfer_queue:
            if t["transfer_id"] == transfer_id:
                idx = self.transfer_queue.index(t)
                t["queue_position"] = idx
                t["estimated_wait"] = f"约 {idx * 2 + 1} 分钟"
                return t
        raise ValueError(f"转接编号不存在: {transfer_id}")


if __name__ == "__main__":
    server = HumanServer()
    server.run()
