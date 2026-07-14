# ============================================
# 知识库初始化脚本
# ============================================
"""
初始化 Chroma 知识库，加载默认知识文档。

用法:
    python scripts/init_knowledge.py
"""
import os
import sys

# 确保 backend 在 Python 路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from knowledge.chroma_store import ChromaStore


def main():
    print("=" * 50)
    print("📚 初始化知识库...")
    print("=" * 50)

    chroma_dir = os.path.join(os.path.dirname(__file__), "..", "chroma_data")

    store = ChromaStore(
        persist_dir=os.path.abspath(chroma_dir),
        collection_name="knowledge_base",
    )
    store.initialize()

    # 添加额外的业务知识
    extra_docs = [
        ("常见问题-开机故障", "如果设备无法开机，请检查：1) 电源线是否连接正确；2) 电源开关是否打开；3) 电池是否有电。如仍无法解决，请创建工单。"),
        ("常见问题-联网问题", "无法连接 Wi-Fi 时：1) 检查路由器是否正常工作；2) 确认密码输入正确；3) 重启设备和路由器。"),
        ("常见问题-蓝牙连接", "蓝牙连接失败时：1) 确认设备在配对模式；2) 距离不超过 10 米；3) 关闭并重新打开蓝牙。"),
        ("售后政策-换货", "收到商品 15 天内，如发现质量问题可申请换货。换货商品需保持原包装完整。"),
        ("售后政策-维修", "超过退换期限的商品，如仍在保修期内，可申请免费维修。超出保修期的商品按收费标准维修。"),
        ("企业客户-批量采购", "企业批量采购请联系企业客服专线 400-888-0001，或发送邮件至 enterprise@example.com。"),
        ("企业客户-定制服务", "我们提供 OEM/ODM 定制服务，最小起订量 100 件起，交货周期 15-30 个工作日。"),
    ]

    for title, content in extra_docs:
        try:
            import asyncio
            doc_id = asyncio.run(store.add_document(content, source=title, category="业务知识"))
            print(f"  ✅ 已添加: {title} (ID: {doc_id})")
        except Exception as e:
            print(f"  ⚠️  添加失败: {title} - {e}")

    print()
    print("=" * 50)
    print("✅ 知识库初始化完成！")
    print("=" * 50)


if __name__ == "__main__":
    main()
