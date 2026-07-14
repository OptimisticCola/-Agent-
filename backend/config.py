# ============================================
# 后端配置管理
# ============================================
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

# 计算项目根目录的 .env 绝对路径（不依赖 CWD）
_PROJECT_ROOT: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ENV_FILE: str = os.path.join(_PROJECT_ROOT, ".env")


class Settings(BaseSettings):
    # --- LLM ---
    openai_api_key: str = ""  # 在 .env 中设置 OPENAI_API_KEY
    openai_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-v4-pro"
    llm_temperature: float = 0.7

    # --- Embedding（独立于 LLM，DeepSeek 不支持 embeddings） ---
    embedding_api_key: str = ""
    embedding_base_url: str = "https://api.siliconflow.cn/v1"
    embedding_model: str = "BAAI/bge-large-zh-v1.5"

    # --- Milvus ---
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection_name: str = "customer_service_knowledge"

    # --- Chroma ---
    chroma_persist_dir: str = "./backend/chroma_data"

    # --- 后端服务 ---
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # --- MCP Servers ---
    mcp_knowledge_port: int = 8001
    mcp_ticket_port: int = 8002
    mcp_order_port: int = 8003
    mcp_human_port: int = 8004
    mcp_knowledge_url: str = ""
    mcp_ticket_url: str = ""
    mcp_order_url: str = ""
    mcp_human_url: str = ""

    def _mcp_url(self, port: int, override: str) -> str:
        return override or f"http://localhost:{port}"

    # --- 日志 ---
    log_level: str = "INFO"

    @property
    def milvus_uri(self) -> str:
        return f"http://{self.milvus_host}:{self.milvus_port}"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
