# ============================================
# 健康检查 API
# ============================================
from fastapi import APIRouter
from datetime import datetime

router = APIRouter(tags=["健康检查"])


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "智能客服 Agent 系统",
        "version": "1.0.0",
    }
