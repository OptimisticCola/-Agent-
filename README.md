<img width="1920" height="1080" alt="图片1" src="https://github.com/user-attachments/assets/078c212d-6bc5-44ac-9c31-cd8947b9b713" />
<img width="1920" height="1080" alt="图片2" src="https://github.com/user-attachments/assets/519d8cb8-269a-4b0b-9d79-fcc5e6ee50b0" />
<img width="1920" height="1080" alt="图片3" src="https://github.com/user-attachments/assets/049f3406-09ae-432b-95d3-54ba7085dd6c" />
<img width="1920" height="1080" alt="图片4" src="https://github.com/user-attachments/assets/8fe549b0-6706-4cfe-b679-4fa21dca1c1b" />
<img width="1920" height="1080" alt="图片5" src="https://github.com/user-attachments/assets/f5d9dbb8-ed80-48b7-a127-763beff987b3" />
<img width="1920" height="1080" alt="图片6" src="https://github.com/user-attachments/assets/0fc6c4f0-b34f-4a4d-b608-ed1fd8a1d0e9" />



# 智能客服 Agent 系统

基于 **LangGraph + MCP + Vue 3** 的全栈智能客服/工单分诊系统。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Vite + Element Plus |
| 后端 | FastAPI + LangChain + LangGraph |
| 工具协议 | MCP (Model Context Protocol) |
| 向量数据库 | Milvus + Chroma |
| 容器化 | Docker + Docker Compose |

## 功能特性

- 🤖 **智能对话** — 基于 LangGraph 的多轮对话 Agent
- 🔧 **工具调用** — 4 个 MCP Server：知识检索、工单创建、订单查询、人工转接
- 📚 **RAG 检索增强** — Chroma 本地知识库 + Milvus 向量检索
- 💬 **流式响应** — SSE 实时推送，打字机效果
- 🎨 **现代化 UI** — 类 ChatGPT 界面，深色模式，响应式布局
- 📊 **溯源展示** — 显示 LLM 参考的知识来源
- 🔍 **工具可视化** — 实时展示 Agent 的工具调用过程

## 快速开始

### 前置要求

- Python 3.10+
- Node.js 18+
- Docker Desktop

### 一键启动

**Windows:**
```powershell
.\start.ps1
```

**Linux/macOS:**
```bash
bash start.sh
```

### 手动启动

```bash
# 1. 启动基础设施
docker-compose up -d

# 2. 启动后端
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
python scripts/init_knowledge.py
uvicorn main:app --reload --port 8000

# 3. 启动前端
cd frontend
npm install
npm run dev
```

## 项目结构

```
my-agent-project/
├── backend/
│   ├── api/                 # FastAPI 路由
│   │   ├── __init__.py
│   │   ├── chat.py          # 聊天 API (SSE)
│   │   ├── knowledge.py     # 知识库管理
│   │   ├── tools.py         # 工具列表
│   │   └── health.py        # 健康检查
│   ├── agent/               # LangGraph Agent
│   │   ├── __init__.py
│   │   ├── graph.py         # 工作流图定义
│   │   ├── state.py         # 状态定义
│   │   ├── nodes.py         # 图节点
│   │   └── tools.py         # 工具绑定
│   ├── mcp_servers/         # MCP Server (4个)
│   │   ├── __init__.py
│   │   ├── base.py          # MCP 基础类
│   │   ├── knowledge_server.py
│   │   ├── ticket_server.py
│   │   ├── order_server.py
│   │   └── human_server.py
│   ├── knowledge/           # Chroma 知识库
│   │   ├── __init__.py
│   │   └── chroma_store.py
│   ├── scripts/
│   │   └── init_knowledge.py
│   ├── config.py            # 配置管理
│   ├── main.py              # 应用入口
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/             # API 请求层
│   │   ├── components/      # Vue 组件
│   │   ├── stores/          # Pinia 状态管理
│   │   ├── types/           # TypeScript 类型
│   │   ├── composables/     # 组合式函数
│   │   └── router/          # 路由
│   └── package.json
├── docker-compose.yml       # 全栈部署
├── .env.example
├── start.ps1                # Windows 启动脚本
├── start.sh                 # Linux/macOS 启动脚本
└── README.md
```

## API 文档

启动后端后访问 http://localhost:8000/docs 查看 Swagger 文档。

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/chat | 发送消息 (SSE) |
| GET | /api/chat/history/{session_id} | 获取会话历史 |
| POST | /api/chat/session | 创建新会话 |
| GET | /api/chat/sessions | 获取会话列表 |
| POST | /api/knowledge/upload | 上传知识文档 |
| GET | /api/tools | 获取工具列表 |
| GET | /api/health | 健康检查 |

## MCP 工具

| 工具 | 功能 | 端口 |
|------|------|------|
| knowledge_server | 知识库检索 (Chroma) | 8001 |
| ticket_server | 工单创建与管理 | 8002 |
| order_server | 订单查询 | 8003 |
| human_server | 人工客服转接 | 8004 |

## Agent 工作流

```
用户输入 → 意图识别 → 路由决策 → MCP工具调用 → 回答生成
```

基于 LangGraph 的状态图实现，支持条件路由和工具循环调用。
