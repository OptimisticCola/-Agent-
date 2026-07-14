# ============================================
# MCP Server: 医疗知识库检索 (Milvus)
# ============================================
import os
import sys
from typing import Dict, Any, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mcp_servers.base import MCPServerBase, MCPServerConfig


class KnowledgeServer(MCPServerBase):
    """医疗知识库检索服务 — 基于 Milvus 向量数据库"""

    def __init__(self):
        config = MCPServerConfig(
            name="knowledge_server",
            description="医疗知识库 MCP Server — Milvus 向量检索",
            port=8001,
        )
        super().__init__(config)

    def list_tools(self) -> Dict[str, Any]:
        return {
            "search": {
                "description": "搜索医疗知识库",
                "parameters": {
                    "query": {"type": "string", "description": "搜索查询"},
                    "top_k": {"type": "integer", "default": 1, "description": "返回结果数"},
                },
            },
        }

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        if tool_name == "search":
            return await self._search(arguments)
        else:
            raise ValueError(f"未知工具: {tool_name}")

    async def _search(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        query = arguments.get("query", "")
        top_k = arguments.get("top_k", 1)

        from pymilvus import Collection, connections
        from knowledge.embeddings import get_embeddings

        # 连接 Milvus（Docker 内部用 milvus:19530，本地用 localhost:19530）
        milvus_host = os.environ.get("MILVUS_HOST", "localhost")
        milvus_port = int(os.environ.get("MILVUS_PORT", "19530"))
        collection_name = os.environ.get("MILVUS_COLLECTION_NAME", "customer_service_knowledge")

        connections.connect(alias="default", host=milvus_host, port=milvus_port, timeout=10)
        collection = Collection(collection_name)
        collection.load()

        # 生成查询向量
        query_vectors = await get_embeddings([query])
        query_vector = query_vectors[0]

        # 向量检索
        search_results = collection.search(
            data=[query_vector],
            anns_field="embedding",
            param={"metric_type": "COSINE", "params": {"nprobe": 16}},
            limit=top_k,
            output_fields=["title", "content", "category", "tags"],
        )

        results = []
        if search_results and search_results[0]:
            for hit in search_results[0]:
                results.append({
                    "title": hit.entity.get("title", ""),
                    "content": hit.entity.get("content", ""),
                    "category": hit.entity.get("category", ""),
                    "tags": hit.entity.get("tags", "[]"),
                    "score": round(hit.distance, 4),
                })

        return results


if __name__ == "__main__":
    server = KnowledgeServer()
    server.run()
