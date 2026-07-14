# ============================================
# LangGraph 工作流节点
# ============================================
import json
import logging
from typing import Dict, Any, List

import httpx

from agent.state import AgentState, Intent, ToolCall
from config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# MCP 调用辅助
# ---------------------------------------------------------------------------
# Session 级短期记忆：记住每个会话最近创建的预约 ID
_session_last_appointment: Dict[str, str] = {}


async def _call_mcp(base_url: str, tool: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """调用 MCP Server 的工具接口。"""
    url = f"{base_url}/tools/{tool}"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json={"arguments": arguments})
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(data.get("error", "MCP 调用失败"))
        return data.get("result", {})


async def _extract_appointment_params(message: str) -> Dict[str, str]:
    """用 LLM 从用户自然语言中提取就诊预约参数。"""
    from openai import AsyncOpenAI
    import re

    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )

    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=[{
            "role": "system",
            "content": (
                "从用户输入中提取就诊预约信息。严格按以下格式输出四行，不要任何额外内容：\n"
                "科室: <用户提到的科室，没有则写 未指定>\n"
                "医生: <用户提到的医生姓名，没有则写 系统分配>\n"
                "时间: <用户提到的时间，没有则写 待定>\n"
                "患者: <用户或患者姓名，没有则写 患者>\n\n"
                "示例输入: 预约心内科李主任明天下午三点\n"
                "示例输出:\n"
                "科室: 心内科\n医生: 李主任\n时间: 明天下午三点\n患者: 患者"
            ),
        }, {
            "role": "user",
            "content": message,
        }],
        max_tokens=200,
        temperature=0,
    )

    raw = (response.choices[0].message.content or "").strip() if response.choices else ""
    logger.info("📅 LLM 原始返回: %s", raw)

    # 按行解析
    params: Dict[str, str] = {
        "patient_name": "患者", "department": "未指定",
        "appointment_date": "待定", "doctor": "系统分配",
    }
    key_map = {"科室": "department", "医生": "doctor", "时间": "appointment_date", "患者": "patient_name"}

    for line in raw.split("\n"):
        line = line.strip()
        for cn_key, en_key in key_map.items():
            m = re.match(rf"{cn_key}[：:]\s*(.+)", line)
            if m:
                val = m.group(1).strip()
                if val and val not in ("未指定", "系统分配", "待定", "患者"):
                    params[en_key] = val
                break

    logger.info("📅 解析结果: %s", params)
    return params


# --- 意图识别 ---

# 快速关键词：明显闲聊直接短路，不调用 LLM
FAST_CHITCHAT_KEYWORDS: List[str] = [
    # 问候
    "你好", "您好", "嗨", "哈喽", "在吗", "hello", "hi", "hey",
    "早上好", "下午好", "晚上好", "早安", "晚安", "午安",
    "good morning", "good afternoon", "good evening",
    # 道别
    "再见", "拜拜", "回见", "bye", "goodbye", "see you",
    # 感谢
    "谢谢", "多谢", "感谢", "thanks", "thank you",
    # 身份询问
    "你是谁", "你谁", "你叫什么", "你叫什么名字", "你的名字",
    "你是机器人", "你是机器人吗", "你是人吗", "你是真人吗",
    "你是AI", "你是人工智能", "你是AI吗", "你是什么",
    # 能力询问
    "你能做什么", "你会什么", "你有什么功能", "你能干嘛",
    "你会干嘛", "你能帮我", "你可以做什么", "你有什么用",
    # 情感
    "我爱你", "我喜欢你", "我想你", "你真好", "你真棒", "你真聪明",
    # 闲聊
    "哈哈", "呵呵", "嘿嘿", "嘻嘻", "好笑", "有意思", "无聊",
    "讲个笑话", "讲笑话", "说个笑话", "聊天", "聊聊天",
    "今天天气", "天气怎么", "天气不错",
    # 测试
    "test", "测试", "test123", "ping",
]


