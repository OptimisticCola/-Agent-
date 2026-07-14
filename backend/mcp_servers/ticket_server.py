# ============================================
# MCP Server: 挂号预约
# ============================================
import os
import sys
from typing import Dict, Any
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mcp_servers.base import MCPServerBase, MCPServerConfig


class TicketServer(MCPServerBase):
    """挂号预约服务 — 创建、查询、管理就诊预约"""

    def __init__(self):
        config = MCPServerConfig(
            name="ticket_server",
            description="挂号预约 MCP Server — 创建、查询和管理就诊预约",
            port=8002,
        )
        super().__init__(config)
        self.appointments: Dict[str, Dict[str, Any]] = {}
        self._counter = 1000
        self._seed_appointments()

    def _seed_appointments(self):
        """初始化示例预约"""
        sample = {
            "APPT-1001": {
                "appointment_id": "APPT-1001",
                "patient_name": "张三",
                "department": "心内科",
                "doctor": "李主任",
                "appointment_date": "2024-01-15 09:30",
                "status": "已确认",
                "location": "门诊楼 3 层 302 诊室",
                "created_at": "2024-01-14T10:00:00",
                "note": "请提前 15 分钟到达取号",
            },
            "APPT-1002": {
                "appointment_id": "APPT-1002",
                "patient_name": "李四",
                "department": "骨科",
                "doctor": "王医生",
                "appointment_date": "2024-01-16 14:00",
                "status": "已确认",
                "location": "门诊楼 2 层 205 诊室",
                "created_at": "2024-01-14T11:00:00",
                "note": "请携带既往影像资料",
            },
        }
        self.appointments.update(sample)
        self._counter = 1002

    def list_tools(self) -> Dict[str, Any]:
        return {
            "create": {
                "description": "创建就诊预约",
                "parameters": {
                    "patient_name": {"type": "string", "description": "患者姓名"},
                    "department": {"type": "string", "description": "预约科室"},
                    "doctor": {"type": "string", "description": "指定医生（可选）", "default": "系统分配"},
                    "appointment_date": {"type": "string", "description": "期望就诊时间"},
                },
            },
            "query": {
                "description": "查询预约状态",
                "parameters": {
                    "appointment_id": {"type": "string", "description": "预约编号"},
                },
            },
            "list_all": {
                "description": "列出所有预约",
                "parameters": {},
            },
        }

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        if tool_name == "create":
            return await self._create(arguments)
        elif tool_name == "query":
            return await self._query(arguments)
        elif tool_name == "list_all":
            return list(self.appointments.values())
        else:
            raise ValueError(f"未知工具: {tool_name}")

    async def _create(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        self._counter += 1
        appointment_id = f"APPT-{self._counter}"

        appointment = {
            "appointment_id": appointment_id,
            "patient_name": arguments.get("patient_name", "未提供"),
            "department": arguments.get("department", "未指定"),
            "doctor": arguments.get("doctor", "系统分配"),
            "appointment_date": arguments.get("appointment_date", "待定"),
            "status": "已预约",
            "location": "系统将自动分配诊室",
            "created_at": datetime.now().isoformat(),
            "note": "请提前 15 分钟到达取号",
        }
        self.appointments[appointment_id] = appointment
        print(f"✅ 预约已创建: {appointment_id}")
        return appointment

    async def _query(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        appointment_id = arguments.get("appointment_id", "")
        appointment = self.appointments.get(appointment_id)
        if appointment:
            return appointment
        raise ValueError(f"预约不存在: {appointment_id}")


if __name__ == "__main__":
    server = TicketServer()
    server.run()
