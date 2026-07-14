# ============================================
# Windows 启动脚本
# 功能: 一键启动智能客服 Agent 系统
# ============================================

param(
    [switch]$SkipDocker,
    [switch]$SkipFrontend,
    [switch]$SkipBackend,
    [switch]$InstallOnly
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  智能客服 Agent 系统 - 启动脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# --- 检查前置条件 ---
Write-Host "[1/5] 检查前置条件..." -ForegroundColor Yellow

try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python 未安装！请安装 Python 3.10+" -ForegroundColor Red
    exit 1
}

try {
    $nodeVersion = node --version 2>&1
    Write-Host "  ✓ Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Node.js 未安装！请安装 Node.js 18+" -ForegroundColor Red
    exit 1
}

if (-not $SkipDocker) {
    try {
        $dockerVersion = docker --version 2>&1
        Write-Host "  ✓ Docker: $dockerVersion" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠ Docker 未运行！将跳过 Docker Compose" -ForegroundColor Yellow
        $SkipDocker = $true
    }
}

Write-Host ""

# --- Python 虚拟环境 ---
Write-Host "[2/5] 配置 Python 虚拟环境..." -ForegroundColor Yellow

Set-Location "$ProjectRoot\backend"

if (-not (Test-Path "venv")) {
    Write-Host "  创建虚拟环境..."
    python -m venv venv
}

& "$ProjectRoot\backend\venv\Scripts\Activate.ps1"
Write-Host "  ✓ 虚拟环境已激活" -ForegroundColor Green

python -m pip install --upgrade pip -q
Write-Host "  ✓ pip 已升级" -ForegroundColor Green

Write-Host ""

# --- 安装后端依赖 ---
Write-Host "[3/5] 安装后端依赖..." -ForegroundColor Yellow
pip install -r "$ProjectRoot\backend\requirements.txt" -q
Write-Host "  ✓ 后端依赖安装完成" -ForegroundColor Green

Write-Host ""

# --- 安装前端依赖 ---
if (-not $SkipFrontend) {
    Write-Host "[4/5] 安装前端依赖..." -ForegroundColor Yellow
    Set-Location "$ProjectRoot\frontend"
    npm install --silent
    Write-Host "  ✓ 前端依赖安装完成" -ForegroundColor Green
} else {
    Write-Host "[4/5] 跳过前端依赖安装" -ForegroundColor Yellow
}

Write-Host ""

if ($InstallOnly) {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  依赖安装完成！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    exit 0
}

# --- 启动 Docker Compose ---
if (-not $SkipDocker) {
    Write-Host "[5/5] 启动 Docker Compose..." -ForegroundColor Yellow
    Set-Location $ProjectRoot

    docker-compose up -d 2>&1 | Out-Null
    Write-Host "  ✓ Docker 服务已启动" -ForegroundColor Green
    Write-Host "  ⏳ 等待服务就绪 (10秒)..."
    Start-Sleep -Seconds 10
} else {
    Write-Host "[5/5] 跳过 Docker Compose" -ForegroundColor Yellow
}

Write-Host ""

# --- 启动后端 ---
if (-not $SkipBackend) {
    Write-Host "🚀 启动后端服务 (端口 8000)..." -ForegroundColor Yellow

    Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
cd '$ProjectRoot\backend'
.\venv\Scripts\Activate.ps1
Write-Host '🚀 后端 API 已启动: http://localhost:8000/docs' -ForegroundColor Green
python main.py
"@

    Write-Host "  ✓ 后端已启动" -ForegroundColor Green
    Start-Sleep -Seconds 3
}

# --- 启动前端 ---
if (-not $SkipFrontend) {
    Write-Host "🎨 启动前端服务 (端口 5173)..." -ForegroundColor Yellow

    Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
cd '$ProjectRoot\frontend'
Write-Host '🎨 前端已启动: http://localhost:5173' -ForegroundColor Green
npm run dev
"@

    Write-Host "  ✓ 前端已启动" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  系统启动完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  前端: http://localhost:5173" -ForegroundColor Cyan
Write-Host "  后端: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

Set-Location $ProjectRoot