# 快速关键词：明显意图直接短路，不调用 LLM
FAST_APPOINTMENT_KEYWORDS: List[str] = [
    "预约", "挂号", "约医生", "预约医生", "预约挂号", "怎么预约",
    "如何预约", "预约流程", "预约科室", "挂个号", "约个",
    "就诊", "看病", "看医生", "挂号预约",
]
FAST_QUERY_KEYWORDS: List[str] = [
    "查询预约", "查看预约", "我的预约", "预约记录", "挂号记录", "预约状态", "就诊时间",
    "查预约", "看预约", "预约查询", "就诊记录", "挂号信息",
]
FAST_TRANSFER_KEYWORDS: List[str] = [
    "转人工", "人工客服", "人工", "找人工", "联系客服", "我要投诉", "投诉",
]


async def recognize_intent(state: AgentState) -> Dict[str, Any]:
    """
    意图识别节点 — LLM 自主决策 + 快速关键词短路。

    意图类型:
      - knowledge_search: 医疗知识检索（疾病、症状、用药、健康咨询等）
      - create_ticket:   就诊预约 / 挂号 / 预约医生
      - query_order:     预约查询 / 就诊记录 / 预约状态
      - transfer_human:  转人工客服 / 投诉 / 联系医护人员
      - chitchat:        闲聊问候（你好、谢谢、再见等）
    """
    message = state.user_message.lower()

    # 1. 快速路径：闲聊
    if any(kw in message for kw in FAST_CHITCHAT_KEYWORDS):
        logger.info("意图识别: chitchat (快速匹配)")
        return {"intent": Intent.CHITCHAT, "intent_confidence": 0.99}

    # 2. 快速路径：转人工（先于预约，避免"转人工预约"误匹配）
    if any(kw in message for kw in FAST_TRANSFER_KEYWORDS):
        logger.info("意图识别: transfer_human (快速匹配)")
        return {"intent": Intent.TRANSFER_HUMAN, "intent_confidence": 0.99}

    # 3. 快速路径：预约查询（先于就诊预约！"查看预约"优先查，不是创建）
    if any(kw in message for kw in FAST_QUERY_KEYWORDS):
        logger.info("意图识别: query_order (快速匹配)")
        return {"intent": Intent.QUERY_ORDER, "intent_confidence": 0.99}

    # 4. 快速路径：就诊预约
    if any(kw in message for kw in FAST_APPOINTMENT_KEYWORDS):
        logger.info("意图识别: create_ticket (快速匹配)")
        return {"intent": Intent.CREATE_TICKET, "intent_confidence": 0.99}

    # 5. LLM 分类：兜底
    intent, confidence = await _llm_classify_intent(state.user_message)
    logger.info("意图识别: %s (LLM, 置信度: %.2f)", intent.value, confidence)
    return {"intent": intent, "intent_confidence": confidence}


async def _llm_classify_intent(query: str) -> tuple[Intent, float]:
    """用 LLM 将用户输入分类到 5 种意图之一。"""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )

    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=[{
            "role": "system",
            "content": (
                "你是一个医院智能助手意图分类器。分析患者输入，从以下 5 种意图中选择最匹配的一个：\n\n"
                "1. knowledge_search — 医疗健康知识查询（疾病、症状、治疗、用药、养生、体检等）\n"
                "2. create_ticket — 就诊预约、挂号、预约医生、预约体检，含「怎么预约」「如何挂号」「预约流程」等预约相关咨询\n"
                "3. query_order — 查询预约状态、就诊记录、预约时间、挂号信息\n"
                "4. transfer_human — 转接人工客服、投诉、联系医护人员\n"
                "5. chitchat — 闲聊、问候、与医院业务无关的对话\n\n"
                "严格只回复一个单词，不要有任何其他内容：knowledge_search | create_ticket | query_order | transfer_human | chitchat"
            ),
        }, {
            "role": "user",
            "content": query,
        }],
        max_tokens=10,
        temperature=0,
    )

    raw = response.choices[0].message.content.strip().lower() if response.choices else "knowledge_search"

    # 映射 LLM 输出到 Intent 枚举
    intent_map = {
        "knowledge_search": Intent.KNOWLEDGE_SEARCH,
        "create_ticket": Intent.CREATE_TICKET,
        "query_order": Intent.QUERY_ORDER,
        "transfer_human": Intent.TRANSFER_HUMAN,
        "chitchat": Intent.CHITCHAT,
    }

    for key, intent in intent_map.items():
        if key in raw:
            return intent, 0.9

    # 兜底
    logger.warning("LLM 意图分类返回未知值: '%s'，兜底为知识检索", raw)
    return Intent.KNOWLEDGE_SEARCH, 0.5


