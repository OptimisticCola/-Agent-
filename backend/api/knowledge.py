# ============================================
# 知识库管理 API
# ============================================
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List

router = APIRouter(tags=["知识库"])

# 模拟知识库存储
knowledge_docs: list = []


@router.post("/knowledge/upload")
async def upload_knowledge(files: List[UploadFile] = File(...)):
    """上传知识文档"""
    results = []

    for file in files:
        try:
            content = await file.read()
            text = content.decode("utf-8", errors="ignore")

            # 保存文档元数据
            doc = {
                "id": str(__import__("uuid").uuid4()),
                "filename": file.filename,
                "size": len(content),
                "content_preview": text[:200],
                "type": file.content_type or "text/plain",
            }
            knowledge_docs.append(doc)

            # TODO: 实际项目中应调用 Chroma 入库
            # from knowledge.chroma_store import add_document
            # await add_document(text, metadata=doc)

            results.append({
                "success": True,
                "doc_id": doc["id"],
                "filename": file.filename,
            })

        except Exception as e:
            results.append({
                "success": False,
                "filename": file.filename,
                "error": str(e),
            })

    return {
        "uploaded": len([r for r in results if r["success"]]),
        "failed": len([r for r in results if not r["success"]]),
        "results": results,
    }


@router.get("/knowledge/list")
async def list_knowledge():
    """列出已上传文档"""
    return {"documents": knowledge_docs, "total": len(knowledge_docs)}
