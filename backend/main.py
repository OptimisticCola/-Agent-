# ============================================
# FastAPI 应用入口
# ============================================
import sys
import os

# 确保 backend 目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from api.chat import router as chat_router
from api.knowledge import router as knowledge_router
from api.tools import router as tools_router
from api.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    print("🚀 智能客服 Agent 系统启动中...")
    print(f"📡 LLM: {settings.llm_model}")
    print(f"🗄️  Milvus: {settings.milvus_host}:{settings.milvus_port}")
    print(f"📚 Chroma: {settings.chroma_persist_dir}")
    yield
    print("👋 系统关闭")


app = FastAPI(
    title="智能客服 Agent 系统",
    description="基于 LangGraph + MCP 的智能客服/工单分诊系统",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat_router, prefix="/api")
app.include_router(knowledge_router, prefix="/api")
app.include_router(tools_router, prefix="/api")
app.include_router(health_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