# --- 路由决策 ---

def route_by_intent(state: AgentState) -> str:
    """根据意图路由到不同处理节点"""
    intent = state.intent

    routing_map = {
        Intent.KNOWLEDGE_SEARCH: "search_knowledge",
        Intent.CREATE_TICKET: "create_ticket",
        Intent.QUERY_ORDER: "query_order",
        Intent.TRANSFER_HUMAN: "transfer_human",
        Intent.CHITCHAT: "generate_answer",
        Intent.UNKNOWN: "search_knowledge",
    }

    target = routing_map.get(intent, "generate_answer")
    logger.info(f"路由决策: {intent.value} → {target}")
    return target


# --- 工具调用节点 ---

async def search_knowledge_node(state: AgentState) -> Dict[str, Any]:
    """知识库检索 — 优先走 MCP，失败时直连 Milvus。"""
    tool_call = ToolCall(
        tool_name="search_knowledge",
        arguments={"query": state.user_message, "top_k": 1},
        status="running",
    )

    results: List[Dict[str, Any]] = []

    # 尝试 MCP，失败则直连 Milvus
    try:
        results = await _call_mcp(
            base_url=settings._mcp_url(settings.mcp_knowledge_port, settings.mcp_knowledge_url),
            tool="search",
            arguments={"query": state.user_message, "top_k": 1},
        )
        logger.info("✅ [MCP] 知识检索返回 %d 条", len(results))
    except Exception as e:
        logger.warning("⚠️  [MCP] 不可用 (%s)，直连 Milvus", e)
        try:
            results = await _search_milvus(query=state.user_message, top_k=1)
            logger.info("✅ [本地] 知识检索返回 %d 条", len(results))
        except Exception as e2:
            logger.error("❌ [本地] Milvus 检索也失败: %s", e2)

    tool_call.result = json.dumps(results, ensure_ascii=False)
    tool_call.status = "completed" if results else "failed"

    return {
        "tool_calls": [tool_call],
        "knowledge_results": results,
    }


async def _search_milvus(query: str, top_k: int = 1) -> List[Dict[str, Any]]:
    """本地直连 Milvus（MCP 不可用时的兜底）。"""
    from pymilvus import Collection, connections
    from knowledge.embeddings import get_embeddings

    connections.connect(alias="default", uri=settings.milvus_uri, timeout=10)
    collection = Collection(settings.milvus_collection_name)
    collection.load()

    query_vectors = await get_embeddings([query])
    search_results = collection.search(
        data=[query_vectors[0]],
        anns_field="embedding",
        param={"metric_type": "COSINE", "params": {"nprobe": 16}},
        limit=top_k,
        output_fields=["title", "content", "category", "tags"],
    )

    results: List[Dict[str, Any]] = []
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


