# 情报智探系统 (Intel Aggregation System)

基于 React + FastAPI 构建的现代化情报聚合与 Agent 搜索演示系统。

## 项目结构

```
intel-agent-app/
├── backend/                # FastAPI 后端
│   ├── app/
│   │   ├── agent/         # Agent 编排逻辑 (Orchestrator)
│   │   ├── routes/        # API 路由
│   │   ├── models.py      # Pydantic 模型
│   │   ├── store.py       # 内存数据存储与 Mock 数据
│   │   └── main.py        # 入口文件
│   └── requirements.txt
└── frontend/               # React + Vite 前端
    ├── src/
    │   ├── components/    # UI 组件
    │   ├── hooks/         # 自定义 Hooks (useIntelQuery)
    │   ├── pages/         # 页面组件
    │   └── api.ts         # API 接口层
    └── package.json
```

## 快速开始

### 1. 启动后端 (Backend)

确保已安装 Python 3.8+。

```bash
cd backend
# 安装依赖
python3 -m pip install -r requirements.txt
# 启动服务
python3 -m uvicorn app.main:app --reload --port 8000
```

后端服务将运行在: `http://localhost:8000`
API 文档: `http://localhost:8000/docs`

### 2. 启动前端 (Frontend)

确保已安装 Node.js 16+。

```bash
cd frontend
npm install
npm run dev
```

前端页面将运行在: `http://localhost:5173`

## 功能特性

*   **Agent 搜索**: 模拟 "检索 -> 重排 -> 摘要 -> 标签 -> 生成回答" 的全流程，通过 SSE (Server-Sent Events) 实时流式输出进度。
*   **情报列表**: 支持按 "今日热点" / "历史情报" 筛选，支持时间范围过滤。
*   **交互功能**: 收藏/取消收藏，CSV 数据导出。
*   **Mock 数据**: 内置 50+ 条模拟数据，包含不同标签颜色和时间戳。

## 扩展指南

### 替换真实数据库
修改 `backend/app/store.py`。目前使用内存列表 `self.items`。
建议引入 `SQLAlchemy` 或 `Tortoise-ORM`，将 `get_intel` 等方法替换为 SQL 查询。

### 接入真实 LLM
修改 `backend/app/agent/orchestrator.py`。
在 `run_stream` 方法中，将 `asyncio.sleep` 模拟步骤替换为真实的 LangChain 或 OpenAI API 调用。
例如：
- Retrieve: 调用 VectorDB (Pinecone/Milvus)。
- Summarize: 调用 GPT-4 生成摘要。

### 鉴权 (Authentication)
在 `backend/app/main.py` 中添加 `OAuth2` 或 `JWT` 中间件。
前端在 `api.ts` 的 Axios 拦截器中添加 `Authorization` 头。
