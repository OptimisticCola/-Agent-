# ============================================
# MCP Server 基础类
# ============================================
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """MCP Server 配置"""
    name: str
    description: str
    host: str = "0.0.0.0"
    port: int = 8000


class MCPServerBase:
    """
    MCP Server 基类
    提供简化的 MCP 协议实现 (HTTP + JSON)
    """

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.app = FastAPI(
            title=f"MCP Server: {config.name}",
            description=config.description,
            version="1.0.0",
        )
        self._register_routes()

    def _register_routes(self):
        """注册标准 MCP 路由"""

        @self.app.get("/health")
        async def health():
            return {"status": "ok", "server": self.config.name}

        @self.app.get("/info")
        async def info():
            return {
                "name": self.config.name,
                "description": self.config.description,
                "tools": self.list_tools(),
            }

        @self.app.post("/tools/{tool_name}")
        async def call_tool(tool_name: str, request: Request):
            body = await request.json()
            arguments = body.get("arguments", {})
            try:
                result = await self.execute_tool(tool_name, arguments)
                return JSONResponse(content={
                    "success": True,
                    "tool": tool_name,
                    "result": result,
                })
            except Exception as e:
                logger.error(f"工具执行失败: {tool_name} - {e}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "tool": tool_name,
                        "error": str(e),
                    },
                )

    def list_tools(self) -> Dict[str, Any]:
        """子类需重写，返回工具列表"""
        raise NotImplementedError

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """子类需重写，执行工具"""
        raise NotImplementedError

    def run(self):
        """启动 MCP Server"""
        logger.info(f"🚀 启动 MCP Server: {self.config.name} (端口: {self.config.port})")
        uvicorn.run(
            self.app,
            host=self.config.host,
            port=self.config.port,
            log_level="info",
        )
