#!/bin/bash
# ============================================
# Linux/macOS 启动脚本
# ============================================
set -e

SKIP_DOCKER=false
SKIP_FRONTEND=false
SKIP_BACKEND=false
INSTALL_ONLY=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-docker) SKIP_DOCKER=true; shift ;;
    --skip-frontend) SKIP_FRONTEND=true; shift ;;
    --skip-backend) SKIP_BACKEND=true; shift ;;
    --install-only) INSTALL_ONLY=true; shift ;;
    *) echo "未知参数: $1"; exit 1 ;;
  esac
done

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "========================================"
echo "  智能客服 Agent 系统 - 启动脚本"
echo "========================================"
echo ""

# --- 检查前置条件 ---
echo "[1/6] 检查前置条件..."

if command -v python3 &> /dev/null; then
  echo "  ✓ Python: $(python3 --version)"
  PYTHON=python3
elif command -v python &> /dev/null; then
  echo "  ✓ Python: $(python --version)"
  PYTHON=python
else
  echo "  ✗ Python 未安装！"
  exit 1
fi

if command -v node &> /dev/null; then
  echo "  ✓ Node.js: $(node --version)"
else
  echo "  ✗ Node.js 未安装！"
  exit 1
fi

if [ "$SKIP_DOCKER" = false ]; then
  if command -v docker &> /dev/null; then
    echo "  ✓ Docker: $(docker --version)"
  else
    echo "  ⚠ Docker 未运行！将跳过 Docker Compose"
    SKIP_DOCKER=true
  fi
fi

echo ""

# --- Python 虚拟环境 ---
echo "[2/6] 配置 Python 虚拟环境..."

cd "$PROJECT_ROOT/backend"

if [ ! -d "venv" ]; then
  echo "  创建虚拟环境..."
  $PYTHON -m venv venv
fi

source venv/bin/activate
echo "  ✓ 虚拟环境已激活"

pip install --upgrade pip -q
echo "  ✓ pip 已升级"

echo ""

# --- 安装后端依赖 ---
echo "[3/6] 安装后端依赖..."
pip install -r requirements.txt -q
echo "  ✓ 后端依赖安装完成"

echo ""

# --- 安装前端依赖 ---
if [ "$SKIP_FRONTEND" = false ]; then
  echo "[4/6] 安装前端依赖..."
  cd "$PROJECT_ROOT/frontend"
  npm install --silent
  echo "  ✓ 前端依赖安装完成"
else
  echo "[4/6] 跳过前端依赖安装"
fi

echo ""

if [ "$INSTALL_ONLY" = true ]; then
  echo "========================================"
  echo "  依赖安装完成！"
  echo "========================================"
  exit 0
fi

# --- 启动 Docker Compose ---
if [ "$SKIP_DOCKER" = false ]; then
  echo "[5/6] 启动 Docker Compose..."
  cd "$PROJECT_ROOT"

  docker-compose up -d milvus mcp-knowledge mcp-ticket mcp-order mcp-human 2>/dev/null

  echo "  ⏳ 等待服务就绪..."

  for i in $(seq 1 30); do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
      echo "  ✓ MCP 服务已就绪"
      break
    fi
    echo "  等待 MCP 服务启动... ($i/30)"
    sleep 2
  done
else
  echo "[5/6] 跳过 Docker Compose"
fi

echo ""

# --- 启动后端 ---
if [ "$SKIP_BACKEND" = false ]; then
  echo "[6/6] 启动后端服务..."
  cd "$PROJECT_ROOT/backend"
  source venv/bin/activate

  # 后台启动
  nohup uvicorn main:app --host 0.0.0.0 --port 8000 > "$PROJECT_ROOT/logs/backend.log" 2>&1 &
  BACKEND_PID=$!
  echo "  ✓ 后端已启动 (PID: $BACKEND_PID, 端口: 8000)"
  sleep 2
fi

echo ""

# --- 启动前端 ---
if [ "$SKIP_FRONTEND" = false ]; then
  echo "🎨 启动前端开发服务器..."
  cd "$PROJECT_ROOT/frontend"
  npm run dev &
  FRONTEND_PID=$!
  echo "  ✓ 前端已启动 (PID: $FRONTEND_PID)"
fi

echo ""
echo "========================================"
echo "  系统启动完成！"
echo "========================================"
echo ""
echo "  前端: http://localhost:5173"
echo "  后端: http://localhost:8000/docs"
echo "  MCP Servers:"
echo "    knowledge_server: http://localhost:8001/info"
echo "    ticket_server:    http://localhost:8002/info"
echo "    order_server:     http://localhost:8003/info"
echo "    human_server:     http://localhost:8004/info"
echo ""

cd "$PROJECT_ROOT"
