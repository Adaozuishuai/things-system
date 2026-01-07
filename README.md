# 情报智探系统 (Intel Aggregation System)

**AI 驱动的实时情报采集与分析平台 (v2.0)**

本项目是一个端到端的现代化情报系统，能够自动从外部数据源（Payload CMS）采集情报，利用 LLM（Large Language Model）进行智能提炼（去噪、翻译、摘要、打标），并通过实时通道（SSE）推送给前端大屏展示。

**v2.0 新特性**: 新增用户认证、个性化设置、深色模式与收藏功能。

---

## 🚀 系统概述 (System Overview)

本系统旨在解决海量原始情报的**实时获取**与**高效处理**问题。

### 核心工作流
1.  **采集 (Ingestion)**: 自动轮询外部 CMS 系统，获取原始情报数据。
2.  **提炼 (Refinement)**: 利用 **Aliyun Qwen-Max** 模型对原始文本进行深度清洗、中文化翻译、摘要重写及智能打标。
3.  **分发 (Distribution)**: 通过 Server-Sent Events (SSE) 技术，将处理后的高价值情报毫秒级推送到前端界面。
4.  **交互 (Interaction)**: 用户可注册登录，收藏感兴趣的情报，并自定义界面主题（深色/浅色）。

---

## 🛠️ 技术栈 (Tech Stack)

### 后端 (Backend)
*   **Framework**: FastAPI (Python)
*   **AI Framework**: AgentScope (Multi-Agent Orchestration)
*   **LLM Provider**: DashScope (Aliyun Qwen-Max)
*   **Database**: PostgreSQL (JSONB Tags, User Data)
*   **Auth**: JWT + BCrypt
*   **Real-time**: Server-Sent Events (SSE)

### 前端 (Frontend)
*   **Framework**: React 18 + Vite
*   **Styling**: Tailwind CSS (Dark Mode Support)
*   **Language**: TypeScript
*   **State Management**: React Hooks + Context API (Auth)

---

## 📦 快速开始 (Getting Started)

### 1. 环境准备
*   **Python**: 3.8+
*   **Node.js**: 16+
*   **PostgreSQL**: 确保数据库服务已启动。

### 2. 启动后端
```bash
cd backend

# 创建并激活虚拟环境 (可选)
python -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量 (.env)
# 必须配置: DASHSCOPE_API_KEY, POSTGRES_URL, CMS_URL, SECRET_KEY (JWT)

# 启动服务
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 启动前端
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```
前端访问地址: `http://localhost:5173`

---

## 🧪 自动化测试 (Testing)

项目包含完整的测试套件，用于验证核心逻辑：

| 测试脚本 | 描述 |
| :--- | :--- |
| `backend/tests/test_auth_flow.py` | **认证集成测试**。验证注册、登录、Token 鉴权流程。 |
| `backend/tests/test_settings_flow.py` | **用户设置测试**。验证资料修改与数据库同步。 |
| `backend/tests/test_real_api_ingestion.py` | **全链路集成测试**。验证 CMS 抓取 -> AI 处理 -> DB 存储 -> API 查询的全过程。 |
| `backend/tests/test_agent_tags_generation.py` | **AI 解析测试**。验证 LLM 返回 JSON 的解析健壮性。 |

运行测试示例：
```bash
# 运行认证流程测试
python backend/tests/test_auth_flow.py
```

---

## 📂 项目结构概览

```
system_mvp/
├── backend/                # FastAPI 后端
│   ├── app/
│   │   ├── agent/          # AgentScope 智能体与编排
│   │   ├── services/       # 业务服务 (Auth, Poller)
│   │   ├── routes/         # API 路由 (Auth, Intel, Users)
│   │   └── db_models.py    # 数据库模型 (User, IntelItem)
│   └── tests/              # 全面测试套件
├── frontend/               # React 前端
│   ├── src/
│   │   ├── components/     # UI 组件 (支持 Dark Mode)
│   │   ├── context/        # 全局状态 (AuthContext)
│   │   ├── hooks/          # 逻辑复用 (useGlobalIntel)
│   │   └── pages/          # 页面视图 (Login, Settings, Intel)
└── PROJECT_REVIEW.md       # 详细的技术复盘文档
```