async def create_ticket_node(state: AgentState) -> Dict[str, Any]:
    """就诊预约 — LLM 提取参数 + MCP 创建预约。"""
    tool_call = ToolCall(
        tool_name="create_appointment",
        arguments={"patient_request": state.user_message[:100]},
        status="running",
    )

    # 用 LLM 从用户输入中提取科室和就诊时间
    params = await _extract_appointment_params(state.user_message)
    logger.info("📅 LLM 提取预约参数: %s", params)

    try:
        result = await _call_mcp(
            base_url=settings._mcp_url(settings.mcp_ticket_port, settings.mcp_ticket_url),
            tool="create",
            arguments=params,
        )
        tool_call.result = json.dumps(result, ensure_ascii=False)
        tool_call.status = "completed"
        # 记住本次预约 ID
        aid = result.get("appointment_id", "")
        _session_last_appointment[state.session_id] = aid

        # 同步到 order_server
        try:
            await _call_mcp(
                base_url=settings._mcp_url(settings.mcp_order_port, settings.mcp_order_url),
                tool="register",
                arguments={
                    "appointment_id": aid,
                    "patient_name": result.get("patient_name", "患者"),
                    "department": result.get("department", "未指定"),
                    "doctor": result.get("doctor", "系统分配"),
                    "appointment_date": result.get("appointment_date", "待定"),
                },
            )
        except Exception:
            pass

        response = (
            f"✅ **就诊预约成功！**\n\n"
            f"| 项目 | 详情 |\n"
            f"|------|------|\n"
            f"| 预约编号 | {result.get('appointment_id', 'N/A')} |\n"
            f"| 科室 | {result.get('department', 'N/A')} |\n"
            f"| 医生 | {result.get('doctor', 'N/A')} |\n"
            f"| 就诊时间 | {result.get('appointment_date', 'N/A')} |\n\n"
            f"📌 请提前 15 分钟到达医院取号。"
        )
    except Exception as e:
        logger.warning("⚠️  [MCP] 预约不可用 (%s)，使用本地兜底", e)
        tool_call.status = "completed"
        response = (
            "📅 **就诊预约功能正在完善中，敬请期待！**\n\n"
            "如需预约，请通过以下方式：\n"
            "- 拨打医院预约电话\n"
            "- 前往医院挂号窗口\n"
            "- 使用医院官方APP或小程序\n\n"
            "如有疑问，请回复「转人工」联系客服。"
        )

    return {"tool_calls": [tool_call], "final_response": response}


async def query_order_node(state: AgentState) -> Dict[str, Any]:
    """预约查询 — 从上下文提取最近预约 ID，优先查 MCP。"""
    tool_call = ToolCall(
        tool_name="query_appointment",
        arguments={},
        status="running",
    )

    # 从 session 缓存取最近预约 ID
    last_appointment_id: str = _session_last_appointment.get(state.session_id, "")

    # 缓存没命中，尝试从对话历史提取
    if not last_appointment_id and state.history:
        import re as _re
        for msg in reversed(state.history):
            content = msg.get("content", "")
            m = _re.search(r"APPT-\d+", content)
            if m:
                last_appointment_id = m.group()
                _session_last_appointment[state.session_id] = last_appointment_id
                logger.info("📅 从历史提取预约 ID: %s", last_appointment_id)
                break

    try:
        if last_appointment_id:
            result = await _call_mcp(
                base_url=settings._mcp_url(settings.mcp_order_port, settings.mcp_order_url),
                tool="query",
                arguments={"appointment_id": last_appointment_id},
            )
        else:
            result = {"appointment_id": "N/A", "department": "无", "doctor": "无",
                       "appointment_date": "无", "status": "无记录", "location": "无"}

        tool_call.result = json.dumps(result, ensure_ascii=False)
        tool_call.status = "completed"

        response = (
            f"📋 **预约查询结果**\n\n"
            f"| 项目 | 详情 |\n"
            f"|------|------|\n"
            f"| 预约编号 | {result.get('appointment_id', 'N/A')} |\n"
            f"| 科室 | {result.get('department', 'N/A')} |\n"
            f"| 医生 | {result.get('doctor', 'N/A')} |\n"
            f"| 就诊时间 | {result.get('appointment_date', 'N/A')} |\n"
            f"| 状态 | {result.get('status', 'N/A')} |\n"
            f"| 就诊地点 | {result.get('location', 'N/A')} |"
        )
    except Exception as e:
        logger.warning("⚠️  [MCP] 预约查询不可用 (%s)，使用本地兜底", e)
        tool_call.status = "completed"
        response = "📋 暂无预约记录。回复「预约」即可创建新预约。"

    return {"tool_calls": [tool_call], "final_response": response}


