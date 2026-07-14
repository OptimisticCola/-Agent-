# ============================================
# Chroma 向量存储
# ============================================
import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ChromaStore:
    """Chroma 向量数据库封装"""

    def __init__(self, persist_dir: str = "./chroma_data", collection_name: str = "knowledge_base"):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self._initialized = False

    def initialize(self):
        """初始化 Chroma 连接"""
        try:
            import chromadb
            from chromadb.config import Settings

            os.makedirs(self.persist_dir, exist_ok=True)

            self.client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=os.path.abspath(self.persist_dir),
                anonymized_telemetry=False,
            ))

            # 获取或创建集合
            try:
                self.collection = self.client.get_collection(self.collection_name)
            except Exception:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
                self._seed_default_data()

            self._initialized = True
            logger.info(f"✅ ChromaStore 已初始化: {self.collection_name}")

        except ImportError:
            logger.warning("⚠️  ChromaDB 未安装，ChromaStore 不可用")
        except Exception as e:
            logger.error(f"ChromaStore 初始化失败: {e}")

    def _seed_default_data(self):
        """初始化默认知识数据"""
        default_docs = [
            ("退款政策", "购买后 7 天内可无条件退款，退款将在 3-5 个工作日内原路返回。特殊商品（数字下载、定制商品等）不支持退款。"),
            ("退货流程", "退货步骤：联系客服获取 RMA 号 → 完整包装商品 → 寄回仓库 → 验收后 3 个工作日内退款。"),
            ("保修说明", "电子产品享 1 年免费保修。非人为损坏免费维修，人为损坏收取成本费。"),
            ("配送政策", "全国包邮（偏远地区除外），满 99 元免运费。标准配送 3-5 天，加急 1-2 天。"),
            ("会员权益", "银卡 9.5 折，金卡 9 折，钻石 8.5 折。积分可兑换优惠券（100积分=1元）。"),
            ("联系客服", "在线客服：工作日 9:00-18:00；电话：400-888-0000（7×24小时）。"),
            ("支付方式", "支持微信支付、支付宝、信用卡、花呗分期、京东白条等多种支付方式。"),
        ]

        try:
            for i, (title, content) in enumerate(default_docs):
                self.collection.add(
                    ids=[f"default_{i}"],
                    documents=[content],
                    metadatas=[{"source": title, "category": "通用知识"}],
                )
            logger.info(f"✅ 已加载 {len(default_docs)} 条默认知识")
        except Exception as e:
            logger.warning(f"种子数据加载失败: {e}")

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter_category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """向量相似度搜索"""
        if not self._initialized:
            return self._mock_search(query, top_k)

        try:
            where_filter = None
            if filter_category:
                where_filter = {"category": filter_category}

            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_filter,
            )

            items = []
            if results and results.get("documents"):
                docs = results["documents"][0]
                metas = results.get("metadatas", [[]])[0]
                distances = results.get("distances", [[]])[0]

                for i, doc in enumerate(docs):
                    items.append({
                        "content": doc,
                        "source": metas[i].get("source", "") if i < len(metas) else "",
                        "score": round(1 - min(distances[i], 1), 4) if i < len(distances) else 0,
                    })

            return items

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return self._mock_search(query, top_k)

    async def add_document(
        self,
        content: str,
        source: str = "",
        category: str = "",
    ) -> str:
        """添加文档到向量库"""
        if not self._initialized:
            return "mock_id"

        import uuid
        doc_id = f"doc_{uuid.uuid4().hex[:12]}"

        self.collection.add(
            ids=[doc_id],
            documents=[content],
            metadatas=[{"source": source, "category": category}],
        )

        return doc_id

    def _mock_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """模拟搜索（无 Chroma 时使用）"""
        mock_knowledge = [
            ("退款政策：购买后 7 天内可无条件退款，退款在 3-5 个工作日内原路返回。", "退款政策", 0.95),
            ("退货流程：联系客服获取 RMA 号，寄回商品后 3 个工作日内退款。", "退货流程", 0.90),
            ("保修说明：电子类产品享受 1 年免费保修服务。", "保修政策", 0.85),
            ("配送政策：全国包邮，标准配送 3-5 个工作日，满99元免运费。", "配送说明", 0.80),
            ("联系客服：拨打电话 400-888-0000，工作时间为 9:00-18:00。", "客服信息", 0.75),
        ]

        return [
            {"content": c, "source": s, "score": sc}
            for c, s, sc in mock_knowledge[:top_k]
        ]
