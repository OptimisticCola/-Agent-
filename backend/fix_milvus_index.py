# ============================================
# Milvus 索引修复脚本
# ============================================
"""
修复 customer_service_knowledge 集合的索引问题，创建索引并加载集合。

用法:
    cd backend
    python fix_milvus_index.py

依赖:
    pip install pymilvus
"""
import sys
from typing import Optional

from pymilvus import (
    Collection,
    connections,
    utility,
    MilvusException,
)

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
COLLECTION_NAME: str = "customer_service_knowledge"
MILVUS_HOST: str = "localhost"
MILVUS_PORT: int = 19530

INDEX_TYPE: str = "IVF_FLAT"
INDEX_METRIC_TYPE: str = "COSINE"
INDEX_NLIST: int = 128

SEARCH_METRIC_TYPE: str = "COSINE"
SEARCH_NPROBE: int = 16


# ---------------------------------------------------------------------------
# 连接 Milvus
# ---------------------------------------------------------------------------
def connect_milvus(host: str = MILVUS_HOST, port: int = MILVUS_PORT) -> None:
    """连接到 Milvus 服务。"""
    print(f"🔗 正在连接 Milvus ({host}:{port}) ...")
    try:
        connections.connect(
            alias="default",
            host=host,
            port=port,
            timeout=10,
        )
        print("✅ Milvus 连接成功")
    except MilvusException as e:
        print(f"❌ Milvus 连接失败: {e}")
        raise ConnectionError(f"无法连接到 Milvus ({host}:{port}): {e}") from e


# ---------------------------------------------------------------------------
# 获取集合
# ---------------------------------------------------------------------------
def get_collection(name: str) -> Optional[Collection]:
    """获取已存在的集合，不存在则返回 None。"""
    if not utility.has_collection(name):
        print(f"❌ 集合 '{name}' 不存在")
        return None
    print(f"📂 集合 '{name}' 已存在")
    return Collection(name)


# ---------------------------------------------------------------------------
# 创建索引
# ---------------------------------------------------------------------------
def ensure_index(collection: Collection) -> None:
    """确保集合的向量字段已创建索引。"""
    if collection.has_index():
        print("📌 索引已存在，跳过创建")
        return

    print(f"🔧 正在创建索引 (类型: {INDEX_TYPE}, 度量: {INDEX_METRIC_TYPE}, nlist: {INDEX_NLIST}) ...")

    index_params: dict[str, object] = {
        "index_type": INDEX_TYPE,
        "metric_type": INDEX_METRIC_TYPE,
        "params": {"nlist": INDEX_NLIST},
    }

    try:
        collection.create_index(
            field_name="embedding",
            index_params=index_params,
        )
        print("✅ 索引创建成功")
    except MilvusException as e:
        print(f"❌ 索引创建失败: {e}")
        raise


# ---------------------------------------------------------------------------
# 加载集合
# ---------------------------------------------------------------------------
def load_collection(collection: Collection) -> None:
    """将集合加载到内存。"""
    print("📥 正在加载集合到内存 ...")
    try:
        collection.load()
        print("✅ 集合加载完成")
    except MilvusException as e:
        print(f"❌ 集合加载失败: {e}")
        raise


# ---------------------------------------------------------------------------
# 检查集合数据量
# ---------------------------------------------------------------------------
def print_collection_stats(collection: Collection) -> None:
    """打印集合的数据统计信息。"""
    try:
        row_count: int = collection.num_entities
        print(f"📊 集合中有 {row_count} 条数据")
    except MilvusException as e:
        print(f"⚠️  获取数据量失败: {e}")


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main() -> None:
    """脚本主入口。"""
    print("")
    print("=" * 50)
    print("🩺 Milvus 索引修复脚本")
    print("=" * 50)
    print(f"  集合名称: {COLLECTION_NAME}")
    print(f"  Milvus 地址: {MILVUS_HOST}:{MILVUS_PORT}")
    print("=" * 50)
    print("")

    # 1. 连接 Milvus
    connect_milvus()

    # 2. 获取集合
    collection: Optional[Collection] = get_collection(COLLECTION_NAME)
    if collection is None:
        sys.exit(1)

    # 3. 确保索引存在并创建
    ensure_index(collection)

    # 4. 加载集合
    load_collection(collection)

    # 5. 检查数据
    print_collection_stats(collection)

    # 6. 清理
    connections.disconnect("default")

    print("")
    print("=" * 50)
    print("🎉 修复完成！集合已就绪")
    print("=" * 50)
    print("")


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("⚠️ 用户中断执行")
    except Exception as e:
        print(f"❌ 脚本执行异常: {e}")
        sys.exit(1)