async def transfer_human_node(state: AgentState) -> Dict[str, Any]:
    """转接人工客服 — 优先走 MCP，失败时本地兜底。"""
    tool_call = ToolCall(
        tool_name="transfer_to_human",
        arguments={"reason": "患者请求人工客服", "priority": "normal", "summary": state.user_message[:100]},
        status="running",
    )

    try:
        result = await _call_mcp(
            base_url=settings._mcp_url(settings.mcp_human_port, settings.mcp_human_url),
            tool="transfer",
            arguments={"reason": "患者请求人工客服", "priority": "normal", "summary": state.user_message[:100]},
        )
        tool_call.result = json.dumps(result, ensure_ascii=False)
        tool_call.status = "completed"
        staff = result.get("assigned_staff") or {}
        response = (
            f"👩‍⚕️ **正在为您转接人工客服**\n\n"
            f"- 排队位置: 第 {result.get('queue_position', '?')} 位\n"
            f"- 预计等待: {result.get('estimated_wait', '未知')}\n"
            f"- 客服人员: {staff.get('name', '系统分配')}\n\n"
            f"转接编号: {result.get('transfer_id', 'N/A')}"
        )
    except Exception as e:
        logger.warning("⚠️  [MCP] 转接不可用 (%s)，使用本地兜底", e)
        tool_call.status = "completed"
        response = (
            "👩‍⚕️ **转接人工客服**\n\n"
            "当前为离线模式，请拨打医院咨询电话或前往医院服务台获取人工帮助。"
        )

    return {"tool_calls": [tool_call], "final_response": response}


# --- 回答生成 ---

async def generate_answer_node(state: AgentState) -> Dict[str, Any]:
    """基于知识库结果 / 上下文生成最终回答"""
    if state.final_response:
        return {}

    # 如果有知识库结果，直接构建回答（意图分类已判定为医疗查询，无需二次验证）
    if state.knowledge_results:
        r = state.knowledge_results[0]
        title = r.get("title", "未知")
        content = r.get("content", "")
        category = r.get("category", "")
        score = r.get("score", 0)

        answer = (
            f"### {title}（{category}）\n\n"
            f"{content}\n\n"
            f"📅 如需进一步诊疗，建议预约 **{category}** 就诊。"
        )
        return {
            "final_response": answer,
            "sources": [{"source": title, "score": score}],
        }

    # 闲聊回复
    chitchat_responses = {
        "你好": (
            "您好！我是医院智能助手，很高兴为您服务。\n\n"
            "我可以帮您：\n"
            "🩺 查询医疗健康知识\n"
            "📅 预约挂号 / 就诊预约\n"
            "📋 查询预约状态和就诊记录\n"
            "👩‍⚕️ 转接人工客服\n\n"
            "请问有什么可以帮到您的？"
        ),
        "谢谢": "不客气！祝您身体健康！如果还有其他问题，随时找我 😊",
        "再见": "再见！祝您早日康复！👋",
    }

    msg = state.user_message.strip()
    for key, resp in chitchat_responses.items():
        if key in msg:
            return {"final_response": resp}

    # 默认回复
    return {
        "final_response": _medical_only_prompt(),
    }


def _medical_only_prompt() -> str:
    """非医疗查询时的统一回复。"""
    return (
        "您好！我是医院智能助手，专注于医疗健康服务。\n\n"
        "我可以帮您：\n"
        "🩺 **医疗知识查询** — 疾病症状、治疗、用药指导\n"
        "📅 **就诊预约** — 预约挂号、选择科室和医生\n"
        "📋 **预约查询** — 查看预约状态和就诊记录\n"
        "👩‍⚕️ **转接人工** — 联系客服或医护人员\n\n"
        "请描述您需要的医疗服务，我来帮您处理。"
    )
