# ============================================
# Embedding 向量生成模块
# ============================================
"""
使用 OpenAI 兼容 API 生成文本嵌入向量。

用法:
    from knowledge.embeddings import get_embeddings
    vectors = await get_embeddings(["文本1", "文本2"])
"""
import logging
import sys
import os
from typing import List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import settings

logger = logging.getLogger(__name__)

# 默认嵌入模型与向量维度
DEFAULT_EMBEDDING_MODEL: str = settings.embedding_model
DEFAULT_EMBEDDING_DIM: int = 1024  # BGE-large-zh-v1.5 输出 1024 维


async def get_embeddings(
    texts: List[str],
    model: Optional[str] = None,
) -> List[List[float]]:
    """
    使用 OpenAI 兼容 API 生成文本向量。

    优先使用 embedding 专用配置，API Key 未设置时回退到 LLM 的 API Key。

    Args:
        texts: 待编码的文本列表，每个元素为一段文本
        model: 嵌入模型名称，默认使用 settings.embedding_model

    Returns:
        向量列表，与 texts 一一对应，每个向量为 float 列表

    Raises:
        RuntimeError: API 调用失败且无降级方案时抛出
    """
    if not texts:
        return []

    model = model or DEFAULT_EMBEDDING_MODEL
    api_key = settings.embedding_api_key or settings.openai_api_key

    # 诊断日志：打印请求关键信息（Key 脱敏）
    _masked_key: str = (
        api_key[:8] + "****" + api_key[-4:] if len(api_key) > 12 else "***"
    )
    _from: str = "EMBEDDING_API_KEY" if settings.embedding_api_key else "OPENAI_API_KEY (fallback)"
    logger.info("🌐 Embedding API 请求:")
    logger.info("   URL:    %s/embeddings", settings.embedding_base_url)
    logger.info("   Model:  %s", model)
    logger.info("   Key:    %s (来源: %s)", _masked_key, _from)
    logger.info("   Texts:  %d 条", len(texts))

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=api_key,
            base_url=settings.embedding_base_url,
        )

        response = await client.embeddings.create(
            model=model,
            input=texts,
        )

        embeddings: List[List[float]] = [item.embedding for item in response.data]
        logger.info(
            "✅ 已生成 %d 个向量，维度: %d", len(embeddings), len(embeddings[0])
        )
        return embeddings

    except Exception as e:
        _detail: str = str(e)
        if hasattr(e, "response"):
            try:
                _detail += f" | status={e.response.status_code} body={e.response.text[:500]}"
            except Exception:
                pass
        logger.warning("⚠️ 嵌入 API 调用失败: %s", _detail)

        # 额外的诊断提示
        if not settings.embedding_api_key:
            logger.warning("💡 提示: EMBEDDING_API_KEY 未设置，使用了 LLM 的 OPENAI_API_KEY (DeepSeek)")
            logger.warning("   DeepSeek 不支持 embeddings，请在 .env 中设置 EMBEDDING_API_KEY")
        elif "401" in str(e) or "Unauthorized" in str(e):
            logger.warning("💡 提示: 401 认证失败，请检查 EMBEDDING_API_KEY 是否有效")
        elif "404" in str(e):
            logger.warning("💡 提示: 404 未找到，请检查 EMBEDDING_BASE_URL 是否正确")

        logger.warning("⚠️ 使用模拟向量降级方案")
        return _generate_mock_embeddings(len(texts))


def _generate_mock_embeddings(count: int, dim: int = DEFAULT_EMBEDDING_DIM) -> List[List[float]]:
    """
    生成模拟向量用于开发/测试环境。

    Args:
        count: 需要生成的向量数量
        dim: 向量维度

    Returns:
        模拟向量列表
    """
    import random
    random.seed(42)
    return [
        [round(random.uniform(-1.0, 1.0), 6) for _ in range(dim)]
        for _ in range(count)
    ]
