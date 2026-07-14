# ============================================
# MCP Server: 预约查询
# ============================================
import os
import sys
from typing import Dict, Any
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mcp_servers.base import MCPServerBase, MCPServerConfig


class OrderServer(MCPServerBase):
    """预约查询服务 — 查询就诊预约记录和状态"""

    def __init__(self):
        config = MCPServerConfig(
            name="order_server",
            description="预约查询 MCP Server — 查询就诊预约记录、状态和排班信息",
            port=8003,
        )
        super().__init__(config)
        self.appointments: Dict[str, Dict[str, Any]] = {}
        self._seed_appointments()

    def _seed_appointments(self):
        """初始化示例预约记录"""
        samples = {
            "APPT-2024-001": {
                "appointment_id": "APPT-2024-001",
                "patient_name": "张三",
                "department": "心内科",
                "doctor": "李主任",
                "appointment_date": "2024-07-15 09:30",
                "status": "已确认",
                "location": "门诊楼 3 层 302 诊室",
                "payment_status": "已支付",
                "fee": "¥50.00（挂号费）",
                "created_at": "2024-07-10T08:00:00",
            },
            "APPT-2024-002": {
                "appointment_id": "APPT-2024-002",
                "patient_name": "张三",
                "department": "检验科",
                "doctor": "系统分配",
                "appointment_date": "2024-07-15 10:30",
                "status": "已完成",
                "location": "医技楼 1 层 检验大厅",
                "payment_status": "已支付",
                "fee": "¥120.00（血常规+生化全套）",
                "created_at": "2024-07-10T08:05:00",
            },
            "APPT-2024-003": {
                "appointment_id": "APPT-2024-003",
                "patient_name": "李四",
                "department": "骨科",
                "doctor": "王医生",
                "appointment_date": "2024-07-18 14:00",
                "status": "已确认",
                "location": "门诊楼 2 层 205 诊室",
                "payment_status": "已支付",
                "fee": "¥50.00（挂号费）",
                "created_at": "2024-07-12T09:00:00",
            },
            "APPT-2024-004": {
                "appointment_id": "APPT-2024-004",
                "patient_name": "王五",
                "department": "体检中心",
                "doctor": "体检团队",
                "appointment_date": "2024-07-20 08:00",
                "status": "已确认",
                "location": "体检中心 5 层",
                "payment_status": "已支付",
                "fee": "¥880.00（体检套餐A）",
                "created_at": "2024-07-14T10:00:00",
            },
        }
        self.appointments.update(samples)

    def list_tools(self) -> Dict[str, Any]:
        return {
            "register": {
                "description": "注册新预约记录（由 ticket_server 创建后同步）",
                "parameters": {
                    "appointment_id": {"type": "string"},
                    "patient_name": {"type": "string"},
                    "department": {"type": "string"},
                    "doctor": {"type": "string"},
                    "appointment_date": {"type": "string"},
                    "location": {"type": "string", "default": "待分配"},
                },
            },
            "query": {
                "description": "查询预约信息",
                "parameters": {
                    "appointment_id": {"type": "string", "description": "预约编号"},
                },
            },
            "query_by_patient": {
                "description": "根据患者姓名查询预约列表",
                "parameters": {
                    "patient_name": {"type": "string", "description": "患者姓名"},
                },
            },
            "query_by_department": {
                "description": "按科室查询预约排班",
                "parameters": {
                    "department": {"type": "string", "description": "科室名称"},
                },
            },
        }

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        if tool_name == "register":
            return await self._register(arguments)
        elif tool_name == "query":
            return await self._query(arguments)
        elif tool_name == "query_by_patient":
            return await self._query_by_patient(arguments)
        elif tool_name == "query_by_department":
            return await self._query_by_department(arguments)
        else:
            raise ValueError(f"未知工具: {tool_name}")

    async def _register(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """注册预约记录"""
        appointment_id = arguments.get("appointment_id", "")
        record = {
            "appointment_id": appointment_id,
            "patient_name": arguments.get("patient_name", "患者"),
            "department": arguments.get("department", "未指定"),
            "doctor": arguments.get("doctor", "系统分配"),
            "appointment_date": arguments.get("appointment_date", "待定"),
            "status": "已预约",
            "location": arguments.get("location", "待分配"),
            "payment_status": "未支付",
            "fee": "待定",
            "created_at": __import__("datetime").datetime.now().isoformat(),
        }
        self.appointments[appointment_id] = record
        print(f"✅ 预约已同步到查询服务: {appointment_id}")
        return record

    async def _query(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        appointment_id = arguments.get("appointment_id", "")
        appointment = self.appointments.get(appointment_id)
        if appointment:
            return appointment
        print(f"⚠️  预约 {appointment_id} 未找到")
        return self.appointments.get("APPT-2024-001", {})

    async def _query_by_patient(self, arguments: Dict[str, Any]) -> list:
        patient_name = arguments.get("patient_name", "")
        return [a for a in self.appointments.values() if a.get("patient_name") == patient_name]

    async def _query_by_department(self, arguments: Dict[str, Any]) -> list:
        department = arguments.get("department", "")
        return [a for a in self.appointments.values() if department in a.get("department", "")]


if __name__ == "__main__":
    server = OrderServer()
    server.run()
